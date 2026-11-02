# NEW: ทดสอบส่วน "ตรรกะ" ของหน้าตาใหม่ (theme / explain / layout) -- ไม่เปิดหน้าต่าง ไม่แตะ Engine
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from interface import explain as ex                     # noqa: E402
from interface.theme import THEMES, THEME_ORDER, contrast  # noqa: E402
from simulator.assembler import assemble_file           # noqa: E402
from simulator.cpu import CPU                           # noqa: E402

PROGRAMS = [('factorial', (5, 0)), ('factorial', (0, 0)), ('ncr_factorial', (5, 2)),
            ('nck_optimized', (5, 2)), ('nck_optimized', (10, 5)), ('nck_optimized', (26, 13))]


def _run(name, a0, a1):
    cpu = CPU()
    cpu.load(assemble_file(str(ROOT / 'programs' / f'{name}.asm')), {4: a0, 5: a1})
    out = []
    while cpu.status not in ('HALTED', 'OVERFLOW', 'BAD_MEMORY', 'BAD_OPCODE', 'BAD_PC', 'MAX_STEPS') and len(out) < 20000:
        step = cpu.step()
        out.append((step, cpu.regs.copy()))
    return cpu, out


def test_every_theme_is_readable():
    for key in THEME_ORDER:
        t = THEMES[key]
        assert contrast(t['text'], t['bg']) >= 7, key
        assert contrast(t['muted'], t['bg']) >= 4.5, key
        assert contrast(t['muted'], t['surface2']) >= 4.5, key
        assert contrast(t['on_primary'], t['primary']) >= 4.5, key
        for c in ('primary', 'pink', 'blue', 'yellow', 'green', 'violet', 'red'):
            assert contrast(t[c + '_ink'], t[c + '_soft']) >= 4.5, (key, c)


def test_light_themes_have_white_background_and_dark_keeps_original():
    for key in ('pastel', 'sky', 'rose', 'sunny'):
        assert THEMES[key]['bg'] == '#FFFFFF'
    assert THEMES['night']['bg'] == '#0B1220'


def test_explain_covers_every_step_of_every_program():
    for name, (a0, a1) in PROGRAMS:
        cpu, steps = _run(name, a0, a1)
        assert steps, name
        for step, regs in steps:
            e = ex.explain_step(step, regs)
            assert e['title'] and e['sentence'].strip(), (name, step.instr.raw)
            assert len(ex.stage_info(step)) == 5
            row = ex.history_row(step)
            assert len(row) == 5 and row[1]
            if step.completed and step.instr.op not in ('LW', 'SW', 'LUI', 'SLL', 'SRL'):
                assert e['result'], (name, step.instr.raw)


def test_overflow_step_is_explained_in_plain_language():
    cpu, steps = _run('nck_optimized', 26, 13)
    step, regs = steps[-1]
    assert cpu.status == 'OVERFLOW' and not step.completed
    e = ex.explain_step(step, regs)
    assert e['tone'] == 'error' and '32' in e['sentence']


def test_stage_flags_follow_the_instruction_type():
    _, steps = _run('ncr_factorial', 5, 2)
    seen = {}
    for step, _ in steps:
        seen.setdefault(step.instr.op, ex.stage_info(step))
    used = lambda op: [s['used'] for s in seen[op]]
    assert used('ADD') == [True, True, True, True, True]
    assert used('BEQ') == [True, True, True, True, False]      # เปรียบเทียบ แต่ไม่เขียนผล
    assert used('SW') == [True, True, True, True, True]
    assert used('JR') == [True, True, True, False, False]


def test_live_registers_marks_changes():
    _, steps = _run('factorial', 5, 0)
    step, regs = steps[6]                                    # ADDI $v0 $zero 1
    chips = ex.live_registers(regs, step.reg_changes, ex.ROLES['factorial'], always=(2, 4))
    by = {c['idx']: c for c in chips}
    assert by[2]['changed'] and by[2]['value'] == 1
    assert by[4]['value'] == 5 and not by[4]['changed']


def test_calc_outcome_messages():
    class Row:
        pass
    ok = Row(); ok.status, ok.prog_status, ok.result, ok.counters, ok.matches_reference = 'HALTED', 0, 120, {'instr': 118}, True
    assert ex.calc_outcome(ok)['ok'] and ex.calc_outcome(ok)['value'] == 120
    ov = Row(); ov.status, ov.prog_status, ov.result, ov.counters, ov.matches_reference = 'OVERFLOW', 0, None, {'instr': 704}, None
    assert not ex.calc_outcome(ov)['ok'] and '32' in ex.calc_outcome(ov)['message']


def test_formula_and_cost_estimate():
    assert ex.formula_text('factorial', 5) == '5! = 5 × 4 × 3 × 2 × 1'
    assert ex.formula_text('ncr', 5, 2) == '5C2 = 5! ÷ (2! × 3!)'
    assert ex.division_rounds(12, 6) == 665280 and ex.division_rounds(5, 2) == 20


def test_cpu_path_layout_fits_every_width():
    from interface.cpu_visualizer import compute_layout
    for scale in (1.0, 1.25, 1.5, 2.0):
        for w in range(360, 1801, 40):
            L = compute_layout(w, scale)
            assert len(L['rects']) == 5 and len(L['arrows']) == 4
            for x1, y1, x2, y2 in L['rects']:
                assert x1 >= 0 and x2 <= w, (w, scale)
                assert x2 - x1 >= 50, (w, scale)              # กล่องต้องไม่หายไปแม้หน้าต่างแคบมาก
