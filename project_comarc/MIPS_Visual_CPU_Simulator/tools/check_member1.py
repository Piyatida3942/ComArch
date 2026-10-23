# NEW: Member 1 standalone command-line verification; does not masquerade as production CPU.
from pathlib import Path
from math import factorial
from tools.refsim import run

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = (ROOT / 'programs/factorial.asm').read_text(encoding='utf-8')
    failures = 0
    print('MEMBER 1 / independent reference interpreter (not production CPU)')
    for n in list(range(13)) + [-1, 13]:
        v0, v1, steps, counters, regs = run(source, n)
        expected = (factorial(n), 0) if 0 <= n <= 12 else (0, 3)
        valid = (v0, v1) == expected and regs[4] == n and regs[29] == 0x1fffc
        if n == 5: valid &= steps == 118
        if n == 12: valid &= steps == 496
        failures += not valid
        print(f"{'PASS' if valid else 'FAIL'} n={n:>3} v0={v0:>10} v1={v1} instr={steps}")
    print(f'RESULT: {15-failures}/15 PASS')
    return 0 if failures == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())
