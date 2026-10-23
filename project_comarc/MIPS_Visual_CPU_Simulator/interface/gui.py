# MODIFIED: Two-screen guided MIPS simulator, with optional technical drill-down.
import tkinter as tk
from math import factorial, comb
from tkinter import ttk
from integration.controller import Controller
from simulator.contract import REG_NAMES, hex8
from .cpu_visualizer import CPUDiagram

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MIPS Visual CPU Simulator')
        self.geometry('1160x790')
        self.minsize(890, 610)
        self.dark = tk.BooleanVar(value=True)
        self.kind = tk.StringVar(value='factorial')
        self.algo = tk.StringVar(value='optimized')
        self.n = tk.StringVar(value='5')
        self.r = tk.StringVar(value='2')
        self.details = tk.BooleanVar(value=True)
        self.speed = tk.StringVar(value='1× · Learn')
        self.message = tk.StringVar(value='Choose a program and enter your values.')
        self.controller = Controller(scheduler=self.after, on_update=self.render)
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.palette = {}
        self.page = None
        self.apply_theme()
        self.show_setup()

    def apply_theme(self):
        dark = self.dark.get()
        self.palette = dict(bg='#0B1220' if dark else '#F4F7FB',
                            card='#162237' if dark else '#FFFFFF',
                            elevated='#22334D' if dark else '#EAF0F8',
                            fg='#F1F5FB' if dark else '#15243B',
                            muted='#A0B2CE' if dark else '#5B6C83',
                            accent='#5EEAD4' if dark else '#087F75',
                            border='#31425B' if dark else '#D8E1EC')
        p=self.palette
        self.configure(bg=p['bg'])
        s=self.style
        s.configure('.',font=('Segoe UI',11),background=p['bg'],foreground=p['fg'])
        s.configure('TFrame',background=p['bg'])
        s.configure('Card.TFrame',background=p['card'])
        s.configure('TLabel',background=p['bg'],foreground=p['fg'])
        s.configure('Card.TLabel',background=p['card'],foreground=p['fg'])
        s.configure('Muted.TLabel',background=p['bg'],foreground=p['muted'])
        s.configure('CardMuted.TLabel',background=p['card'],foreground=p['muted'])
        s.configure('Hero.TLabel',background=p['bg'],foreground=p['fg'],font=('Segoe UI',25,'bold'))
        s.configure('Section.TLabel',background=p['bg'],foreground=p['fg'],font=('Segoe UI',16,'bold'))
        s.configure('Metric.TLabel',background=p['card'],foreground=p['accent'],font=('Segoe UI',17,'bold'))
        s.configure('Answer.TLabel',background=p['accent'],foreground=p['bg'],font=('Segoe UI',14,'bold'),padding=(12,6))
        s.configure('TButton',padding=(16,11),background=p['elevated'],foreground=p['fg'],borderwidth=0)
        s.map('TButton',background=[('active',p['accent']),('disabled',p['card'])],foreground=[('active',p['bg']),('disabled',p['muted'])])
        s.configure('Accent.TButton',background=p['accent'],foreground=p['bg'],font=('Segoe UI',11,'bold'))
        s.map('Accent.TButton',background=[('active',p['accent'])])
        s.configure('TEntry',fieldbackground=p['card'],foreground=p['fg'],padding=9)
        s.configure('TCombobox',fieldbackground=p['card'],foreground=p['fg'],padding=8)
        s.configure('Treeview',background=p['card'],fieldbackground=p['card'],foreground=p['fg'],rowheight=27)
        s.configure('Treeview.Heading',background=p['elevated'],foreground=p['fg'])
        s.map('Treeview',background=[('selected',p['accent'])],foreground=[('selected',p['bg'])])

    def _clear(self):
        if self.page is not None:
            self.page.destroy()
        self.page=ttk.Frame(self,padding=(35,22))
        self.page.pack(fill='both',expand=True)
        top=ttk.Frame(self.page)
        top.pack(fill='x',pady=(0,24))
        ttk.Label(top,text='◈  MIPS VISUAL CPU',font=('Segoe UI',13,'bold')).pack(side='left')
        ttk.Button(top,text='☀  /  ☾  Theme',command=self.toggle_theme).pack(side='right')
        return self.page

    def toggle_theme(self):
        self.dark.set(not self.dark.get())
        self.apply_theme()
        if self.current_screen=='setup': self.show_setup()
        else: self.show_simulation()

    def show_setup(self):
        self.controller.pause()
        self.current_screen='setup'
        root=self._clear()
        ttk.Label(root,text='01  /  PROGRAM SETUP',style='Muted.TLabel').pack(anchor='w')
        ttk.Label(root,text='What would you like to simulate?',style='Hero.TLabel').pack(anchor='w',pady=(8,7))
        ttk.Label(root,text='Choose a calculation, enter its input, then explore MIPS execution one instruction at a time.',style='Muted.TLabel').pack(anchor='w',pady=(0,25))
        options=ttk.Frame(root)
        options.pack(fill='x',pady=(0,18))
        self.mode_buttons=[]
        for key,title,description in [('factorial','Factorial  (n!)','One input · Example: 5! = 120'),('ncr','Combination  (nCr)','Two inputs · Example: 5C2 = 10')]:
            frame=ttk.Frame(options,style='Card.TFrame',padding=20)
            frame.pack(side='left',fill='both',expand=True,padx=(0,12))
            btn=ttk.Radiobutton(frame,text=title,variable=self.kind,value=key,command=self.update_inputs)
            btn.pack(anchor='w')
            ttk.Label(frame,text=description,style='CardMuted.TLabel').pack(anchor='w',pady=(9,0))
            self.mode_buttons.append(btn)
        self.input_card=ttk.Frame(root,style='Card.TFrame',padding=24)
        self.input_card.pack(fill='x',pady=(0,14))
        ttk.Label(self.input_card,text='INPUT PARAMETERS',style='CardMuted.TLabel').pack(anchor='w',pady=(0,12))
        self.input_fields=ttk.Frame(self.input_card,style='Card.TFrame')
        self.input_fields.pack(anchor='w')
        ttk.Label(self.input_card,textvariable=self.message,style='CardMuted.TLabel',wraplength=820).pack(anchor='w',pady=(15,0))
        bottom=ttk.Frame(root)
        bottom.pack(fill='x',pady=(12,0))
        ttk.Button(bottom,text='Next  →  Open Simulator',style='Accent.TButton',command=self.next_page).pack(side='right')
        self.update_inputs()

    def update_inputs(self):
        for widget in self.input_fields.winfo_children():widget.destroy()
        self._input('n',self.n,0)
        if self.kind.get()=='ncr':
            self._input('r',self.r,1)
            ttk.Label(self.input_fields,text='Algorithm',style='Card.TLabel').grid(row=0,column=2,sticky='w',padx=(18,0))
            ttk.Combobox(self.input_fields,textvariable=self.algo,values=['optimized','factorial_based'],state='readonly',width=19).grid(row=1,column=2,padx=(18,0),sticky='w')
            self.message.set('Use integers 0 ≤ r ≤ n. Optimized and factorial-based algorithms produce the same result.')
        else:
            self.message.set('Enter an integer n. The simulator computes n! using MIPS assembly.')

    def _input(self,name,var,col):
        ttk.Label(self.input_fields,text=name,style='Card.TLabel').grid(row=0,column=col,sticky='w',padx=(0,18))
        ttk.Entry(self.input_fields,textvariable=var,width=13).grid(row=1,column=col,sticky='w',padx=(0,18),pady=(6,0))

    def next_page(self):
        kind=self.kind.get()
        ok,msg,values=self.controller.validate_input(kind,self.algo.get(),self.n.get(),self.r.get())
        if not ok:
            self.message.set('⚠  '+msg)
            return
        try:self.controller.load(kind,self.algo.get(),*values)
        except Exception as exc:
            self.message.set('⚠  Unable to load program: '+str(exc))
            return
        self.show_simulation()

    def show_simulation(self):
        self.current_screen='simulation'
        root=self._clear()
        # Vertical split: a compact simulation workspace and a draggable execution log.
        splitter=ttk.Panedwindow(root,orient='vertical')
        splitter.pack(fill='both',expand=True)
        upper=ttk.Frame(splitter)
        lower=ttk.Frame(splitter,style='Card.TFrame',padding=(10,8))
        splitter.add(upper,weight=4)
        splitter.add(lower,weight=1)
        self.after(100,lambda: self._set_initial_split(splitter))

        head=ttk.Frame(upper)
        head.pack(fill='x',pady=(0,8))
        ttk.Button(head,text='←  Inputs',command=self.show_setup).pack(side='left')
        mode='Factorial' if self.kind.get()=='factorial' else 'Combination'
        n=int(self.n.get());r=int(self.r.get()) if self.kind.get()=='ncr' else None
        formula=f'{n}!' if r is None else f'{n}C{r}'
        expected=factorial(n) if r is None else comb(n,r)
        ttk.Label(head,text=f'02  /  {mode}  ·  {formula}  =',style='Section.TLabel').pack(side='left',padx=(15,7))
        ttk.Label(head,text=f'{expected:,}',style='Answer.TLabel').pack(side='left')
        ttk.Label(head,text='Expected answer',style='Muted.TLabel').pack(side='left',padx=9)
        # Expected reference is shown from the beginning; simulated answer is shown only after HALT.
        ttk.Label(upper,text='Reference answer above  ·  Compare it with the simulated result when execution finishes.',style='Muted.TLabel').pack(anchor='w',pady=(0,9))
        metrics=ttk.Frame(upper)
        metrics.pack(fill='x',pady=(0,8))
        self.status=tk.StringVar();self.pc=tk.StringVar();self.count=tk.StringVar();self.answer=tk.StringVar()
        for name,var in [('CPU STATUS',self.status),('PROGRAM COUNTER',self.pc),('INSTRUCTIONS',self.count),('SIMULATED RESULT',self.answer)]:
            tile=ttk.Frame(metrics,style='Card.TFrame',padding=(11,8))
            tile.pack(side='left',fill='both',expand=True,padx=(0,8))
            ttk.Label(tile,text=name,style='CardMuted.TLabel',font=('Segoe UI',8,'bold')).pack(anchor='w')
            ttk.Label(tile,textvariable=var,style='Metric.TLabel').pack(anchor='w',pady=(3,0))
        canvas_frame=ttk.Frame(upper,style='Card.TFrame',padding=(11,8))
        canvas_frame.pack(fill='x',pady=(0,9))
        ttk.Label(canvas_frame,text='CPU EXECUTION PATH',style='Card.TLabel',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(0,4))
        self.diagram=CPUDiagram(canvas_frame)
        self.diagram.set_theme(self.dark.get())
        self.diagram.pack(fill='x')
        self.explain=tk.StringVar()
        ttk.Label(canvas_frame,textvariable=self.explain,style='CardMuted.TLabel',wraplength=1050).pack(anchor='w',pady=(4,0))

        # Controls stay immediately below the compact datapath, above the history panel.
        actions=ttk.Frame(upper)
        actions.pack(fill='x',pady=(1,10))
        self.back_button=ttk.Button(actions,text='◀  Back',command=self.back)
        self.back_button.pack(side='left',padx=(0,7))
        self.step_button=ttk.Button(actions,text='Step  ▶',style='Accent.TButton',command=self.step)
        self.step_button.pack(side='left',padx=(0,7))
        self.run_button=ttk.Button(actions,text='▶  Run',command=self.run)
        self.run_button.pack(side='left',padx=(0,7))
        ttk.Button(actions,text='Ⅱ  Pause',command=self.pause).pack(side='left',padx=(0,7))
        ttk.Button(actions,text='↺  Reset',command=self.reset).pack(side='left',padx=(0,7))
        ttk.Label(actions,text='Speed:',style='Muted.TLabel').pack(side='left',padx=(12,5))
        ttk.Combobox(actions,textvariable=self.speed,values=['1× · Learn','2×','5×','20×','Turbo'],state='readonly',width=12).pack(side='left')

        bar=ttk.Frame(lower,style='Card.TFrame')
        bar.pack(fill='x',pady=(0,5))
        ttk.Label(bar,text='EXECUTION HISTORY  ↕  Drag divider to expand',style='Card.TLabel',font=('Segoe UI',10,'bold')).pack(side='left')
        ttk.Checkbutton(bar,text='Show assembly / registers',variable=self.details,command=self.toggle_details).pack(side='right')
        ttk.Label(lower,text='Scroll through recorded instructions. Select a row to inspect its details; Back restores a previous CPU state.',style='CardMuted.TLabel').pack(anchor='w',pady=(0,5))
        self.detail_area=ttk.Frame(lower,style='Card.TFrame')
        self.detail_area.pack(fill='both',expand=True)
        self.toggle_details()
        self.render(self.controller.get_view())

    def _set_initial_split(self,splitter):
        try:
            h=splitter.winfo_height()
            if h>200:splitter.sashpos(0,int(h*.77))
        except tk.TclError:pass

    def toggle_details(self):
        for widget in self.detail_area.winfo_children():widget.destroy()
        self.instructions=None;self.registers=None
        history=ttk.Frame(self.detail_area,style='Card.TFrame')
        history.pack(side='left',fill='both',expand=True)
        cols=('Step','PC','Instruction','Effect')
        self.history_tree=ttk.Treeview(history,columns=cols,show='headings',height=5,selectmode='browse')
        for col,width in [('Step',70),('PC',120),('Instruction',250),('Effect',380)]:
            self.history_tree.heading(col,text=col)
            self.history_tree.column(col,width=width,anchor='w',stretch=(col=='Effect'))
        scroll=ttk.Scrollbar(history,orient='vertical',command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.history_tree.pack(fill='both',expand=True)
        self.history_tree.bind('<<TreeviewSelect>>',self.inspect_history)
        self.history_info=tk.StringVar(value='Select a step to see its operation and register changes.')
        ttk.Label(history,textvariable=self.history_info,style='CardMuted.TLabel',wraplength=740).pack(anchor='w',pady=(3,0))
        if self.details.get():
            right=ttk.Notebook(self.detail_area)
            right.pack(side='right',fill='both',expand=True,padx=(10,0))
            for title,cols,attr in [('Assembly',('PC','Instruction'),'instructions'),('Registers',('Register','Decimal','Hex'),'registers')]:
                panel=ttk.Frame(right,padding=4)
                right.add(panel,text=title)
                tree=ttk.Treeview(panel,columns=cols,show='headings',height=5)
                for c in cols:tree.heading(c,text=c);tree.column(c,width=120,anchor='w')
                sb=ttk.Scrollbar(panel,command=tree.yview)
                tree.configure(yscrollcommand=sb.set)
                sb.pack(side='right',fill='y');tree.pack(fill='both',expand=True)
                setattr(self,attr,tree)
        self.render(self.controller.get_view())

    def inspect_history(self,event=None):
        selection=self.history_tree.selection()
        if not selection:return
        try:idx=int(selection[0])
        except (ValueError,IndexError):return
        trace=self.controller.cpu.trace
        if idx>=len(trace):return
        s=trace[idx]
        changes=', '.join(f'${REG_NAMES[k]}: {old} → {new}' for k,(old,new) in s.reg_changes.items())
        detail=changes or s.alu_text or ('Branch taken' if s.branch_taken else 'No register change')
        self.history_info.set(f'Step {s.step_no:,} · {s.instr.raw} · {detail}')

    def refresh_history(self):
        tree=getattr(self,'history_tree',None)
        if tree is None or not tree.winfo_exists():return
        trace=self.controller.cpu.trace
        # The CPU stores the latest 5,000 trace entries; retain scroll position on refresh.
        old_count=len(tree.get_children())
        if old_count==len(trace) and getattr(self,'_history_last_no',None)==(trace[-1].step_no if trace else None):return
        selection=tree.selection()
        tree.delete(*tree.get_children())
        for i,s in enumerate(trace):
            effect=s.alu_text or ('Branch taken' if s.branch_taken else 'Branch not taken' if s.branch_taken is False else 'Control / data movement')
            tree.insert('','end',iid=str(i),values=(f'{s.step_no:,}',f'0x{s.pc_before:08X}',s.instr.raw,effect))
        self._history_last_no=trace[-1].step_no if trace else None
        if selection and tree.exists(selection[0]):tree.selection_set(selection[0])
        elif trace:tree.see(str(len(trace)-1))

    def step(self):self.controller.step()
    def back(self):self.controller.back_step()
    def run(self):
        if self.controller.program and self.controller.mode not in ('finished','error'):
            self.controller.run(steps_per_tick={'1× · Learn':1,'2×':1,'5×':1,'20×':2,'Turbo':200}.get(self.speed.get(),1),delay_ms={'1× · Learn':500,'2×':250,'5×':100,'20×':100,'Turbo':1}.get(self.speed.get(),500))
    def pause(self):
        self.controller.pause()
        if self.controller.mode=='running':self.controller.mode='paused'
        self.render(self.controller.get_view())
    def reset(self):
        if self.controller.program:self.controller.reset()

    def render(self,view):
        if getattr(self,'current_screen',None)!='simulation':return
        state=view.cpu
        self.status.set(view.mode.upper())
        self.pc.set(f'0x{state.pc:08X}' if state else '—')
        self.count.set(f'{state.counters["instr"]:,}' if state else '0')
        # $v0 is a working register until HALT; only present it as the final answer on success.
        self.answer.set(f'{view.result:,}' if view.mode=='finished' and view.result is not None else '—')
        self.diagram.show_step(view.last_step)
        self.refresh_history()
        if view.last_step:
            s=view.last_step
            self.explain.set(f'Step {s.step_no:,}: {s.instr.raw}   |   PC 0x{s.pc_before:08X} → 0x{s.pc_after:08X}   |   {s.alu_text or "Control / data movement"}')
        else:self.explain.set('Ready. Press Step to execute the first MIPS instruction.')
        if view.mode=='finished':self.explain.set(self.explain.get()+'   •   '+view.message)
        if view.mode=='error':self.explain.set('Execution error: '+view.message)
        self.back_button.configure(state='normal' if self.controller.can_back else 'disabled')
        self.step_button.configure(state='disabled' if view.mode in ('running','finished','error') else 'normal')
        self.run_button.configure(state='disabled' if view.mode in ('running','finished','error') else 'normal')
        if self.instructions is not None:
            tree=self.instructions;tree.delete(*tree.get_children())
            if view.program:
                for ins in view.program.instrs:
                    tree.insert('','end',values=(f'0x{ins.addr:08X}',ins.raw),tags=('current',) if state and state.pc==ins.addr else ())
                tree.tag_configure('current',background=self.palette['elevated'])
        if self.registers is not None:
            tree=self.registers;tree.delete(*tree.get_children())
            if state:
                for i,val in enumerate(state.regs):tree.insert('','end',values=('$'+REG_NAMES[i],val,hex8(val)))
