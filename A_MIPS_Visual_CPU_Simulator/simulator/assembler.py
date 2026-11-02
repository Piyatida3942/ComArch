# NEW: two-pass assembler, named registers, labels and MIPS machine encoding
import re
from pathlib import Path
from .contract import Instr,Program,AsmError,TEXT_BASE
from .isa import INSTR_TABLE,reg_number,encode

def assemble(source:str,name:str='program')->Program:
    labels={};lines=[];pc=TEXT_BASE;first=pc;pending=None
    for ln,raw in enumerate(source.splitlines(),1):
        line=raw.split('#')[0].strip()
        if not line:continue
        if line.upper().startswith('.ORG'):
            try:pc=int(line.split()[1],0);first=pc
            except Exception:raise AsmError(ln,'invalid .ORG')
            continue
        while True:
            m=re.match(r'^([A-Za-z_]\w*):\s*(.*)$',line)
            if not m:break
            if m[1] in labels:raise AsmError(ln,'duplicate label '+m[1])
            labels[m[1]]=pc;pending=m[1];line=m[2]
        if line:lines.append((ln,pc,line,pending));pc+=4;pending=None
    out=[]
    def reg(t,ln):
        try:return reg_number(t)
        except AsmError:raise AsmError(ln,'invalid register '+t)
    def number(t,ln):
        try:return int(t,0)
        except ValueError:raise AsmError(ln,'invalid immediate '+t)
    for idx,(ln,addr,raw,label) in enumerate(lines):
        p=raw.replace(',',' ').split();op=p[0].upper();a=p[1:]
        if op not in INSTR_TABLE:raise AsmError(ln,'unknown instruction '+op)
        ent=INSTR_TABLE[op]
        if ent['status']=='UNSUPPORTED':raise AsmError(ln,'unsupported instruction '+op)
        kind=ent['kind'];rd=rs=rt=shamt=imm=target=0
        form=ent['form']
        try:
            if form=='rd rs rt':rd,rs,rt=map(lambda x:reg(x,ln),a)
            elif form=='rd rt shamt':rd,rt=reg(a[0],ln),reg(a[1],ln);shamt=number(a[2],ln)
            elif form=='rs':rs=reg(a[0],ln)
            elif form=='rt rs imm':rt,rs=reg(a[0],ln),reg(a[1],ln);imm=number(a[2],ln)
            elif form=='rt imm':rt=reg(a[0],ln);imm=number(a[1],ln)
            elif form=='rs rt imm':
                rs,rt=reg(a[0],ln),reg(a[1],ln)
                imm=(labels[a[2]]-addr-4)//4 if a[2] in labels else number(a[2],ln)
            elif form=='target':target=labels[a[0]] if a[0] in labels else number(a[0],ln)
            elif form=='rt off(rs)':
                m=re.fullmatch(r'([^()]+)\(([^()]+)\)',a[1]);
                if not m:raise AsmError(ln,'bad memory operand')
                rt=reg(a[0],ln);imm=number(m[1],ln);rs=reg(m[2],ln)
            elif a:raise AsmError(ln,'unexpected operands')
        except (IndexError,ValueError,TypeError):raise AsmError(ln,'wrong operands for '+op)
        if kind=='I' and not (-32768<=imm<=32767 or op in ('ANDI','ORI','LUI') and 0<=imm<=65535):raise AsmError(ln,'immediate out of range')
        if not 0<=shamt<=31:raise AsmError(ln,'shamt out of range')
        h,b=encode(op,kind,rd,rs,rt,shamt,imm,target)
        out.append(Instr(idx,addr,ln,raw,label,op,kind,rd,rs,rt,shamt,imm,target,h,b))
    return Program(name,first,out,labels,source,labels.get('main',first))
def assemble_file(path:str)->Program:return assemble(Path(path).read_text(encoding='utf-8'),Path(path).stem)
