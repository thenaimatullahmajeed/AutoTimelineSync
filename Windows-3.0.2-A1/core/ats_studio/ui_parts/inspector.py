"""Reference-sized optional inspector; product settings and render logic are unchanged."""
from PySide6.QtCore import Signal,Qt,QRectF,QPropertyAnimation,QEasingCurve
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QStackedWidget,QPushButton,QGraphicsOpacityEffect,QSizePolicy
from PySide6.QtGui import QPainter,QColor,QPen,QPainterPath,QImage
from ..product import PRESETS
from .common import pixel_font,text_label,button,scroll,ClickSlider,ClickCombo,Segmented,Accordion,reduced_motion

class CaptionCard(QPushButton):
    def __init__(self,title,preset):
        super().__init__();self.title,self.preset=title,preset;self.setCheckable(True);self.setFixedHeight(66)
        self.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);self.setToolTip(preset);self.setAccessibleName(title+' caption style')
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);rect=QRectF(self.rect()).adjusted(.75,.75,-.75,-.75)
        path=QPainterPath();path.addRoundedRect(rect,12,12);p.setClipPath(path)
        p.fillRect(self.rect(),QColor('#15181D'));p.fillRect(QRectF(0,0,self.width(),40),QColor('#0B0D10'))
        font=pixel_font(12,800);p.setFont(font);fm=p.fontMetrics();y=25
        def runs(first,second,color,box=False):
            gap=4;total=fm.horizontalAdvance(first)+gap+fm.horizontalAdvance(second)+(10 if box else 0);x=(self.width()-total)/2
            p.setPen(QColor('#FFFFFF'));p.drawText(round(x),y,first);x+=fm.horizontalAdvance(first)+gap
            if box:
                p.setPen(Qt.NoPen);p.setBrush(QColor(color));p.drawRoundedRect(QRectF(x-2,13,fm.horizontalAdvance(second)+10,16),4,4);p.setPen(QColor('#FFFFFF'));p.drawText(round(x+3),y,second)
            else:p.setPen(QColor(color));p.drawText(round(x),y,second)
        if self.title=='Hormozi':runs('BIG','IDEA','#FFE600')
        elif self.title=='Viral Pop':
            p.save();p.translate(self.width()/2,20);p.rotate(-3);p.translate(-self.width()/2,-20);runs('WOW','NOW','#FF2D2D');p.restore()
        elif self.title=='Karaoke':runs('the','idea','#8A2BE2',True)
        elif self.title=='Neon Glow':
            if not hasattr(self,'glow') or self.glow.width()!=self.width():
                from PIL import Image,ImageFilter
                mask=QImage(self.width(),40,QImage.Format_RGBA8888);mask.fill(Qt.transparent);ink=QPainter(mask);ink.setFont(font);ink.setPen(QColor('#FFFFFF'));ink.drawText(QRectF(0,0,self.width(),40),Qt.AlignCenter,'NEON');ink.end()
                alpha=Image.frombytes('RGBA',(mask.width(),40),bytes(mask.constBits())).getchannel('A');glow=Image.new('RGBA',(mask.width(),40))
                for radius in (8,4):
                    layer=Image.new('RGBA',glow.size,(0,240,255,0));layer.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius)));glow=Image.alpha_composite(glow,layer)
                self.glow=QImage(glow.tobytes(),glow.width,40,QImage.Format_RGBA8888).copy()
            p.drawImage(0,0,self.glow)
            p.setPen(QColor('#FFFFFF'));p.drawText(QRectF(0,0,self.width(),40),Qt.AlignCenter,'NEON')
        elif self.title=='Highlighter':
            p.setPen(Qt.NoPen);p.setBrush(QColor('#FFE600'));p.drawRoundedRect(QRectF(self.width()/2-15,12,30,17),4,4);p.setPen(QColor('#000000'));p.drawText(QRectF(0,0,self.width(),40),Qt.AlignCenter,'TIP')
        elif self.title=='Documentary':runs('The','idea','#A3E635')
        else:
            p.setFont(pixel_font(12,400 if self.title=='Cinematic' else 500));p.setPen(QColor('#C9CFD8' if self.title=='Cinematic' else '#E8EAED'))
            p.drawText(QRectF(0,0,self.width(),40),Qt.AlignCenter,{'Cinematic':'quiet idea','Typewriter':'the idea_'}.get(self.title,'The idea'))
        name_font=pixel_font(11,500);p.setFont(name_font)
        if p.fontMetrics().horizontalAdvance(self.title)>self.width()-16:name_font.setStretch(90);p.setFont(name_font)
        p.setPen(QColor('#E8EAED'));p.drawText(QRectF(8,46,self.width()-16,14),Qt.AlignLeft|Qt.AlignVCenter,self.title)
        p.setClipping(False);p.setPen(QPen(QColor('#A3E635' if self.isChecked() else '#232830'),1.5));p.setBrush(Qt.NoBrush);p.drawRoundedRect(rect,12,12);p.end()

class ScriptSwitch(QWidget):
    """Read-only script state; it never invents engine/JSON override keys."""
    def __init__(self,parent=None):super().__init__(parent);self.on=True;self.setFixedSize(44,26);self.setToolTip('From script — change this in your ChatGPT package.')
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.setPen(Qt.NoPen);p.setBrush(QColor('#A3E635' if self.on else '#3A424F'));p.drawRoundedRect(QRectF(self.rect()),13,13)
        p.setBrush(QColor('#10130A'));p.drawEllipse(QRectF(21 if self.on else 3,3,20,20));p.end()

class MomentRow(QWidget):
    def __init__(self,title,detail,height=52):
        super().__init__();self.setFixedHeight(height);self.setObjectName('momentRow');self.setAttribute(Qt.WA_StyledBackground,True);self.setStyleSheet('QWidget#momentRow{background:#15181D;border:1px solid #232830;border-radius:12px;}')
        h=QHBoxLayout(self);h.setContentsMargins(14,10,14,10);h.setSpacing(12);v=QVBoxLayout();v.setSpacing(0)
        v.addWidget(text_label(title,14,700));self.detail=text_label(detail,12,400,'#8B93A1');self.detail.setWordWrap(True);v.addWidget(self.detail);h.addLayout(v,1)
        self.switch=ScriptSwitch();h.addWidget(self.switch)

class Inspector(QWidget):
    changed=Signal(str,object);reset_requested=Signal();currentChanged=Signal(int)
    def __init__(self,parent=None):
        super().__init__(parent);self.setObjectName('inspector');self.setAttribute(Qt.WA_StyledBackground,True);self.setFixedWidth(320);self.buttons={};self.updating=False
        root=QVBoxLayout(self);root.setContentsMargins(25,20,24,20);root.setSpacing(12)
        self.tabs=Segmented(['Captions','Look','Sound']);root.addWidget(self.tabs)
        self.stack=QStackedWidget();root.addWidget(self.stack,1);self.tabs.currentIndexChanged.connect(self.setCurrentIndex)
        captions=QWidget();v=QVBoxLayout(captions);v.setContentsMargins(0,0,0,0);v.setSpacing(12)
        title=QHBoxLayout();title.setSpacing(0);title.addWidget(text_label('Style',14,700,height=16));title.addStretch();self.origin=text_label('From script',11,500,'#8B93A1',16);title.addWidget(self.origin);v.addLayout(title)
        self.card_grid=QWidget();grid=QGridLayout(self.card_grid);grid.setContentsMargins(0,0,0,0);grid.setSpacing(8)
        for col in range(3):grid.setColumnStretch(col,1)
        for i,(short,preset) in enumerate((item for item in PRESETS.items() if item[0]!='Off')):
            b=CaptionCard(short,preset);b.clicked.connect(lambda checked=False,preset=preset:self.emit_change('preset',preset));self.buttons[preset]=b;grid.addWidget(b,i//3,i%3)
        self.buttons[PRESETS['Hormozi']].setChecked(True);self.card_grid.setFixedHeight(214);v.addWidget(self.card_grid)
        v.addWidget(text_label('Position',14,700,height=16));self.position=Segmented(['Top','Center','Bottom']);self.position.setCurrentText('Bottom');self.position.currentTextChanged.connect(lambda value:self.emit_change('position',value));v.addWidget(self.position)
        self.customize=Accordion('Customize',self.toggle_customize);v.addWidget(self.customize)
        self.custom=QWidget();c=QVBoxLayout(self.custom);c.setContentsMargins(0,0,0,0);c.setSpacing(8)
        self.size=ClickSlider();self.size.setRange(50,180);self.size.valueChanged.connect(lambda value:self.emit_change('size',value));c.addWidget(text_label('Text size',12,500,'#8B93A1'));c.addWidget(self.size)
        self.off=button('Off',lambda:self.emit_change('preset','Off'));self.off.setCheckable(True);self.buttons['Off']=self.off;c.addWidget(self.off);c.addWidget(button('Reset to script',self.reset_requested.emit));self.custom.hide();v.addWidget(self.custom);v.addStretch()
        self.stack.addWidget(scroll(captions))
        look=QWidget();l=QVBoxLayout(look);l.setContentsMargins(0,0,0,0);l.setSpacing(12)
        l.addWidget(text_label('Energy',14,700,height=16));self.energy=Segmented(['Subtle','Balanced','High\nenergy'],['SUBTLE','BALANCED','HIGH_ENERGY']);self.energy.setCurrentIndex(1);self.energy.currentTextChanged.connect(lambda value:self.emit_change('energy',value));l.addWidget(self.energy)
        self.director=MomentRow('Smart Director','Picks camera moves and transitions',66);self.director.switch.setToolTip('Smart Director is always on.');l.addWidget(self.director)
        l.addWidget(text_label('Special moments',14,700,height=16));self.date_row=MomentRow('Date cards','0 found in your JSON');self.circle_row=MomentRow('Circle markers','0 found in your JSON');l.addWidget(self.date_row);l.addWidget(self.circle_row)
        self.fine=Accordion('Fine-tune',self.toggle_fine);l.addWidget(self.fine)
        self.fine_panel=QWidget();f=QVBoxLayout(self.fine_panel);f.setContentsMargins(0,0,0,0);f.setSpacing(8)
        self.framing=ClickCombo();self.framing.addItems(['Fill frame (crop)','Fit entire image']);self.framing.currentIndexChanged.connect(lambda value:self.emit_change('framing','FILL' if value==0 else 'FIT'))
        f.addWidget(text_label('Framing',12,500,'#8B93A1'));f.addWidget(self.framing);f.addWidget(button('Reset to script',self.reset_requested.emit));self.fine_panel.hide();l.addWidget(self.fine_panel);l.addStretch();self.stack.addWidget(scroll(look))
        sound=QWidget();s=QVBoxLayout(sound);s.setContentsMargins(0,0,0,0);s.setSpacing(12);s.addWidget(text_label('From script',11,500,'#8B93A1'));self.gains={};self.gain_labels={}
        for title,key in [('Voice','voice_volume'),('Music','music_volume')]:
            row=QHBoxLayout();row.addWidget(text_label(title,14,700));value=text_label('100%',12,500,'#8B93A1');self.gain_labels[key]=value;row.addStretch();row.addWidget(value);s.addLayout(row)
            slider=ClickSlider();slider.setRange(0,100);slider.valueChanged.connect(lambda value,key=key:self.emit_change(key,value/100));self.gains[key]=slider;s.addWidget(slider)
        detail=text_label('Music loops, crossfades and ducks under narration automatically.',12,400,'#8B93A1');detail.setWordWrap(True);s.addWidget(detail)
        s.addWidget(button('Reset to script',self.reset_requested.emit));s.addStretch();self.stack.addWidget(scroll(sound));self.currentChanged.connect(self.fade_tab)
    def currentIndex(self):return self.stack.currentIndex()
    def widget(self,index):return self.stack.widget(index)
    def setCurrentIndex(self,index):
        old=self.stack.currentIndex();self.stack.setCurrentIndex(index);self.tabs.setCurrentIndex(index)
        if old!=index:self.currentChanged.emit(index)
    def emit_change(self,key,value):
        if not self.updating:self.changed.emit(key,value)
    def toggle_customize(self):self.custom.setVisible(not self.custom.isVisible())
    def toggle_fine(self):self.fine_panel.setVisible(not self.fine_panel.isVisible())
    def set_moments(self,moments):
        for row,kind in [(self.date_row,'DATE_CARD'),(self.circle_row,'CIRCLE')]:
            count=sum(m.get('type')==kind for m in moments);row.detail.setText(f'{count} found in your JSON');row.switch.on=bool(count);row.switch.update()
    def set_settings(self,settings,overrides):
        self.updating=True;self.origin.setText('Custom' if overrides else 'From script')
        for preset,b in self.buttons.items():b.setChecked(preset==settings.caption_preset)
        self.energy.setCurrentText(settings.visual_director.mode);self.size.setValue(settings.caption_size);self.position.setCurrentText(settings.caption_position)
        self.framing.setCurrentIndex(0 if settings.aspect_policy=='FOCUS_CROP' else 1)
        for key,slider in self.gains.items():value=round(getattr(settings,key)*100);slider.setValue(value);self.gain_labels[key].setText(f'{value}%')
        self.updating=False
    def fade_tab(self,index):
        if reduced_motion():return
        widget=self.widget(index);old=getattr(self,'_tab_anim',None)
        if old:old.stop()
        effect=QGraphicsOpacityEffect(widget);widget.setGraphicsEffect(effect);a=QPropertyAnimation(effect,b'opacity',self);a.setDuration(150);a.setStartValue(.55);a.setEndValue(1);a.setEasingCurve(QEasingCurve.OutCubic);self._tab_anim=a;a.start()
