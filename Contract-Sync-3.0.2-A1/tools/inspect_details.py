import sys,dis
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import application
application()
from ats_studio.pro_compositor import ProCompositor
for name in ['_soft_source']:
    print('METHOD',name)
    groups={};line=0
    for i in dis.get_instructions(getattr(ProCompositor,name)):
        if i.starts_line:line=i.starts_line
        groups.setdefault(line,[]).append(i)
    for line,ops in groups.items():
        print(line,' | '.join(i.argrepr for i in ops if i.opname.startswith(('LOAD','STORE')) or i.opname in ['BINARY_OP','COMPARE_OP']))
