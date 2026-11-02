# NEW (Member 2): Acceptance Table (ข้อ 9.3 ของ MASTER PROMPT) -- ตรวจทั้งผลลัพธ์และจำนวนคำสั่ง
import time
from simulator.contract import Status
from integration.runner import run_asm

# (โปรแกรม, (a0, a1), $v0 ที่คาดหวัง, $v1 ที่คาดหวัง, จำนวนคำสั่งที่คาดหวัง)
CASES = [
    ("factorial",     (5, 0),   120,        0, 118),
    ("factorial",     (12, 0),  479001600,  0, 496),
    ("ncr_factorial", (5, 2),   10,         0, 387),
    ("ncr_factorial", (6, 3),   20,         0, 997),
    ("ncr_factorial", (8, 4),   70,         0, 9198),
    ("ncr_factorial", (10, 5),  252,        0, 153089),
    ("ncr_factorial", (12, 1),  12,         0, 1088),
    ("ncr_factorial", (12, 6),  924,        0, 3331860),   # ช้าที่สุด (~3.3 ล้านคำสั่ง)
    ("nck_optimized", (5, 2),   10,         0, 127),
    ("nck_optimized", (6, 3),   20,         0, 234),
    ("nck_optimized", (8, 4),   70,         0, 567),
    ("nck_optimized", (10, 5),  252,        0, 1580),
    ("nck_optimized", (12, 1),  12,         0, 29),
    ("nck_optimized", (12, 6),  924,        0, 5063),
]
# Input ผิด -> โปรแกรมคืน $v1 = 3 ; ค่ากลางเกิน 32-bit -> CPU หยุดด้วย OVERFLOW
BAD_INPUT = [("factorial", (13, 0)), ("factorial", (-1, 0)),
             ("ncr_factorial", (13, 2)), ("ncr_factorial", (5, 6)),
             ("nck_optimized", (27, 1)), ("nck_optimized", (4, 5))]
TRAPS = [("nck_optimized", (18, 9)), ("nck_optimized", (26, 13))]


def run_selftest(verbose=True) -> bool:
    ok_all = True
    def line(ok, text):
        nonlocal ok_all
        ok_all &= ok
        if verbose:
            print(("PASS  " if ok else "FAIL  ") + text)
    for name, (a0, a1), v0, v1, instr in CASES:
        t = time.time()
        r = run_asm(f"programs/{name}.asm", a0, a1)
        s = r.state
        good = (r.status == Status.HALTED and s.regs[2] == v0 and s.regs[3] == v1
                and s.counters["instr"] == instr)
        line(good, f"{name:14s} ({a0},{a1})  got v0={s.regs[2]} v1={s.regs[3]} instr={s.counters['instr']:,}"
                   f"  want v0={v0} instr={instr:,}  [{r.status}, {time.time()-t:.2f}s]")
    for name, (a0, a1) in BAD_INPUT:
        s = run_asm(f"programs/{name}.asm", a0, a1).state
        line(s.regs[3] == 3 and s.regs[2] == 0, f"{name:14s} ({a0},{a1})  bad input -> v1={s.regs[3]} (want 3)")
    for name, (a0, a1) in TRAPS:
        r = run_asm(f"programs/{name}.asm", a0, a1)
        line(r.status == Status.OVERFLOW, f"{name:14s} ({a0},{a1})  status={r.status} (want OVERFLOW)")
    if verbose:
        print("RESULT:", "ALL PASS" if ok_all else "SOME FAILED")
    return ok_all
