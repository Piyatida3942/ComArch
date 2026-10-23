# NEW -- tests for simulator/cpu.py (Member 3)
import os
import time

import pytest

from simulator.assembler import assemble, assemble_file
from simulator.contract import (Instr, Program, REG_RA, REG_SP, STACK_TOP, Status, TEXT_BASE,
                                TRACE_LIMIT)
from simulator.cpu import CPU
from simulator.isa import reg_number

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make(src, init=None, max_steps=10_000_000):
    c = CPU(max_steps=max_steps)
    c.load(assemble(src), init)
    return c


def run(src, init=None, **kw):
    c = make(src, init, **kw)
    return c, c.run()


def reg(c, name):
    return c.get_state().regs[reg_number(name)]


# ---------------------------------------------------------------- คำสั่งทีละตัว
@pytest.mark.parametrize("src,name,expected", [
    ("ADDI $t0 $zero 7\nADDI $t1 $zero 5\nADD $t2 $t0 $t1", "$t2", 12),
    ("ADDI $t0 $zero 7\nADDI $t1 $zero 5\nSUB $t2 $t1 $t0", "$t2", -2),
    ("ADDI $t0 $zero -1\nADDIU $t1 $t0 1", "$t1", 0),
    ("ADDI $t0 $zero 12\nADDI $t1 $zero 10\nAND $t2 $t0 $t1", "$t2", 8),
    ("ADDI $t0 $zero 12\nADDI $t1 $zero 10\nOR $t2 $t0 $t1", "$t2", 14),
    ("NOR $t2 $zero $zero", "$t2", -1),
    ("ADDI $t0 $zero -1\nANDI $t1 $t0 0xff00", "$t1", 0xFF00),
    ("ORI $t1 $zero 0xffff", "$t1", 0xFFFF),
    ("LUI $t0 0x1234\nORI $t0 $t0 0x5678", "$t0", 0x12345678),
    ("LUI $t0 0xffff", "$t0", -65536),
    ("ADDI $t0 $zero -3\nADDI $t1 $zero 2\nSLT $t2 $t0 $t1", "$t2", 1),
    ("ADDI $t0 $zero -3\nADDI $t1 $zero 2\nSLTU $t2 $t0 $t1", "$t2", 0),
    ("ADDI $t0 $zero 5\nSLTI $t1 $t0 6", "$t1", 1),
    ("ADDI $t0 $zero 5\nSLTIU $t1 $t0 -1", "$t1", 1),     # -1 -> 0xffffffff แบบ unsigned
    ("ADDI $t0 $zero 3\nSLL $t1 $t0 4", "$t1", 48),
    ("ADDI $t0 $zero -16\nSRL $t1 $t0 28", "$t1", 15),       # logical shift
])
def test_single_instruction(src, name, expected):
    c, r = run(src + "\nHALT")
    assert r.status == Status.HALTED
    assert reg(c, name) == expected


def test_zero_register_cannot_be_written():
    c, r = run("ADDI $zero $zero 5\nADD $0 $t0 $t0\nHALT")
    assert reg(c, "$zero") == 0 and r.status == Status.HALTED
    assert c.validate() == []


def test_lw_sw_roundtrip_and_sign():
    c, r = run("ADDI $t0 $zero -2\nSW $t0 -4($sp)\nLW $t1 -4($sp)\nHALT")
    assert reg(c, "$t1") == -2
    st = c.get_state()
    assert [st.memory[STACK_TOP - 4 + i] for i in range(4)] == [0xFF, 0xFF, 0xFF, 0xFE]


# ---------------------------------------------------------------- overflow / wrap
@pytest.mark.parametrize("src", [
    "LUI $t0 0x7fff\nORI $t0 $t0 0xffff\nADDI $t1 $t0 1",          # 0x7fffffff + 1
    "LUI $t0 0x7fff\nORI $t0 $t0 0xffff\nADDI $t2 $zero 1\nADD $t1 $t0 $t2",
    "LUI $t0 0x8000\nADDI $t2 $zero 1\nSUB $t1 $t0 $t2",            # -2^31 - 1
])
def test_overflow_trap(src):
    c = make(src + "\nHALT")
    r = c.run()
    assert r.finished and r.status == Status.OVERFLOW
    st = c.get_state()
    assert reg(c, "$t1") == 0                       # ไม่เขียนผลลัพธ์
    last = c.trace[-1]
    assert last.completed is False and last.pc_after == last.pc_before == st.pc
    assert "overflow" in last.error.lower()
    n = st.counters["instr"]
    again = c.step()                                # เรียกต่อ -> ได้ผลเดิม ไม่เกิดอะไร
    assert again is last and c.get_state().counters["instr"] == n


def test_addu_wraps():
    c, r = run("LUI $t0 0x7fff\nORI $t0 $t0 0xffff\nADDI $t2 $zero 1\nADDU $t1 $t0 $t2\nSUBU $t3 $zero $t2\nHALT")
    assert reg(c, "$t1") == -(1 << 31) and reg(c, "$t3") == -1 and r.status == Status.HALTED


def test_slti_sltiu_do_not_modify_rs():
    c, _ = run("LUI $t0 0xffff\nORI $t0 $t0 0xffff\nSLTI $t1 $t0 0\nSLTIU $t2 $t0 1\nHALT")
    assert reg(c, "$t0") == -1
    assert reg(c, "$t1") == 1 and reg(c, "$t2") == 0


# ---------------------------------------------------------------- branch / jump
def test_branch_forward_and_backward():
    c, _ = run("""
        ADDI $t0 $zero 3
    loop: ADDI $t1 $t1 10
        ADDI $t0 $t0 -1
        BNE  $t0 $zero loop        # backward 2 ครั้ง
        BEQ  $zero $zero skip      # forward
        ADDI $t1 $t1 999
    skip: HALT""")
    assert reg(c, "$t1") == 30
    st = c.get_state()
    assert st.counters["branch"] == 4 and st.counters["branch_taken"] == 3


def test_jal_jr_and_ra():
    c = make(".ORG 0x2000\nmain: JAL f\nHALT\nf: ADDI $v0 $zero 42\nJR $ra")
    s1 = c.step()
    assert s1.pc_after == 0x2008 and reg(c, "$ra") == 0x2004
    assert s1.reg_changes[REG_RA] == (0, 0x2004)
    c.run()
    assert reg(c, "$v0") == 42 and c.get_state().status == Status.HALTED
    assert c.get_state().counters["call"] == 1


def test_j_to_label():
    c, _ = run("J end\nADDI $t0 $zero 1\nend: HALT")
    assert reg(c, "$t0") == 0


# ---------------------------------------------------------------- errors
@pytest.mark.parametrize("src", ["ADDI $t0 $zero 2\nLW $t1 0($t0)",       # ไม่ align
                                 "ADDI $t0 $zero 4\nSW $t0 -8($zero)",    # ติดลบ
                                 "LUI $t0 0x7000\nLW $t1 0($t0)"])        # นอก MEM_SIZE
def test_bad_memory(src):
    c, r = run(src + "\nHALT")
    assert r.status == Status.BAD_MEMORY and "line 2" in c.trace[-1].error


def test_bad_pc_when_no_halt():
    c, r = run("ADDI $t0 $zero 1")
    assert r.status == Status.BAD_PC and c.get_state().counters["instr"] == 1


def test_jr_to_garbage_is_bad_pc():
    _, r = run("ADDI $t0 $zero 3\nJR $t0\nHALT")
    assert r.status == Status.BAD_PC


def test_unknown_opcode_is_bad_opcode():
    ins = Instr(index=0, addr=TEXT_BASE, line_no=1, raw="LBU $t0 0($sp)", label=None, op="LBU", kind="I")
    c = CPU()
    c.load(Program("x", TEXT_BASE, [ins], {}, "LBU $t0 0($sp)"))
    assert c.step().status == Status.BAD_OPCODE


@pytest.mark.parametrize("use_step", [False, True])
def test_max_steps(use_step):
    c = make("loop: J loop", max_steps=100)
    if use_step:
        for _ in range(150):
            c.step()
        st = c.get_state()
    else:
        r = c.run()
        assert r.finished
        st = r.state
    assert st.status == Status.MAX_STEPS and st.counters["instr"] == 100


def test_exact_max_steps_with_halt_is_ok():
    c, r = run("ADDI $t0 $zero 1\nHALT", max_steps=2)
    assert r.status == Status.HALTED


# ---------------------------------------------------------------- step / run / reset / state
def test_step_executes_exactly_one():
    c = make("ADDI $t0 $zero 1\nADDI $t0 $t0 1\nHALT")
    assert c.get_state().status == Status.READY
    r = c.step()
    assert r.step_no == 1 and r.completed and r.pc_before == TEXT_BASE and r.pc_after == TEXT_BASE + 4
    assert r.reg_changes == {8: (0, 1)} and r.alu_text == "0 + 1 = 1"
    assert reg(c, "$t0") == 1 and c.get_state().counters["instr"] == 1


def test_step_result_details():
    c = make("ADDI $t0 $zero 9\nSW $t0 -4($sp)\nLW $t1 -4($sp)\nBEQ $t0 $t1 x\nx: HALT")
    c.step()
    sw = c.step()
    assert sw.mem_writes == [(STACK_TOP - 4, 9)] and sw.reg_changes == {}
    lw = c.step()
    assert lw.mem_reads == [STACK_TOP - 4] and lw.reg_changes == {9: (0, 9)}
    br = c.step()
    assert br.branch_taken is True and br.alu_text.endswith("-> equal")
    h = c.step()
    assert h.status == Status.HALTED and h.pc_after == h.pc_before
    assert c.step() is h                              # หยุดแล้ว คืนผลเดิม


def test_halt_counted_once():
    c, r = run("HALT")
    assert r.state.counters["instr"] == 1 and r.steps_executed == 1


def test_run_stop_after_is_resumable():
    c = make("ADDI $t0 $zero 50\nloop: ADDI $t0 $t0 -1\nBNE $t0 $zero loop\nHALT")
    r1 = c.run(stop_after=10)
    assert not r1.finished and r1.steps_executed == 10 and r1.status == Status.RUNNING
    r2 = c.run(stop_after=10, record_trace=True)
    assert r2.steps_executed == 10 and len(c.trace) == 10
    r3 = c.run()
    assert r3.finished and r3.status == Status.HALTED
    assert r1.steps_executed + r2.steps_executed + r3.steps_executed == r3.state.counters["instr"] == 102


def test_reset_restores_after_load_state():
    c = make("ADDI $a0 $a0 1\nHALT", init={4: 41, 5: 7})
    before = c.get_state()
    c.run()
    assert reg(c, "$a0") == 42
    c.reset()
    after = c.get_state()
    assert after.regs == before.regs and after.pc == before.pc and after.status == Status.READY
    assert after.counters["instr"] == 0 and c.trace == [] and after.memory == before.memory
    assert after.regs[REG_SP] == STACK_TOP and after.regs[5] == 7


def test_load_writes_machine_code_to_text():
    c = make(".ORG 0x2000\nADD $t2 $t0 $t1\nHALT")
    assert c.memory.read_word(0x2000) == 0x01095020


def test_get_state_is_copy():
    c = make("HALT")
    st = c.get_state()
    st.regs[8] = 123
    st.memory[0] = 5
    assert reg(c, "$t0") == 0 and 0 not in c.get_state().memory


def test_set_reg():
    c = make("HALT")
    c.set_reg(0, 5)
    c.set_reg(8, 0xFFFFFFFF)
    assert reg(c, "$zero") == 0 and reg(c, "$t0") == -1
    with pytest.raises(ValueError):
        c.set_reg(32, 1)


def test_trace_matches_counter_and_ring_buffer():
    c = make("ADDI $t0 $zero 3000\nloop: ADDI $t0 $t0 -1\nBNE $t0 $zero loop\nHALT")
    r = c.run(record_trace=True)
    completed = [s for s in c.trace if s.completed]
    assert r.state.counters["instr"] == 6002
    assert len(c.trace) == TRACE_LIMIT                           # เก็บล่าสุด 5000 แถว
    assert completed[-1].step_no == 6002
    c2 = make("ADDI $t0 $zero 10\nloop: ADDI $t0 $t0 -1\nBNE $t0 $zero loop\nHALT")
    r2 = c2.run(record_trace=True)
    assert len([s for s in c2.trace if s.completed]) == r2.state.counters["instr"]


# ---------------------------------------------------------------- โปรแกรมของโปรเจกต์ (Acceptance Table ข้อ 9.3)
ACCEPT = [
    ("factorial", 5, 0, 120, 118), ("factorial", 12, 0, 479001600, 496),
    ("ncr_factorial", 5, 2, 10, 387), ("nck_optimized", 5, 2, 10, 127),
    ("ncr_factorial", 6, 3, 20, 997), ("nck_optimized", 6, 3, 20, 234),
    ("ncr_factorial", 8, 4, 70, 9198), ("nck_optimized", 8, 4, 70, 567),
    ("ncr_factorial", 10, 5, 252, 153089), ("nck_optimized", 10, 5, 252, 1580),
    ("ncr_factorial", 12, 6, 924, 3331860), ("nck_optimized", 12, 6, 924, 5063),
    ("ncr_factorial", 12, 1, 12, 1088), ("nck_optimized", 12, 1, 12, 29),
]


def run_program(name, a0, a1=0, record_trace=False):
    c = CPU()
    c.load(assemble_file(os.path.join(ROOT, "programs", f"{name}.asm")), {4: a0, 5: a1})
    return c, c.run(record_trace=record_trace)


@pytest.mark.parametrize("name,n,r,value,count", ACCEPT)
def test_acceptance_table(name, n, r, value, count):
    c, res = run_program(name, n, r)
    st = res.state
    assert res.status == Status.HALTED
    assert st.regs[2] == value and st.regs[3] == 0
    assert st.counters["instr"] == count


def test_factorial_based_calls_and_stack():
    _, res = run_program("ncr_factorial", 6, 3)
    cnt = res.state.counters
    assert cnt["call"] == 6 and cnt["mem_read"] == 7 and cnt["mem_write"] == 7
    assert res.state.regs[REG_SP] == STACK_TOP


@pytest.mark.parametrize("n,r", [(18, 9), (26, 13)])
def test_optimized_overflow_cases(n, r):
    c, res = run_program("nck_optimized", n, r)
    assert res.status == Status.OVERFLOW and "line" in c.trace[-1].error


def test_optimized_26c1_ok():
    _, res = run_program("nck_optimized", 26, 1)
    assert res.status == Status.HALTED and res.state.regs[2] == 26


@pytest.mark.parametrize("name,n,r", [("factorial", 13, 0), ("factorial", -1, 0), ("ncr_factorial", 5, 6)])
def test_programs_bad_input(name, n, r):
    _, res = run_program(name, n, r)
    assert res.status == Status.HALTED and res.state.regs[3] == 3


@pytest.mark.parametrize("name,n,r", [("factorial", 6, 0), ("ncr_factorial", 7, 3), ("nck_optimized", 9, 4)])
def test_step_path_equals_fast_path(name, n, r):
    _, fast = run_program(name, n, r)
    _, slow = run_program(name, n, r, record_trace=True)
    assert fast.state.regs == slow.state.regs and fast.state.counters == slow.state.counters
    assert fast.state.memory == slow.state.memory and fast.state.pc == slow.state.pc


def test_speed_at_least_300k_per_second():
    c = CPU()
    c.load(assemble_file(os.path.join(ROOT, "programs", "ncr_factorial.asm")), {4: 10, 5: 5})
    t = time.perf_counter()
    res = c.run()
    dt = time.perf_counter() - t
    rate = res.state.counters["instr"] / dt
    assert rate >= 300_000, f"{rate:,.0f} instructions/second"
