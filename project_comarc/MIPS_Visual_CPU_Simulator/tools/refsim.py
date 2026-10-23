# NEW: independent reference interpreter from specification
"""Independent mini MIPS interpreter used ONLY to validate the seed .asm files (not cpuSimV7)."""

import re, math

REGS={'zero':0,'v0':2,'v1':3,'a0':4,'a1':5,'sp':29,'ra':31}

for i in range(8): REGS[f't{i}']=8+i; REGS[f's{i}']=16+i

REGS['t8']=24; REGS['t9']=25

def reg(s):

    s=s.lstrip('$'); return int(s) if s.isdigit() else REGS[s]

def s32(x): x&=0xffffffff; return x-(1<<32) if x>>31 else x

class Overflow(Exception): pass

def assemble(text):

    base=0x2000; lines=[]; labels={}; pc=None

    for raw in text.splitlines():

        l=raw.split('#')[0].strip()

        if not l: continue

        if l.startswith('.ORG'): base=int(l.split()[1],0); pc=base; continue

        if pc is None: pc=base

        m=re.match(r'^(\w+):\s*(.*)$',l)

        if m:

            labels[m.group(1)]=pc; l=m.group(2)

            if not l: continue

        lines.append((pc,l)); pc+=4

    return base,lines,labels

def run(text,a0,a1=0,maxsteps=50_000_000):

    base,lines,labels=assemble(text)

    prog={pc:l for pc,l in lines}

    R=[0]*32; R[4]=a0; R[5]=a1; R[29]=0x1FFFC

    mem={}; pc=base; steps=0; cnt={'branch':0,'mem_r':0,'mem_w':0,'call':0}

    while True:

        l=prog[pc]; p=l.replace(',',' ').split(); op=p[0].upper(); a=p[1:]

        steps+=1

        if steps>maxsteps: raise RuntimeError("max steps")

        npc=pc+4

        def chk(v):

            if not -2**31<=v<2**31: raise Overflow(f"{op} at {pc:#x}")

            return v

        if op=='ADD': R[reg(a[0])]=chk(R[reg(a[1])]+R[reg(a[2])])

        elif op=='SUB': R[reg(a[0])]=chk(R[reg(a[1])]-R[reg(a[2])])

        elif op=='SLT': R[reg(a[0])]=int(R[reg(a[1])]<R[reg(a[2])])

        elif op=='ADDI': R[reg(a[0])]=chk(R[reg(a[1])]+int(a[2],0))

        elif op=='SLTI': R[reg(a[0])]=int(R[reg(a[1])]<int(a[2],0))

        elif op in('BEQ','BNE'):

            cnt['branch']+=1

            eq=R[reg(a[0])]==R[reg(a[1])]

            if eq==(op=='BEQ'): npc=labels[a[2]]

        elif op=='J': npc=labels[a[0]]

        elif op=='JAL': R[31]=pc+4; npc=labels[a[0]]; cnt['call']+=1

        elif op=='JR': npc=R[reg(a[0])]

        elif op in('LW','SW'):

            off,b=re.match(r'(-?\w+)\((\$?\w+)\)',a[1]).groups(); ad=R[reg(b)]+int(off,0)

            if op=='LW': R[reg(a[0])]=mem.get(ad,0); cnt['mem_r']+=1

            else: mem[ad]=R[reg(a[0])]; cnt['mem_w']+=1

        elif op=='HALT': break

        else: raise ValueError(op)

        R[0]=0; pc=npc

    return R[2],R[3],steps,cnt,R
