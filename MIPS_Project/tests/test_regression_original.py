# NEW -- Regression: instructions.txt ของอาจารย์ต้องได้ผลเหมือนเดิมบน Engine ใหม่ (Member 3)
#   รัน cpuSimV7 ต้นฉบับจริง (references/original_cpuSimV7, ไม่แก้) แล้วเทียบ register สุดท้าย
import contextlib
import io
import os
import sys

from simulator.assembler import assemble
from simulator.contract import REG_SP, Status, s32
from simulator.cpu import CPU

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(ROOT, "references", "original_cpuSimV7")


def _load_lines(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip()]


def run_original(lines):
    """รัน cpuSimV7 ต้นฉบับ (ซ่อน output ที่พิมพ์ทุก step) คืน register 32 ตัว"""
    names = ("isa", "cpu", "memory")
    saved = {k: sys.modules.pop(k) for k in names if k in sys.modules}
    sys.path.insert(0, ORIG)
    try:
        import cpu as orig_cpu        # noqa: E402  (ไฟล์ของอาจารย์)
        import memory as orig_memory  # noqa: E402
        with contextlib.redirect_stdout(io.StringIO()):
            c = orig_cpu.CPU(lines, orig_memory.Memory())
            c.run()
        return list(c.registers)
    finally:
        sys.path.remove(ORIG)
        for k in names:
            sys.modules.pop(k, None)
        sys.modules.update(saved)


def test_original_files_untouched_exist():
    for f in ("cpu.py", "isa.py", "memory.py", "main.py", "instructions.txt", "Readme3-7.txt"):
        assert os.path.exists(os.path.join(ORIG, f)), f


def test_instructions_txt_same_result_as_cpusimv7():
    lines = _load_lines(os.path.join(ORIG, "instructions.txt"))
    expected = run_original(lines)
    assert expected[3] == 55                          # 10+9+...+1 (ค่าที่ cpuSimV7 ได้)

    c = CPU()
    c.load(assemble("\n".join(lines), "instructions"))
    res = c.run()
    assert res.status == Status.HALTED
    ours = res.state.regs
    for i in range(32):
        if i == REG_SP:                               # Engine ใหม่ตั้ง $sp = STACK_TOP (ของเดิมเป็น 0)
            continue
        assert ours[i] == s32(expected[i]), f"register ${i}"
