# NEW: วิดเจ็ตพื้นฐานที่ใช้ซ้ำ -- ปุ่มโค้งมน, ไอคอนเส้นเรียบ, แท็บ, พื้นที่เลื่อน, layout ที่ปรับตามขนาดหน้าต่าง
import math
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

from .theme import blend


# ------------------------------------------------------------------ วาดรูปพื้นฐาน
def round_rect(c, x1, y1, x2, y2, r=10, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def draw_icon(c, name, cx, cy, s, color, tag='icon'):
    """ไอคอนเส้นเรียบๆ วาดด้วย canvas (ไม่พึ่งฟอนต์ จึงหน้าตาเหมือนกันทุกเครื่อง)"""
    h = s / 2.0
    lw = max(2, int(round(s / 7)))
    fk = dict(fill=color, outline=color, width=lw, joinstyle='round', tags=tag)
    lk = dict(fill=color, width=lw, capstyle='round', joinstyle='round', tags=tag)
    if name == 'play':
        c.create_polygon(cx - h * .45, cy - h * .8, cx - h * .45, cy + h * .8, cx + h * .8, cy, **fk)
    elif name == 'pause':
        c.create_line(cx - h * .4, cy - h * .75, cx - h * .4, cy + h * .75, **lk)
        c.create_line(cx + h * .4, cy - h * .75, cx + h * .4, cy + h * .75, **lk)
    elif name == 'step':
        c.create_polygon(cx - h * .8, cy - h * .7, cx - h * .8, cy + h * .7, cx + h * .35, cy, **fk)
        c.create_line(cx + h * .8, cy - h * .7, cx + h * .8, cy + h * .7, **lk)
    elif name == 'back':
        c.create_polygon(cx + h * .8, cy - h * .7, cx + h * .8, cy + h * .7, cx - h * .35, cy, **fk)
        c.create_line(cx - h * .8, cy - h * .7, cx - h * .8, cy + h * .7, **lk)
    elif name == 'reset':
        r = h * .8
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=60, extent=290, style='arc',
                     outline=color, width=lw, tags=tag)
        a = math.radians(350)                       # ปลายเส้นโค้ง
        px, py = cx + r * math.cos(a), cy - r * math.sin(a)
        tx, ty = -math.sin(a), -math.cos(a)         # ทิศที่เส้นโค้งกำลังไป
        nx, ny = -ty, tx
        k = h * .55
        c.create_polygon(px + tx * k, py + ty * k, px + nx * k * .8, py + ny * k * .8,
                         px - nx * k * .8, py - ny * k * .8, **fk)
    elif name == 'chevron_left':
        c.create_line(cx + h * .35, cy - h * .7, cx - h * .35, cy, cx + h * .35, cy + h * .7, **lk)
    elif name == 'arrow_right':
        c.create_line(cx - h * .8, cy, cx + h * .8, cy, **lk)
        c.create_line(cx + h * .2, cy - h * .6, cx + h * .8, cy, cx + h * .2, cy + h * .6, **lk)
    elif name == 'check':
        c.create_line(cx - h * .7, cy, cx - h * .15, cy + h * .55, cx + h * .75, cy - h * .55, **lk)
    elif name == 'chip':       # โลโก้: ชิปเล็กๆ
        c.create_rectangle(cx - h * .5, cy - h * .5, cx + h * .5, cy + h * .5, outline=color, width=lw, tags=tag)
        for d in (-.25, .25):
            c.create_line(cx + h * d, cy - h * .5, cx + h * d, cy - h * .95, **lk)
            c.create_line(cx + h * d, cy + h * .5, cx + h * d, cy + h * .95, **lk)
            c.create_line(cx - h * .5, cy + h * d, cx - h * .95, cy + h * d, **lk)
            c.create_line(cx + h * .5, cy + h * d, cx + h * .95, cy + h * d, **lk)
    elif name == 'list':
        for dy in (-.55, 0, .55):
            c.create_line(cx - h * .8, cy + h * dy, cx + h * .8, cy + h * dy, **lk)
    elif name == 'dot':
        c.create_oval(cx - h * .45, cy - h * .45, cx + h * .45, cy + h * .45, fill=color, outline=color, tags=tag)


def text_width(font, text):
    try:
        return tkfont.Font(font=font).measure(text)
    except tk.TclError:
        return len(text) * 8


# ------------------------------------------------------------------ ปุ่ม Pill
class Pill(tk.Canvas):
    """ปุ่มโค้งมน kind: primary | soft | ghost | seg_on | seg_off"""

    def __init__(self, parent, text='', icon=None, command=None, kind='soft', theme=None,
                 font=None, height=38, padx=16, bg=None, width=None, icon_size=13, radius=None):
        self.t = theme
        self.kind, self.text, self.icon = kind, text, icon
        self.command, self.enabled = command, True
        self._font = font or ('TkDefaultFont', 10, 'bold')
        self._h, self._padx, self._isz = height, padx, icon_size
        self._r = radius if radius is not None else height / 2
        self._hover = self._down = False
        self._fixed_w = width
        super().__init__(parent, width=self._req_w(), height=height, bg=bg or theme['bg'],
                         highlightthickness=0, bd=0, cursor='hand2', takefocus=1)
        self.bind('<Configure>', lambda e: self.draw())
        self.bind('<Enter>', self._enter)
        self.bind('<Leave>', self._leave)
        self.bind('<ButtonPress-1>', self._press)
        self.bind('<ButtonRelease-1>', self._release)
        self.bind('<Return>', lambda e: self.invoke())
        self.bind('<space>', lambda e: self.invoke())
        self.draw()

    def _req_w(self):
        if self._fixed_w:
            return self._fixed_w
        w = text_width(self._font, self.text) + 2 * self._padx if self.text else 2 * self._padx
        if self.icon:
            w += self._isz + (8 if self.text else 0)
        return int(max(w, self._h))

    def _colors(self):
        t, k = self.t, self.kind
        if not self.enabled:
            return t['surface2'], t['faint'], t['surface2']
        if k == 'primary':
            f = t['primary']
            f = blend(f, '#FFFFFF' if t['dark'] else '#000000', .14 if self._hover else 0)
            return (blend(f, '#000000', .1) if self._down else f), t['on_primary'], f
        if k == 'soft':
            f = blend(t['primary_soft'], t['primary'], .22 if self._hover else .0)
            return f, t['primary_ink'], f
        if k == 'seg_on':
            return t['surface'], t['primary_ink'], t['border']
        if k == 'seg_off':
            return t['surface2'], t['text'] if self._hover else t['muted'], t['surface2']
        # ghost
        f = t['surface2'] if self._hover else t['surface']
        return f, t['text'], t['border']

    def draw(self):
        self.delete('all')
        w = max(self.winfo_width(), 4)
        if w <= 4:
            w = self._req_w()
        h = self._h
        fill, fg, outline = self._colors()
        round_rect(self, 1, 1, w - 1, h - 1, self._r, fill=fill, outline=outline, width=1)
        tw = text_width(self._font, self.text) if self.text else 0
        total = tw + ((self._isz + (8 if self.text else 0)) if self.icon else 0)
        x = (w - total) / 2.0
        if self.icon:
            draw_icon(self, self.icon, x + self._isz / 2.0, h / 2.0, self._isz, fg)
            x += self._isz + (8 if self.text else 0)
        if self.text:
            self.create_text(x, h / 2.0 + 0.5, text=self.text, anchor='w', fill=fg, font=self._font)

    # --- สถานะ
    def set_enabled(self, on):
        on = bool(on)
        if on != self.enabled:
            self.enabled = on
            self.configure(cursor='hand2' if on else 'arrow')
            self.draw()

    def set_text(self, text, icon='__keep__'):
        new_icon = self.icon if icon == '__keep__' else icon
        if text == self.text and new_icon == self.icon:
            return
        self.text, self.icon = text, new_icon
        self.configure(width=self._req_w())
        self.draw()

    def invoke(self):
        if self.enabled and self.command:
            self.command()

    def _enter(self, e):
        self._hover = True
        self.draw()

    def _leave(self, e):
        self._hover = self._down = False
        self.draw()

    def _press(self, e):
        if self.enabled:
            self._down = True
            self.draw()

    def _release(self, e):
        was = self._down
        self._down = False
        self.draw()
        if was and 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self._h:
            self.invoke()


# ------------------------------------------------------------------ แท็บ / ตัวเลือกแบบ segmented
class Segmented(tk.Canvas):
    def __init__(self, parent, options, value, command=None, theme=None, font=None,
                 bg=None, height=36, padx=14, min_seg=0):
        self.t, self.options, self.value, self.command = theme, options, value, command
        self._font = font or ('TkDefaultFont', 10, 'bold')
        self._h, self._hover = height, None
        self._ws = [max(min_seg, text_width(self._font, label) + 2 * padx) for _, label in options]
        super().__init__(parent, width=int(sum(self._ws) + 8), height=height, bg=bg or theme['bg'],
                         highlightthickness=0, bd=0, cursor='hand2')
        self.bind('<ButtonRelease-1>', self._click)
        self.bind('<Motion>', self._motion)
        self.bind('<Leave>', lambda e: self._set_hover(None))
        self.draw()

    def _index_at(self, x):
        acc = 4
        for i, w in enumerate(self._ws):
            if acc <= x < acc + w:
                return i
            acc += w
        return None

    def _click(self, e):
        i = self._index_at(e.x)
        if i is not None:
            self.set(self.options[i][0], notify=True)

    def _motion(self, e):
        self._set_hover(self._index_at(e.x))

    def _set_hover(self, i):
        if i != self._hover:
            self._hover = i
            self.draw()

    def set(self, value, notify=False):
        changed = value != self.value
        self.value = value
        self.draw()
        if notify and changed and self.command:
            self.command(value)

    def draw(self):
        t = self.t
        self.delete('all')
        w = int(sum(self._ws) + 8)
        round_rect(self, 1, 1, w - 1, self._h - 1, self._h / 2, fill=t['surface2'], outline=t['border'])
        x = 4
        for i, ((key, label), sw) in enumerate(zip(self.options, self._ws)):
            on = key == self.value
            if on:
                round_rect(self, x, 4, x + sw, self._h - 4, (self._h - 8) / 2,
                           fill=t['surface'], outline=t['primary'] if not t['dark'] else t['primary'], width=1)
            fg = t['primary_ink'] if on else (t['text'] if self._hover == i else t['muted'])
            self.create_text(x + sw / 2.0, self._h / 2.0 + 0.5, text=label, fill=fg, font=self._font)
            x += sw


# ------------------------------------------------------------------ พื้นที่เลื่อน
class ScrollFrame(tk.Frame):
    """เลื่อนแนวตั้ง; เนื้อหา (self.body) กว้างเท่าพื้นที่เสมอ จึงปรับตามขนาดหน้าต่างได้
    จำตำแหน่งที่ผู้ใช้เลื่อนไว้ (self._want) -- ถ้าเนื้อหาเปลี่ยนความสูงระหว่าง Run จะไม่ดึงหน้าจอกลับ/กระตุก"""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self._want = 0.0
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient='vertical', command=self._yview,
                                 style='Soft.Vertical.TScrollbar')
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.body = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor='nw')
        self.body.bind('<Configure>', self._on_body)
        self.canvas.bind('<Configure>', self._on_canvas)

    def _yview(self, *args):                    # เรียกจากแถบเลื่อนที่ผู้ใช้ลาก
        self.canvas.yview(*args)
        self._want = self.canvas.canvasy(0)

    def _on_body(self, e):
        self.canvas.configure(scrollregion=(0, 0, e.width, e.height))
        self._restore()

    def _restore(self):
        h = max(self.body.winfo_reqheight(), 1)
        target = max(0.0, min(self._want, h - self.canvas.winfo_height()))
        if abs(self.canvas.canvasy(0) - target) > 0.5:
            self.canvas.yview_moveto(target / h)

    def _on_canvas(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)

    def can_scroll(self):
        return self.body.winfo_reqheight() > self.canvas.winfo_height() + 2

    def wheel(self, units):
        if self.can_scroll():
            self.canvas.yview_scroll(units, 'units')
            self._want = self.canvas.canvasy(0)

    def to_top(self):
        self._want = 0.0
        self.canvas.yview_moveto(0)


# ------------------------------------------------------------------ layout ที่ปรับตามความกว้าง
class Centered(tk.Frame):
    """จำกัดความกว้างเนื้อหา (max_w) และจัดกึ่งกลางเมื่อหน้าต่างกว้างมาก"""

    def __init__(self, parent, bg, max_w=1080, min_pad=22):
        super().__init__(parent, bg=bg)
        self.max_w, self.min_pad = max_w, min_pad
        self.inner = tk.Frame(self, bg=bg)
        self.inner.pack(fill='both', expand=True, padx=min_pad)
        self.bind('<Configure>', self._on)

    def _on(self, e):
        pad = max(self.min_pad, (e.width - self.max_w) // 2)
        self.inner.pack_configure(padx=pad)


class Flow(tk.Frame):
    """วางลูกเรียงข้างกัน เมื่อกว้างพอ และเรียงซ้อนลงมาเมื่อแคบ"""

    def __init__(self, parent, bg, breakpoint=760, gap=14):
        super().__init__(parent, bg=bg)
        self.bp, self.gap, self.items, self._mode = breakpoint, gap, [], None
        self.bind('<Configure>', lambda e: self._layout())

    def add(self, widget, weight=1):
        self.items.append((widget, weight))
        self._layout(force=True)

    def _layout(self, force=False):
        w = self.winfo_width()
        mode = 'row' if (w >= self.bp or w <= 1) else 'col'
        if mode == self._mode and not force:
            return
        self._mode = mode
        n = len(self.items)
        for i in range(max(n, 6)):
            self.grid_columnconfigure(i, weight=0, uniform='')
            self.grid_rowconfigure(i, weight=0)
        for wd, _ in self.items:
            wd.grid_forget()
        g = self.gap
        for i, (wd, wt) in enumerate(self.items):
            if mode == 'row':
                wd.grid(row=0, column=i, sticky='nsew', padx=(0 if i == 0 else g // 2, 0 if i == n - 1 else g // 2))
                self.grid_columnconfigure(i, weight=wt, uniform='flow')
            else:
                wd.grid(row=i, column=0, sticky='nsew', pady=(0 if i == 0 else g // 2, 0))
                self.grid_columnconfigure(0, weight=1)
        if mode == 'row':
            self.grid_rowconfigure(0, weight=1)


# ------------------------------------------------------------------ ตัวช่วยเล็กๆ
def make_card(parent, t, bg=None, padx=18, pady=16, border=None):
    bg = bg or t['surface']
    bc = border or t['border']
    outer = tk.Frame(parent, bg=bg, highlightthickness=1, highlightbackground=bc,
                     highlightcolor=bc, bd=0)
    outer.inner = tk.Frame(outer, bg=bg)
    outer.inner.pack(fill='both', expand=True, padx=padx, pady=pady)
    return outer


def chip(parent, text, bg, fg, font, padx=10, pady=3):
    return tk.Label(parent, text=text, bg=bg, fg=fg, font=font, padx=padx, pady=pady, bd=0)


def autowrap(label, container, pad=0, minw=140):
    container.bind('<Configure>', lambda e: label.configure(wraplength=max(minw, e.width - pad)), add='+')


def apply_ttk_style(root, t, f, scale=1.0):
    """ตั้งค่า ttk (เฉพาะ Entry / Treeview / Scrollbar ที่ต้องใช้ ttk)"""
    s = ttk.Style(root)
    try:
        s.theme_use('clam')
    except tk.TclError:
        pass
    s.configure('Soft.TEntry', fieldbackground=t['surface'], foreground=t['text'],
                insertcolor=t['text'], bordercolor=t['border'], lightcolor=t['border'],
                darkcolor=t['border'], padding=(int(10 * scale), int(9 * scale)), relief='flat')
    s.map('Soft.TEntry', bordercolor=[('focus', t['primary'])], lightcolor=[('focus', t['primary'])],
          darkcolor=[('focus', t['primary'])])
    s.configure('Hist.Treeview', background=t['surface'], fieldbackground=t['surface'],
                foreground=t['text'], rowheight=int(34 * scale), borderwidth=0, relief='flat', font=f['hist'])
    s.configure('Hist.Treeview.Heading', background=t['surface2'], foreground=t['muted'],
                font=f['hist_head'], relief='flat', borderwidth=0, padding=(int(8 * scale), int(7 * scale)))
    s.map('Hist.Treeview', background=[('selected', t['primary_soft'])],
          foreground=[('selected', t['primary_ink'])])
    s.map('Hist.Treeview.Heading', background=[('active', t['surface2'])])
    s.layout('Hist.Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
    s.configure('Soft.Vertical.TScrollbar', background=t['border'], troughcolor=t['bg'],
                bordercolor=t['bg'], arrowcolor=t['muted'], lightcolor=t['border'],
                darkcolor=t['border'], gripcount=0, relief='flat', arrowsize=int(14 * scale))
    s.map('Soft.Vertical.TScrollbar', background=[('active', t['faint'])])
    return s
