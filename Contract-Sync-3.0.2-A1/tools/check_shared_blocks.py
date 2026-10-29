import sys,hashlib,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT
a=(ROOT/'Inputs/FINAL_SYNC_INSTRUCTION.txt').read_text(encoding='utf-8')
p=Path('C:/Users/naima/Downloads/autodownload/FINAL_SYNC_INSTRUCTION_FOR_CHATGPT_MASTER_PROMPT.txt')
b=p.read_text(encoding='utf-8')
def block(text):
    return '1. IDENTITY'+text.split('1. IDENTITY',1)[1].split('Nobody may claim these.',1)[0]+'Nobody may claim these.'
same=block(a)==block(b)
result={'shared_sections_1_to_8_identical':same,'codex_sha256':hashlib.sha256(block(a).encode()).hexdigest(),'chatgpt_sha256':hashlib.sha256(block(b).encode()).hexdigest(),'status':'Shared A block unchanged; candidate B proposed separately.'}
(ROOT/'Evidence/shared-contract-identity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result)
assert same,'SYNC ISSUE: supplied shared blocks differ'
