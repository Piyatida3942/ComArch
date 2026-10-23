# NEW: GUI-facing application controller
from pathlib import Path
import copy
from simulator.contract import *
from simulator.assembler import assemble_file
from simulator.cpu import CPU
from reference.reference import factorial_ref,ncr_ref
ROOT=Path(__file__).resolve().parents[1]
class Controller:
 def __init__(self,scheduler=None,on_update=None):
  self.scheduler=scheduler;self.on_update=on_update;self.cpu=CPU();self.program=None;self.mode='idle';self.message='';self.kind='factorial';self.algo=None;self.n=0;self.r=None;self.turbo=False;self.running=False;self._history=[];self._history_limit=500
 def validate_input(self,kind,algo,n_text,r_text):
  try:n=int(n_text);r=int(r_text) if kind=='ncr' else None
  except (TypeError,ValueError):return False,'กรุณากรอกจำนวนเต็มให้ครบ',None
  if kind not in ('factorial','ncr'):return False,'ชนิดโปรแกรมไม่ถูกต้อง',None
  spec=PROGRAM_SPECS[spec_key(kind,algo)]
  if n<0 or n>spec.n_max or (r is not None and (r<0 or r>n)):return False,f'กรุณาใช้ n = 0..{spec.n_max} และ 0 <= r <= n',None
  return True,'ถูกต้อง',(n,r)
 def load(self,kind,algo,n,r):
  self.pause();self._history.clear();self.kind=kind;self.algo=algo;self.n=n;self.r=r
  spec=PROGRAM_SPECS[spec_key(kind,algo)];self.program=assemble_file(str(ROOT/spec.asm_path));self.cpu.load(self.program,{4:n,5:r or 0});self.mode='ready';self.message='พร้อมทำงาน';self.turbo=False;return self._emit()
 def _emit(self):
  view=self.get_view()
  if self.on_update:self.on_update(view)
  return view
 def _finish(self):
  if self.cpu.status==Status.HALTED:
   self.mode='finished';ref=factorial_ref(self.n) if self.kind=='factorial' else ncr_ref(self.n,self.r)
   self.message=('✔ ผลลัพธ์ตรงกับ Reference' if self.cpu.regs[3]==0 and self.cpu.regs[2]==ref else '✘ ผลลัพธ์ไม่ตรง Reference')
  elif self.cpu.status in Status.ERRORS:self.mode='error';self.message=self.cpu.error or self.cpu.status
 def step(self):
  if self.program and self.cpu.status not in (Status.HALTED,*Status.ERRORS):
   self._history.append((copy.deepcopy(self.cpu),self.mode,self.message));self._history=self._history[-self._history_limit:];self.cpu.step();self._finish();self.mode='paused' if self.mode not in ('finished','error') else self.mode
  return self._emit()
 def run(self,steps_per_tick=1,delay_ms=500):
  self.pause();self.running=True;self.mode='running';self.turbo=steps_per_tick>50
  # Schedule individual CPU steps for learning; do not discard Back history.
  def tick():
   if not self.running:return
   for _ in range(steps_per_tick):
    if self.cpu.status in (Status.HALTED,*Status.ERRORS):break
    if self.cpu.counters['instr']>=self.cpu.max_steps:
     self.cpu.status=Status.MAX_STEPS;self.cpu.error='Maximum steps exceeded';break
    if not self.turbo:
     self._history.append((copy.deepcopy(self.cpu),self.mode,self.message))
     self._history=self._history[-self._history_limit:]
    self.cpu.step()
   self._finish();self._emit()
   if self.mode in ('finished','error'):self.running=False
   elif self.scheduler:self.scheduler(delay_ms,tick)
   else:
    # In headless mode finish iteratively, not recursively.
    while self.running and self.mode not in ('finished','error'):
     for _ in range(steps_per_tick):
      if self.cpu.status in (Status.HALTED,*Status.ERRORS):break
      self.cpu.step()
     self._finish()
    self._emit()
  tick()
 def pause(self):self.running=False
 def reset(self):
  self.pause();self._history.clear();self.cpu.reset();self.mode='ready';self.message='Reset';return self._emit()
 def back_step(self):
  self.pause()
  if self._history:
   self.cpu,self.mode,self.message=self._history.pop()
   self.mode='paused' if self.mode not in ('idle','ready') else self.mode
  return self._emit()
 @property
 def can_back(self):return bool(self._history)
 def get_view(self):
  state=self.cpu.get_state() if self.program else None
  return ViewState(self.mode,self.program,state,self.cpu.last,self.cpu.trace,state.regs[2] if state and self.mode=='finished' and state.regs[3]==0 else None,state.regs[3] if state else None,self.message,self.turbo)
 def run_headless(self,kind,algo,n,r):
  spec=PROGRAM_SPECS[spec_key(kind,algo)];cpu=CPU();cpu.load(assemble_file(str(ROOT/spec.asm_path)),{4:n,5:r or 0});res=cpu.run();state=res.state
  ref=factorial_ref(n) if kind=='factorial' else ncr_ref(n,r)
  return CompareRow(n,r or 0,spec.key,state.regs[2] if state.status==Status.HALTED and state.regs[3]==0 else None,state.status,state.regs[3],state.counters,state.regs[2]==ref if state.status==Status.HALTED and state.regs[3]==0 else None)
 def compare(self,cases,methods):
  rows=[]
  for n,r in cases:
   for method in methods:rows.append(self.run_headless('factorial' if method=='factorial' else 'ncr','optimized' if method=='nck_optimized' else 'factorial_based',n,r))
  return rows
 def compare_async(self,cases,methods,on_progress,on_done):
  rows=[];jobs=[(n,r,m) for n,r in cases for m in methods]
  def tick():
   if not jobs:on_done(rows);return
   n,r,m=jobs.pop(0);rows.append(self.run_headless('ncr','optimized' if m=='nck_optimized' else 'factorial_based',n,r));on_progress(len(rows),len(rows)+len(jobs))
   if self.scheduler:self.scheduler(1,tick)
   else:tick()
  tick()
