# NEW (ปรับจาก gui.py ฉบับเดิม): Main menu / Calculate / Simulator, ธีม Day & Night, English + ไทย
# ใช้ Controller เดิมทุกเมธอด (validate_input, load, step, back_step, run, pause, reset, run_headless, get_view, can_back)
# ไม่แก้ simulator/, integration/, reference/, programs/, main.py, interface/
import queue
import sys
import threading
import traceback
import tkinter as tk
from tkinter import ttk

from integration.controller import Controller
from simulator.contract import PROGRAM_SPECS, REG_NAMES, hex8, s32, u32, spec_key
from reference.reference import factorial_ref, ncr_ref

from . import explain as ex
from .cpu_visualizer import CPUDiagram
from .home_anim import HomeHero
from .i18n import tr
from .theme import DEFAULT_THEME, THEME_ORDER, THEMES, make_fonts, ui_scale
from .widgets import (Centered, Flow, Pill, ScrollFrame, Segmented, apply_ttk_style, autowrap,
                      chip, draw_icon, make_card, round_rect)

# ความเร็ว: (คำสั่งต่อรอบ, หน่วงมิลลิวินาที) -- เหมือน GUI เดิม ยกเว้น Turbo 200 -> 1000 คำสั่ง/รอบ (วาดหน้าจอน้อยลง 5 เท่า)
# speed เป็นตัวคูณความเร็วจริง: x1 = 0.5, x2 = 1, x10 = 10
# Controller รับค่าเป็นช่วงหน่วงต่อ tick (ms) จึงแปลงจาก 1000 / speed
SPEEDS = {'x1': (1, 2000), 'x2': (1, 1000), 'x10': (1, 100)}
SPEED_ORDER = ['x1', 'x2', 'x10']
DEFAULT_N, DEFAULT_R = '5', '2'
HISTORY_ROWS = 300          # แสดงประวัติล่าสุดกี่ขั้น (ให้ไม่รก/ไม่หนัก)

TOPICS = {
    'factorial': dict(math='n!', color='pink', glyph='n!', example='5! = 120'),
    'ncr': dict(math='nCr', color='blue', glyph='nCr', example='5C2 = 10'),
}
ALGO_KEYS = ['optimized', 'factorial_based']
TONE_COLOR = {'alu': 'blue', 'branch': 'yellow', 'jump': 'violet', 'mem': 'green',
              'halt': 'green', 'error': 'red'}


def _enable_dpi_awareness():
    """บอก Windows ว่าโปรแกรมรองรับจอความละเอียดสูง -- ไม่งั้น Windows จะขยายภาพทั้งหน้าต่างให้ใหญ่เอง ทำให้เบลอ/แตก"""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:                                  # noqa: BLE001
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:                                      # noqa: BLE001
        pass


class RoundBar(tk.Canvas):
    """แถบมนความสูงคงที่ (ใช้เป็นตัวบอกขั้นของ CPU Execution Status) เปลี่ยนสีได้โดยไม่สร้างวิดเจ็ตใหม่"""

    def __init__(self, parent, color, bg, height=10):
        super().__init__(parent, width=1, height=height, bg=bg, highlightthickness=0, bd=0)
        self._color = color
        self.bind('<Configure>', lambda _e: self._draw())

    def set_color(self, color):
        if color != self._color:
            self._color = color
            self._draw()

    def _draw(self):
        self.delete('all')
        w, h = max(self.winfo_width(), 2), max(self.winfo_height(), 2)
        r = h / 2
        c = self._color
        self.create_oval(0, 0, h, h, fill=c, outline=c)
        self.create_oval(w - h - 1, 0, w - 1, h, fill=c, outline=c)
        self.create_rectangle(r, 0, w - r - 1, h, fill=c, outline=c)


class App(tk.Tk):
    def __init__(self):
        _enable_dpi_awareness()                            # ต้องเรียกก่อนสร้างหน้าต่างแรก
        super().__init__()
        self.lang = 'en'
        self.theme_key = DEFAULT_THEME
        self.t = THEMES[self.theme_key]
        self.f = make_fonts(self)
        self.scale = ui_scale(self)
        self.title('MIPS Visual CPU Simulator')
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(int(1180 * self.scale), sw - 60), min(int(860 * self.scale), sh - 110)
        self.geometry(f'{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}')
        self.minsize(min(int(740 * self.scale), w), min(int(620 * self.scale), h))
        self.n_var = tk.StringVar(value=DEFAULT_N)
        self.r_var = tk.StringVar(value=DEFAULT_R)
        self.algo_var = tk.StringVar(value='optimized')
        self.speed_key = 'x1'
        self._active_control = None
        self.controller = Controller(scheduler=self.after, on_update=self.render)
        self.screen, self.topic, self.tab = 'home', 'factorial', 'calc'
        self.header = self.content = self.hero = self._err_bar = None
        self._sim_ready = self._calc_ready = False
        self._loaded_key = None
        self._calc_token, self._calc_pending = 0, 0
        self._calc_q = queue.Queue()
        self._debounce = None
        self._run_blocked, self._run_delay = False, 2000
        self._prev_step_no = None
        self.diagram = None
        self._skey = 'factorial'
        self._by_addr, self._always, self._formula = {}, set(), '?'
        self._tech_visible, self._tech_mode = False, 'asm'
        self.n_var.trace_add('write', lambda *a: self._input_changed())
        self.r_var.trace_add('write', lambda *a: self._input_changed())
        self.algo_var.trace_add('write', lambda *a: self._input_changed())
        self.bind_all('<MouseWheel>', self._on_wheel)
        self.bind_all('<Button-4>', lambda e: self._on_wheel(e, -1))
        self.bind_all('<Button-5>', lambda e: self._on_wheel(e, 1))
        self.bind('<Right>', lambda e: self._shortcut(self.step))
        self.bind('<Left>', lambda e: self._shortcut(self.back))
        self.bind('<space>', lambda e: self._shortcut(self.toggle_run))
        self._build_all()

    def tr(self, key, **kw):
        return tr(self.lang, key, **kw)

    # ================================================================ แจ้ง error บนหน้าจอ (ไม่ให้เงียบหาย)
    def report_callback_exception(self, exc, val, tb):
        traceback.print_exception(exc, val, tb)            # ยังพิมพ์ใน terminal เหมือนเดิม
        try:
            self._show_error(f'{exc.__name__}: {val}')
        except Exception:                                  # noqa: BLE001
            pass

    def _show_error(self, msg):
        if self._err_bar is not None:
            try:
                self._err_bar.destroy()
            except tk.TclError:
                pass
        t = self.t
        bar = tk.Frame(self, bg=t['red_soft'], highlightthickness=2, highlightbackground=t['red'])
        if self.content is not None:
            bar.pack(side='bottom', fill='x', before=self.content)
        else:
            bar.pack(side='bottom', fill='x')
        lbl = tk.Label(bar, text=self.tr('ui_error', err=msg), bg=t['red_soft'], fg=t['red_ink'],
                       font=self.f['small_b'], justify='left', anchor='w')
        lbl.pack(side='left', fill='x', expand=True, padx=14, pady=8)
        autowrap(lbl, bar, pad=140)
        Pill(bar, text=self.tr('close'), kind='ghost', theme=t, font=self.f['btn'], height=int(32 * self.scale),
             command=lambda: bar.destroy(), bg=t['red_soft']).pack(side='right', padx=12, pady=6)
        self._err_bar = bar

    # ================================================================ โครงหลัก / ธีม / ภาษา
    def _build_all(self):
        self.t = THEMES[self.theme_key]
        apply_ttk_style(self, self.t, self.f, self.scale)
        self.configure(bg=self.t['bg'])
        self._leave_sim()
        self._stop_hero()
        for w in (self.header, self.content, self._err_bar):
            if w is not None:
                try:
                    w.destroy()
                except tk.TclError:
                    pass
        self._err_bar = None
        self._build_header()
        self.content = tk.Frame(self, bg=self.t['bg'])
        self.content.pack(side='top', fill='both', expand=True)
        self._show()

    def set_theme(self, key):
        if key in THEMES and key != self.theme_key:
            self.theme_key = key
            self._build_all()

    def set_lang(self, lang):
        if lang != self.lang:
            self.lang = lang
            self._build_all()

    def _stop_hero(self):
        if self.hero is not None:
            try:
                self.hero.stop()
            except tk.TclError:
                pass
            self.hero = None

    def _show(self):
        self._sim_ready = self._calc_ready = False
        self._stop_hero()
        for w in self.content.winfo_children():
            w.destroy()
        if self.screen == 'home':
            self._build_home()
        else:
            self._build_topic()

    def go_home(self):
        self._leave_sim()
        self.screen = 'home'
        self._show()

    def open_topic(self, topic, tab='calc'):
        self._leave_sim()
        self.screen, self.topic, self.tab = 'topic', topic, tab
        self._show()

    def set_tab(self, tab):
        if tab == self.tab and self.screen == 'topic':
            return
        self._leave_sim()
        self.tab = tab
        self._show()

    # ---------------------------------------------------------------- ตัวช่วยสร้าง widget
    def L(self, parent, text='', font='body', fg=None, bg=None, **kw):
        return tk.Label(parent, text=text, font=self.f[font], fg=fg or self.t['text'],
                        bg=bg or parent.cget('bg'), bd=0, **kw)

    def pill(self, parent, text='', icon=None, command=None, kind='soft', **kw):
        kw.setdefault('bg', parent.cget('bg'))
        kw['height'] = int(kw.get('height', 40) * self.scale)
        kw.setdefault('icon_size', int(14 * self.scale))
        return Pill(parent, text=text, icon=icon, command=command, kind=kind,
                    theme=self.t, font=self.f['btn'], **kw)

    def seg(self, parent, options, value, command, **kw):
        kw.setdefault('bg', parent.cget('bg'))
        kw['height'] = int(kw.get('height', 36) * self.scale)
        return Segmented(parent, options, value, command, theme=self.t, font=self.f['btn'], **kw)

    # ================================================================ Header
    def _build_header(self):
        t, bg, s = self.t, self.t['bg'], self.scale
        self.header = tk.Frame(self, bg=bg)
        self.header.pack(side='top', fill='x')
        row = tk.Frame(self.header, bg=bg)
        row.pack(fill='x', padx=24, pady=(12, 12))
        size = int(40 * s)
        logo = tk.Canvas(row, width=size, height=size, bg=bg, highlightthickness=0, bd=0, cursor='hand2')
        round_rect(logo, 1, 1, size - 1, size - 1, 13 * s, fill=t['primary_soft'], outline=t['primary'], width=2)
        draw_icon(logo, 'chip', size / 2, size / 2, 18 * s, t['primary_ink'])
        logo.pack(side='left')
        title = self.L(row, self.tr('app_title'), 'h3', bg=bg, cursor='hand2')
        title.pack(side='left', padx=(12, 0))
        for w in (logo, title):
            w.bind('<Button-1>', lambda e: self.go_home())
        self.seg(row, [('day', self.tr('theme_day')), ('night', self.tr('theme_night'))], self.theme_key,
                 self.set_theme, bg=bg, height=34, padx=14).pack(side='right')
        self.seg(row, [('en', 'EN'), ('th', 'ไทย')], self.lang, self.set_lang,
                 bg=bg, height=34, padx=12).pack(side='right', padx=(0, 10))
        self.main_menu_btn = None
        if self.screen == 'topic':
            self.main_menu_btn = self.pill(row, self.tr('main_menu'), 'chevron_left',
                                           self.go_home, kind='ghost', height=34)
            self.main_menu_btn.pack(side='right', padx=(0, 10))
        tk.Frame(self.header, bg=t['border'], height=2).pack(fill='x')

    # ================================================================ หน้าแรก
    def _build_home(self):
        t, bg, s = self.t, self.t['bg'], self.scale
        sf = ScrollFrame(self.content, bg)
        sf.pack(fill='both', expand=True)
        box = Centered(sf.body, bg, max_w=1800)
        box.pack(fill='x')
        b = box.inner
        self.hero = HomeHero(b, theme=t, fonts=self.f, scale=s, title=self.tr('hero_title'),
                             subtitle=self.tr('hero_sub'), lines=[self.tr(f'mascot_{i}') for i in range(1, 6)])
        self.hero.pack(fill='x', pady=(18, 0))
        self.L(b, self.tr('home_pick'), 'h1', bg=bg).pack(anchor='w', pady=(30, 14))
        flow = Flow(b, bg, breakpoint=860, gap=26)
        flow.pack(fill='x')
        for i, key in enumerate(('factorial', 'ncr')):
            flow.add(self._topic_card(flow, key, i))
        self.L(b, self.tr('how_title'), 'h2', bg=bg).pack(anchor='w', pady=(34, 12))
        how = Flow(b, bg, breakpoint=760, gap=18)
        how.pack(fill='x', pady=(0, 36))
        for i, col in enumerate(('pink', 'blue', 'yellow'), start=1):
            card = make_card(how, t, bg=t[col + '_soft'], padx=20, pady=18, border=t[col])
            row = tk.Frame(card.inner, bg=t[col + '_soft'])
            row.pack(fill='x')
            dot = int(46 * s)
            num = tk.Canvas(row, width=dot, height=dot, bg=t[col + '_soft'], highlightthickness=0, bd=0)
            num.create_oval(2, 2, dot - 2, dot - 2, fill=t[col], outline=t[col + '_ink'], width=2)
            num.create_text(dot / 2, dot / 2, text=str(i), font=self.f['h3'], fill='#111827')
            num.pack(side='left')
            txt = tk.Frame(row, bg=t[col + '_soft'])
            txt.pack(side='left', padx=(14, 0), fill='x', expand=True)
            self.L(txt, self.tr(f'how{i}_t'), 'body_b', fg=t[col + '_ink']).pack(anchor='w')
            d = self.L(txt, self.tr(f'how{i}_d'), 'small', fg=t['text'], justify='left')
            d.pack(anchor='w')
            autowrap(d, txt, pad=4, minw=120)
            how.add(card)
        self.hero.start()

    def _topic_card(self, parent, key, idx):
        t, info, s = self.t, TOPICS[key], self.scale
        c = info['color']
        card = make_card(parent, t, bg=t[c + '_soft'], padx=30, pady=28, border=t[c])
        inner = card.inner
        top = tk.Frame(inner, bg=t[c + '_soft'])
        top.pack(fill='x')
        bsz = int(96 * s)
        badge = tk.Canvas(top, width=bsz, height=bsz + int(10 * s), bg=t[c + '_soft'], highlightthickness=0, bd=0)
        round_rect(badge, 3, 8 * s, bsz - 3, bsz + 4 * s, 28 * s, fill=t[c], outline=t[c + '_ink'], width=3, tags='badge')
        badge.create_text(bsz / 2, bsz / 2 + 6 * s, text=info['glyph'], font=self.f['h1'], fill='#111827', tags='badge')
        badge.pack(side='left')
        if self.hero is not None:
            self.hero.add_bobber(badge, 'badge', amplitude=4 * s, phase=idx * 1.9)
        names = tk.Frame(top, bg=t[c + '_soft'])
        names.pack(side='left', padx=(20, 0))
        self.L(names, self.tr(key), 'h1', fg=t[c + '_ink']).pack(anchor='w')
        chip(names, info['example'], t['surface'], t[c + '_ink'], self.f['body_b'], padx=14, pady=3).pack(
            anchor='w', pady=(6, 0))
        d = self.L(inner, self.tr('card_' + key + '_desc'), 'body', fg=t['text'], justify='left')
        d.pack(anchor='w', pady=(20, 22))
        autowrap(d, inner)
        btns = tk.Frame(inner, bg=t[c + '_soft'])
        btns.pack(anchor='w')
        self.pill(btns, self.tr('btn_calculate'), 'arrow_right', lambda k=key: self.open_topic(k, 'calc'),
                  kind='primary', height=50, padx=28).pack(side='left')
        self.pill(btns, self.tr('btn_simulator'), 'play', lambda k=key: self.open_topic(k, 'sim'),
                  kind='ghost', height=50, padx=28).pack(side='left', padx=(12, 0))
        return card

    # ================================================================ หน้าหัวข้อ (Factorial / nCr)
    def _build_topic(self):
        t, bg, info = self.t, self.t['bg'], TOPICS[self.topic]
        page = tk.Frame(self.content, bg=bg)
        page.pack(fill='both', expand=True)
        top = Centered(page, bg, max_w=1800)
        top.pack(side='top', fill='x')
        if self.tab == 'sim':
            self._controls_bar(page)
        area = tk.Frame(page, bg=bg)
        area.pack(side='top', fill='both', expand=True)
        if self.tab == 'calc':
            self._build_calc(area)
        else:
            self._build_sim(area)

    def _topic_input_header(self, parent):
        """หัวข้อและแท็บอยู่บรรทัดเดียวกัน เหนือช่องกรอกค่า"""
        t = self.t
        row = tk.Frame(parent, bg=parent.cget('bg'))
        row.pack(fill='x', pady=(12, 22))
        c = TOPICS[self.topic]['color']
        self.L(row, self.tr(self.topic), 'h1', bg=parent.cget('bg')).pack(side='left')
        chip(row, TOPICS[self.topic]['math'], t[c + '_soft'], t[c + '_ink'],
             self.f['body_b'], padx=12, pady=3).pack(side='left', padx=(8, 18))
        self.seg(row, [('calc', self.tr('tab_calc')), ('sim', self.tr('tab_sim'))],
                 self.tab, self.set_tab, height=40, padx=20).pack(side='left')
        return row

    # ---------------------------------------------------------------- ช่องกรอกตัวเลข (ใช้ทั้งใน Calculate และ Simulator)
    def _inputs_row(self, parent, on_enter, big=True):
        t = self.t
        bg = parent.cget('bg')
        wrap = tk.Frame(parent, bg=bg)
        font = self.f['num'] if big else self.f['body_b']
        cols = [('n', self.n_var)] + ([('r', self.r_var)] if self.topic == 'ncr' else [])
        for name, var in cols:
            cell = tk.Frame(wrap, bg=bg)
            cell.pack(side='left', padx=(0, 16))
            self.L(cell, name.upper(), 'body_b', fg=t['muted'], bg=bg).pack(anchor='w', pady=(0, 6))
            e = ttk.Entry(cell, textvariable=var, width=6 if big else 5, style='Soft.TEntry',
                          font=font, justify='center')
            e.pack()
            e.bind('<Return>', lambda ev: on_enter())
        return wrap

    def _algo_picker(self, parent, info_label):
        bg = parent.cget('bg')
        options = [(k, self.tr('algo_' + k)) for k in ALGO_KEYS]

        def pick(v):
            self.algo_var.set(v)
            info_label.configure(text=self.tr('algo_' + v + '_info'))
            if self.screen == 'topic' and self.tab == 'sim' and self._sim_ready:
                self.sim_load(force=True)        # เปลี่ยนวิธีใน Simulator -> โหลดโปรแกรมใหม่ให้ทันที
        seg = self.seg(parent, options, self.algo_var.get(), pick, height=36, padx=16, bg=bg)
        info_label.configure(text=self.tr('algo_' + self.algo_var.get() + '_info'))
        return seg

    def _range_hint(self):
        mx = PROGRAM_SPECS[spec_key(self.topic, self.algo_var.get())].n_max
        return self.tr('hint_factorial' if self.topic == 'factorial' else 'hint_ncr', mx=mx)

    def _validate(self, kind, algo, n_text, r_text):
        """ตรวจ input ด้วย Controller เดิม (ผลจริง) แต่แสดงข้อความเป็นภาษาที่เลือก"""
        ok, msg, vals = self.controller.validate_input(kind, algo, n_text, r_text)
        if ok:
            return True, '', vals
        mx = PROGRAM_SPECS[spec_key(kind, algo)].n_max
        try:
            n = int(n_text)
            r = int(r_text) if kind == 'ncr' else None
        except (TypeError, ValueError):
            return False, self.tr('err_int'), None
        if n < 0 or n > mx:
            return False, self.tr('err_n_range', mx=mx), None
        if r is not None and (r < 0 or r > n):
            return False, self.tr('err_r_range'), None
        return False, msg, None

    # ================================================================ แท็บ Calculate
    def _build_calc(self, area):
        t, bg = self.t, self.t['bg']
        sf = ScrollFrame(area, bg)
        sf.pack(fill='both', expand=True)
        ct = Centered(sf.body, bg, max_w=1800)
        ct.pack(fill='both', expand=True)
        # Keep the original wide 4:5 card proportions and center the pair vertically.
        stage = tk.Frame(ct.inner, bg=bg)
        stage.pack(fill='both', expand=True)
        stage.grid_columnconfigure(0, weight=1)
        stage.grid_rowconfigure(0, weight=1)
        stage.grid_rowconfigure(2, weight=1)
        flow = Flow(stage, bg, breakpoint=860, gap=22)
        flow.grid(row=1, column=0, sticky='ew')

        ic = make_card(flow, t, padx=28, pady=26)
        flow.add(ic, 4)
        inner = ic.inner
        self._topic_input_header(inner)
        self.L(inner, self.tr('enter_numbers'), 'h2').pack(anchor='w')
        self.hint_lbl = self.L(inner, self._range_hint(), 'small', fg=t['muted'], justify='left')
        self.hint_lbl.pack(anchor='w', pady=(4, 18))
        autowrap(self.hint_lbl, inner)
        self._inputs_row(inner, lambda: None).pack(anchor='w')
        if self.topic == 'ncr':
            self.L(inner, self.tr('method'), 'small_b', fg=t['muted']).pack(anchor='w', pady=(22, 6))
            info = self.L(inner, '', 'small', fg=t['muted'], justify='left')
            self._algo_picker(inner, info).pack(anchor='w')
            info.pack(anchor='w', pady=(8, 0))
            autowrap(info, inner)
        self.pill(inner, self.tr('btn_calculate'), 'arrow_right', lambda: self.calc_now(), kind='primary',
                  height=50, padx=30).pack(anchor='w', pady=(26, 0))

        rc = make_card(flow, t, bg=t['blue_soft'], padx=30, pady=26, border=t['blue'])
        flow.add(rc, 5)
        r = rc.inner
        bgc = t['blue_soft']
        self.L(r, self.tr('result'), 'h3', fg=t['blue_ink'], bg=bgc).pack(anchor='center')
        self.res_big = self.L(r, '—', 'big', fg=t['blue_ink'], bg=bgc)
        self.res_big.pack(anchor='center', pady=(8, 4))
        self.res_formula = self.L(r, '', 'h3', fg=t['text'], bg=bgc, justify='left')
        self.res_formula.pack(anchor='center')
        self.res_msg = self.L(r, '', 'body', fg=t['text'], bg=bgc, justify='left')
        self.res_msg.pack(anchor='center', pady=(8, 0))
        autowrap(self.res_msg, r)
        self.res_chips = tk.Frame(r, bg=bgc)
        self.res_chips.pack(anchor='center', pady=(14, 0))
        self.res_open = self.pill(r, self.tr('see_sim'), 'play', lambda: self.set_tab('sim'),
                                  kind='ghost', bg=bgc)
        self._res_card = rc
        self._calc_ready = True
        self._set_result('idle')

    def _set_result(self, state, **kw):
        if not self._calc_ready:
            return
        t = self.t
        for w in self.res_chips.winfo_children():
            w.destroy()
        self.res_open.pack_forget()
        big, formula, msg, color = '—', '', '', t['blue_ink']
        if state == 'idle':
            msg = kw.get('msg', self.tr('res_idle'))
        elif state == 'busy':
            big, msg = '…', self.tr('res_busy')
        elif state == 'error':
            msg, color = kw.get('msg', ''), t['red_ink']
        elif state == 'ok':
            big, formula = f"{kw['value']:,}", kw['formula']
            chip(self.res_chips, self.tr('chip_instr', n=f"{kw['instr']:,}"), t['surface'], t['blue_ink'],
                 self.f['small_b'], padx=12, pady=4).pack(side='left', padx=(0, 8))
            if kw.get('verified') is True:
                chip(self.res_chips, self.tr('chip_ok'), t['green_soft'], t['green_ink'],
                     self.f['small_b'], padx=12, pady=4).pack(side='left')
            elif kw.get('verified') is False:
                chip(self.res_chips, self.tr('chip_bad'), t['red_soft'], t['red_ink'],
                     self.f['small_b'], padx=12, pady=4).pack(side='left')
            self.res_open.pack(anchor='w', pady=(16, 0))
        self.res_big.configure(text=big, fg=color)
        self.res_formula.configure(text=formula)
        self.res_msg.configure(text=msg, fg=t['red_ink'] if state == 'error' else t['text'])

    def _input_changed(self):
        # Calculate: เปลี่ยน input แล้วรอให้ผู้ใช้กด Calculate เอง
        if self.screen == 'topic' and self.tab == 'calc' and self._calc_ready:
            if hasattr(self, 'hint_lbl'):
                self.hint_lbl.configure(text=self._range_hint())
            self._calc_token += 1  # ยกเลิกผลลัพธ์เก่าที่อาจกำลังคำนวณอยู่
            self._set_result('idle')
        # Simulator: อัปเดต display/formula ทันที แต่ไม่โหลดโปรแกรมจนกว่าจะกด Reload
        if self.screen == 'topic' and self.tab == 'sim' and self._sim_ready:
            n_text, r_text = self.n_var.get(), self.r_var.get()
            formula = f'{n_text}!' if self.topic == 'factorial' else f'{n_text}C{r_text}'
            self.sim_title.configure(text=self._sim_answer_text(formula, n_text, r_text))
            ok, msg, _ = self._validate(self.topic, self.algo_var.get(), n_text, r_text)
            self.sim_msg.configure(text='' if ok else '⚠  ' + msg)

    def _sim_answer_text(self, formula, n_text, r_text):
        """Show the mathematical answer beside the formula while the CPU is simulated."""
        ok, _msg, vals = self._validate(self.topic, self.algo_var.get(), n_text, r_text)
        if not ok:
            return f'{formula} = —'
        n, r = vals
        answer = factorial_ref(n) if self.topic == 'factorial' else ncr_ref(n, r)
        return f'{formula} = {answer:,}'

    def calc_now(self, auto=False):
        """คำนวณด่วนผ่าน Controller.run_headless (CPU ตัวแยก ไม่กระทบ Simulator ที่กำลังเปิดอยู่)"""
        if not self._calc_ready:
            return
        kind, algo = self.topic, self.algo_var.get()
        ok, msg, vals = self._validate(kind, algo, self.n_var.get(), self.r_var.get())
        if not ok:
            self._set_result('error', msg=msg)
            return
        n, r = vals
        if auto and kind == 'ncr' and algo == 'factorial_based' and ex.division_rounds(n, r) > 150000:
            self._set_result('idle', msg=self.tr('res_heavy'))
            return
        self._calc_token += 1
        token = self._calc_token
        self._set_result('busy')
        self._calc_pending += 1
        threading.Thread(target=self._calc_worker, args=(token, kind, algo, n, r), daemon=True).start()
        self.after(40, self._poll_calc)

    def _calc_worker(self, token, kind, algo, n, r):      # ทำงานใน thread แยก (ไม่แตะ widget)
        try:
            row = self.controller.run_headless(kind, algo, n, r)
            self._calc_q.put((token, 'ok', row, (kind, n, r)))
        except Exception as exc:                          # noqa: BLE001
            self._calc_q.put((token, 'err', str(exc), None))

    def _poll_calc(self):
        try:
            while True:
                token, status, payload, meta = self._calc_q.get_nowait()
                self._calc_pending = max(0, self._calc_pending - 1)
                if token != self._calc_token or not self._calc_ready:
                    continue
                if status == 'err':
                    self._set_result('error', msg=self.tr('calc_failed', err=payload))
                    continue
                out = ex.calc_outcome(payload, self.lang)
                if out['ok']:
                    kind, n, r = meta
                    self._set_result('ok', value=out['value'], instr=out['instr'],
                                     verified=out['verified'], formula=ex.formula_text(kind, n, r))
                else:
                    self._set_result('error', msg=out['message'])
        except queue.Empty:
            pass
        if self._calc_pending > 0:
            self.after(40, self._poll_calc)

    # ================================================================ แท็บ Simulator
    def _controls_bar(self, page):
        """แถบปุ่มควบคุมติดขอบล่างเสมอ (เลื่อนหน้าจอแล้วปุ่มยังอยู่)"""
        t, bg = self.t, self.t['surface']
        bar = tk.Frame(page, bg=bg)
        bar.pack(side='bottom', fill='x')
        tk.Frame(bar, bg=t['border'], height=2).pack(fill='x')
        ct = Centered(bar, bg, max_w=1800)
        ct.pack(fill='x')
        fl = Flow(ct.inner, bg, breakpoint=860, gap=10)
        fl.pack(fill='x', pady=12)
        left = tk.Frame(fl, bg=bg)
        right = tk.Frame(fl, bg=bg)
        self.btn_back = self.pill(left, self.tr('btn_back'), 'back', lambda: self._control_action('back', self.back), kind='ghost', height=44)
        self.btn_step = self.pill(left, self.tr('btn_step'), 'step', lambda: self._control_action('step', self.step), kind='ghost', height=44, padx=24)
        self.btn_run = self.pill(left, self.tr('btn_run'), 'play', lambda: self._control_action('run', self.toggle_run), kind='ghost', height=44, padx=24)
        self.btn_reset = self.pill(left, self.tr('btn_reset'), 'reset', lambda: self._control_action('reset', self.reset), kind='ghost', height=44)
        for b in (self.btn_back, self.btn_step, self.btn_run, self.btn_reset):
            b.pack(side='left', padx=(0, 10))
        self.L(right, self.tr('speed'), 'small_b', fg=t['muted'], bg=bg).pack(side='left', padx=(0, 10))
        self.seg(right, [('x1', 'x1'), ('x2', 'x2'), ('x10', 'x10')], self.speed_key, self._set_speed,
                 bg=bg, height=38, padx=13).pack(side='left')
        fl.add(left, 1)
        fl.add(right, 1)
        right.pack_propagate(True)
        # Align the speed selector against the far-right edge, symmetric with the controls.
        right.bind('<Configure>', lambda _e: self._align_speed_right(right), add='+')

    def _align_speed_right(self, frame):
        for child in frame.winfo_children():
            if isinstance(child, Segmented):
                child.pack_configure(side='right')

    def _control_action(self, key, action):
        self._active_control = key
        self._refresh_control_styles()
        action()

    def _refresh_control_styles(self):
        for key, attr in (('back', 'btn_back'), ('step', 'btn_step'), ('run', 'btn_run'), ('reset', 'btn_reset')):
            button = getattr(self, attr, None)
            if button is not None:
                button.kind = 'primary' if self._active_control == key else 'ghost'
                button.draw()

    def _build_sim(self, area):
        t, bg = self.t, self.t['bg']
        sf = ScrollFrame(area, bg)
        sf.pack(fill='both', expand=True)
        ct = Centered(sf.body, bg, max_w=1800)
        ct.pack(fill='x')
        b = ct.inner

        # --- ค่าที่ใช้
        ic = tk.Frame(b, bg=bg)
        ic.pack(fill='x', pady=(8, 6))
        ic.inner = tk.Frame(ic, bg=bg)
        ic.inner.pack(fill='x', padx=20, pady=2)
        self._topic_input_header(ic.inner)
        row = tk.Frame(ic.inner, bg=bg)
        row.pack(fill='x')
        self.L(row, self.tr('values'), 'small_b', fg=t['muted'], bg=bg).pack(side='left', padx=(0, 16))
        self._inputs_row(row, lambda: self.sim_load(force=True), big=False).pack(side='left')
        self.pill(row, self.tr('reload'), 'reset', lambda: self.sim_load(force=True), kind='soft',
                  height=38).pack(side='left', padx=(8, 0), pady=(18, 0))
        self.sim_title = self.L(row, '', 'h1', bg=bg)
        self.sim_title.pack(side='right', padx=(16, 0), pady=(12, 0))
        if self.topic == 'ncr':
            r2 = tk.Frame(ic.inner, bg=t['surface'])
            r2.pack(fill='x', pady=(12, 0))
            info = self.L(r2, '', 'small', fg=t['muted'], justify='left')
            self._algo_picker(r2, info).pack(side='left')
            info.pack(side='left', padx=(14, 0), fill='x', expand=True)
            autowrap(info, r2, pad=330)
        self.sim_msg = self.L(ic.inner, '', 'small', fg=t['red_ink'], justify='left')
        self.sim_msg.pack(anchor='w', pady=(2, 0))

        # --- หัวเรื่อง + สถานะ
        head = tk.Frame(b, bg=bg)
        head.pack(fill='x', pady=(0, 4))
        chips = tk.Frame(head, bg=bg)
        chips.pack(side='right')
        self.chip_status = chip(chips, '', t['blue_soft'], t['blue_ink'], self.f['small_b'], padx=14, pady=5)
        self.chip_steps = chip(chips, '', t['surface2'], t['text'], self.f['small_b'], padx=14, pady=5)
        self.chip_pc = chip(chips, '', t['surface2'], t['text'], self.f['small_b'], padx=14, pady=5)
        for c in (self.chip_status, self.chip_steps, self.chip_pc):
            c.pack(side='left', padx=(8, 0))
        self.banner_slot = tk.Frame(b, bg=bg)
        self.banner_slot.pack(fill='x')

        # --- CPU Execution Path
        pc = make_card(b, t, padx=12, pady=9)
        pc.pack(fill='x', pady=(2, 7))
        self.L(pc.inner, self.tr('path_title'), 'small_b', fg=t['muted']).pack(anchor='w', padx=4, pady=(0, 3))
        self.diagram = CPUDiagram(pc.inner, theme=t, fonts=self.f, scale=self.scale, lang=self.lang)
        self.diagram.pack(fill='x')

        # --- Dashboard: What just happened stays prominent on the left.
        # Execution History uses the available space on the right.
        fl = Flow(b, bg, breakpoint=900, gap=10)
        fl.pack(fill='x')

        left_stack = tk.Frame(fl, bg=bg)
        fl.add(left_stack, 3)

        ec = make_card(left_stack, t, padx=18, pady=12)
        ec.pack(fill='x')
        e = ec.inner
        self.L(e, self.tr('what_now'), 'small_b', fg=t['muted']).pack(anchor='w')
        self.ex_step = self.L(e, '', 'h3')
        self.ex_step.pack(anchor='w', pady=(2, 5))
        self.ex_code = tk.Label(e, text='', font=self.f['mono_b'], fg=t['text'], bg=t['surface2'],
                                padx=14, pady=7, anchor='w', justify='left', bd=0)
        self.ex_code.pack(anchor='w')
        self.ex_sentence = self.L(e, '', 'body', justify='left')
        self.ex_sentence.pack(anchor='w', pady=(7, 0))
        autowrap(self.ex_sentence, e)
        self.ex_result = self.L(e, '', 'num', fg=t['blue_ink'])
        self.ex_result.pack(anchor='w', pady=(6, 0))
        self.ex_next = self.L(e, '', 'small', fg=t['muted'], justify='left')
        self.ex_next.pack(anchor='w', pady=(6, 0))
        autowrap(self.ex_next, e)

        # CPU Execution Status: show the instruction lifecycle and the stage
        # most relevant to the latest executed instruction. This is a logical
        # stage view, not a cycle-accurate pipelined CPU trace.
        lc = make_card(left_stack, t, padx=22, pady=18)
        lc.pack(fill='x', pady=(7, 0))
        # หัวการ์ด: ชื่อ (ซ้าย) + ป้ายสถานะ (ขวา)
        top = tk.Frame(lc.inner, bg=t['surface'])
        top.pack(fill='x')
        self.insight_heading = self.L(top, self.tr('exec_status_title'), 'body_b')
        self.insight_heading.pack(side='left')
        self.exec_pill = tk.Label(top, text='', font=self.f['small_b'], fg=t['green_ink'], bg=t['green_soft'],
                                  bd=0, padx=14, pady=3)
        self.exec_pill.pack(side='right')
        # ชื่อขั้นปัจจุบันตัวใหญ่ + คำสั่งปัจจุบัน
        self.exec_status_label = self.L(lc.inner, '', 'h1')
        self.exec_status_label.pack(anchor='w', pady=(14, 0))
        self.insight_sub = self.L(lc.inner, '', 'small', fg=t['muted'], justify='left')
        self.insight_sub.pack(anchor='w', pady=(8, 10))
        # แถบ 5 ขั้น: ขั้นปัจจุบันเป็นสีน้ำเงิน ขั้นอื่นไม่มีสี
        self.exec_stage_row = tk.Frame(lc.inner, bg=t['surface'])
        self.exec_stage_row.pack(fill='x')
        self.exec_stage_labels = []         # (bar, label, stage_key)
        for i, stage_key in enumerate(('stage_fetch', 'stage_decode', 'stage_execute', 'stage_memory', 'stage_writeback')):
            col = tk.Frame(self.exec_stage_row, bg=t['surface'])
            col.grid(row=0, column=i, sticky='ew', padx=(0 if i == 0 else 4, 0))
            self.exec_stage_row.grid_columnconfigure(i, weight=1, uniform='esstage')
            bar = RoundBar(col, t['surface2'], t['surface'], height=int(10 * self.scale))
            bar.pack(fill='x')
            label = self.L(col, self.tr(stage_key), 'small', fg=t['muted'])
            label.pack(anchor='w', pady=(4, 0))
            self.exec_stage_labels.append((bar, label, stage_key))
        tk.Frame(lc.inner, bg=t['border'], height=1).pack(fill='x', pady=(14, 12))
        # ตาราง 2x2: Current PC / Next PC / ALU Operation / Result
        self.insight_grid = tk.Frame(lc.inner, bg=t['surface'])
        self.insight_grid.pack(fill='x')
        self.insight_grid.grid_columnconfigure(0, weight=1, uniform='esg')
        self.insight_grid.grid_columnconfigure(1, weight=1, uniform='esg')
        self._es_caps, self._es_vals = {}, {}
        for idx, key in enumerate(('es_cur_pc', 'es_next_pc', 'es_alu_op', 'es_result')):
            cell = tk.Frame(self.insight_grid, bg=t['surface'])
            cell.grid(row=idx // 2, column=idx % 2, sticky='nw', pady=(0, 10 if idx < 2 else 0))
            cap = self.L(cell, self.tr(key), 'small', fg=t['muted'])
            cap.pack(anchor='w')
            val = self.L(cell, '—', 'h3')
            val.pack(anchor='w', pady=(2, 0))
            self._es_caps[key], self._es_vals[key] = cap, val
        self._insight_sig = None
        self._insight_widgets = []
        self._es_job, self._es_step_no, self._es_cur, self._es_plan = None, None, -1, []

        # Execution History occupies the right-hand dashboard column.
        hc = make_card(fl, t, padx=14, pady=11)
        fl.add(hc, 2)
        hh = tk.Frame(hc.inner, bg=t['surface'])
        hh.pack(fill='x')
        self.L(hh, self.tr('hist_title'), 'h3').pack(side='left')
        self.hist_count = self.L(hh, '', 'small', fg=t['muted'])
        self.hist_count.pack(side='left', padx=(10, 0))
        self.btn_tech = self.pill(hh, self.tr('tech'), 'list', self._toggle_tech, kind='ghost', height=34)
        self.btn_tech.pack(side='right')
        tf = tk.Frame(hc.inner, bg=t['surface'])
        tf.pack(fill='both', expand=True, pady=(6, 0))
        cols = ('n', 'ins', 'what', 'res')
        self.hist = ttk.Treeview(tf, columns=cols, show='headings', height=6, selectmode='browse',
                                 style='Hist.Treeview')
        for c, key, w, st, anc in [('n', 'col_n', 52, False, 'center'), ('ins', 'col_ins', 180, True, 'w'),
                                   ('what', 'col_what', 130, False, 'w'), ('res', 'col_res', 150, True, 'w')]:
            self.hist.heading(c, text=self.tr(key), anchor='w' if anc == 'w' else 'center')
            self.hist.column(c, width=int(w * self.scale), stretch=st, anchor=anc)
        vs = ttk.Scrollbar(tf, orient='vertical', command=self.hist.yview, style='Soft.Vertical.TScrollbar')
        self.hist.configure(yscrollcommand=vs.set)
        vs.pack(side='right', fill='y')
        self.hist.pack(side='left', fill='both', expand=True)
        self.hist.tag_configure('latest', background=t['primary_soft'])
        for tone, col in (('branch', 'yellow'), ('jump', 'violet'), ('mem', 'green'), ('error', 'red'),
                          ('halt', 'green')):
            self.hist.tag_configure(tone, foreground=t[col + '_ink'])
        self.hist.bind('<<TreeviewSelect>>', self._on_hist_select)
        self.hist.bind('<Configure>', self._hist_columns)
        self.hist_info = self.L(hc.inner, self.tr('hist_hint'), 'small', fg=t['muted'], justify='left')
        self.hist_info.pack(anchor='w', pady=(5, 0))
        autowrap(self.hist_info, hc.inner)

        self._tech_visible = True
        self.tech_frame = tk.Frame(hc.inner, bg=t['surface'])
        self._build_tech(self.tech_frame)
        self.tech_frame.pack(fill='x', pady=(8, 0))
        self.btn_tech.set_text(self.tr('tech'))
        self._hist_reset()
        self._prev_step_no = None
        self._sim_ready = True
        self.sim_load()
        self.render(self.controller.get_view())

    # ---------------------------------------------------------------- เริ่ม / โหลดโปรแกรม
    def sim_load(self, force=False):
        kind, algo = self.topic, self.algo_var.get()
        ok, msg, vals = self._validate(kind, algo, self.n_var.get(), self.r_var.get())
        if not ok:
            self.sim_msg.configure(text='⚠  ' + msg)
            return False
        n, r = vals
        key = (kind, algo if kind == 'ncr' else '-', n, r)
        if not force and key == self._loaded_key and self.controller.program is not None:
            self.sim_msg.configure(text='')
            return True
        self._hist_reset()
        try:
            self.controller.load(kind, algo, n, r)
        except Exception as exc:                          # noqa: BLE001
            self.sim_msg.configure(text='⚠  ' + self.tr('load_failed', err=exc))
            self._loaded_key = None
            return False
        self.sim_msg.configure(text='')
        self._loaded_key = key
        prog = self.controller.program
        self._by_addr = {i.addr: i for i in prog.instrs}
        self._skey = spec_key(kind, algo)
        self._always = {2, 4} | ({5} if kind == 'ncr' else set())
        self._formula = f'{n}!' if kind == 'factorial' else f'{n}C{r}'
        if hasattr(self, 'sim_title'):
            self.sim_title.configure(text=self._sim_answer_text(self._formula, str(n), str(r if r is not None else self.r_var.get())))
        self._prev_step_no = None
        self._fill_asm(prog)
        if self.diagram is not None:
            self.diagram.clear()
        return True

    # ---------------------------------------------------------------- ปุ่มควบคุม
    def step(self):
        c = self.controller
        if c.program and c.mode in ('ready', 'paused'):
            c.step()

    def back(self):
        if self.controller.can_back:
            self.controller.back_step()

    def toggle_run(self):
        c = self.controller
        if c.mode == 'running':
            self.pause()
        elif c.program and c.mode in ('ready', 'paused') and not self._run_blocked:
            steps, delay = SPEEDS[self.speed_key]
            self._run_delay = delay
            c.run(steps_per_tick=steps, delay_ms=delay)

    def pause(self):
        c = self.controller
        c.pause()
        if c.mode == 'running':
            c.mode = 'paused'
        self._block_run()
        self.render(c.get_view())

    def reset(self):
        c = self.controller
        if c.program:
            was_running = c.mode == 'running'
            self._hist_reset()
            c.reset()
            self._prev_step_no = None
            self.diagram.clear()
            if was_running:
                self._block_run()

    def _block_run(self):
        """กันกด Run ซ้ำทันทีหลัง Pause/Reset: tick ที่ค้างอยู่ใน scheduler ของ Controller อาจยังไม่หมดอายุ
        (ถ้ากดเร็วเกินไปจะเกิดลูปซ้อน 2 ชุด) จึงหน่วงปุ่ม Run ไว้เท่ากับเวลาหน่วงของความเร็วที่เลือก"""
        self._run_blocked = True
        self.after(self._run_delay + 60, self._unblock_run)

    def _unblock_run(self):
        self._run_blocked = False
        if self._sim_ready:
            self.render(self.controller.get_view())

    def _set_speed(self, key):
        self.speed_key = key
        self._run_delay = SPEEDS[key][1]
        if self.controller.mode == 'running':       # เปลี่ยนความเร็วระหว่างรัน: หยุดให้ก่อน แล้วให้กด Run ต่อ
            self.pause()

    def _shortcut(self, fn):
        if self.screen != 'topic' or self.tab != 'sim' or not self._sim_ready:
            return
        w = self.focus_get()
        if w is not None and (w.winfo_class() in ('TEntry', 'Entry') or isinstance(w, Pill)):
            return                      # กำลังพิมพ์ หรือโฟกัสอยู่ที่ปุ่ม (ปุ่มรับ Enter/Space เองอยู่แล้ว)
        fn()

    def _leave_sim(self):
        self._es_cancel()
        if getattr(self, 'controller', None) is not None and self.screen == 'topic' and self.tab == 'sim':
            c = self.controller
            c.pause()
            if c.mode == 'running':
                c.mode = 'paused'
        if self.diagram is not None:
            try:
                self.diagram.stop()
            except tk.TclError:
                pass
            self.diagram = None
        self._sim_ready = False

    # ================================================================ render (Controller เรียกทุกครั้งที่สถานะเปลี่ยน)
    def render(self, view):
        if not (self._sim_ready and self.screen == 'topic' and self.tab == 'sim'):
            return
        t = self.t
        st, mode, step = view.cpu, view.mode, view.last_step
        turbo = view.turbo and mode == 'running'

        tone = {'ready': 'blue', 'running': 'yellow', 'paused': 'yellow', 'finished': 'green',
                'error': 'red'}.get(mode, 'blue')
        self.chip_status.configure(text='●  ' + ex.mode_name(mode, self.lang), bg=t[tone + '_soft'], fg=t[tone + '_ink'])
        self.chip_steps.configure(text=self.tr('unit_instr', n=f"{st.counters['instr']:,}") if st
                                  else self.tr('unit_instr', n='0'))
        self.chip_pc.configure(text=f"{self.tr('pc')} 0x{st.pc:08X}" if st else f"{self.tr('pc')} —")
        self._update_buttons(view)
        self._update_execution_stages(step, mode, turbo)
        if turbo:                                   # Turbo: อัปเดตเฉพาะตัวเลขหลัก เพื่อไม่ให้หน้าจอค้าง
            self.ex_sentence.configure(text=self.tr('turbo_text'))
            return

        final = mode == 'finished' and view.result is not None
        self.sim_title.configure(text=f'{self._formula} = {view.result:,}' if final else self._sim_answer_text(self._formula, self.n_var.get(), self.r_var.get()))
        self._update_banner(view)

        # CPU path (วิ่งตามขั้น ถ้าเป็นขั้นใหม่และความเร็วไม่เร็วเกินไป)
        new_step = step is not None and step.step_no != self._prev_step_no
        if new_step:
            running = mode == 'running'
            anim = (not running) or self._run_delay >= 250
            ms = 900 if not running else int(self._run_delay * 0.8)
            self.diagram.show_step(step, animate=anim, anim_ms=ms)
            self._prev_step_no = step.step_no
        elif step is None:
            self.diagram.clear()

        # คำอธิบายขั้นนี้
        if step is not None:
            e = ex.explain_step(step, st.regs, self.lang)
            self.ex_step.configure(text=f'{self.tr("step_n", n=format(step.step_no, ","))}  ·  {e["title"]}')
            self.ex_code.configure(text=ex.clean(step.instr.raw))
            self.ex_sentence.configure(text=e['sentence'])
            self.ex_result.configure(text=e['result'] or '', fg=t[TONE_COLOR.get(e['tone'], 'blue') + '_ink'])
            changes = step.reg_changes
        else:
            self.ex_step.configure(text=self.tr('ready_title'))
            self.ex_code.configure(text='—')
            self.ex_sentence.configure(text=self.tr('ready_text'))
            self.ex_result.configure(text='')
            changes = {}
        nxt = self._by_addr.get(st.pc) if st and mode in ('ready', 'paused', 'running') else None
        if nxt is not None:
            ttl, detail = ex.explain_next(nxt, st.regs, self.lang)
            self.ex_next.configure(text=f'{self.tr("next")}:  {ex.clean(nxt.raw)}  —  {ttl}' + (f'  ({detail})' if detail else ''))
        else:
            self.ex_next.configure(text='')

        self._update_instruction_insight(step, st, mode)
        self._update_history(view)
        if self._tech_visible:
            self._update_tech(view)

    def _update_buttons(self, view):
        c, mode = self.controller, view.mode
        has = view.program is not None
        running = mode == 'running'
        self.btn_run.set_text(self.tr('btn_pause') if running else self.tr('btn_run'), 'pause' if running else 'play')
        self.btn_run.set_enabled(has and (running or (mode in ('ready', 'paused') and not self._run_blocked)))
        if running:
            self._active_control = 'run'
        elif self._active_control == 'run':
            self._active_control = None
        self._refresh_control_styles()
        self.btn_step.set_enabled(has and mode in ('ready', 'paused'))
        self.btn_back.set_enabled(has and c.can_back and not running)
        self.btn_reset.set_enabled(has)

    def _update_banner(self, view):
        t = self.t
        for w in self.banner_slot.winfo_children():
            w.destroy()
        mode = view.mode
        if mode == 'finished' and view.result is not None:
            col, big = 'green', f'{self._formula} = {view.result:,}'
            ref = self.tr('ref_ok') if str(view.message).startswith('✔') else (
                self.tr('ref_bad') if str(view.message).startswith('✘') else '')
            sub = f"{self.tr('done', n=format(view.cpu.counters['instr'], ','))}   {ref}"
        elif mode == 'finished':
            col, big = 'red', self.tr('cannot_calc')
            sub = ex.tx(self.lang, 'k.bad_range') if view.prog_status == 3 else (
                ex.tx(self.lang, 'k.div0') if view.prog_status == 2 else ex.tx(self.lang, 'e.generic'))
        elif mode == 'error':
            col, big = 'red', self.tr('cpu_stopped')
            sub = ex.friendly_error(view.cpu.status if view.cpu else '', view.message, self.lang)
        else:
            return
        card = make_card(self.banner_slot, t, bg=t[col + '_soft'], padx=22, pady=14, border=t[col])
        card.pack(fill='x', pady=(0, 8))
        self.L(card.inner, big, 'h2', fg=t[col + '_ink']).pack(anchor='w')
        lbl = self.L(card.inner, sub, 'body', fg=t['text'], justify='left')
        lbl.pack(anchor='w', pady=(2, 0))
        autowrap(lbl, card.inner)

    # ---------------------------------------------------------------- CPU Execution Status stage tracker
    STAGE_KEYS = ('stage_fetch', 'stage_decode', 'stage_execute', 'stage_memory', 'stage_writeback')

    def _stage_plan(self, step):
        """ลำดับขั้นที่คำสั่งนี้ผ่านจริง (index 0-4): Fetch -> Decode -> Execute -> [Memory] -> [Write Back]"""
        op = step.instr.op.upper()
        if op == 'SW':
            return [0, 1, 2, 3]
        if op == 'LW':
            return [0, 1, 2, 3, 4]
        if op in ('ADD', 'ADDU', 'SUB', 'SUBU', 'ADDI', 'ADDIU', 'AND', 'OR', 'NOR', 'ANDI', 'ORI',
                  'SLT', 'SLTU', 'SLTI', 'SLTIU', 'SLL', 'SRL', 'LUI', 'JAL'):
            return [0, 1, 2, 4]
        return [0, 1, 2]

    def _es_cancel(self):
        job = getattr(self, '_es_job', None)
        if job is not None:
            try:
                self.after_cancel(job)
            except tk.TclError:
                pass
        self._es_job = None

    def _es_draw(self, active, step, mode):
        """วาดการ์ดตามขั้นที่ active (-1 = ยังไม่เริ่ม)"""
        t = self.t
        up = (lambda x: x.upper()) if self.lang == 'en' else (lambda x: x)
        animating = self._es_job is not None
        if step is None or active < 0:
            pill, head = self.tr('es_pill_ready'), up(self.tr('exec_status_ready'))
        elif mode == 'finished' and step.instr.op.upper() == 'HALT' and not animating:
            pill, head = self.tr('es_pill_halted'), up(self.tr('exec_status_halted'))
        else:
            head = up(self.tr(self.STAGE_KEYS[active]))
            pill = self.tr('es_pill_exec') if (animating or mode == 'running') else self.tr('es_pill_done')
        self.exec_pill.configure(text=pill)
        self.exec_status_label.configure(text=head)
        for index, (bar, label, key) in enumerate(self.exec_stage_labels):
            on = index == active
            bar.set_color(t['primary'] if on else t['surface2'])
            label.configure(text=self.tr(key), fg=t['text'] if on else t['muted'],
                            font=self.f['small_b'] if on else self.f['small'])

    def _es_tick(self, step, mode_fn, pos, per):
        self._es_job = None
        if not self._sim_ready:
            return
        self._es_cur = self._es_plan[pos]
        if pos + 1 < len(self._es_plan):
            self._es_job = self.after(per, self._es_tick, step, mode_fn, pos + 1, per)
        self._es_draw(self._es_cur, step, mode_fn())

    def _update_execution_stages(self, step, mode, turbo=False):
        mode_fn = lambda: self.controller.mode if getattr(self, 'controller', None) is not None else mode
        if step is None:
            self._es_cancel()
            self._es_step_no, self._es_cur, self._es_plan = None, -1, []
            self._es_draw(-1, None, mode)
            return
        if step.step_no != self._es_step_no:                # คำสั่งใหม่ -> เริ่มวิ่งตั้งแต่ Fetch
            self._es_cancel()
            self._es_step_no = step.step_no
            self._es_plan = self._stage_plan(step)
            running = mode == 'running'
            if turbo or (running and self._run_delay < 250):   # เร็วเกินจะเห็น (เช่น x10): ข้ามไปขั้นสุดท้าย
                self._es_cur = self._es_plan[-1]
            else:
                per = int(self._run_delay * 0.8 / len(self._es_plan)) if running else 350
                self._es_tick(step, mode_fn, 0, max(60, per))
                return
        self._es_draw(self._es_cur, step, mode)            # คำสั่งเดิม (เช่น เปลี่ยนโหมด) แค่วาดซ้ำ

    # ---------------------------------------------------------------- CPU Execution Status details
    def _update_instruction_insight(self, step, state, mode):
        if state is None:
            return
        if step is None:
            sub = self.tr('es_no_instr')
            vals = {'es_cur_pc': f'0x{state.pc:08X}', 'es_next_pc': '—', 'es_alu_op': '—', 'es_result': '—'}
        else:
            ins = step.instr
            op = ins.op.upper()
            sub = self.tr('es_cur_instr', ins=ex.clean(ins.raw))
            result = '—'
            changed = step.reg_changes or {}
            r_type = ('ADD', 'ADDU', 'SUB', 'SUBU', 'AND', 'OR', 'NOR', 'SLT', 'SLTU', 'SLL', 'SRL')
            i_type = ('ADDI', 'ADDIU', 'ANDI', 'ORI', 'SLTI', 'SLTIU', 'LUI', 'LW')
            if op in r_type:
                result = str(s32(state.regs[ins.rd]))       # ค่าที่อยู่ใน register ปลายทางหลังทำคำสั่ง (แม้ไม่เปลี่ยน)
            elif op in i_type:
                result = str(s32(state.regs[ins.rt]))
            elif changed:
                result = str(s32(next(iter(changed.values()))[1]))
            elif step.mem_writes:
                result = str(s32(step.mem_writes[0][1]))
            alu = op if op not in ('LW', 'SW', 'BEQ', 'BNE', 'J', 'JAL', 'JR', 'HALT') else (
                'ADD' if op in ('LW', 'SW') else ('SUB' if op in ('BEQ', 'BNE') else '—'))
            vals = {'es_cur_pc': f'0x{step.pc_before:08X}', 'es_next_pc': f'0x{step.pc_after:08X}',
                    'es_alu_op': alu, 'es_result': result}
        sig = (sub, tuple(vals.items()))
        if sig == self._insight_sig:
            return
        self._insight_sig = sig
        self.insight_sub.configure(text=sub)
        for key, text in vals.items():
            self._es_vals[key].configure(text=text)

    # ---------------------------------------------------------------- chips ตัวเลขตอนนี้ (เก็บไว้สำหรับ compatibility; ไม่ใช้แสดงในหน้า Simulator)
    def _update_chips(self, regs, changes):
        roles = ex.roles_for(self._skey, self.lang)
        chips = ex.live_registers(regs, changes, roles, self._always)
        sig = tuple((c['idx'], c['value'], c['changed']) for c in chips)
        if sig == self._chips_sig:
            return
        self._chips_sig = sig
        t = self.t
        for w in self._chip_widgets:
            w.destroy()
        self._chip_widgets = []
        for c in chips:
            col = 'pink' if c['changed'] else 'blue'
            f = tk.Frame(self.chips_box, bg=t[col + '_soft'], highlightthickness=2,
                         highlightbackground=t[col], bd=0)
            if c['role']:
                lb = self.L(f, c['role'], 'tiny_b', fg=t[col + '_ink'], bg=t[col + '_soft'], justify='left',
                            wraplength=int(150 * self.scale))
                lb.pack(anchor='w', padx=10, pady=(8, 0))
            val = f"{c['old']} → {c['value']}" if c['changed'] and c['old'] != c['value'] else f"{c['value']}"
            self.L(f, val, 'num', fg=t[col + '_ink'], bg=t[col + '_soft']).pack(anchor='w', padx=10)
            self.L(f, c['name'], 'small', fg=t['muted'], bg=t[col + '_soft']).pack(anchor='w', padx=10, pady=(0, 8))
            self._chip_widgets.append(f)
        self._layout_chips()

    def _layout_chips(self):
        if not getattr(self, '_chip_widgets', None):
            return
        w = max(self.chips_box.winfo_width(), 200)
        cols = max(1, w // int(180 * self.scale))
        for i, f in enumerate(self._chip_widgets):
            f.grid_forget()
            f.grid(row=i // cols, column=i % cols, sticky='nsew', padx=(0, 8), pady=(0, 8))
        for i in range(cols):
            self.chips_box.grid_columnconfigure(i, weight=1, uniform='chips')

    # ---------------------------------------------------------------- Execution History
    def _tags_of(self, iid):
        v = self.hist.item(iid, 'tags')
        if isinstance(v, str):
            return tuple(v.split()) if v else ()
        return tuple(v or ())

    def _hist_reset(self):
        self._h_last = None
        self._h_steps = {}
        self._h_latest = None
        if getattr(self, 'hist', None) is not None and self._sim_ready:
            try:
                self.hist.delete(*self.hist.get_children())
            except tk.TclError:
                pass

    def _hist_columns(self, e=None):
        try:
            w = self.hist.winfo_width()
            self.hist.configure(displaycolumns=('n', 'ins', 'what', 'res') if w >= 660 * self.scale else ('n', 'ins', 'res'))
        except tk.TclError:
            pass

    def _row_values(self, s):
        n, ins, what, res, tone = ex.history_row(s, self.lang)
        return (n, ins, what, res), tone

    def _update_history(self, view):
        trace = view.trace_tail
        last_no = trace[-1].step_no if trace else None
        tree = self.hist
        if last_no == self._h_last:
            return
        rebuild = (self._h_last is None or last_no is None or last_no < self._h_last
                   or last_no - self._h_last > HISTORY_ROWS)
        if rebuild:
            tree.delete(*tree.get_children())
            self._h_steps = {}
            todo = trace[-HISTORY_ROWS:]
        else:
            todo = [s for s in trace[-(last_no - self._h_last):]] if last_no > self._h_last else []
        if self._h_latest and tree.exists(self._h_latest):
            tree.item(self._h_latest, tags=tuple(x for x in self._tags_of(self._h_latest) if x != 'latest'))
        for s in todo:
            iid = f's{s.step_no}'
            vals, tone = self._row_values(s)
            tree.insert('', 'end', iid=iid, values=vals, tags=(tone,))
            self._h_steps[iid] = s
        kids = tree.get_children()
        if len(kids) > HISTORY_ROWS:
            drop = kids[:len(kids) - HISTORY_ROWS]
            tree.delete(*drop)
            for k in drop:
                self._h_steps.pop(k, None)
        self._h_last = last_no
        if last_no is not None:
            self._h_latest = f's{last_no}'
            if tree.exists(self._h_latest):
                tree.item(self._h_latest, tags=self._tags_of(self._h_latest) + ('latest',))
                tree.see(self._h_latest)
        self.hist_count.configure(text=self.tr('hist_count', n=min(len(trace), HISTORY_ROWS)) if trace else '')

    def _on_hist_select(self, e=None):
        sel = self.hist.selection()
        if not sel:
            return
        s = self._h_steps.get(sel[0])
        if s is None:
            return
        view = self.controller.get_view()
        latest = view.last_step is not None and view.last_step.step_no == s.step_no
        ee = ex.explain_step(s, view.cpu.regs if latest and view.cpu else None, self.lang)
        self.hist_info.configure(text=self.tr('hist_detail', n=format(s.step_no, ','), raw=ex.clean(s.instr.raw),
                                              sentence=ee['sentence']))

    # ---------------------------------------------------------------- รายละเอียดเชิงเทคนิค (Assembly / Registers)
    def _build_tech(self, parent):
        t = self.t
        self._tech_mode = 'asm'
        self.tech_seg = self.seg(parent, [('asm', self.tr('tab_asm')), ('regs', self.tr('tab_regs'))], 'asm',
                                 self._set_tech_mode, height=34, padx=14)
        self.tech_seg.pack(anchor='w', pady=(16, 10))
        self.tech_asm_f = tk.Frame(parent, bg=t['surface'])
        self.tech_reg_f = tk.Frame(parent, bg=t['surface'])
        self.asm = ttk.Treeview(self.tech_asm_f, columns=('addr', 'label', 'ins'), show='headings',
                                height=9, style='Hist.Treeview', selectmode='none')
        for c, key, w, st in [('addr', 'col_addr', 120, False), ('label', 'col_label', 150, False), ('ins', 'col_ins', 320, True)]:
            self.asm.heading(c, text=self.tr(key), anchor='w')
            self.asm.column(c, width=int(w * self.scale), stretch=st, anchor='w')
        s1 = ttk.Scrollbar(self.tech_asm_f, orient='vertical', command=self.asm.yview, style='Soft.Vertical.TScrollbar')
        self.asm.configure(yscrollcommand=s1.set)
        s1.pack(side='right', fill='y')
        self.asm.pack(side='left', fill='x', expand=True)
        self.asm.tag_configure('current', background=t['yellow_soft'], foreground=t['yellow_ink'])
        self.regs = ttk.Treeview(self.tech_reg_f, columns=('name', 'role', 'dec', 'hex'), show='headings',
                                 height=9, style='Hist.Treeview', selectmode='none')
        for c, key, w, st in [('name', 'col_reg', 100, False), ('role', 'col_role', 260, True),
                              ('dec', 'col_dec', 130, False), ('hex', 'col_hex', 130, False)]:
            self.regs.heading(c, text=self.tr(key), anchor='w')
            self.regs.column(c, width=int(w * self.scale), stretch=st, anchor='w')
        s2 = ttk.Scrollbar(self.tech_reg_f, orient='vertical', command=self.regs.yview, style='Soft.Vertical.TScrollbar')
        self.regs.configure(yscrollcommand=s2.set)
        s2.pack(side='right', fill='y')
        self.regs.pack(side='left', fill='x', expand=True)
        self.regs.tag_configure('chg', background=t['pink_soft'], foreground=t['pink_ink'])
        self.tech_asm_f.pack(fill='x')
        self._asm_cur, self._reg_cache = None, {}

    def _toggle_tech(self):
        self._tech_visible = not self._tech_visible
        if self._tech_visible:
            self.tech_frame.pack(fill='x')
            self._fill_asm(self.controller.program)
            self._update_tech(self.controller.get_view())
        else:
            self.tech_frame.pack_forget()

    def _set_tech_mode(self, mode):
        self._tech_mode = mode
        self.tech_asm_f.pack_forget()
        self.tech_reg_f.pack_forget()
        (self.tech_asm_f if mode == 'asm' else self.tech_reg_f).pack(fill='x')
        self._update_tech(self.controller.get_view())

    def _fill_asm(self, prog):
        if not getattr(self, 'asm', None) or prog is None or not self._sim_ready:
            return
        self.asm.delete(*self.asm.get_children())
        for ins in prog.instrs:
            self.asm.insert('', 'end', iid=f'a{ins.addr}', values=(f'0x{ins.addr:08X}', ins.label or '', ex.clean(ins.raw)))
        self._asm_cur = None

    def _update_tech(self, view):
        st = view.cpu
        if st is None:
            return
        if self._tech_mode == 'asm':
            cur = f'a{st.pc}'
            if cur != self._asm_cur and self.asm.exists(cur):
                if self._asm_cur and self.asm.exists(self._asm_cur):
                    self.asm.item(self._asm_cur, tags=())
                self.asm.item(cur, tags=('current',))
                self.asm.see(cur)
                self._asm_cur = cur
        else:
            roles = ex.roles_for(self._skey, self.lang)
            changed = set(view.last_step.reg_changes) if view.last_step else set()
            for i, v in enumerate(st.regs):
                iid = f'r{i}'
                sig = (v, i in changed)
                if self._reg_cache.get(iid) == sig:
                    continue
                vals = ('$' + REG_NAMES[i], roles.get(i, ''), s32(v), hex8(v))
                tags = ('chg',) if i in changed else ()
                if self.regs.exists(iid):
                    self.regs.item(iid, values=vals, tags=tags)
                else:
                    self.regs.insert('', 'end', iid=iid, values=vals, tags=tags)
                self._reg_cache[iid] = sig

    # ================================================================ เมาส์วีล
    def _on_wheel(self, e, direction=None):
        units = direction if direction is not None else (-1 if e.delta > 0 else 1)
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):          # บั๊กที่รู้กันของ Tkinter เมื่อเมาส์อยู่เหนือ popup บางชนิด
            return
        while w is not None:
            if isinstance(w, ttk.Treeview):
                return
            if isinstance(w, ScrollFrame):
                w.wheel(units * 2)
                return
            w = getattr(w, 'master', None)
