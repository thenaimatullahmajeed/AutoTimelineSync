"""Owned background workers with bounded requests and cancellable export."""
from __future__ import annotations
from collections import OrderedDict, deque
from pathlib import Path
import threading
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QImageReader
from PySide6.QtCore import Qt
from ..renderer import export_video, RenderCancelled
class ProPreviewWorker(QThread):
    """Render requested preview frames with the exact Pro compositor off the UI thread."""
    frame_ready = Signal(int, int, object)

    def __init__(self) -> None:
        super().__init__()
        self._condition = threading.Condition()
        self._configuration = None
        self._frame = 0
        self._generation = 0
        self._pending = False
        self._stopping = False

    def configure(self, spec, images, settings, width: int, height: int, frame: int,
                  captions_visible: bool = True) -> int:
        with self._condition:
            self._generation += 1
            self._configuration = (spec,images,settings,width,height,captions_visible)
            self._frame = frame
            self._pending = True
            self._condition.notify()
            return self._generation

    def request(self, frame: int) -> None:
        with self._condition:
            self._frame = frame
            self._pending = True
            self._condition.notify()

    def run(self) -> None:
        from ..pro_compositor import ProCompositor
        compositor = None
        previous = None
        while True:
            with self._condition:
                while not self._pending and not self._stopping:
                    self._condition.wait()
                if self._stopping:return
                configuration=self._configuration
                generation=self._generation
                frame=self._frame
                self._pending=False
            if configuration is None:continue
            if previous is not configuration:
                spec,images,settings,width,height,captions_visible=configuration
                compositor=ProCompositor(spec,images,settings,width,height,128*1024**2)
                compositor.captions_visible=captions_visible
                previous=configuration
            try:
                image=compositor.render_frame(frame)
            except Exception:
                image=QImage()
            self.frame_ready.emit(generation,frame,image)

    def stop(self) -> None:
        with self._condition:
            self._stopping=True
            self._condition.notify_all()
        self.wait(6000)




class ExportWorker(QThread):
    progress_changed = Signal(str, float, str)
    completed = Signal(object)
    failed = Signal(str)
    stopped = Signal()

    def __init__(self, package: Package, images: dict[str, Path], audio: Path,
                 output: Path, settings: RenderSettings) -> None:
        super().__init__()
        self.package, self.images, self.audio = package, images, audio
        self.output, self.settings = output, settings
        self.cancel_event = threading.Event()

    def run(self) -> None:
        try:
            result = export_video(self.package, self.images, self.audio, self.output,
                                  self.settings, self.cancel_event, self.progress_changed.emit)
            self.completed.emit(result)
        except RenderCancelled:
            self.stopped.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


