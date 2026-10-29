"""Recover our own source edits and verify them against installed 3.0.1 bytecode."""
from pathlib import Path
import json, marshal, re, types, hashlib, ast

ROOT=Path(__file__).resolve().parent
LOG=Path.home()/'.codex/sessions/2026/09/25/rollout-2026-09-25T05-34-40-01a0d88f-8ad4-7dd0-934f-8baefbbe927e.jsonl'
BASE=ROOT/'core'

def normalized(c):
    if isinstance(c,types.CodeType):
        return (c.co_code,c.co_names,c.co_varnames,c.co_freevars,c.co_cellvars,
                c.co_argcount,c.co_kwonlyargcount,c.co_posonlyargcount,c.co_flags,
                c.co_exceptiontable,tuple(normalized(v) for v in c.co_consts))
    if isinstance(c,tuple):return tuple(normalized(v) for v in c)
    return c

def patch(text,diff):
    lines=text.replace('\r\n','\n').splitlines(keepends=True)
    parts=re.split(r'(?m)^(@@[^\n]*)\n',diff.replace('\r\n','\n'))
    offset=0;delta=0
    for part in range(1,len(parts),2):
        header,h=parts[part:part+2]
        rows=h.splitlines(keepends=True)
        old=[r[1:] for r in rows if r.startswith((' ','-'))]
        new=[r[1:] for r in rows if r.startswith((' ','+'))]
        # Compare ignoring end-of-file line terminators, keeping indentation exact.
        expected=[v.rstrip('\n') for v in old]
        candidates=[i for i in range(len(lines)-len(old)+1)
                    if [v.rstrip('\n') for v in lines[i:i+len(old)]]==expected]
        if not candidates:raise ValueError('Diff context absent')
        numbered=re.match(r'@@ -(\d+)',header)
        if numbered:
            expected_position=int(numbered.group(1))-1+delta
            i=min(candidates,key=lambda x:abs(x-expected_position))
        else:
            anchor=header[2:].strip()
            if anchor:
                anchors=[n for n,v in enumerate(lines) if v.strip()==anchor]
                if anchors:offset=max(offset,anchors[0]+1)
            after=[i for i in candidates if i>=offset]
            i=after[0] if after else candidates[0]
        lines[i:i+len(old)]=new;offset=i+len(new);delta+=len(new)-len(old)
    return ''.join(lines)

targets={}
for p in (BASE/'ats_studio').rglob('*.pyc'):
    rel=p.relative_to(BASE).with_suffix('.py').as_posix()
    targets[rel]=marshal.loads(p.read_bytes()[16:])
states={};matches={};failures=[]
logical={}
def check(rel,source,path,line):
    if rel not in targets:return
    try:c=compile(source,targets[rel].co_filename,'exec',optimize=0)
    except Exception:return
    if normalized(c)==normalized(targets[rel]):
        matches[rel]=dict(source=source,path=path,line=line,sha256=hashlib.sha256(source.encode()).hexdigest())

class MemoryPath:
    def __init__(self,p='.'):
        self.p=str(p).replace('\\','/')
    def __str__(self):return self.p
    def __truediv__(self,other):return MemoryPath(self.p+'/'+str(other))
    @property
    def parent(self):return MemoryPath(self.p.rsplit('/',1)[0])
    @property
    def name(self):return self.p.rsplit('/',1)[-1]
    @property
    def stem(self):return self.name.rsplit('.',1)[0]
    @property
    def suffix(self):return '.'+self.name.rsplit('.',1)[-1] if '.' in self.name else ''
    def key(self):
        if 'ats_studio/' in self.p:return 'ats_studio/'+self.p.split('ats_studio/',1)[1]
        raise PermissionError('Outside app source')
    def read_text(self,**kw):return logical[self.key()]
    def write_text(self,value,**kw):
        key=self.key()
        if not key.endswith('.py'):raise PermissionError('Not Python source')
        logical[key]=value;check(key,value,'history shell write',CURRENT_LINE)
        return len(value)
    def mkdir(self,**kw):pass
    def exists(self):
        try:return self.key() in logical
        except:return False
    def glob(self,*args):return []
    def resolve(self):return self

def restricted_import(name,*args):
    if name=='pathlib':return types.SimpleNamespace(Path=MemoryPath)
    if name in {'re','json','hashlib','ast'}:return __import__(name,*args)
    raise ImportError('History replay disallows '+name)

def replay_command(payload):
    code=payload.get('input',payload.get('arguments',''))
    templates=re.findall(r'(?:String\.raw)?`(.*?)`',code,re.S)
    if payload.get('name')=='apply_patch':patches=[code]
    else:
        patches=[]
        for m in re.finditer(r'tools\.apply_patch\(\s*("(?:[^"\\]|\\.)*")',code):
            try:patches.append(json.loads(m.group(1)))
            except:pass
    patches.extend(t for t in templates if t.startswith('*** Begin Patch'))
    for p in patches:
        sections=re.split(r'(?m)^\*\*\* (Add|Update|Delete) File: ([^\n]+)\n',p)
        for i in range(1,len(sections),3):
            kind,path,body=sections[i:i+3]
            path=path.replace('\\','/');rel='ats_studio/'+path.split('ats_studio/',1)[1] if 'ats_studio/' in path else ''
            if not rel.endswith('.py'):continue
            body=body.split('*** End Patch',1)[0].split('*** Move to:',1)[0]
            if kind=='Add':logical[rel]=''.join(v[1:]+'\n' for v in body.splitlines() if v.startswith('+'))
            elif kind=='Update' and rel in logical:
                try:logical[rel]=patch(logical[rel],body)
                except:continue
            else:continue
            check(rel,logical[rel],'history patch',CURRENT_LINE)
    commands=[]
    for m in re.finditer(r'cmd\s*:\s*("(?:[^"\\]|\\.)*")',code):
        try:commands.append(json.loads(m.group(1)))
        except:pass
    commands.extend(t for t in templates if '.write_text(' in t)
    for cmd in commands:
        if '.write_text(' not in cmd:continue
        scripts=re.findall(r"@'\s*\n(.*?)\n'@",cmd,re.S)
        if not scripts and cmd.lstrip().startswith(('from pathlib','import ')):scripts=[cmd]
        for source in scripts:
            if 'ats_studio' not in source:continue
            safe=dict(vars(__import__('builtins')))
            safe['__import__']=restricted_import
            safe['open']=lambda *a,**k:(_ for _ in ()).throw(PermissionError('No real filesystem'))
            try:exec(compile(source,'<history edit>','exec'),{'__builtins__':safe})
            except Exception:pass

# Some unmodified files already remain in the old workspace.
for rel in targets:
    p=ROOT.parent/rel
    if p.exists():
        logical[rel]=p.read_text(encoding='utf8');check(rel,logical[rel],str(p),'workspace')
for number,line in enumerate(LOG.open(encoding='utf8'),1):
    if 'ats_studio' not in line:continue
    CURRENT_LINE=number
    payload=json.loads(line).get('payload',{})
    if payload.get('type')=='custom_tool_call':replay_command(payload);continue
    item=payload.get('item',{})
    if item.get('type')!='FileChange':continue
    for raw,d in item.get('changes',{}).items():
        path=raw.replace('\\','/')
        if '/ats_studio/' not in path or not path.endswith('.py'):continue
        rel='ats_studio/'+path.split('/ats_studio/',1)[1]
        if d.get('type')=='add':states[path]=d['content']
        elif d.get('type')=='delete':states.pop(path,None);continue
        elif d.get('type')=='update':
            base=logical.get(rel,states.get(path))
            if base is None:continue
            try:states[path]=patch(base,d['unified_diff'])
            except Exception as e:
                try:states[path]=patch(states[path],d['unified_diff'])
                except:failures.append(dict(line=number,path=path,error=str(e)));continue
        else:continue
        logical[rel]=states[path]
        check(rel,states[path],path,number)
for rel,m in matches.items():
    dest=BASE/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(m.pop('source'),encoding='utf8')
report=dict(matched=matches,missing=sorted(set(targets)-set(matches)),patch_failures=failures)
(ROOT/'SOURCE_RECOVERY_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf8')
for rel,source in logical.items():
    if rel in targets and rel not in matches:
        dest=ROOT/'candidates'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(source,encoding='utf8')
print(json.dumps(dict(matched=len(matches),missing=report['missing'],patch_failures=len(failures)),indent=2))
