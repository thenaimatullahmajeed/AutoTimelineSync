"""Standalone Windows entry, with additive diagnostics installed before import."""
from bootstrap import install,application,ROOT,CORE
install(ui=True)
import json,sys
from pathlib import Path

if __name__=='__main__':
    if '--sync-check' in sys.argv:
        # Test bundled parser/UI import without depending on the source checkout.
        import copy
        from ats_studio.sync_diagnostics import validate_all,copy_message
        from ats_studio.sync_core import CONTRACT_ID,SEED_ERROR
        from ats_studio.ui_parts.dialogs import ImportWorker
        from ats_studio.product import Project
        from ats_studio.schema import PackageError
        from ats_studio.product import parse_script
        application()
        index=sys.argv.index('--sync-check')
        project_path,output=map(Path,sys.argv[index+1:index+3])
        output.mkdir(parents=True,exist_ok=True)
        raw=json.loads(project_path.read_text(encoding='utf-8'))
        p=Project(raw['name'],raw['narration'],raw['image_folder'],raw['script'])
        worker=ImportWorker(p);accepted=[];failed=[]
        worker.ready.connect(lambda p,spec:accepted.append(p));worker.failed.connect(failed.append)
        worker.run()
        if failed:raise RuntimeError(failed[0])
        assert accepted,'Bundled ImportWorker did not return a project'
        usage=accepted[0].sync_utilization
        assert (usage['mode'],usage['noncut_boundaries'],usage['fancy_boundaries'],usage['sfx_cue_count'])==('RICH',22,8,6)
        base=json.loads(raw['script']);broken=copy.deepcopy(base)
        broken['style']={'seed':2147483648}
        try:parse_script(json.dumps(broken))
        except PackageError as exc:seed=str(exc)
        else:raise AssertionError('Invalid seed accepted')
        assert '$.style.seed: '+SEED_ERROR in seed
        broken['captions'][0]['id']='1';broken['caption_style']['animation']='POP'
        report=validate_all(json.dumps(broken));message=copy_message(report)
        assert sum(x['severity']=='ERROR' for x in report['diagnostics'])>=3
        (output/'copy-errors.txt').write_text(message,encoding='utf-8')
        (output/'sync-check.json').write_text(json.dumps({'ok':True,'version':'3.0.2-A1','contract':CONTRACT_ID,'root':str(ROOT),'core':str(CORE),'seed_error':seed,'diagnostics':report,'utilization':usage},ensure_ascii=False,indent=2),encoding='utf-8')
    elif '--smoke-test' in sys.argv:
        from ats_studio.portable_smoke import run
        i=sys.argv.index('--smoke-test')
        sys.exit(run(application(),sys.argv[i+1]))
    else:
        from ats_studio.__main__ import main
        main()
