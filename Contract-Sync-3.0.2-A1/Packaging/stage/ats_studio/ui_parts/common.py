"""Shared visual language and non-blocking, reduced-motion-aware polish."""
import ctypes
import sys
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QAbstractAnimation, QRect, Signal, QRectF, QSize
from PySide6.QtWidgets import QPushButton, QLabel, QComboBox, QSlider, QDialog, QScrollArea, QWidget, QVBoxLayout,QGraphicsDropShadowEffect,QHBoxLayout,QStyleOption,QStyle
from PySide6.QtGui import QColor,QPainter,QPen,QFont,QIcon,QPixmap
from PySide6.QtSvg import QSvgRenderer

ACCENT='#A3E635'
STYLE='''
QWidget { background:transparent; color:#E8EAED; font-family:Inter; font-size:13px; }
QMainWindow { background:#0E1013; }
QDialog { background:#101318; border:1px solid #232830; border-radius:20px; }
QDialog#launchDialog { border-top-left-radius:0; border-top-right-radius:0; }
QDialog#exportDialog { background:transparent; border:none; }
QMenu { background:#101318; }
QLabel { background:transparent; }
QLabel[muted="true"] { color:#8B93A1; font-size:12px; }
QLabel[heading="true"] { font-size:24px; font-weight:800; }
QPushButton { background:#232830; border:none; border-radius:12px; padding:0 24px; min-height:44px; font-size:15px; font-weight:700; }
QPushButton:hover { background:#2A303A; }
QPushButton:pressed { background:#303743; }
QPushButton:disabled { color:#6B7280; background:#232830; }
QPushButton[primary="true"] { background:#A3E635; color:#10130A; }
QPushButton[primary="true"]:hover { background:#B0EC4F; }
QPushButton[primary="true"]:pressed { background:#93D12D; }
QPushButton[primary="true"]:disabled { background:#232830; color:#6B7280; }
QPushButton[ghost="true"] { background:transparent; color:#8B93A1; }
QPushButton[ghost="true"]:hover { color:#E8EAED; }
QPushButton[accordion="true"] { background:#15181D; border:1px solid #232830; padding:0 14px; text-align:left; font-size:14px; min-height:48px; max-height:48px; }
QPushButton[accordion="true"]:disabled { background:#15181D; color:#E8EAED; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox { background:#15181D; border:1px solid #232830; border-radius:10px; padding:0 14px; min-height:44px; selection-background-color:#2A303A; }
QComboBox::drop-down { border:none; width:22px; }
QComboBox QAbstractItemView { background:#1E232B; selection-background-color:#2A303A; padding:6px; }
QScrollArea { border:none; background:transparent; }
QScrollBar:vertical { background:#0E1013; width:6px; border-radius:3px; }
QScrollBar::handle:vertical { background:#3A424F; border-radius:3px; min-height:32px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QSlider::groove:horizontal { height:4px; background:#232830; border-radius:2px; }
QSlider::sub-page:horizontal { background:#FFFFFF; border-radius:2px; }
QSlider::handle:horizontal { background:#FFFFFF; width:12px; height:12px; margin:-4px 0; border-radius:6px; }
QSlider[transport="true"]::handle:horizontal { width:0px; }
QMenuBar { background:transparent; padding:0; color:#C9CFD8; font-size:14px; }
QMenuBar::item { padding:13px 12px; border-radius:7px; }
QMenuBar::item:selected, QMenu::item:selected { background:#2A303A; }
QMenu { border:1px solid #232830; padding:6px; }
QMenu::item { padding:8px 22px; }
QProgressBar { border:none; background:#232830; border-radius:6px; min-height:10px; text-align:center; }
QProgressBar::chunk { background:#A3E635; border-radius:6px; }
QToolTip { background:#1E232B; color:#E8EAED; border:1px solid #3A424F; padding:8px; }
QWidget#topBar, QWidget#timeline { border-bottom:1px solid #232830; }
QWidget#timeline { border-top:1px solid #232830; border-bottom:none; }
QWidget#inspector { border-left:1px solid #232830; }
QWidget#launchSidebar { background:#101318; border-right:1px solid #232830; }
QWidget#rowCard { background:#15181D; border:1px solid #232830; border-radius:14px; }
QWidget#rowCard QLabel { background:transparent; border:none; }
QLabel#chip { background:transparent; border:1px solid #2A303A; border-radius:10px; padding:2px 9px; color:#8B93A1; font-size:11px; font-weight:700; }
QLabel#projectPill { background:#15181D; border:1px solid #232830; border-radius:15px; padding:5px 14px; color:#E8EAED; font-size:13px; font-weight:500; }
'''

def reduced_motion():
    if sys.platform!='win32':return False
    value=ctypes.c_int(1)
    try:return not bool(ctypes.windll.user32.SystemParametersInfoW(0x1042,0,ctypes.byref(value),0) and value.value)
    except Exception:return True

def fade_window(widget,duration=220,scale=False):
    if reduced_motion():return
    old=getattr(widget,'_fade',None)
    if old:old.stop()
    widget.setWindowOpacity(0)
    anim=QPropertyAnimation(widget,b'windowOpacity',widget);anim.setDuration(duration)
    anim.setStartValue(0.0);anim.setEndValue(1.0);anim.setEasingCurve(QEasingCurve.OutCubic)
    widget._fade=anim;anim.start()
    if scale:
        end=widget.geometry();start=QRect(end);start.setSize(end.size()*.98);start.moveCenter(end.center())
        geometry=QPropertyAnimation(widget,b'geometry',widget);geometry.setDuration(duration);geometry.setStartValue(start);geometry.setEndValue(end);geometry.setEasingCurve(QEasingCurve.OutCubic)
        widget._scale=geometry;geometry.start()

def dark_titlebar(widget):
    if sys.platform=='win32':
        try:
            value=ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(int(widget.winId())),20,ctypes.byref(value),ctypes.sizeof(value))
        except Exception:pass

class Dialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.setStyleSheet(STYLE)
    def paintEvent(self,event):
        option=QStyleOption();option.initFrom(self);p=QPainter(self);self.style().drawPrimitive(QStyle.PE_Widget,option,p,self);p.end()
    def showEvent(self,event):
        super().showEvent(event);dark_titlebar(self);fade_window(self,180,True)

class ClickCombo(QComboBox):
    def wheelEvent(self,event):event.ignore()

class ClickSlider(QSlider):
    def __init__(self,parent=None):super().__init__(Qt.Horizontal,parent)
    def wheelEvent(self,event):event.ignore()
    def paintEvent(self,event):
        mini=bool(self.property('mini'))
        if not (self.property('transport') or mini):return super().paintEvent(event)
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.setPen(Qt.NoPen);rect=QRectF(7 if mini else 0,(self.height()-4)/2,self.width()-(14 if mini else 0),4);p.setBrush(QColor('#2A303A' if mini else '#232830'));p.drawRoundedRect(rect,2,2)
        fraction=(self.value()-self.minimum())/max(1,self.maximum()-self.minimum())
        if fraction>0:p.setBrush(QColor('#C9CFD8' if mini else '#FFFFFF'));p.drawRoundedRect(QRectF(rect.x(),rect.y(),rect.width()*fraction,4),2,2)
        if mini:p.setBrush(QColor('#FFFFFF'));p.drawEllipse(QRectF(rect.x()+rect.width()*fraction-7,(self.height()-14)/2,14,14))
        p.end()
    def mini_value(self,event):
        fraction=max(0,min(1,(event.position().x()-7)/max(1,self.width()-14)));self.setValue(round(self.minimum()+fraction*(self.maximum()-self.minimum())))
    def mousePressEvent(self,event):
        if self.property('mini') and event.button()==Qt.LeftButton:self.setSliderDown(True);self.mini_value(event);event.accept()
        else:super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self.property('mini') and self.isSliderDown():self.mini_value(event);event.accept()
        else:super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if self.property('mini') and event.button()==Qt.LeftButton:self.setSliderDown(False);event.accept()
        else:super().mouseReleaseEvent(event)

def button(text,callback=None,primary=False):
    b=QPushButton(text);b.setProperty('primary',primary)
    if callback:b.clicked.connect(callback)
    return b

def label(text,muted=False,heading=False):
    l=QLabel(text);l.setProperty('muted',muted);l.setProperty('heading',heading);l.setWordWrap(True);return l

def scroll(widget):
    s=QScrollArea();s.setWidgetResizable(True);s.setWidget(widget);widget.setAutoFillBackground(False);s.viewport().setAutoFillBackground(False);s.setFrameShape(QScrollArea.NoFrame);return s

def human_time(seconds):
    seconds=max(0,int(seconds));return f'{seconds//60:02}:{seconds%60:02}' if seconds<3600 else f'{seconds//3600}:{seconds%3600//60:02}:{seconds%60:02}'

def pixel_font(size,weight=500):
    f=QFont('Inter');f.setPixelSize(size);f.setWeight(QFont.Weight(weight));return f

def text_label(text,size=13,weight=500,color='#E8EAED',height=None):
    l=QLabel(text);l.setFont(pixel_font(size,weight));l.setStyleSheet(f'background:transparent;color:{color};font-size:{size}px;font-weight:{weight};');l.setWordWrap(False)
    if height is not None:l.setFixedHeight(height)
    return l

PATHS={
 'logo':'<rect x="3" y="4" width="18" height="16" rx="4"/><path d="M10 9l5 3-5 3z" fill="currentColor"/>',
 'audio':'<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
 'images':'<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
 'json':'<path d="M8 4c-2 0-3 1-3 3v2c0 1-1 2-2 3 1 1 2 2 2 3v2c0 2 1 3 3 3M16 4c2 0 3 1 3 3v2c0 1 1 2 2 3-1 1-2 2-2 3v2c0 2-1 3-3 3"/>',
 'music':'<path d="M9 18V6l10-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/>',
 'check':'<path d="M5 12l5 5 9-10"/>','dot':'<circle cx="12" cy="12" r="12" fill="currentColor" stroke="none"/>','chevron':'<path d="M9 6l6 6-6 6"/>',
 'down':'<path d="M6 9l6 6 6-6"/>','close':'<path d="M6 6l12 12M18 6L6 18"/>',
 'play':'<path d="M8 5v14l11-7z" fill="currentColor"/>',
 'pause':'<path d="M8 5v14M16 5v14"/>'}

def svg_icon(name,size=20,color='#E8EAED'):
    body=PATHS[name].replace('currentColor',color)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{1.8 if name=="logo" else 2}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    pix=QPixmap(size,size);pix.fill(Qt.transparent);p=QPainter(pix);QSvgRenderer(svg.encode()).render(p);p.end();return QIcon(pix)

class IconTile(QWidget):
    def __init__(self,name,size=40,icon_size=20,tile=True,parent=None):
        super().__init__(parent);self.name,self.icon_size,self.tile=name,icon_size,tile;self.setFixedSize(size,size)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        if self.tile:p.setPen(Qt.NoPen);p.setBrush(QColor('#1E232B'));p.drawRoundedRect(QRectF(self.rect()),10,10)
        pix=svg_icon(self.name,self.icon_size,'#C9CFD8' if self.tile else '#FFFFFF').pixmap(self.icon_size,self.icon_size)
        p.drawPixmap((self.width()-self.icon_size)//2,(self.height()-self.icon_size)//2,pix);p.end()

class Segmented(QWidget):
    currentIndexChanged=Signal(int);currentTextChanged=Signal(str)
    def __init__(self,labels=(),values=None,parent=None):
        super().__init__(parent);self.items=[];self.values=[];self.index=0;self.setFixedHeight(52)
        self.setAttribute(Qt.WA_StyledBackground,True)
        self.setStyleSheet('Segmented{background:#15181D;border:1px solid #232830;border-radius:10px;}')
        self.box=QHBoxLayout(self);self.box.setContentsMargins(4,4,4,4);self.box.setSpacing(2)
        self.addItems(labels,values)
    def addItems(self,labels,values=None):
        for title,value in zip(labels,values or labels):
            b=QPushButton(title);b.setCheckable(True);b.setMinimumHeight(0);b.setFixedHeight(44);b.setFont(pixel_font(13,500))
            b.setStyleSheet('QPushButton{background:transparent;color:#8B93A1;border:0;border-radius:7px;padding:0;font-size:13px;font-weight:500;min-height:0;} QPushButton:checked{background:#2A303A;color:#FFFFFF;}')
            i=len(self.items);b.clicked.connect(lambda checked=False,i=i:self.setCurrentIndex(i));self.items.append(b);self.values.append(value);self.box.addWidget(b,1)
        self.sync()
    def sync(self):
        for i,b in enumerate(self.items):b.setChecked(i==self.index)
    def count(self):return len(self.items)
    def currentIndex(self):return self.index
    def currentText(self):return self.values[self.index] if self.values else ''
    def setCurrentIndex(self,index):
        if 0<=index<len(self.items):
            changed=self.index!=index;self.index=index;self.sync()
            if changed:self.currentIndexChanged.emit(index);self.currentTextChanged.emit(self.currentText())
    def setCurrentText(self,text):
        if text in self.values:self.setCurrentIndex(self.values.index(text))

def ghost(text,callback=None,size=15,padding=24):
    b=button(text,callback);b.setProperty('ghost',True);b.setStyleSheet(f'font-size:{size}px;padding:0 {padding}px;');return b

class StatusButton(QPushButton):
    def __init__(self,text,callback):
        super().__init__(text);self.clicked.connect(callback);self.setProperty('ghost',True);self.setFixedHeight(44);self.setStyleSheet('background:transparent;color:#C9CFD8;font-size:13px;font-weight:700;padding:0 8px;')
    def sizeHint(self):return QSize(self.fontMetrics().horizontalAdvance(self.text())+32,44)
    def minimumSizeHint(self):return self.sizeHint()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.drawPixmap(8,18,self.icon().pixmap(8,8));p.setFont(self.font());p.setPen(QColor('#C9CFD8'));p.drawText(QRectF(24,0,self.width()-32,44),Qt.AlignLeft|Qt.AlignVCenter,self.text());p.end()

class Accordion(QPushButton):
    def __init__(self,title,callback):
        super().__init__(title);self.setProperty('accordion',True);self.setFixedHeight(50);self.clicked.connect(callback)
    def paintEvent(self,event):
        super().paintEvent(event);p=QPainter(self);p.drawPixmap(self.width()-30,(self.height()-16)//2,svg_icon('down',16).pixmap(16,16));p.end()
