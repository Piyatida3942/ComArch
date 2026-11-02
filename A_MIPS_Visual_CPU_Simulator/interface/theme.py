# NEW: สีและฟอนต์ -- เหลือ 2 ธีม: Day (สว่าง pastel ชมพู/ฟ้า/เหลือง บนพื้นขาว) และ Night (พื้นมืดเดิม เน้นขาว/ฟ้าอ่อน)
# เฉดสีอ้างอิงจากไฟล์ sorter_gui_final.py แต่ปรับให้ "ชัด" ขึ้น: เส้นขอบเข้มขึ้น, ตัวอักษรเข้มขึ้น, สีเน้นอิ่มขึ้น
#
# แก้สี/ฟอนต์ได้ที่ไฟล์นี้ที่เดียว (โปรแกรมเลือกฟอนต์ตัวแรกในรายการที่เครื่องมี)

# ---------- ฟอนต์ ----------
FONT_PREFS = {
    'ui':   ['Segoe UI', 'Leelawadee UI', 'Tahoma', 'Noto Sans Thai', 'Helvetica Neue', 'DejaVu Sans'],
    'soft': ['Leelawadee UI', 'Segoe UI', 'Tahoma', 'Noto Sans Thai', 'Helvetica Neue', 'DejaVu Sans'],  # Step / History
    'mono': ['Cascadia Mono', 'Consolas', 'Menlo', 'DejaVu Sans Mono', 'Courier New'],
}


def pick_family(available, prefs, fallback):
    have = {a.lower(): a for a in available}
    for name in prefs:
        if name.lower() in have:
            return have[name.lower()]
    return fallback


def ui_scale(root):
    """ตัวคูณสำหรับสิ่งที่วาดเอง (ปุ่ม/กล่อง) ให้โตตามฟอนต์เมื่อ Windows ตั้งขยายหน้าจอ 125-150%"""
    try:
        return max(1.0, min(2.5, float(root.tk.call('tk', 'scaling')) / 1.3333))
    except Exception:       # noqa: BLE001
        return 1.0


def make_fonts(root):
    """คืน dict ของฟอนต์ (family, size[, weight]) ที่เครื่องนี้มีจริง"""
    import tkinter.font as tkfont
    avail = set(tkfont.families(root))
    ui = pick_family(avail, FONT_PREFS['ui'], 'TkDefaultFont')
    soft = pick_family(avail, FONT_PREFS['soft'], ui)
    mono = pick_family(avail, FONT_PREFS['mono'], 'TkFixedFont')
    return {
        'family': ui, 'mono_family': mono,
        'body': (ui, 12), 'body_b': (ui, 12, 'bold'),
        'small': (ui, 10), 'small_b': (ui, 10, 'bold'),
        'tiny_b': (ui, 9, 'bold'),
        'h1': (ui, 30, 'bold'), 'h2': (ui, 20, 'bold'), 'h3': (ui, 15, 'bold'),
        'hero': (ui, 38, 'bold'), 'hero_sub': (ui, 14),
        'big': (ui, 54, 'bold'), 'num': (ui, 22, 'bold'),
        'step': (soft, 11, 'bold'),             # Step / ชื่อขั้นของ CPU Path (มน + หนาเล็กน้อย)
        'hist': (soft, 11, 'bold'),             # Execution History
        'hist_head': (soft, 10, 'bold'),
        'mono': (mono, 11), 'mono_b': (mono, 11, 'bold'),
        'btn': (ui, 11, 'bold'),
    }


# ---------- สี ----------
def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return '#%02X%02X%02X' % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def blend(c1, c2, t):
    """ผสมสี c1 -> c2 ที่สัดส่วน t (0..1)"""
    a, b = _hex_to_rgb(c1), _hex_to_rgb(c2)
    return _rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def _lum(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in _hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


THEMES = {
    # Day: พื้นขาว ชมพู / ฟ้า / เหลือง (+ เขียว ม่วง แดง ใช้บอกสถานะ) เส้นและตัวอักษรเข้มพอให้ชัด
    'day': dict(
        dark=False,
        bg='#FFFFFF', surface='#FFFFFF', surface2='#F1F5F9', border='#B6C2D2',
        text='#0F172A', muted='#475569', faint='#8493A8',
        primary='#2563EB', primary_soft='#DBEAFE', primary_ink='#1E40AF', on_primary='#FFFFFF',
        pink='#EC4899', pink_soft='#FCE7F3', pink_ink='#9D174D',
        blue='#0EA5E9', blue_soft='#E0F2FE', blue_ink='#075985',
        yellow='#F59E0B', yellow_soft='#FEF3C7', yellow_ink='#92400E',
        green='#10B981', green_soft='#D1FAE5', green_ink='#065F46',
        violet='#8B5CF6', violet_soft='#EDE9FE', violet_ink='#5B21B6',
        red='#EF4444', red_soft='#FEE2E2', red_ink='#991B1B',
    ),
    # Night: พื้นมืดเดิม (#0B1220) เน้นขาว + ฟ้าอ่อน
    'night': dict(
        dark=True,
        bg='#0B1220', surface='#162237', surface2='#1F3050', border='#4A6285',
        text='#F8FAFC', muted='#BBC8DE', faint='#7C8FAD',
        primary='#7DD3FC', primary_soft='#17344F', primary_ink='#BAE6FD', on_primary='#0B1220',
        pink='#F9A8D4', pink_soft='#3A2038', pink_ink='#FBCFE8',
        blue='#7DD3FC', blue_soft='#17344F', blue_ink='#BAE6FD',
        yellow='#FDE68A', yellow_soft='#3A3418', yellow_ink='#FDE68A',
        green='#6EE7B7', green_soft='#14352B', green_ink='#A7F3D0',
        violet='#C4B5FD', violet_soft='#2A2650', violet_ink='#DDD6FE',
        red='#FCA5A5', red_soft='#3B1D24', red_ink='#FECACA',
    ),
}
THEME_ORDER = ['day', 'night']
THEME_LABELS = {'day': 'Day', 'night': 'Night'}
DEFAULT_THEME = 'day'

# สีประจำ 5 ขั้นของ CPU Execution Path (ชื่อคีย์ในธีม)
STAGE_COLORS = ['blue', 'violet', 'pink', 'yellow', 'green']
