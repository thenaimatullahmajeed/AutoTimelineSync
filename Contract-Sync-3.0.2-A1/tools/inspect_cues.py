import sys,dis
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import application
application()
from ats_studio.pro_audio import choose_cues
groups={};line=0
for instruction in dis.get_instructions(choose_cues):
    if instruction.starts_line:line=instruction.starts_line
    groups.setdefault(line,[]).append(instruction)
for line,ops in groups.items():
    print(line,' | '.join(i.argrepr for i in ops if i.opname.startswith(('LOAD','STORE')) or i.opname in ['BINARY_OP','COMPARE_OP']))
