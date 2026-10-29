"""Import exact supplied final JSON and render with the unchanged real exporter."""
import sys,json,time,threading,subprocess,hashlib,copy
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,application,install
app=application();install(ui=True)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPainter,QColor,QFont,QLinearGradient,QPen
from ats_studio.product import Project,parse_script,script_settings
from ats_studio.ui_parts.dialogs import ImportWorker
from ats_studio.pro_spec import build_spec
from ats_studio.pro_compositor import ProCompositor
from ats_studio.fast_export import export_pro_video
from ats_studio.media import bundled_binary
from ats_studio.sync_diagnostics import validate_all,copy_message

input_file=ROOT/'Inputs/FINAL_RICH_03_ATS_PACKAGE_V2.json'
data=json.loads(input_file.read_text(encoding='utf-8-sig'))
out=ROOT/'Evidence/Acceptance';images=out/'images';frames=out/'frames'
images.mkdir(parents=True,exist_ok=True);frames.mkdir(exist_ok=True)
for i in range(1,35):
    image=QImage(1080,1920,QImage.Format_RGB888);p=QPainter(image)
    g=QLinearGradient(0,0,1080,1920);g.setColorAt(0,QColor.fromHsv(i*37%360,100,80));g.setColorAt(1,QColor.fromHsv((i*37+90)%360,130,140));p.fillRect(image.rect(),g)
    p.setPen(QPen(QColor('#769096'),3))
    for x in range(0,1080,120):p.drawLine(x,0,x,1920)
    for y in range(0,1920,120):p.drawLine(0,y,1080,y)
    p.fillRect(70,160,940,170,QColor('#F0EBDE'));font=QFont('Inter');font.setPixelSize(55);p.setFont(font);p.setPen(QColor('#182C34'))
    p.drawText(85,230,f'SCENE {i:03d} — PLACEHOLDER');font.setPixelSize(32);p.setFont(font);p.drawText(85,290,'9:16 import / camera / transition test')
    p.end();assert image.save(str(images/f'{i:03d}.png'))
audio_records=json.loads((ROOT/'Evidence/audio-location.json').read_text(encoding='utf-8'))
audio=next(Path(x['path']) for x in audio_records if 'probe' in x and abs(x['probe'][0]-data['audio_duration'])<=1/data['fps'])
project=Project(data['project_title'],str(audio),str(images),input_file.read_text(encoding='utf-8-sig'),'')
worker=ImportWorker(project);ready=[];failed=[];worker.ready.connect(lambda *x:ready.append(x));worker.failed.connect(failed.append);worker.run()
assert ready and not failed,failed
project,spec=ready[0];worker.deleteLater();app.processEvents()
diag=validate_all(project.script,str(images),str(audio));assert diag['valid'],diag
(out/'all-errors.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'copy-errors.txt').write_text(copy_message(diag),encoding='utf-8')
usage=project.sync_utilization
(out/'utilization.json').write_text(json.dumps(usage,ensure_ascii=False,indent=2),encoding='utf-8')
assert (usage['mode'],usage['noncut_boundaries'],usage['fancy_boundaries'],usage['moments_by_type']['DATE_CARD'],usage['sfx_cue_count'])==('RICH',22,8,3,6),usage
project.save(str(out/'project.ats3'))
settings=replace(project.settings(tier=1),encoder='CPU x264',encoder_preset='ultrafast',workers=2,crf=18)
print('IMPORT PASS',usage['utilization_line'],flush=True)
print('AUDIO',audio,'RESOLUTION',settings.width,settings.height,'MASTER',data['audio']['master'],flush=True)

# Verify the explicit effects using the exact final package, not a generic base.
energy_results={}
for energy in ['SUBTLE','BALANCED','HIGH_ENERGY']:
    d=copy.deepcopy(data);d['direction']['energy']=energy
    p=parse_script(json.dumps(d,ensure_ascii=False));s=script_settings(p,'VERTICAL');s=replace(s,width=180,height=320)
    es=build_spec(p,project.images,s);comp=ProCompositor(es,project.images,s);pixels={}
    for f in [0,100,365,800,1900]:
        im=comp.render_frame(f);pixels[str(f)]=hashlib.sha256(bytes(im.bits())).hexdigest()
    energy_results[energy]={'seed':es.seed,'decisions':[(x.motion,x.transition_applied,x.transition_frames,x.direction) for x in es.scenes],'pixels':pixels}
(out/'energy-comparison.json').write_text(json.dumps(energy_results,indent=2),encoding='utf-8')

video=out/'RICH-Hindi-Acceptance.mp4';started=time.monotonic()
def progress(*args):
    # Emit stage/progress on changes supplied by the engine; never invent an ETA.
    if time.monotonic()-progress.last>=15:
        print('RENDER',*[str(x)[:180] for x in args],flush=True);progress.last=time.monotonic()
progress.last=started
export_pro_video(project.effective_package(),project.images,audio,video,settings,threading.Event(),progress)
elapsed=time.monotonic()-started
report=json.loads(video.with_name(video.name+'.report.json').read_text(encoding='utf-8'))
assert report['final_file']['frames']==project.package.total_frames
def extract(name,frame):
    subprocess.run([str(bundled_binary('ffmpeg')),'-v','error','-nostdin','-ss',str(frame/data['fps']),'-i',str(video),'-frames:v','1','-y',str(frames/name)],check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
checks=[]
for ident in ['002','005','011','013','016','020','022','028','034']:
    plan=next(x for x in spec.scenes if x.id==ident)
    f=plan.first_frame+min(round(.6*data['fps']),max(0,plan.frames-1))
    extract(f'scene-{ident}.png',f)
    if plan.transition_frames:extract(f'transition-{ident}.png',plan.first_frame+max(1,plan.transition_frames//2))
    checks.append({'scene_id':ident,'frame':f,'transition':plan.transition_applied,'transition_frames':plan.transition_frames})
for moment in spec.changes.get('moments',[]):
    if moment['type']=='DATE_CARD':extract('date-'+moment['text']+'.png',(moment['first_frame']+moment['end_frame'])//2)
extract('ending-before.png',project.package.total_frames-18);extract('ending-final.png',project.package.total_frames-1)
result={'import':'PASS','export':'PASS','audio':str(audio),'audio_is_original':True,'json_sha256':hashlib.sha256(input_file.read_bytes()).hexdigest(),
        'resolution':[settings.width,settings.height],'frames':report['final_file']['frames'],'render_seconds':round(elapsed,3),'utilization':usage,
        'warnings':diag['diagnostics'],'requested_scene_checks':checks,'audio_master':data['audio']['master'],'ending':data['ending'],
        'visual_review':'PENDING: view all extracted frames before reporting fit/appearance'}
(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('EXPORT PASS',result['frames'],'frames',result['render_seconds'],'seconds',flush=True)
