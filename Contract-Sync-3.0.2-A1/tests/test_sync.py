import copy,json,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,CORE,application,install
app=application();install(ui=True)
from ats_studio.product import parse_script,script_settings,Project
from ats_studio.schema import PackageError
from ats_studio.pro_spec import build_spec
from ats_studio.sync_core import SEED_ERROR
from ats_studio.sync_diagnostics import validate_all,copy_message,font_warnings,COPY_HEADER,COPY_COLUMNS,RTL_WARNING
from ats_studio.sync_modes import classify_counts,FANCY,utilization
base=json.loads((CORE/'Examples/ATS3_vertical.json').read_text())
image=ROOT.parent/'ats_contract_audit_3_0_2/Golden/minimal/images/001.png'

def types(b,n,f):
    result=['HARD_CUT']*b
    for i in range(n):result[i]=['CROSSFADE','DISSOLVE'][i%2]
    for i in range(f):result[i*2]=sorted(FANCY)[i%len(FANCY)]
    return result

@pytest.mark.parametrize('b,n,f,energy,frequency,expected',[
 (0,0,0,'BALANCED',.15,'NONE'),(20,11,4,'BALANCED',.15,'RICH'),(20,14,5,'BALANCED',.15,'RICH'),
 (20,10,4,'BALANCED',.15,'NONE'),(20,15,4,'BALANCED',.15,'NONE'),(20,12,3,'BALANCED',.15,'NONE'),(20,12,6,'BALANCED',.15,'NONE'),
 (20,20,7,'BALANCED',0,'MAX'),(20,20,8,'BALANCED',1,'NONE'),(20,19,7,'BALANCED',1,'NONE'),
 (20,8,3,'BALANCED',1,'STANDARD'),(20,9,3,'BALANCED',1,'NONE'),(20,8,4,'BALANCED',1,'NONE'),
 (20,8,4,'HIGH_ENERGY',1,'STANDARD'),(20,8,1,'SUBTLE',0,'NONE'),(20,8,1,'SUBTLE',.01,'STANDARD'),
 (33,22,8,'HIGH_ENERGY',.5,'RICH'),(33,18,7,'BALANCED',.3,'NONE'),(33,19,7,'BALANCED',.3,'RICH'),(33,24,8,'BALANCED',.3,'NONE'),
])
def test_mode_integer_thresholds(b,n,f,energy,frequency,expected):
    assert classify_counts(types(b,n,f),energy,frequency)['mode']==expected

def test_adjacent_fancy_repeated_noncut_and_same_fancy_limits():
    t=types(20,12,4);t[1]='FILM_BURN';assert classify_counts(t)['mode']=='NONE'
    t=types(20,12,4);t[9]=t[10]='DISSOLVE';assert classify_counts(t)['mode']=='NONE'
    t=types(20,12,4)
    for i in [0,2,4,6]:t[i]='FILM_BURN'
    assert classify_counts(t)['mode']=='NONE'

@pytest.mark.parametrize('value',[-1,2147483648,9223372036854775807,True,1.5,None,'1'])
def test_seed_rejected_early_exact_path(value):
    d=copy.deepcopy(base);d['style']={'seed':value}
    with pytest.raises(PackageError) as e:parse_script(json.dumps(d))
    assert '$.style.seed: '+SEED_ERROR in str(e.value)
@pytest.mark.parametrize('value',[0,2147483647])
def test_seed_boundaries_accepted(value):
    d=copy.deepcopy(base);d['style']={'seed':value};parse_script(json.dumps(d))

@pytest.mark.parametrize('offset',[-301,301])
def test_offset_error(offset):
    d=copy.deepcopy(base);d['scenes'][1]['sfx']=[{'id':'TICK_SOFT','offset_ms':offset}]
    with pytest.raises(PackageError) as e:parse_script(json.dumps(d))
    assert '$.scenes[1].sfx[0].offset_ms: must be a number between -300 and 300' in str(e.value)
def test_caption_id_and_creator_animation_collect_together():
    d=copy.deepcopy(base);d['caption_style'].update(preset='Hormozi Style',animation='POP');d['captions'][0]['id']='1';d['scenes'][1]['sfx']=[{'id':'TICK_SOFT','offset_ms':301}]
    r=validate_all(json.dumps(d));paths={e['path'] for e in r['diagnostics'] if e['severity']=='ERROR'}
    assert {'$.caption_style.animation','$.captions[0].id','$.scenes[1].sfx[0].offset_ms'}<=paths
    assert any(e['message']=='Caption 001 id should be "001".' for e in r['diagnostics'])
def test_exact_copy_format():
    r={'diagnostics':[{'path':'$.style.seed','rule':'seed','value':-1,'expected':SEED_ERROR,'severity':'ERROR'}]}
    assert copy_message(r)==COPY_HEADER+'\n'+COPY_COLUMNS+'\n$.style.seed | seed | -1 | '+SEED_ERROR+' | ERROR'
def test_copy_format_preserves_one_line_per_diagnostic():
    r={'diagnostics':[{'path':'$.captions[0].text','rule':'text','value':'one | two\nthree','expected':'x | y\nnext','severity':'WARN'}]}
    output=copy_message(r);assert len(output.splitlines())==3 and output.splitlines()[-1].count(' | ')==4

@pytest.mark.parametrize('text',['مرحبا بالعالم','שלום עולם','یہ ایک کہانی ہے'])
def test_creator_rtl_warn_only(text):
    raw={'caption_style':{'preset':'Hormozi Style','font':'Poppins'},'captions':[{'text':text}]}
    notices=font_warnings(raw);assert any(x['message']==RTL_WARNING and x['severity']=='WARN' for x in notices)
def test_generic_rtl_no_creator_warning():
    raw={'caption_style':{'preset':'Documentary Highlight','font':'DejaVu Sans'},'captions':[{'text':'مرحبا بالعالم'}]}
    assert not any(x['rule']=='creator_rtl' for x in font_warnings(raw))
@pytest.mark.parametrize('text,font,recommend',[('भारत की कहानी','Montserrat','Poppins'),('مرحبا بالعالم','Poppins','DejaVu Sans'),('یہ ایک کہانی ہے','Poppins','Noto Nastaliq Urdu')])
def test_script_font_warning(text,font,recommend):
    r=font_warnings({'caption_style':{'preset':'Hormozi Style','font':font},'captions':[{'text':text}]})
    assert any(x['rule']=='script_font' and x['severity']=='WARN' and font in x['message'] and recommend in x['message'] for x in r)
def test_native_hindi_poppins_no_script_warning():
    assert not font_warnings({'caption_style':{'preset':'Hormozi Style','font':'Poppins'},'captions':[{'text':'भारत की कहानी'}]})

@pytest.mark.parametrize('energy',['SUBTLE','BALANCED','HIGH_ENERGY'])
def test_budgets_never_reject_or_downgrade_explicit_effects(energy):
    d=copy.deepcopy(base);d.update(audio_duration=80,words=[],captions=[],moments=[])
    d['scenes']=[{'id':f'{i+1:03d}','image_id':f'{i+1:03d}','start':i*4,'end':(i+1)*4,'voice_text':'Evidence','motion':'TINY_PUNCH_IN','transition':'HARD_CUT' if not i else 'FILM_BURN'} for i in range(20)]
    d['direction'].update(energy=energy,transition_frequency=0)
    p=parse_script(json.dumps(d));s=script_settings(p,'VERTICAL');spec=build_spec(p,{x.image_id:image for x in p.scenes},s)
    assert sum(x.transition_applied=='FILM_BURN' for x in spec.scenes)==19 and not spec.warnings

@pytest.mark.parametrize('folder',[p.name for p in (ROOT.parent/'ats_contract_audit_3_0_2/Golden').iterdir() if p.is_dir()])
def test_real_import_worker_preserves_valid_fixtures(folder):
    from ats_studio.ui_parts.dialogs import ImportWorker
    f=ROOT.parent/'ats_contract_audit_3_0_2/Golden'/folder
    p=Project(folder,str(f/'narration.wav'),str(f/'images'),(f/'ATS_PACKAGE_V2.json').read_text(encoding='utf-8'),str(f/'music.wav') if (f/'music.wav').exists() else '')
    w=ImportWorker(p);ready=[];failed=[];w.ready.connect(lambda *x:ready.append(x));w.failed.connect(failed.append);w.run()
    assert ready and not failed,failed
    p,spec=ready[0];assert p.sync_diagnostics['valid'] and p.sync_utilization['utilization_line'].startswith('Mode ')
    w.deleteLater();app.processEvents()

def test_report_dialog_copy_buttons():
    from ats_studio.sync_ui import report_dialog
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    r=validate_all(json.dumps(base));u={'utilization_line':'Mode NONE: 0 non-cut of 0, 0 fancy, 0 date cards, 0 sound cues, 0 overlays, features unused: none.'}
    d=report_dialog(None,r,u);d.show();app.processEvents();saved=app.clipboard().text()
    try:
        QTest.mouseClick(d.copy_errors,Qt.LeftButton);assert app.clipboard().text()==copy_message(r)
        QTest.mouseClick(d.copy_utilization,Qt.LeftButton);assert app.clipboard().text()==u['utilization_line']
        d.grab().save(str(ROOT/'Evidence/review-report-dialog.png'))
    finally:app.clipboard().setText(saved);d.close()

def test_cut_config_off_animation_photo_corner_house_rules_still_accepted():
    d=copy.deepcopy(base);d['scenes'][0]['transition_config']={'frames':8};d['caption_style'].update(preset='Off',animation='POP')
    d['overlays']=[{'id':'n','type':'PHOTO_NOTE','scene_id':'001','text':'Proof','start':0,'end':1,'points':[[.2,.2],[.2,.7],[.7,.7],[.7,.2]]}]
    parse_script(json.dumps(d))

def test_final_rich_preflight_has_no_spurious_cue_plan_error():
    text=(ROOT/'Inputs/FINAL_RICH_03_ATS_PACKAGE_V2.json').read_text(encoding='utf-8-sig')
    result=validate_all(text)
    assert result['valid'] and not result['diagnostics']
    assert copy_message(result)==COPY_HEADER+'\n'+COPY_COLUMNS

def test_contract_enums_and_current_seed_are_in_sync():
    from ats_studio.capabilities import current_capabilities
    c=json.loads((ROOT/'ATS_CAPABILITIES.json').read_text(encoding='utf-8'))
    assert c['enums']==current_capabilities()['enums']
    assert c['fields']['$.style.seed']['minimum']==0 and c['fields']['$.style.seed']['maximum']==2147483647
    assert c['fields']['$.style.seed']['effective_error']==SEED_ERROR

def test_final_rich_actual_import_matches_expected_utilization():
    from ats_studio.ui_parts.dialogs import ImportWorker
    record=json.loads((ROOT/'Evidence/Acceptance/project.ats3').read_text(encoding='utf-8'))
    p=Project(record['name'],record['narration'],record['image_folder'],record['script'],record['music'])
    w=ImportWorker(p);ready=[];failed=[];w.ready.connect(lambda *args:ready.append(args));w.failed.connect(failed.append);w.run()
    assert ready and not failed,failed
    actual=ready[0][0].sync_utilization
    assert (actual['mode'],actual['noncut_boundaries'],actual['fancy_boundaries'],actual['moments_by_type']['DATE_CARD'],actual['sfx_cue_count'])==('RICH',22,8,3,6)
    w.deleteLater();app.processEvents()

def test_actual_launch_validate_all_button_and_copy(tmp_path):
    from ats_studio.ui_parts.dialogs import LaunchDialog
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    d=LaunchDialog();d.resize(1100,720);d.show()
    bad=copy.deepcopy(base);bad['caption_style'].update(preset='Hormozi Style',animation='POP');bad['style']={'seed':-1}
    d.script_text=json.dumps(bad);saved=app.clipboard().text()
    try:
        QTest.mouseClick(d.all_errors,Qt.LeftButton);app.processEvents();report=d.sync_report_dialog
        QTest.mouseClick(report.copy_errors,Qt.LeftButton);app.processEvents()
        assert '$.style.seed' in app.clipboard().text() and '$.caption_style.animation' in app.clipboard().text()
        report.grab().save(str(ROOT/'Evidence/real-launch-validation.png'))
    finally:app.clipboard().setText(saved);d.reject();app.processEvents()

def test_existing_import_error_copy_uses_same_exchange_format():
    from ats_studio.ui_parts.dialogs import LaunchDialog
    d=LaunchDialog();d.script_text=json.dumps(base);d.show_error('Could not read selected JSON file.')
    assert d.error.startswith(COPY_HEADER+'\n'+COPY_COLUMNS+'\n')
    assert 'Could not read selected JSON file.' in d.error
    d.reject();app.processEvents()

def test_real_editor_shows_utilization_after_import(tmp_path):
    from ats_studio.ui import MainWindow
    from PySide6.QtCore import QSettings
    f=ROOT.parent/'ats_contract_audit_3_0_2/Golden/minimal'
    p=Project('Integration report test',str(f/'narration.wav'),str(f/'images'),(f/'ATS_PACKAGE_V2.json').read_text(encoding='utf-8'),'').validate()
    w=MainWindow(show_launch=False);w.store=QSettings(str(tmp_path/'preferences.ini'),QSettings.IniFormat)
    w.resize(1280,800);w.show();w.apply_project(p);app.processEvents()
    try:
        assert w.sync_report_dialog.isVisible()
        assert p.sync_utilization['mode']=='NONE'
        w.sync_report_dialog.grab().save(str(ROOT/'Evidence/real-editor-utilization.png'))
    finally:w.close();app.processEvents()
