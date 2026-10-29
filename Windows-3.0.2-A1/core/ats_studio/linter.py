"""ATS 3.0 package and media diagnostics, separate from Explain Package."""
import json
from pathlib import Path
from .product import Project
from .media import preflight_pro_media
from .pro_spec import build_spec
from .pro_audio import choose_cues

def lint(package_path,images_path,audio_path,settings=None):
    result={'valid':False,'errors':[],'warnings':[],'info':[]}
    try:
        p=Project('Linter',str(audio_path),str(images_path),Path(package_path).read_text(encoding='utf-8')).validate()
        s=settings or p.settings();spec=build_spec(p.effective_package(),p.images,s)
        choose_cues(spec,0,p.package.pro.get('direction',{}).get('sfx_enabled',True))
        result['warnings']=[m for level,m in p.notices if level=='warning']+list(spec.warnings)+preflight_pro_media(p.package,p.images,s.width,s.height,s.framing)
        result['info']=[m for level,m in p.notices if level=='info']+spec.changes.get('moment_notices',[])
        result['valid']=True;result['frames']=p.package.total_frames;result['schema']=p.package.schema_version
    except (ValueError,OSError,TypeError) as exc:result['errors']=str(exc).splitlines()
    return result

def main(argv=None):
    import argparse
    from PySide6.QtWidgets import QApplication
    app=QApplication.instance() or QApplication([])
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--package',type=Path,required=True);parser.add_argument('--images',type=Path,required=True);parser.add_argument('--audio',type=Path,required=True);parser.add_argument('--json',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv);result=lint(args.package,args.images,args.audio)
    text=json.dumps(result,ensure_ascii=False,indent=2) if args.json else ('PASS' if result['valid'] else 'FAIL')+'\n'+'\n'.join(result['errors']+result['warnings']+result['info'])
    if args.output:args.output.write_text(text,encoding='utf-8')
    print(text);return 0 if result['valid'] else 1
