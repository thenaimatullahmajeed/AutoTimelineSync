"""Single-generation preview mixes and bounded waveform data."""
from pathlib import Path
from PySide6.QtCore import QThread,Signal

class MixWorker(QThread):
    ready=Signal(int,str);failed=Signal(str)
    def __init__(self,generation,spec,audio,settings,work):
        super().__init__();self.generation,self.spec,self.audio,self.settings,self.work=generation,spec,audio,settings,work
    def run(self):
        try:
            from ..pro_audio import build_audio_mix,master_preview_audio
            mix,_,_,_=build_audio_mix(self.spec,Path(self.audio),self.settings,self.work,cancelled=self.isInterruptionRequested)
            result=master_preview_audio(mix,self.spec,self.settings,self.work,self.isInterruptionRequested)
            if not self.isInterruptionRequested():self.ready.emit(self.generation,str(result))
        except Exception as exc:
            if not self.isInterruptionRequested():self.failed.emit(str(exc))

class WaveWorker(QThread):
    ready=Signal(int,object,object)
    def __init__(self,generation,project):super().__init__();self.generation,self.project=generation,project
    def run(self):
        try:
            import numpy as np
            from ..pro_audio import _decode_narration,_decode_user_music,SAMPLE_RATE,loop_seams
            from ..media import probe_audio
            p=self.project;frames=round(p.package.audio_duration*SAMPLE_RATE);result={};seams=[]
            for key,path in [('voice',p.narration),('music',p.music)]:
                if not path or not Path(path).is_file():continue
                samples=np.asarray((_decode_narration(Path(path),frames,self.isInterruptionRequested) if key=='voice' else _decode_user_music(Path(path),frames,self.isInterruptionRequested)),dtype=np.float32)
                groups=np.array_split(samples,min(600,len(samples)));peaks=[float(np.max(np.abs(g))) for g in groups];peak=max(peaks,default=1)
                result[key]=[x/max(peak,1e-6) for x in peaks]
                if key=='music':seams=loop_seams(probe_audio(Path(path))[0],p.package.audio_duration)
            if not self.isInterruptionRequested():self.ready.emit(self.generation,result,seams)
        except Exception:pass
