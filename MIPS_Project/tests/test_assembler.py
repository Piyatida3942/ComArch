# NEW -- tests for simulator/assembler.py (Member 3)
import os

import pytest

from simulator.assembler import assemble, assemble_file
from simulator.contract import AsmError, TEXT_BASE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_backward_and_forward_labels():
    p = assemble("""
    .ORG 0x2000
    top:  ADDI $t0 $t0 1
          BEQ  $t0 $t1 done     # forward
          J    top               # backward
    done: HALT
    """)
    assert p.labels == {"top": 0x2000, "done": 0x200C}
    beq, j, halt = p.instrs[1], p.instrs[2], p.instrs[3]
    assert beq.imm == 1                 # 0x200C = 0x2004 + 4 + 1*4
    assert j.target == 0x2000
    assert halt.label == "done" and halt.kind == "SIM" and halt.hex8 is None


def test_branch_backward_offset():
    p = assemble("loop: ADDI $t0 $t0 -1\n BNE $t0 $zero loop\n HALT")
    assert p.instrs[1].imm == -2


def test_duplicate_label():
    with pytest.raises(AsmError) as e:
        assemble("a: HALT\na: HALT")
    assert e.value.line_no == 2


def test_missing_label():
    with pytest.raises(AsmError) as e:
        assemble("ADD $t0 $t0 $t0\nJ nowhere")
    assert e.value.line_no == 2 and "nowhere" in e.value.message


@pytest.mark.parametrize("line", ["ADDI $t0 $t0 70000", "ADDI $t0 $t0 -40000", "LW $t0 99999($sp)", "SLL $t0 $t0 32"])
def test_immediate_out_of_range(line):
    with pytest.raises(AsmError):
        assemble(line)


def test_immediate_16bit_pattern_accepted():
    p = assemble("ADDI $t0 $zero 0xffff\nORI $t1 $zero -1")
    assert p.instrs[0].imm == -1          # sign-extend
    assert p.instrs[1].imm == 0xFFFF      # zero-extend


def test_register_both_styles_give_same_code():
    a = assemble("ADD $t2 $t0 $t1").instrs[0]
    b = assemble("ADD $10 $8 $9").instrs[0]
    assert a.hex8 == b.hex8 == "01095020"


def test_bad_register_reports_line():
    with pytest.raises(AsmError) as e:
        assemble("HALT\nADD $t0 $q1 $t1")
    assert e.value.line_no == 2


def test_unsupported_opcode():
    with pytest.raises(AsmError) as e:
        assemble("LBU $t0 0($sp)")
    assert "unsupported instruction" in e.value.message


def test_unknown_opcode():
    with pytest.raises(AsmError):
        assemble("MUL $t0 $t1 $t2")


def test_wrong_operand_count():
    with pytest.raises(AsmError):
        assemble("ADD $t0 $t1")


def test_no_org_uses_text_base_and_entry():
    p = assemble("ADDI $t0 $zero 1\nmain: HALT")
    assert p.text_base == TEXT_BASE
    assert p.instrs[0].addr == TEXT_BASE
    assert p.entry == TEXT_BASE + 4       # = label main


def test_entry_defaults_to_text_base():
    p = assemble(".ORG 0x100\nHALT")
    assert p.text_base == 0x100 and p.entry == 0x100


def test_org_after_instruction_is_error():
    with pytest.raises(AsmError):
        assemble("HALT\n.ORG 0x2000")


def test_commas_case_comments_and_label_same_line():
    p = assemble("start: addi $t0, $zero, 5   # comment\n  lw $t1, 8( $sp )\n  halt")
    assert [i.op for i in p.instrs] == ["ADDI", "LW", "HALT"]
    assert p.instrs[0].imm == 5 and p.instrs[0].label == "start"
    assert (p.instrs[1].rs, p.instrs[1].imm) == (29, 8)
    assert p.instrs[0].raw.startswith("addi") and p.instrs[0].line_no == 1


def test_mem_without_offset():
    assert assemble("LW $t0 ($sp)").instrs[0].imm == 0


def test_teacher_style_numeric_branch_and_jump():
    p = assemble(".ORG 0\nORI $2 $0 10\nBNE $0 $2 -3\nJ 0x0")
    assert p.instrs[1].imm == -3 and p.instrs[2].target == 0


def test_jump_target_must_be_aligned():
    with pytest.raises(AsmError):
        assemble("J 0x2002")


@pytest.mark.parametrize("name", ["factorial", "ncr_factorial", "nck_optimized"])
def test_project_programs_assemble(name):
    p = assemble_file(os.path.join(ROOT, "programs", f"{name}.asm"))
    assert p.name == name
    assert p.entry == p.labels["main"] == 0x2000
    assert all(i.hex8 for i in p.instrs if i.op != "HALT")
