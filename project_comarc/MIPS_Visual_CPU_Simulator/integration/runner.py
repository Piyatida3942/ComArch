# NEW (Member 2): รันโปรแกรม .asm จนจบแบบไม่เปิด GUI -- ใช้ใน selftest, tests, benchmark
from pathlib import Path
from simulator.assembler import assemble_file
from simulator.contract import DEFAULT_MAX_STEPS, RunResult
from simulator.cpu import CPU

ROOT = Path(__file__).resolve().parent.parent          # โฟลเดอร์ที่มี main.py


def run_asm(path, a0, a1=0, max_steps=DEFAULT_MAX_STEPS) -> RunResult:
    """Assemble `path` (relative to project root or absolute), set $a0=a0, $a1=a1, run to the end."""
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    cpu = CPU(max_steps=max_steps)
    cpu.load(assemble_file(str(p)), init_regs={4: a0, 5: a1})
    return cpu.run()
