"""Build Android diagnostic tables from the verified B contract and bundled fonts."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
DESKTOP=ROOT.parent/'ats_sync_3_0_2_A1'
if not (DESKTOP/'ATS_CAPABILITIES.json').exists():
    bundled=json.loads((ROOT/'assets/sync-schema.json').read_text(encoding='utf-8'))
    assert bundled['contract_id']=='ATS_SYNC_2026-10-B'
    assert (ROOT/'assets/native-font-coverage.json').exists()
    print('Using bundled verified B schema and font coverage for standalone source rebuild')
    sys.exit(0)
cap=json.loads((DESKTOP/'ATS_CAPABILITIES.json').read_text(encoding='utf-8'))
fields=cap['fields']
for path,key in [('$.scenes[].motion','motions'),('$.scenes[].transition','transitions')]:
    fields[path]={'type':'enum','allowed':cap['enums'][key],'enforcement':'REJECT'}
schema={'contract_id':cap['contract_id'],'fields':fields,'enums':cap['enums']}
(ROOT/'assets/sync-schema.json').write_text(json.dumps(schema,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
sys.path.insert(0,str(DESKTOP))
from bootstrap import application
application()
from PySide6.QtGui import QRawFont
def filename(name):
    special={'Poppins':'Poppins-Black.ttf','Luckiest Guy':'LuckiestGuy.ttf','Bebas Neue':'BebasNeue.ttf','Playfair Display':'playfairdisplay.ttf','Noto Nastaliq Urdu':'notonastaliqurdu.ttf','DejaVu Sans':'DejaVuSans.ttf','Liberation Sans':'LiberationSans-Bold.ttf','Source Code Pro':'SourceCodePro-Regular.ttf','Inconsolata':'Inconsolata-Regular.ttf','Bitstream Vera Sans':'VeraIt.ttf','Oswald':'oswald.ttf'}
    return 'inter.ttf' if name.startswith('Inter') else special.get(name,name+'.ttf')
coverage={}
for name in cap['enums']['fonts']:
    f=ROOT/'assets/fonts'/filename(name)
    raw=QRawFont(str(f),60) if f.exists() else QRawFont()
    codes=[*range(0x0590,0x0700),*range(0x0750,0x0780),*range(0x08a0,0x0a00)]
    coverage[name]={'file':filename(name),'bundled':raw.isValid(),'glyphs':''.join(chr(cp) for cp in codes if raw.isValid() and raw.supportsCharacter(cp))}
(ROOT/'assets/native-font-coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
prompt=ROOT/'assets/MAIN_MASTER_PROMPT_V5.2.5.txt'
assert 'UNIVERSAL_PIPELINE_FINAL_V5.2.5' in prompt.read_text(encoding='utf-8')
assert cap['contract_id']=='ATS_SYNC_2026-10-B'
print('Contract/font assets generated; prompt SHA256',hashlib.sha256(prompt.read_bytes()).hexdigest())
