# NEW -- tests for simulator/isa.py (Member 3)
import json
import os

import pytest

from simulator.assembler import assemble
from simulator.contract import AsmError
from simulator.isa import INSTR_TABLE, decode_word, encode, reg_number

# Golden Machine Code จาก MASTER_PROMPT ข้อ 7
# หมายเหตุ: 2 แถวของ BEQ/BNE ในตาราง (11280003, 1409fffe) มาจาก encoder ของ cpuSimV7 ที่สลับ rs/rt
# ค่าที่ถูกต้องตาม MIPS32 (BEQ rs, rt, offset -> rs อยู่บิต 25-21) คือ 11090003 และ 1520fffe
GOLDEN = {
    "ADD $t2 $t0 $t1": "01095020",
    "ADDI $t0 $zero 5": "20080005",
    "LW $t0 4($sp)": "8fa80004",
    "JR $ra": "03e00008",
    "SUB $s2 $s0 $s1": "02119022",
    "SLT $t1 $a0 $t0": "0088482a",
    "SLTI $t0 $a0 13": "2888000d",
    "ADDI $sp $sp -32": "23bdffe0",
    "SW $ra 28($sp)": "afbf001c",
    "ORI $10 $9 0xfffe": "352afffe",
    "BEQ $t0 $t1 3": "11090003",
    "BNE $t1 $zero -2": "1520fffe",
    "J 0x2030": "0800080c",
    "JAL 0x2008": "0c000802",
    "LUI $9 0xffff": "3c09ffff",
    "ADDIU $t0 $t0 1": "25080001",
}


def _hex_of(line: str) -> str:
    return assemble(".ORG 0x2000\n" + line).instrs[0].hex8


@pytest.mark.parametrize("asm,expected", GOLDEN.items())
def test_golden_machine_code(asm, expected):
    assert _hex_of(asm) == expected


def test_golden_file_from_member1_if_present():
    path = os.path.join(os.path.dirname(__file__), "golden_hex.json")
    if not os.path.exists(path):
        pytest.skip("tests/golden_hex.json not found yet (Member 1)")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    pairs = data.items() if isinstance(data, dict) else [(d["asm"], d["hex"]) for d in data]
    for asm, hx in pairs:
        assert _hex_of(asm) == hx.lower(), asm


def test_bin32_matches_hex():
    ins = assemble("ADD $t2 $t0 $t1").instrs[0]
    assert ins.bin32 == "000000" "01000" "01001" "01010" "00000" "100000"
    assert int(ins.bin32, 2) == int(ins.hex8, 16)


@pytest.mark.parametrize("tok,num", [("$a0", 4), ("a0", 4), ("$4", 4), ("$zero", 0), ("$0", 0),
                                     ("$SP", 29), ("$ra", 31), ("$t8", 24), ("$s8", 30), ("$31", 31)])
def test_reg_number(tok, num):
    assert reg_number(tok) == num


@pytest.mark.parametrize("tok", ["$32", "$x1", "4", "t10", "", "$"])
def test_reg_number_bad(tok):
    with pytest.raises(AsmError):
        reg_number(tok)


def test_table_status():
    for op in ("LBU", "LHU", "LL", "SB", "SC", "SH"):
        assert INSTR_TABLE[op]["status"] == "UNSUPPORTED"
    for op in ("ADD", "ADDI", "JAL", "JR", "SLL", "SRL", "NOR", "LUI", "HALT"):
        assert INSTR_TABLE[op]["status"] == "EXEC"
    assert INSTR_TABLE["HALT"]["kind"] == "SIM"


def test_encode_sim_has_no_machine_code():
    with pytest.raises(ValueError):
        encode("HALT", "SIM")


ROUNDTRIP = [
    ("ADD $t2 $t0 $t1", dict(rd=10, rs=8, rt=9)),
    ("SLL $t0 $t1 4", dict(rd=8, rt=9, shamt=4)),
    ("SRL $t0 $t1 31", dict(rd=8, rt=9, shamt=31)),
    ("JR $ra", dict(rs=31)),
    ("ADDI $t0 $zero -5", dict(rt=8, rs=0, imm=-5)),
    ("ORI $t0 $t0 0xffff", dict(rt=8, rs=8, imm=0xFFFF)),
    ("LW $s0 -8($sp)", dict(rt=16, rs=29, imm=-8)),
    ("BNE $a0 $zero -1", dict(rs=4, rt=0, imm=-1)),
    ("JAL 0x2010", dict(target=0x2010)),
]


@pytest.mark.parametrize("asm,fields", ROUNDTRIP)
def test_decode_word_roundtrip(asm, fields):
    ins = assemble(".ORG 0x2000\n" + asm).instrs[0]
    d = decode_word(int(ins.hex8, 16))
    assert d["op"] == ins.op and d["kind"] == ins.kind
    for k, v in fields.items():
        assert d[k] == v, k


def test_every_exec_instruction_encodes_and_decodes():
    samples = {
        'R3': "{op} $t0 $t1 $t2", 'SHIFT': "{op} $t0 $t1 3", 'JR': "{op} $ra",
        'I3': "{op} $t0 $t1 7", 'LUI': "{op} $t0 7", 'BR': "{op} $t0 $t1 1",
        'MEM': "{op} $t0 4($sp)", 'JUMP': "{op} 0x2000",
    }
    for op, info in INSTR_TABLE.items():
        if info["status"] != "EXEC" or info["kind"] == "SIM":
            continue
        ins = assemble(samples[info["form"]].format(op=op)).instrs[0]
        assert decode_word(int(ins.hex8, 16))["op"] == op


def test_decode_unknown_opcode():
    assert decode_word(0xFC000000)["op"] is None
