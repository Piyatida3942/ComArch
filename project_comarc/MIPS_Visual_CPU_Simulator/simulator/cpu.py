# NEW: functional single-cycle MIPS execution engine (no pipeline)
from collections import deque
from .contract import *
from .memory import Memory,MemoryAccessError
class CPU:
 def __init__(self,memory=None,max_steps=DEFAULT_MAX_STEPS):
  self.memory=memory or Memory();self.max_steps=max_steps;self.program=None;self._trace=deque(maxlen=TRACE_LIMIT);self.reset()
 def load(self,program,init_regs=None):
  self.program=program;self.initial=dict(init_regs or {});self.reset()
 def reset(self):
  self.memory.clear();self.regs=[0]*32;self.regs[29]=STACK_TOP
  for k,v in getattr(self,'initial',{}).items():self.regs[k]=s32(v)
  self.regs[0]=0;self.pc=self.program.entry if self.program else TEXT_BASE;self.status=Status.READY;self.error=None;self.counters=dict.fromkeys(COUNTER_KEYS,0);self._trace.clear();self.last=None
  if self.program:
   self.code={i.addr:i for i in self.program.instrs}
   for i in self.program.instrs:
    if i.hex8 is not None:self.memory.write_word(i.addr,int(i.hex8,16))
 def set_reg(self,idx,value):
  if not 0<=idx<32:raise ValueError('bad register')
  if idx:self.regs[idx]=s32(value)
 @property
 def trace(self):return list(self._trace)
 def get_state(self):return CPUState(self.pc,self.regs.copy(),self.memory.snapshot(),self.counters.copy(),self.status,self.error)
 def step(self):return self._execute(True)
 def _execute(self,record):
  if self.status in Status.ERRORS or self.status==Status.HALTED:return self.last
  i=self.code.get(self.pc) if self.program else None
  if i is None:self.status=Status.BAD_PC;self.error=f'Invalid PC {self.pc:#x}';return None
  oldpc=self.pc;oldregs=self.regs.copy() if record else None;op=i.op;r=self.regs;rs=r[i.rs];rt=r[i.rt];imm=i.imm;nextpc=self.pc+4;alu=None;br=None;reads=[];writes=[]
  def signed(v):
   if not -2147483648<=v<=2147483647:raise OverflowError('signed 32-bit overflow')
   return v
  try:
   if op in ('ADD','ADDU','SUB','SUBU','AND','OR','NOR','SLT','SLTU'):
    if op in ('ADD','ADDU'):v=rs+rt
    elif op in ('SUB','SUBU'):v=rs-rt
    elif op=='AND':v=rs&rt
    elif op=='OR':v=rs|rt
    elif op=='NOR':v=~(rs|rt)
    elif op=='SLT':v=int(rs<rt)
    else:v=int(u32(rs)<u32(rt))
    if op in ('ADD','SUB'):v=signed(v)
    if i.rd:r[i.rd]=s32(v)
    alu=f'{rs} {op} {rt} = {s32(v)}'
   elif op in ('ADDI','ADDIU','ANDI','ORI','SLTI','SLTIU'):
    if op in ('ADDI','ADDIU'):v=rs+imm
    elif op=='ANDI':v=rs&(imm&65535)
    elif op=='ORI':v=rs|(imm&65535)
    elif op=='SLTI':v=int(rs<imm)
    else:v=int(u32(rs)<u32(imm))
    if op=='ADDI':v=signed(v)
    if i.rt:r[i.rt]=s32(v)
    alu=f'{rs} {op} {imm} = {s32(v)}'
   elif op=='LUI':
    if i.rt:r[i.rt]=s32((imm&65535)<<16)
   elif op in ('SLL','SRL'):
    v=u32(rt)<<i.shamt if op=='SLL' else u32(rt)>>i.shamt
    if i.rd:r[i.rd]=s32(v)
   elif op in ('BEQ','BNE'):
    br=(rs==rt) if op=='BEQ' else (rs!=rt)
    if br:nextpc+=imm*4
   elif op in ('J','JAL'):
    if op=='JAL':r[31]=s32(nextpc)
    nextpc=i.target
   elif op=='JR':nextpc=rs
   elif op in ('LW','SW'):
    addr=rs+imm
    if op=='LW':
     v=self.memory.read_word(addr)
     if i.rt:r[i.rt]=s32(v)
     if record:reads.append(addr)
    else:
     self.memory.write_word(addr,rt)
     if record:writes.append((addr,u32(rt)))
   elif op=='HALT':nextpc=self.pc
   else:raise NotImplementedError(op)
  except (OverflowError,MemoryAccessError,NotImplementedError) as e:
   self.status=Status.OVERFLOW if isinstance(e,OverflowError) else Status.BAD_MEMORY if isinstance(e,MemoryAccessError) else Status.BAD_OPCODE
   self.error=f'{op} at {self.pc:#x}: {e}'
   result=StepResult(self.counters['instr']+1,oldpc,oldpc,i,False,status=self.status,error=self.error)
   self.last=result;self._trace.append(result);return result
  r[0]=0;self.pc=nextpc;self.counters['instr']+=1
  if op in ('BEQ','BNE'):
   self.counters['branch']+=1
   if br:self.counters['branch_taken']+=1
  if op in ('LW',):self.counters['mem_read']+=1
  if op in ('SW',):self.counters['mem_write']+=1
  if op=='JAL':self.counters['call']+=1
  if op in ('ADD','ADDU','SUB','SUBU','AND','OR','NOR','SLT','SLTU','SLL','SRL','ADDI','ADDIU','ANDI','ORI','SLTI','SLTIU','LUI'):self.counters['arith']+=1
  if op=='HALT':self.status=Status.HALTED
  else:self.status=Status.RUNNING
  if record:
   changes={n:(v,r[n]) for n,v in enumerate(oldregs) if v!=r[n]}
   result=StepResult(self.counters['instr'],oldpc,self.pc,i,True,changes,reads,writes,alu,br,self.status)
   self._trace.append(result);self.last=result;return result
  return None
 def run(self,stop_after=None,record_trace=False):
  start=self.counters['instr'];limit=stop_after if stop_after is not None else self.max_steps
  while self.status not in (Status.HALTED,*Status.ERRORS) and self.counters['instr']-start<limit:
   if self.counters['instr']>=self.max_steps:self.status=Status.MAX_STEPS;self.error='Maximum steps exceeded';break
   self._execute(record_trace)
  return RunResult(self.status in (Status.HALTED,*Status.ERRORS),self.status,self.counters['instr']-start,self.get_state())
