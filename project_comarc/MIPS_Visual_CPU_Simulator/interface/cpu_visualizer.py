# NEW: responsive, theme-aware functional CPU datapath
import tkinter as tk
class CPUDiagram(tk.Canvas):
 def __init__(self,parent,**kwargs):
  super().__init__(parent,height=150,highlightthickness=0,**kwargs)
  self.dark=True;self.step=None
  self.bind('<Configure>',lambda _:self.draw())
 def set_theme(self,dark):self.dark=dark;self.draw()
 def show_step(self,step):self.step=step;self.draw()
 def draw(self):
  self.delete('all');w=max(600,self.winfo_width());bg='#101b2e' if self.dark else '#f1f5fb';card='#1c2d46' if self.dark else '#ffffff';fg='#e7eefb' if self.dark else '#24344a';muted='#93a7c5' if self.dark else '#64748b';accent='#5eead4' if self.dark else '#087f75'
  self.configure(bg=bg);labels=['Program Counter','Instruction Fetch','Decode / Registers','ALU','Memory / Writeback'];pad=13;gap=12;bw=(w-2*pad-4*gap)/5;y=17
  active=self.step is not None
  for j,label in enumerate(labels):
   x=pad+j*(bw+gap);highlight=active and (j<3 or (j==3 and self.step.alu_text) or (j==4 and (self.step.mem_reads or self.step.mem_writes or self.step.reg_changes)))
   self.create_rectangle(x,y,x+bw,y+80,fill=card,outline=accent if highlight else muted,width=2 if highlight else 1)
   self.create_text(x+bw/2,y+24,text=f'{j+1:02}',fill=accent if highlight else muted,font=('Segoe UI',12,'bold'))
   self.create_text(x+bw/2,y+55,text=label,fill=fg,font=('Segoe UI',9,'bold'),width=bw-8)
   if j<4:self.create_line(x+bw+2,y+40,x+bw+gap-2,y+40,arrow=tk.LAST,fill=accent if active else muted,width=2)
  msg='Load a program, then select Step to inspect the datapath'
  if self.step:msg=f'Step {self.step.step_no:,}   •   {self.step.instr.op}   •   PC 0x{self.step.pc_before:08X} → 0x{self.step.pc_after:08X}   •   {self.step.alu_text or "control flow"}'
  self.create_text(pad,123,text=msg,anchor='w',fill=fg,font=('Segoe UI',10),width=w-2*pad)
