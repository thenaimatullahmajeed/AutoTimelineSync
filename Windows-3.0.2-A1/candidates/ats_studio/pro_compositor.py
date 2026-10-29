"""CPU Qt compositor used unchanged by Pro preview and export.

QPainter samples full-resolution originals at floating-point crop coordinates. The
same RenderSpec and render_frame method serve both paths; preview only changes
the output size. This avoids another runtime dependency on the target machine.
"""

from __future__ import annotations

from collections import OrderedDict
from html import escape
import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QGuiApplication, QImage, QImageReader,
                           QPainter, QPainterPath, QPen, QRadialGradient, QTextDocument,
                           QFontMetricsF, QPolygonF, QTransform)

from .pro_spec import MOTION_PATHS, RenderSpec, ScenePlan, ease, load_preset
from .schema import PackageError


def _noise(seed: int, point: int) -> float:
    value = (seed ^ (point*0x9E3779B97F4A7C15)) & ((1 << 64)-1)
    value ^= value >> 30; value = value*0xBF58476D1CE4E5B9 & ((1 << 64)-1)
    value ^= value >> 27; value = value*0x94D049BB133111EB & ((1 << 64)-1)
    value ^= value >> 31
    return value / 2**64 * 2 - 1


def _smooth_noise(seed: int, frame: int, period: int) -> float:
    a, r = divmod(frame, period)
    t = r/period
    t = t*t*(3-2*t)
    return _noise(seed,a)*(1-t) + _noise(seed,a+1)*t


class ProCompositor:
    _app = None

    def __init__(self, spec: RenderSpec, images: dict[str, Path], settings,
                 width: int | None = None, height: int | None = None,
                 cache_limit_bytes: int = 1536 * 1024**2) -> None:
        if QGuiApplication.instance() is None:
            ProCompositor._app = QGuiApplication([])
        from .fonts import register_bundled_fonts
        register_bundled_fonts()
        self.spec, self.images, self.settings = spec, images, settings
        self.captions_visible = True
        self.width, self.height = width or settings.width, height or settings.height
        self._image_cache: OrderedDict[str, QImage] = OrderedDict()
        self._soft_cache: OrderedDict[tuple[str,int], QImage] = OrderedDict()
        self._soft_bytes = 0
        self._image_bytes = 0
        self._image_limit = cache_limit_bytes
        self._look_cache: dict[str, dict] = {}
        self._caption_cache: OrderedDict[tuple, QTextDocument] = OrderedDict()
        self._creator_caption_cache = OrderedDict()
        self._scene_ends = [s.end_frame for s in spec.scenes]
        self._layers = None
        if spec.layers:
            from .layer_compositor import LayerCompositor
            self._layers=LayerCompositor(spec,images,self.width,self.height)
            self._layers.note_provider=self._photo_notes

    def _image(self, image_id: str) -> QImage:
        if image_id in self._image_cache:
            self._image_cache.move_to_end(image_id)
            return self._image_cache[image_id]
        path = self.images[image_id]
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            raise PackageError(f"Scene image {path.name} cannot be decoded: {reader.errorString()}")
        image = image.convertToFormat(QImage.Format_RGB888)
        size = image.sizeInBytes()
        while self._image_cache and self._image_bytes + size > self._image_limit:
            _, evicted = self._image_cache.popitem(last=False)
            self._image_bytes -= evicted.sizeInBytes()
        self._image_cache[image_id] = image
        self._image_bytes += size
        return image

    def _soft_source(self, plan: ScenePlan, image: QImage) -> QImage:
        if plan.look not in self._look_cache:
            self._look_cache[plan.look]=load_preset("looks",plan.look)
        amount=self._look_cache[plan.look].get("soften",0)*plan.look_intensity
        if amount<=0:
            return image
        key=(plan.image_id,round(amount*100))
        if key in self._soft_cache:
            self._soft_cache.move_to_end(key)
            return self._soft_cache[key]
        small=image.scaled(max(1,image.width()//4),max(1,image.height()//4),
                           Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
        blurred=small.scaled(image.width(),image.height(),Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
        result=image.copy()
        painter=QPainter(result)
        painter.setOpacity(min(.35,amount))
        painter.drawImage(0,0,blurred)
        painter.end()
        while self._soft_cache and self._soft_bytes+result.sizeInBytes()>256*1024**2:
            _,evicted=self._soft_cache.popitem(last=False)
            self._soft_bytes-=evicted.sizeInBytes()
        self._soft_cache[key]=result
        self._soft_bytes+=result.sizeInBytes()
        return result

    def _motion(self, plan: ScenePlan, global_frame: float, image: QImage) -> QRectF:
        definition = MOTION_PATHS[plan.motion]
        raw = max(0.0,(global_frame-plan.first_frame)/max(1, plan.frames-1))
        mode = plan.motion_config.get("ease", definition[6])
        progress = ease(min(1.0,raw),mode)
        if raw > 1:
            velocity = (ease(.98,mode)-ease(.90,mode))/.08
            extra = min(.10,raw-1)
            progress = min(1.12, 1+extra*max(.35,velocity)*(1-extra/.2))
        z0 = plan.motion_config.get("zoom_from",definition[0])
        z1 = plan.motion_config.get("zoom_to",definition[1])
        zoom = max(1.0,min(2.0,z0+(z1-z0)*progress))
        if plan.motion == "TINY_PUNCH_IN" and not plan.motion_config.get("ease"):
            progress = ease(min(1,raw/.35),"EASE_OUT")
            zoom = z0+(z1-z0)*progress
        if (getattr(self.settings,"product_version",0)!=3 and self.spec.auto_direct and not self.spec.strict_json and not plan.motion_config.get('director') and
            self.spec.package.pro.get("auto_direct",{}).get("pattern_interrupt",True) and
            plan.frames > round(3.5*self.spec.package.fps)):
            middle=plan.first_frame+plan.frames//2
            distance=abs(global_frame-middle)
            if distance<4:
                zoom += .015*(1-distance/4)
        dx = definition[2]+(definition[4]-definition[2])*progress
        dy = definition[3]+(definition[5]-definition[3])*progress
        if self.settings.shake:
            handheld = plan.motion_config.get("shake",
                self.settings.shake_strength/100+self.spec.style.get("handheld",0))
            dx += _smooth_noise(self.spec.seed+17,int(global_frame),9)*handheld*.20
            dy += _smooth_noise(self.spec.seed+29,int(global_frame),11)*handheld*.20
            zoom = max(zoom,1+handheld*.025)
        source_ratio = image.width()/image.height()
        output_ratio = self.width/self.height
        if self.settings.framing == "Fit Entire Image":
            base_w,base_h = image.width(),image.height()
        elif source_ratio > output_ratio:
            base_h=image.height(); base_w=base_h*output_ratio
        else:
            base_w=image.width(); base_h=base_w/output_ratio
        crop_w,crop_h = base_w/zoom,base_h/zoom
        room_x=max(0,image.width()-crop_w)
        room_y=max(0,image.height()-crop_h)
        cx=image.width()*plan.focus_x + dx*room_x*.6
        cy=image.height()*plan.focus_y + dy*room_y*.6
        x=max(0,min(image.width()-crop_w,cx-crop_w/2))
        y=max(0,min(image.height()-crop_h,cy-crop_h/2))
        return QRectF(x,y,crop_w,crop_h)

    def _scene_frame(self, plan: ScenePlan, global_frame: float) -> QImage:
        source = self._soft_source(plan,self._image(plan.image_id))
        source = self._photo_notes(plan, source, global_frame)
        out = QImage(self.width,self.height,QImage.Format_RGB888)
        out.fill(QColor("black"))
        painter = QPainter(out)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        samples=1
        if self.settings.quality_tier=="MAX" and plan.motion!="STATIC":
            samples=4
        elif (self.settings.quality_tier=="STANDARD" and
              plan.motion=="TINY_PUNCH_IN" and
              global_frame-plan.first_frame<plan.frames*.35):
            samples=2
        if "blur" in plan.motion_config:
            blur=plan.motion_config["blur"]
            samples=1 if blur==0 else max(2,round(4*blur))
        for index in range(samples):
            sample_frame=global_frame-(samples-index-1)/samples
            crop=self._motion(plan,sample_frame,source)
            if self.settings.framing == "Fit Entire Image":
                scale=min(self.width/crop.width(),self.height/crop.height())
                dest=QRectF((self.width-crop.width()*scale)/2,(self.height-crop.height()*scale)/2,
                            crop.width()*scale,crop.height()*scale)
            else:
                dest=QRectF(0,0,self.width,self.height)
            painter.setOpacity(1/(index+1))
            painter.drawImage(dest,source,crop)
        painter.end()
        return out

    def _transition(self, outgoing: QImage, incoming: QImage, plan: ScenePlan,
                    t: float, frame: int) -> QImage:
        kind=plan.transition_applied
        amount=ease(t,plan.transition_ease)
        from .cinematic_transitions import KINDS, draw_transition
        if kind in KINDS:
            return draw_transition(outgoing,incoming,kind,amount,self.spec.seed,self.settings.visual_director)
        if amount>=1:return incoming.copy()
        if amount<=0:return outgoing.copy()
        if kind=='DISSOLVE':kind='CROSSFADE'
        if kind in {"GENTLE_DISSOLVE","DISSOLVE_BLUR"}:
            blur_factor=(.10 if kind=="GENTLE_DISSOLVE" else .24)*math.sin(math.pi*amount)
            if blur_factor>.01:
                divisor=1+round(blur_factor*20)
                outgoing=outgoing.scaled(max(1,self.width//divisor),max(1,self.height//divisor),
                    Qt.IgnoreAspectRatio,Qt.SmoothTransformation).scaled(
                    self.width,self.height,Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
                incoming=incoming.scaled(max(1,self.width//divisor),max(1,self.height//divisor),
                    Qt.IgnoreAspectRatio,Qt.SmoothTransformation).scaled(
                    self.width,self.height,Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
        out=QImage(self.width,self.height,QImage.Format_RGB888)
        out.fill(Qt.black)
        p=QPainter(out)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        full=QRectF(0,0,self.width,self.height)
        if kind in {"CROSSFADE","GENTLE_DISSOLVE","DISSOLVE_BLUR"}:
            p.drawImage(full,outgoing)
            p.setOpacity(amount);p.drawImage(full,incoming);p.setOpacity(1)
        elif kind in {"FADE_THROUGH_BLACK","FADE_THROUGH_WHITE"}:
            p.fillRect(full,Qt.white if kind.endswith("WHITE") else Qt.black)
            p.setOpacity(max(0,1-2*amount));p.drawImage(full,outgoing)
            p.setOpacity(max(0,2*amount-1));p.drawImage(full,incoming)
            p.setOpacity(1)
        elif kind in {"QUICK_PUSH","WHIP_PAN","SLIDE_SHADOW"}:
            horizontal=plan.direction not in {"UP","DOWN"}
            sign=-1 if plan.direction in {"LEFT","UP","AUTO"} else 1
            span=self.width if horizontal else self.height
            shift=sign*span*amount
            rect_old=QRectF(shift if horizontal else 0,shift if not horizontal else 0,self.width,self.height)
            rect_new=QRectF(shift-sign*span if horizontal else 0,
                             shift-sign*span if not horizontal else 0,self.width,self.height)
            p.drawImage(rect_old,outgoing);p.drawImage(rect_new,incoming)
            if kind == "SLIDE_SHADOW":
                edge=rect_new.right() if sign<0 and horizontal else rect_new.left()
                p.fillRect(QRectF(edge-7,0,14,self.height),QColor(0,0,0,80))
        elif kind == "ZOOM_THROUGH":
            p.drawImage(QRectF(-self.width*amount*.3,-self.height*amount*.3,
                self.width*(1+amount*.6),self.height*(1+amount*.6)),outgoing)
            p.setOpacity(amount)
            z=1.25-.25*amount
            p.drawImage(QRectF((1-z)*self.width/2,(1-z)*self.height/2,self.width*z,self.height*z),incoming)
            p.setOpacity(1)
        elif kind in {"IRIS_WIPE","INK_WIPE","BRUSH_WIPE","PAPER_TEAR"}:
            p.drawImage(full,outgoing)
            clip=QPainterPath()
            if kind=="IRIS_WIPE":
                radius=math.hypot(self.width,self.height)*amount
                clip.addEllipse(QPointF(plan.focus_x*self.width,plan.focus_y*self.height),radius,radius)
            else:
                x=self.width*amount
                clip.moveTo(0,0)
                for y in range(0,self.height+24,24):
                    jitter=_noise(self.spec.seed+frame,y//24)*self.width*(.018 if kind=="PAPER_TEAR" else .04)
                    clip.lineTo(max(0,min(self.width,x+jitter)),y)
                clip.lineTo(0,self.height);clip.closeSubpath()
            p.setClipPath(clip);p.drawImage(full,incoming);p.setClipping(False)
        else:
            p.drawImage(full,outgoing);p.setOpacity(amount);p.drawImage(full,incoming);p.setOpacity(1)
            if kind in {"LIGHT_LEAK_FLASH","FILM_BURN"}:
                alpha=int(150*math.sin(math.pi*amount))
                p.fillRect(full,QColor(255,137 if kind=="FILM_BURN" else 204,51,alpha))
        p.end()
        return out

    def _look(self, image: QImage, name: str, intensity: float, frame: int) -> None:
        if intensity <= 0 or name=="CLEAN":
            return
        if name not in self._look_cache:
            self._look_cache[name]=load_preset("looks",name)
        look=self._look_cache[name]
        weave=look.get("weave",0)*intensity if self.settings.shake else 0
        if weave:
            source=image.copy()
            offset=_smooth_noise(self.spec.seed+111,frame,7)*weave*8
            weave_painter=QPainter(image)
            weave_painter.drawImage(QRectF(offset,0,self.width,self.height),source)
            weave_painter.end()
        p=QPainter(image)
        p.setRenderHint(QPainter.Antialiasing)
        warm=look["warm"]*intensity
        if warm:
            color=QColor(229,146,70,int(abs(warm)*110)) if warm>0 else QColor(44,119,184,int(abs(warm)*110))
            p.fillRect(image.rect(),color)
        mono=look["monochrome"]*intensity
        if mono:
            gray=image.convertToFormat(QImage.Format_Grayscale8)
            p.setOpacity(min(1,mono));p.drawImage(0,0,gray);p.setOpacity(1)
        vignette=look["vignette"]*intensity
        if vignette:
            gradient=QRadialGradient(self.width/2,self.height/2,math.hypot(self.width,self.height)*.55)
            gradient.setColorAt(0,QColor(0,0,0,0));gradient.setColorAt(1,QColor(0,0,0,int(210*vignette)))
            p.fillRect(image.rect(),QBrush(gradient))
        grain=(look["grain"]*intensity)+(self.settings.noise_strength/200 if self.settings.noise else 0)
        if grain:
            count=int(self.width*self.height/1100*grain)
            p.setPen(Qt.NoPen)
            for i in range(count):
                x=int((_noise(self.spec.seed+frame*37,i*2)+1)*.5*self.width)
                y=int((_noise(self.spec.seed+frame*37,i*2+1)+1)*.5*self.height)
                p.fillRect(x,y,2,2,QColor(255,255,255,24))
        if name=="VHS_1980S":
            p.fillRect(image.rect(),QColor(20,18,37,18))
            for y in range(frame%5,self.height,5):
                p.fillRect(0,y,self.width,1,QColor(0,0,0,15))
        if name in {"SILENT_FILM_1910S","NITRATE_1930S"}:
            flicker=_smooth_noise(self.spec.seed+7,frame,5)
            if flicker>0:p.fillRect(image.rect(),QColor(255,255,255,int(11*flicker*intensity)))
            else:p.fillRect(image.rect(),QColor(0,0,0,int(-11*flicker*intensity)))
        p.end()

    def _caption_document(self, text: str, active: int, width: int, animation: str,
                          emphasized: tuple[int,...] = ()) -> QTextDocument:
        from .project_settings import CaptionSettings
        options=self.spec.package.pro.get("caption_style",{})
        preset=options.get("preset",self.settings.caption_preset)
        max_lines=options.get("max_lines",self.settings.caption_max_lines)
        key=(text,active,width,preset,self.settings.caption_font,self.settings.caption_size,max_lines,
             self.settings.caption_text_color,self.settings.caption_highlight_color,emphasized)
        if key in self._caption_cache:
            self._caption_cache.move_to_end(key);return self._caption_cache[key]
        tokens=text.split()
        style=CaptionSettings(preset=preset,text_size=self.settings.caption_size,max_lines=max_lines,
                              font_family=self.settings.caption_font)
        accent=self.settings.caption_highlight_color or style.highlight_color() or self.settings.caption_text_color
        size,split=style.text_layout(tokens,width,self.height)
        pieces=[]
        for i,token in enumerate(tokens):
            if split==i:pieces.append("<br>")
            pieces.append(f'<span style="color:{accent};font-weight:bold">{escape(token)}</span>'
                          if i==active or i in emphasized else escape(token))
        html=" ".join(pieces)
        document=QTextDocument()
        from .fonts import resolve_font_family
        family=resolve_font_family(self.settings.caption_font)
        font=QFont(family)
        font.setPixelSize(size)
        font.setBold(preset not in {"Minimal Documentary","Clean Subtitle","Typewriter"})
        font.setItalic(preset=="Cinematic Story")
        document.setDefaultFont(font);document.setDocumentMargin(0)
        document.setTextWidth(width)
        css=(f"color:{self.settings.caption_text_color};font-family:'{escape(family)}';"
             f"font-size:{size}px;font-weight:{'bold' if font.bold() else 'normal'};"
             f"font-style:{'italic' if font.italic() else 'normal'}")
        document.setHtml(f'<div align="center" style="{css}">{html}</div>')
        document.setTextWidth(min(width, math.ceil(document.idealWidth()+2)))
        self._caption_cache[key]=document
        while len(self._caption_cache)>96:self._caption_cache.popitem(last=False)
        return document

    def _captions(self, image: QImage, frame: int) -> None:
        if not self.captions_visible:
            return
        caption_options=self.spec.package.pro.get("caption_style",{})
        if caption_options.get("preset",self.settings.caption_preset)=="Off" or not self.spec.package.captions_enabled:
            return
        caption=next((c for c in self.spec.captions if c.start_frame<=frame<c.end_frame),None)
        if not caption:return
        active=next((i for i,(start,end,_word) in enumerate(caption.words) if start<=frame<end),-1)
        if not self.spec.package.highlight_current_word:active=-1
        emphasis=caption_options.get("emphasis")
        if emphasis is None and self.spec.auto_direct:
            emphasized=tuple(i for i,(_start,_end,text) in enumerate(caption.words)
                             if any(c.isdigit() for c in text) or text.isupper())
        else:
            emphasis=set(emphasis or [])
            word_index={(round(w.start*self.spec.package.fps),round(w.end*self.spec.package.fps),w.text):w.index
                        for w in self.spec.package.words}
            emphasized=tuple(i for i,word in enumerate(caption.words) if word_index.get(word) in emphasis)
        text=caption.text
        from .caption_presets import NEW_CAPTION_PRESETS, render_caption
        preset=caption_options.get('preset',self.settings.caption_preset)
        if preset in NEW_CAPTION_PRESETS:
            render_caption(image,caption,frame,self.spec.package.fps,preset,self.settings,
                           active,emphasized,self._creator_caption_cache)
            return
        if caption_options.get("preset",self.settings.caption_preset)=="Typewriter":
            visible=max(1,sum(start<=frame for start,_end,_word in caption.words))
            text=" ".join(word for _start,_end,word in caption.words[:visible])
        width=int(self.width*(.76 if self.height>self.width else .86))
        animation=caption_options.get("animation",self.settings.caption_animation)
        document=self._caption_document(text,active,width,animation,emphasized)
        width=math.ceil(document.size().width())
        text_h=document.size().height()
        zone=caption_options.get("safe_zone",self.settings.caption_safe_zone)
        portrait=zone=="PORTRAIT_9_16" or (zone=="AUTO" and self.height>self.width)
        position=self.settings.caption_position
        if position=="Custom":y=self.height*self.settings.caption_custom_y/100-text_h/2
        elif position=="Top":y=self.height*.22-text_h/2
        elif position=="Center":y=self.height*.5-text_h/2
        else:y=self.height*(.63 if portrait else .78)-text_h/2
        if portrait:y=max(self.height*.1,min(y,self.height*.80-text_h))
        else:y=max(self.height*self.settings.caption_safe_margin/100,min(y,self.height*(1-self.settings.caption_safe_margin/100)-text_h))
        x=(self.width-width)/2
        p=QPainter(image);p.setRenderHint(QPainter.Antialiasing)
        age=frame-caption.start_frame
        if animation=="POP" and age<5:
            scale=(.92+(.12*ease(age/4,"EASE_OUT"))) if age<4 else 1
            p.translate(self.width/2,y+text_h/2);p.scale(scale,scale)
            p.translate(-self.width/2,-y-text_h/2)
        elif animation=="FADE" and age<6:
            p.setOpacity(max(.1,age/5))
        if self.settings.caption_background in {"Dark Brush","Solid Box","Paper"}:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(244,238,216,226) if self.settings.caption_background=="Paper" else QColor(3,7,12,165))
            p.drawRoundedRect(QRectF(x-12,y-5,width+24,text_h+10),6,6)
        layer=QImage(width,max(1,math.ceil(text_h)),QImage.Format_ARGB32_Premultiplied)
        layer.fill(Qt.transparent)
        lp=QPainter(layer);document.drawContents(lp);lp.end()
        dark=layer.copy()
        dp=QPainter(dark);dp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        dp.fillRect(dark.rect(),Qt.black);dp.end()
        opacity=p.opacity()
        if self.settings.caption_shadow_on and self.settings.caption_shadow:
            p.setOpacity(opacity*self.settings.caption_shadow/100*.8)
            offset=max(1,round(self.height*.002))
            p.drawImage(QPointF(x+offset,y+offset),dark);p.setOpacity(opacity)
        if self.settings.caption_outline_on and self.settings.caption_outline:
            radius=max(1,round(self.height*.0015*self.settings.caption_outline/100))
            for dx,dy in ((-radius,0),(radius,0),(0,-radius),(0,radius),
                          (-radius,-radius),(-radius,radius),(radius,-radius),(radius,radius)):
                p.drawImage(QPointF(x+dx,y+dy),dark)
        p.drawImage(QPointF(x,y),layer)
        p.end()

    def _photo_notes(self, plan: ScenePlan, source: QImage, frame: float) -> QImage:
        """Place ink on a source-image quad before camera motion and grading."""
        items=[item for item in self.spec.overlays if item.get("type")=="PHOTO_NOTE"
               and item.get("scene_id")==plan.id
               and item.get("start",0)<=frame/self.spec.package.fps<item.get("end",0)]
        if not items:
            return source
        result=source.copy()
        for item in items:
            quad=QPolygonF([QPointF(x*source.width(),y*source.height()) for x,y in item["points"]])
            tile=QImage(800,360,QImage.Format_ARGB32_Premultiplied);tile.fill(Qt.transparent)
            painter=QPainter(tile);painter.setRenderHint(QPainter.TextAntialiasing)
            font=QFont("Caveat");font.setPixelSize(110);font.setWeight(QFont.DemiBold)
            lines=str(item.get("text","")).splitlines()
            while font.pixelSize()>22:
                metrics=QFontMetricsF(font)
                if max((metrics.horizontalAdvance(line) for line in lines),default=0)<=760 and metrics.height()*len(lines)<=330:
                    break
                font.setPixelSize(font.pixelSize()-2)
            painter.setFont(font);painter.setPen(QColor(43,35,31,235))
            painter.drawText(QRectF(20,10,760,340),Qt.AlignCenter,str(item.get("text","")))
            painter.end()
            transform=QTransform()
            if QTransform.quadToQuad(QPolygonF([QPointF(0,0),QPointF(800,0),QPointF(800,360),QPointF(0,360)]),quad,transform):
                painter=QPainter(result);painter.setRenderHint(QPainter.SmoothPixmapTransform)
                painter.setTransform(transform);painter.drawImage(0,0,tile);painter.end()
        return result

    def _overlays(self, image: QImage, frame: int) -> None:
        seconds=frame/self.spec.package.fps
        for item in self.spec.overlays:
            if not item.get("start",0)<=seconds<item.get("end",0):continue
            kind=item.get("type","TEXT")
            if kind=="PHOTO_NOTE":
                continue
            style=item.get("style","PLAIN")
            age=seconds-item.get("start",0)
            progress=min(1,max(0,age/max(.001,item.get("end",seconds+.001)-item.get("start",0))))
            x=float(item.get("x",.5))*self.width;y=float(item.get("y",.2))*self.height
            p=QPainter(image);p.setRenderHint(QPainter.Antialiasing)
            accent=QColor("#e8a33d" if style=="ARCHIVE" else "#9af01c" if style=="MODERN" else "#f6eddc")
            p.setPen(accent);font=QFont("Source Code Pro" if kind=="DATE_STAMP" else "DejaVu Sans")
            font.setPixelSize(max(15,round(self.height*.035)));font.setBold(kind in {"HOOK_CARD","DATE_STAMP"})
            p.setFont(font)
            if kind in {"HOOK_CARD","LOWER_THIRD","DATE_STAMP"}:
                font.setFamily("DejaVu Sans");font.setPixelSize(max(15,round(self.height*.032)))
                p.setFont(font);metrics=QFontMetricsF(font)
                max_width=self.width*.62
                texts=[str(item.get("text","")),str(item.get("text2",""))]
                while max(metrics.horizontalAdvance(t) for t in texts)>max_width and font.pixelSize()>12:
                    font.setPixelSize(font.pixelSize()-1);p.setFont(font);metrics=QFontMetricsF(font)
                pad=max(8,self.height*.014)
                bw=max(metrics.horizontalAdvance(t) for t in texts)+pad*2
                bh=metrics.height()*(2 if texts[1] else 1)+pad*2
                box=QRectF(max(pad,min(x-bw/2,self.width-bw-pad)),max(pad,min(y-bh/2,self.height-bh-pad)),bw,bh)
                p.setPen(Qt.NoPen);p.setBrush(QColor(8,12,16,155));p.drawRoundedRect(box,pad*.6,pad*.6)
                p.setPen(QColor("#f6eddc"));p.setBrush(Qt.NoBrush)
                text=str(item.get("text",""))
                if kind=="DATE_STAMP":text=text[:max(1,round(len(text)*min(1,age/.8)))]
                line_box=QRectF(box.left()+pad,box.top()+pad,box.width()-pad*2,metrics.height())
                p.drawText(line_box,Qt.AlignCenter,text)
                if item.get("text2"):
                    line_box.translate(0,metrics.height());p.setPen(QColor("#c7c2b6"))
                    p.drawText(line_box,Qt.AlignCenter,str(item["text2"]))
            elif kind=="HIGHLIGHT_BOX":
                p.setPen(QPen(QColor("#e8a33d"),max(2,self.width//250)))
                region=QRectF(x,y,float(item.get("w",.2))*self.width,float(item.get("h",.1))*self.height)
                if style=="CIRCLE":p.drawEllipse(region)
                elif style=="ARROW":
                    p.drawLine(region.topLeft(),region.bottomRight())
                    tip=region.bottomRight()
                    p.drawLine(tip,QPointF(tip.x()-self.width*.02,tip.y()))
                    p.drawLine(tip,QPointF(tip.x(),tip.y()-self.height*.02))
                else:p.drawRect(region)
            elif kind=="MAP_ROUTE":
                pts=item.get("points",[])
                p.setPen(QPen(QColor("#e8a33d"),max(2,self.width//250)))
                count=max(0,len(pts)-1)
                for index,(a,b) in enumerate(zip(pts,pts[1:])):
                    part=max(0,min(1,progress*count-index))
                    if part:
                        end=QPointF((a[0]+(b[0]-a[0])*part)*self.width,
                                    (a[1]+(b[1]-a[1])*part)*self.height)
                        p.drawLine(QPointF(a[0]*self.width,a[1]*self.height),end)
            else:
                p.drawText(QRectF(x-self.width*.3,y,self.width*.6,self.height*.12),Qt.AlignCenter,str(item.get("text","")))
            p.end()

    def render_frame(self, frame: int) -> QImage:
        import bisect
        frame=max(0,min(self.spec.package.total_frames-1,frame))
        i=min(len(self.spec.scenes)-1,bisect.bisect_right(self._scene_ends,frame))
        scene=self.spec.scenes[i]
        incoming=self._scene_frame(scene,frame)
        if i and scene.transition_frames and frame<scene.first_frame+scene.transition_frames:
            old=self._scene_frame(self.spec.scenes[i-1],frame)
            t=(frame-scene.first_frame+1)/scene.transition_frames
            incoming=self._transition(old,incoming,scene,t,frame)
        self._look(incoming,scene.look,scene.look_intensity,frame)
        composition=self.spec.package.pro.get('composition',{})
        if composition.get('show_plates',True) is False:
            p=QPainter(incoming)
            if 'gradient' in composition:
                gradient=QRadialGradient(self.width*.5,self.height*.48,max(self.width,self.height)*.6)
                gradient.setColorAt(0,QColor(composition.get('background','#E5E5E5')));gradient.setColorAt(1,QColor(composition['gradient']))
                p.fillRect(incoming.rect(),QBrush(gradient))
            else:p.fillRect(incoming.rect(),QColor(composition.get('background','#E5E5E5')))
            p.end()
        if self._layers:
            def plate_transform(scene_id):
                if scene_id!=scene.id:return None
                image=self._image(scene.image_id);crop=self._motion(scene,frame,image)
                transform=QTransform();transform.translate(-crop.x()/crop.width()*self.width,-crop.y()/crop.height()*self.height)
                transform.scale(image.width()/crop.width(),image.height()/crop.height());return transform
            self._layers.draw(incoming,frame,plate_transform)
        self._overlays(incoming,frame)
        self._captions(incoming,frame)
        ending=self.spec.package.pro.get("ending",{})
        if ending.get("mode")=="FADE_OUT":
            length=ending.get("frames",15)
            remaining=self.spec.package.total_frames-frame
            if length and remaining<=length:
                p=QPainter(incoming)
                p.fillRect(incoming.rect(),QColor(0,0,0,round(255*(1-remaining/length))))
                p.end()
        return incoming
