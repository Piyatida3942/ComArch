# NEW (interface_v2): แอนิเมชันน่ารักๆ ของหน้าเมนูหลัก -- มาสคอต "Chippy" (ชิป CPU ยิ้มได้ กะพริบตา กระโดดเบาๆ)
# + ฟองลอยสีพาสเทล + ตัวเลข/สัญลักษณ์คณิตศาสตร์ลอยขึ้น + ฟองคำพูดที่เปลี่ยนข้อความทุกไม่กี่วินาที
# วาดครั้งเดียวแล้วขยับด้วย move()/coords() จึงเบา (ประมาณ 25 เฟรม/วินาที) และหยุดเองเมื่อออกจากหน้านี้
import math
import random
import tkinter as tk

from .theme import DEFAULT_THEME, THEMES
from .widgets import round_rect, text_width

FRAME_MS = 40


class HomeHero(tk.Canvas):
    def __init__(self, parent, theme=None, fonts=None, scale=1.0, title='', subtitle='', lines=(), bg=None):
        self.t = theme if isinstance(theme, dict) else THEMES[DEFAULT_THEME]
        self.f = fonts
        self.s = scale
        self._title, self._sub, self._lines = title, subtitle, list(lines) or ['Hello!']
        super().__init__(parent, height=int(310 * scale), highlightthickness=0, bd=0, bg=bg or self.t['bg'])
        self._cw = 0
        self._job = None
        self._tick = 0
        self._bob = []                # [(canvas, tag, amplitude, phase)] การ์ดที่ขยับขึ้นลงเบาๆ ตามจังหวะเดียวกัน
        self._bob_last = {}
        self._shapes = []
        self._mdy = 0.0               # ระยะที่มาสคอตกระโดดอยู่ตอนนี้ (พิกเซล)
        self._geo = None
        self._line_i = 0
        self._blink = 0
        self.bind('<Configure>', self._on_configure)

    # ---------------------------------------------------------------- สั่งเริ่ม / หยุด
    def add_bobber(self, canvas, tag, amplitude=3.0, phase=0.0):
        self._bob.append((canvas, tag, amplitude, phase))

    def start(self):
        if self._job is None:
            self._job = self.after(FRAME_MS, self._loop)

    def stop(self):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def destroy(self):
        self.stop()
        super().destroy()

    def _on_configure(self, e):
        if abs(e.width - self._cw) >= 2:
            self._cw = e.width
            self._build(e.width)

    # ---------------------------------------------------------------- เลย์เอาต์
    def _layout(self, w):
        s = self.s
        if w < 780:                                       # แคบ: หัวเรื่องอยู่บน มาสคอตอยู่ล่าง
            H = 540 * s
            my = H - 150 * s
            return dict(narrow=True, H=H, title=(w / 2, 62 * s, 'center'), sub=(w / 2, 120 * s, 'n', w - 70 * s),
                        mx=w / 2, my=my, bubble_y=my - 196 * s, text_bottom=185 * s)
        H = 340 * s                                       # กว้าง: ข้อความซ้าย มาสคอตขวา
        return dict(narrow=False, H=H, title=(46 * s, 92 * s, 'w'), sub=(46 * s, 152 * s, 'nw', w * 0.44),
                    mx=w * 0.78, my=H / 2 + 40 * s, bubble_y=16 * s, text_bottom=212 * s)

    # ---------------------------------------------------------------- สร้างรูปทั้งหมด (เรียกเมื่อกว้างเปลี่ยน)
    def _build(self, w):
        t, f, s = self.t, self.f, self.s
        G = self._layout(w)
        self._geo = G
        self.delete('all')
        self.configure(height=int(G['H']))
        H = G['H']
        px1, py1, px2, py2 = 8, 8, w - 8, H - 8
        round_rect(self, px1, py1, px2, py2, 30 * s, fill=t['blue_soft'], outline=t['blue'], width=3)

        # --- ฟองลอย (ลอยขึ้นช้าๆ พร้อมส่ายซ้ายขวา)
        rnd = random.Random(11)
        kinds = ['circle', 'glyph', 'square', 'plus', 'ring', 'glyph', 'circle', 'glyph', 'plus', 'square', 'glyph', 'ring']
        glyphs = ['5!', 'nCr', '+', '×', '=', '10', '2', 'C', '!', '÷']
        colors = ['pink', 'yellow', 'violet', 'green', 'blue']
        self._shapes = []
        count = 16 if not G['narrow'] else 12
        text_right = 46 * s + max(text_width(f['hero'], self._title),
                                  min(G['sub'][3] if not G['narrow'] else 0, text_width(f['hero_sub'], self._sub)))
        for i in range(count):
            kind = kinds[i % len(kinds)]
            col = colors[i % len(colors)]
            span = (px2 - px1 - 60 * s) / count               # กระจายตามความกว้างให้เท่าๆ กัน ไม่ให้กระจุก
            x = px1 + 30 * s + (i + rnd.uniform(0.2, 0.8)) * span
            size = rnd.uniform(9, 20) * s
            # ฟองที่อยู่ในแนวข้อความ (หรือทุกฟองในโหมดแคบ) ลอยเฉพาะใต้บล็อกข้อความ จะได้ไม่บังหัวเรื่อง
            under_text = G['narrow'] or x < text_right + 30 * s
            top = (G['text_bottom'] + 14 * s) if under_text else py1 + 18 * s
            y = rnd.uniform(top, py2 - 20 * s)
            tag = f'sh{i}'
            if kind == 'circle':
                self.create_oval(x - size, y - size, x + size, y + size, fill=t[col + '_soft'], outline=t[col], width=2, tags=tag)
            elif kind == 'ring':
                self.create_oval(x - size, y - size, x + size, y + size, fill='', outline=t[col], width=3, tags=tag)
            elif kind == 'square':
                round_rect(self, x - size, y - size, x + size, y + size, 6 * s, fill=t[col + '_soft'], outline=t[col], width=2, tags=tag)
            elif kind == 'plus':
                self.create_line(x - size, y, x + size, y, fill=t[col], width=4, capstyle='round', tags=tag)
                self.create_line(x, y - size, x, y + size, fill=t[col], width=4, capstyle='round', tags=tag)
            else:
                self.create_text(x, y, text=glyphs[i % len(glyphs)], fill=t[col + '_ink'], font=f['h2'], tags=tag)
            self._shapes.append(dict(tag=tag, x0=x, y=y, x=x, vy=rnd.uniform(0.25, 0.7) * s,
                                     amp=rnd.uniform(6, 18) * s, ph=rnd.uniform(0, 6.28), top=top, bot=py2 - 18 * s))

        # --- มาสคอต Chippy
        mx, my = G['mx'], G['my']
        self._m = (mx, my)
        self.create_oval(mx - 56 * s, my + 66 * s, mx + 56 * s, my + 82 * s, fill=t['blue'], outline='', tags='shadow',
                         stipple='gray50')
        for k in (-36, -12, 12, 36):              # ขาชิป (บน / ล่าง)
            self.create_line(mx + k * s, my - 52 * s, mx + k * s, my - 68 * s, fill=t['blue'], width=6, capstyle='round', tags='mascot')
            self.create_line(mx + k * s, my + 52 * s, mx + k * s, my + 68 * s, fill=t['blue'], width=6, capstyle='round', tags='mascot')
        for k in (-26, 0, 26):                    # ขาชิป (ซ้าย / ขวา)
            self.create_line(mx - 62 * s, my + k * s, mx - 78 * s, my + k * s, fill=t['blue'], width=6, capstyle='round', tags='mascot')
            self.create_line(mx + 62 * s, my + k * s, mx + 78 * s, my + k * s, fill=t['blue'], width=6, capstyle='round', tags='mascot')
        round_rect(self, mx - 62 * s, my - 54 * s, mx + 62 * s, my + 54 * s, 24 * s, fill=t['surface'], outline=t['blue'], width=5, tags='mascot')
        round_rect(self, mx - 48 * s, my - 40 * s, mx + 48 * s, my + 38 * s, 16 * s, fill=t['blue_soft'], outline=t['blue'], width=2, tags='mascot')
        self.create_line(mx, my - 54 * s, mx, my - 80 * s, fill=t['blue'], width=4, capstyle='round', tags='mascot')   # เสาอากาศ
        self._bulb = self.create_oval(mx - 8 * s, my - 94 * s, mx + 8 * s, my - 78 * s, fill=t['yellow'], outline=t['yellow_ink'], width=2, tags='mascot')
        self._eyes, self._pupils = [], []
        for sx in (-21, 21):
            e = self.create_oval(mx + (sx - 11) * s, my - 24 * s, mx + (sx + 11) * s, my + 2 * s, fill='#FFFFFF', outline=t['blue_ink'], width=2, tags='mascot')
            p = self.create_oval(mx + (sx - 5) * s, my - 14 * s, mx + (sx + 5) * s, my - 2 * s, fill='#0F172A', outline='', tags='mascot')
            self._eyes.append((e, sx)), self._pupils.append((p, sx))
        for sx in (-34, 34):                       # แก้มสีชมพู
            self.create_oval(mx + (sx - 9) * s, my + 6 * s, mx + (sx + 9) * s, my + 18 * s, fill=t['pink'], outline='', tags='mascot')
        self.create_arc(mx - 15 * s, my + 2 * s, mx + 15 * s, my + 24 * s, start=205, extent=130, style='arc',
                        outline='#0F172A', width=4, tags='mascot')

        # --- ฟองคำพูด (อยู่เหนือเสาอากาศเสมอ แม้ตอนมาสคอตกระโดดสูงสุด)
        self._bubble_w = max(text_width(f['body_b'], ln) for ln in self._lines) + 44 * s
        bw, bh = self._bubble_w, 52 * s
        by = G['bubble_y']
        bx = (w / 2 - bw / 2) if G['narrow'] else (mx - bw / 2 - 36 * s)
        bx = max(px1 + 20 * s, min(bx, px2 - bw - 20 * s))
        round_rect(self, bx, by, bx + bw, by + bh, 20 * s, fill=t['surface'], outline=t['pink'], width=3, tags='bubble')
        tail_x = max(bx + 30 * s, min(mx - 6 * s, bx + bw - 44 * s))
        self.create_polygon(tail_x - 10 * s, by + bh - 2, tail_x + 16 * s, by + bh - 2, tail_x + 6 * s, by + bh + 18 * s,
                            fill=t['surface'], outline=t['pink'], width=3, joinstyle='round', tags='bubble')
        self.create_line(tail_x - 7 * s, by + bh, tail_x + 13 * s, by + bh, fill=t['surface'], width=5, tags='bubble')
        self._bubble_txt = self.create_text(bx + bw / 2, by + bh / 2, text=self._lines[self._line_i % len(self._lines)],
                                            fill=t['text'], font=f['body_b'], tags='bubble')

        # --- ข้อความหัวเรื่อง (วาดทีหลังสุด จะอยู่บนสุดเสมอ)
        tx_, ty_, anc = G['title']
        self.create_text(tx_, ty_, text=self._title, anchor=anc, fill=t['text'], font=f['hero'], tags='ui')
        sx_, sy_, sanc, sw_ = G['sub']
        self.create_text(sx_, sy_, text=self._sub, anchor=sanc, fill=t['muted'], font=f['hero_sub'], width=sw_,
                         justify='center' if G['narrow'] else 'left', tags='ui')
        self._mdy = 0.0
        self._bubble_dy = 0.0

    # ---------------------------------------------------------------- แอนิเมชัน
    def _loop(self):
        try:
            self._step()
        except tk.TclError:           # หน้าต่างถูกปิด/ถูกสร้างใหม่ระหว่างนั้น
            self._job = None
            return
        self._job = self.after(FRAME_MS, self._loop)

    def _step(self):
        if self._geo is None:
            return
        self._tick += 1
        n, s, t = self._tick, self.s, self.t
        # ฟองลอย
        for sh in self._shapes:
            new_y = sh['y'] - sh['vy']
            if new_y < sh['top']:
                new_y = sh['bot']
            new_x = sh['x0'] + sh['amp'] * math.sin(sh['ph'] + n * 0.03)
            self.move(sh['tag'], new_x - sh['x'], new_y - sh['y'])
            sh['x'], sh['y'] = new_x, new_y
        # มาสคอตกระโดดเบาๆ (เด้งแบบ |sin|)
        dy = -abs(math.sin(n * 0.075)) * 16 * s
        self.move('mascot', 0, dy - self._mdy)
        self._mdy = dy
        bdy = dy * 0.45
        self.move('bubble', 0, bdy - self._bubble_dy)
        self._bubble_dy = bdy
        mx, my = self._m
        grow = 1.0 - abs(dy) / (16 * s) * 0.35          # เงาเล็กลงเมื่อกระโดดสูง
        self.coords('shadow', mx - 56 * s * grow, my + 66 * s, mx + 56 * s * grow, my + 82 * s)
        # ตาเหลือบซ้ายขวา + กะพริบทุก ~3.2 วินาที
        look = round(3 * math.sin(n * 0.045)) * s
        blinking = (n % 80) in (0, 1, 2)
        for (e, sx), (p, _) in zip(self._eyes, self._pupils):
            if blinking:
                self.coords(e, mx + (sx - 11) * s, my - 12 * s + dy, mx + (sx + 11) * s, my - 8 * s + dy)
                self.coords(p, mx + sx * s, my - 10 * s + dy, mx + sx * s, my - 10 * s + dy)
            else:
                self.coords(e, mx + (sx - 11) * s, my - 24 * s + dy, mx + (sx + 11) * s, my + 2 * s + dy)
                self.coords(p, mx + (sx - 5) * s + look, my - 14 * s + dy, mx + (sx + 5) * s + look, my - 2 * s + dy)
        # หลอดไฟเสาอากาศสลับสีเหลือง/ชมพู
        self.itemconfigure(self._bulb, fill=t['pink'] if (n // 20) % 2 else t['yellow'])
        # เปลี่ยนข้อความในฟองคำพูดทุก ~3.6 วินาที
        if n % 90 == 0:
            self._line_i += 1
            self.itemconfigure(self._bubble_txt, text=self._lines[self._line_i % len(self._lines)])
        # การ์ดที่ขยับขึ้นลงเบาๆ
        for canvas, tag, amp, ph in self._bob:
            off = amp * math.sin(n * 0.09 + ph)
            last = self._bob_last.get((id(canvas), tag), 0.0)
            canvas.move(tag, 0, off - last)
            self._bob_last[(id(canvas), tag)] = off
