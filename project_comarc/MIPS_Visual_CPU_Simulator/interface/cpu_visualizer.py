# NEW (interface_v2, ปรับจาก interface/cpu_visualizer.py เดิม): CPU Execution Path
# กรอบสีหนา + halo + ป้าย WORKING วิ่งตามขั้นที่ CPU กำลังทำ, ขั้นที่ผ่านแล้วเป็นสีอ่อน,
# ขั้นที่คำสั่งนี้ไม่ใช้เป็นเส้นประจาง, และทุกกล่องมีตัวเลขของขั้นนั้นเสมอ
# อ่านข้อมูลจาก StepResult อย่างเดียว ไม่แก้ไขสถานะ CPU
import tkinter as tk

from .explain import DEFAULT_LANG, stage_info, tx
from .i18n import tr
from .theme import DEFAULT_THEME, STAGE_COLORS, THEMES
from .widgets import round_rect

DEFAULT_FONTS = {'small': ('Segoe UI', 10), 'small_b': ('Segoe UI', 10, 'bold'),
                 'step': ('Segoe UI', 11, 'bold'), 'mono_b': ('Consolas', 11, 'bold'),
                 'tiny_b': ('Segoe UI', 9, 'bold')}


def compute_layout(w, s=1.0):
    """คำนวณตำแหน่งกล่อง 5 ใบจากความกว้าง w (พิกเซล) และสเกลหน้าจอ s (ฟังก์ชันล้วน ทดสอบได้)"""
    pad, top = 14 * s, 38 * s
    gap = 30 * s
    bw = (w - 2 * pad - 4 * gap) / 5.0
    if bw >= 118 * s:
        bh = 132 * s
        rects = [(pad + i * (bw + gap), top, pad + i * (bw + gap) + bw, top + bh) for i in range(5)]
        arrows = [[(rects[i][2] + 3, top + bh / 2.0), (rects[i + 1][0] - 3, top + bh / 2.0)] for i in range(4)]
        return dict(compact=False, rects=rects, arrows=arrows, height=int(top + bh + 46 * s), bw=bw, bh=bh)
    gap = 26 * s
    bw = (w - 2 * pad - 2 * gap) / 3.0            # หดตามพื้นที่เสมอ (ข้อความในกล่องตัดบรรทัดเอง)
    bh, rowgap = 118 * s, 58 * s
    rects = []
    for i in range(5):
        row, col = (0, i) if i < 3 else (1, i - 3)
        x = pad + col * (bw + gap)
        y = top + row * (bh + rowgap)
        rects.append((x, y, x + bw, y + bh))
    arrows = [[(rects[i][2] + 3, rects[i][1] + bh / 2.0), (rects[i + 1][0] - 3, rects[i + 1][1] + bh / 2.0)]
              for i in (0, 1, 3)]
    cx2 = (rects[2][0] + rects[2][2]) / 2.0
    cx3 = rects[3][0] + 28 * s                   # ลูกศรเข้าด้านซ้ายของกล่อง (ป้ายอยู่ด้านขวา)
    ymid = rects[2][3] + 12 * s                  # เส้นอยู่สูงกว่าป้าย จึงไม่ซ้อนกัน
    arrows.insert(2, [(cx2, rects[2][3] + 2), (cx2, ymid), (cx3, ymid), (cx3, rects[3][1] - 3)])
    return dict(compact=True, rects=rects, arrows=arrows, height=int(top + 2 * bh + rowgap + 46 * s), bw=bw, bh=bh)


class CPUDiagram(tk.Canvas):
    def __init__(self, parent, theme=None, fonts=None, scale=1.0, lang=DEFAULT_LANG, **kwargs):
        self.t = theme if isinstance(theme, dict) else THEMES[DEFAULT_THEME]
        self.f = fonts or DEFAULT_FONTS
        self.s = scale
        self.lang = lang
        super().__init__(parent, height=int(200 * scale), highlightthickness=0, bd=0, bg=self.t['surface'], **kwargs)
        self.step = None
        self.anim_i = None
        self._ids = []
        self._cw = 0                # (ห้ามใช้ชื่อ _w : เป็นชื่อภายในของ Tkinter เก็บ path ของ widget)
        self.bind('<Configure>', self._on_configure)

    # ---------------------------------------------------------------- API
    def set_theme(self, theme):
        if isinstance(theme, bool):                     # เข้ากับโค้ดเดิม set_theme(dark)
            theme = THEMES['night' if theme else DEFAULT_THEME]
        self.t = theme
        self.configure(bg=self.t['surface'])
        self.draw()

    def set_lang(self, lang):
        self.lang = lang
        self.draw()

    def show_step(self, step, animate=False, anim_ms=0):
        self.stop()
        self.step = step
        self.anim_i = None
        used = [i for i, s in enumerate(stage_info(step, self.lang)) if s['used']] if step is not None else []
        if step is not None and animate and anim_ms >= 120 and used:
            dwell = max(70, int(anim_ms / len(used)))
            self._set_anim(used[0])
            for k, i in enumerate(used[1:], start=1):
                self._ids.append(self.after(k * dwell, lambda i=i: self._set_anim(i)))
            self._ids.append(self.after(len(used) * dwell, lambda: self._set_anim(None)))
        else:
            self.draw()

    def clear(self):
        self.show_step(None)

    def stop(self):
        for i in self._ids:
            try:
                self.after_cancel(i)
            except tk.TclError:
                pass
        self._ids = []

    def destroy(self):
        self.stop()
        super().destroy()

    # ---------------------------------------------------------------- ภายใน
    def _set_anim(self, i):
        self.anim_i = i
        self.draw()

    def _on_configure(self, e):
        if abs(e.width - self._cw) >= 2:
            self._cw = e.width
            self.draw()

    def _state(self, i, info, used_idx):
        if self.step is None:
            return 'idle'
        if not self.step.completed and i == 3:
            return 'error'
        if self.anim_i is not None:
            if i == self.anim_i:
                return 'current'
            if info[i]['used']:
                return 'done' if used_idx.index(i) < used_idx.index(self.anim_i) else 'pending'
            return 'skipped'
        return 'done' if info[i]['used'] else 'skipped'

    def draw(self):
        t, f = self.t, self.f
        self.delete('all')
        w = self.winfo_width()
        w = 900 if w <= 1 else max(w, 360)
        s = self.s
        L = compute_layout(w, s)
        if int(float(self.cget('height'))) != int(L['height']):
            self.configure(height=int(L['height']))
        info = stage_info(self.step, self.lang)
        used_idx = [i for i, st in enumerate(info) if st['used']]
        last_used = used_idx[-1] if used_idx else -1
        compact = L['compact']

        # ลูกศรเชื่อม
        for k, pts in enumerate(L['arrows']):
            lit = (self.step is not None and info[k]['used'] and k < last_used)
            col = t[STAGE_COLORS[k]] if lit else t['border']
            flat = [c for p in pts for c in p]
            self.create_line(*flat, fill=col, width=4 if lit else 2, arrow=tk.LAST,
                             arrowshape=(11, 13, 5), capstyle='round', joinstyle='round')

        # กล่อง 5 ใบ
        for i, (x1, y1, x2, y2) in enumerate(L['rects']):
            col = STAGE_COLORS[i]
            c, soft, ink = t[col], t[col + '_soft'], t[col + '_ink']
            state = self._state(i, info, used_idx)
            if state == 'current':
                round_rect(self, x1 - 6 * s, y1 - 6 * s, x2 + 6 * s, y2 + 6 * s, 20 * s, fill='', outline=c, width=3)
                round_rect(self, x1, y1, x2, y2, 14 * s, fill=soft, outline=c, width=5)
                tw = 92 * s
                cx = (x1 + x2) / 2.0
                if compact:                      # โหมดแคบ: ป้ายชิดมุมขวา ไม่ชนลูกศรโค้งที่เข้ามา
                    cx = x2 - tw / 2.0 - 2
                round_rect(self, cx - tw / 2, y1 - 31 * s, cx + tw / 2, y1 - 9 * s, 11 * s, fill=c, outline=c)
                self.create_text(cx, y1 - 20 * s, text=tr(self.lang, 'tag_working'), fill='#111827', font=f['tiny_b'])
            elif state == 'error':
                round_rect(self, x1 - 5 * s, y1 - 5 * s, x2 + 5 * s, y2 + 5 * s, 19 * s, fill='', outline=t['red'], width=3)
                round_rect(self, x1, y1, x2, y2, 14 * s, fill=t['red_soft'], outline=t['red'], width=5)
                c, ink = t['red'], t['red_ink']
            elif state == 'done':
                round_rect(self, x1, y1, x2, y2, 14 * s, fill=soft, outline=c, width=3)
            elif state == 'skipped':
                round_rect(self, x1, y1, x2, y2, 14 * s, fill=t['surface'], outline=t['border'], width=2, dash=(5, 4))
            else:   # idle / pending
                round_rect(self, x1, y1, x2, y2, 14 * s, fill=t['surface2'], outline=t['border'], width=2)

            active = state in ('current', 'done', 'error')
            title_fg = t['text'] if active else (t['muted'] if state != 'skipped' else t['faint'])
            by = y1 + 20 * s
            self.create_oval(x1 + 9 * s, by - 11 * s, x1 + 31 * s, by + 11 * s, fill=c if active else t['border'],
                             outline=c if active else t['border'])
            self.create_text(x1 + 20 * s, by, text=str(i + 1), fill='#111827' if active else t['muted'],
                             font=f['small_b'])
            self.create_text(x1 + 39 * s, by, text=info[i]['short'] if compact else info[i]['name'],
                             anchor='w', fill=title_fg, font=f['step'], width=x2 - x1 - 46 * s)
            self.create_text(x1 + 12 * s, y1 + 46 * s, text=info[i]['sub'], anchor='w',
                             fill=t['muted'] if active else t['faint'], font=f['small'], width=x2 - x1 - 20 * s)
            if state == 'skipped':
                cap, cap_fg = tx(self.lang, 'c.skipped'), t['faint']
            else:
                cap, cap_fg = info[i]['caption'], (ink if active else t['faint'])
            self.create_text(x1 + 12 * s, y1 + 68 * s, text=cap, anchor='nw', fill=cap_fg,
                             font=f['mono_b'] if not compact else f['small_b'], width=x2 - x1 - 22 * s)

        # บรรทัดสรุป
        bottom = L['height'] - 20 * s
        if self.step is None:
            msg = tr(self.lang, 'path_idle')
        else:
            st = self.step
            msg = tr(self.lang, 'path_step', n=f'{st.step_no:,}', op=st.instr.op,
                     a=f'0x{st.pc_before:08X}', b=f'0x{st.pc_after:08X}')
        self.create_text(14 * s, bottom, text=msg, anchor='w', fill=t['muted'], font=f['small'], width=w - 28 * s)
