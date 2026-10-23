# MODIFIED from cpuSimV7 isa.py
#   คงไว้: ตาราง allCMD ของอาจารย์ (op, type, opcode 6 บิต, funct 6 บิต) เป็นแหล่งข้อมูลหลักของ ISA
#   แก้/เพิ่ม:
#     - R-type ถูก encode เป็น 00000000 (บัค #3) -> encode R/I/J ครบตาม MIPS32
#     - BEQ/BNE เดิม encode สลับ rs/rt (ได้ 11280003 แทน 11090003) -> ใช้ลำดับมาตรฐาน: BEQ rs, rt, offset
#     - รับชื่อ register ได้ทั้ง $a0 และ $4 (บัค #4) -> reg_number()
#     - เพิ่ม status EXEC/UNSUPPORTED (บัค #13), form ของ operand, decode_word() ถอด machine code กลับ
#   การแยก operand จากข้อความย้ายไปอยู่ใน assembler.py (2 pass + label)
"""simulator/isa.py -- ตารางชุดคำสั่ง, ชื่อ register, encode/decode machine code"""
from __future__ import annotations

from simulator.contract import AsmError, REG_NAMES

# ---------- ตารางของอาจารย์ (cpuSimV7 isa.allCMD) ----------
allCMD = [
    ('ADD', 'R', '000000', '100000'),
    ('ADDI', 'I', '001000', '000000'),
    ('ADDIU', 'I', '001001', '000000'),
    ('ADDU', 'R', '000000', '100001'),
    ('AND', 'R', '000000', '100100'),
    ('ANDI', 'I', '001100', '000000'),
    ('BEQ', 'I', '000100', '000000'),
    ('BNE', 'I', '000101', '000000'),
    ('J', 'J', '000010', '000000'),
    ('JAL', 'J', '000011', '000000'),
    ('JR', 'R', '000000', '001000'),
    ('LBU', 'I', '100100', '000000'),
    ('LHU', 'I', '100101', '000000'),
    ('LL', 'I', '110000', '000000'),
    ('LUI', 'I', '001111', '000000'),
    ('LW', 'I', '100011', '000000'),
    ('NOR', 'R', '000000', '100111'),
    ('OR', 'R', '000000', '100101'),
    ('ORI', 'I', '001101', '000000'),
    ('SLT', 'R', '000000', '101010'),
    ('SLTI', 'I', '001010', '000000'),
    ('SLTIU', 'I', '001011', '000000'),
    ('SLTU', 'R', '000000', '101011'),
    ('SLL', 'R', '000000', '000000'),
    ('SRL', 'R', '000000', '000010'),
    ('SB', 'I', '101000', '000000'),
    ('SC', 'I', '111000', '000000'),
    ('SH', 'I', '101001', '000000'),
    ('SW', 'I', '101011', '000000'),
    ('SUB', 'R', '000000', '100010'),
    ('SUBU', 'R', '000000', '100011'),
]

# ---------- รูปแบบ operand ของแต่ละคำสั่ง ----------
#   R3    : OP rd rs rt          SHIFT : OP rd rt shamt     JR   : OP rs
#   I3    : OP rt rs imm         LUI   : OP rt imm          BR   : OP rs rt label|offset
#   MEM   : OP rt off(rs)        JUMP  : OP label|address   NONE : OP
_FORM = {
    'ADD': 'R3', 'ADDU': 'R3', 'AND': 'R3', 'NOR': 'R3', 'OR': 'R3',
    'SLT': 'R3', 'SLTU': 'R3', 'SUB': 'R3', 'SUBU': 'R3',
    'SLL': 'SHIFT', 'SRL': 'SHIFT', 'JR': 'JR',
    'ADDI': 'I3', 'ADDIU': 'I3', 'ANDI': 'I3', 'ORI': 'I3', 'SLTI': 'I3', 'SLTIU': 'I3',
    'LUI': 'LUI', 'BEQ': 'BR', 'BNE': 'BR',
    'LW': 'MEM', 'SW': 'MEM', 'LBU': 'MEM', 'LHU': 'MEM', 'LL': 'MEM',
    'SB': 'MEM', 'SC': 'MEM', 'SH': 'MEM',
    'J': 'JUMP', 'JAL': 'JUMP',
}
UNSUPPORTED = {'LBU', 'LHU', 'LL', 'SB', 'SC', 'SH'}   # มีใน allCMD แต่ไม่มีโค้ด execute
ZERO_EXT_IMM = {'ANDI', 'ORI', 'LUI'}                 # immediate ขยายแบบไม่มีเครื่องหมาย (0..65535)

INSTR_TABLE: dict[str, dict] = {}
for _op, _kind, _opc, _fn in allCMD:
    INSTR_TABLE[_op] = {
        "kind": _kind,
        "opcode": int(_opc, 2),
        "funct": int(_fn, 2),
        "status": "UNSUPPORTED" if _op in UNSUPPORTED else "EXEC",
        "form": _FORM[_op],
    }
# HALT: คำสั่งเฉพาะของ Simulator (ไม่มี machine code)
INSTR_TABLE['HALT'] = {"kind": "SIM", "opcode": None, "funct": None, "status": "EXEC", "form": "NONE"}

# ---------- ชื่อ register ----------
_REG_BY_NAME = {name: i for i, name in enumerate(REG_NAMES)}
_REG_BY_NAME['s8'] = 30            # ชื่อเรียกอีกแบบของ $fp


def reg_number(token: str) -> int:
    """"$a0" / "a0" / "$4" -> 4   (ผิดรูป -> AsmError, line_no = 0 ให้ assembler ใส่เลขบรรทัดเอง)"""
    t = token.strip().lower()
    if t.startswith('$'):
        body = t[1:]
        if body.isdigit():
            n = int(body)
            if 0 <= n < 32:
                return n
            raise AsmError(0, f"register '{token}' out of range ($0-$31)")
    else:
        body = t
        if body.isdigit():                  # ตัวเลขเปล่าๆ อาจเป็น immediate ที่วางผิดที่ จึงไม่รับ
            raise AsmError(0, f"register must start with '$' (got '{token}')")
    if body in _REG_BY_NAME:
        return _REG_BY_NAME[body]
    raise AsmError(0, f"unknown register '{token}'")


# ---------- encode ----------
def encode(op: str, kind: str, rd=0, rs=0, rt=0, shamt=0, imm=0, target=0) -> tuple[str, str]:
    """คืน (hex8, bin32) ของคำสั่ง MIPS32
    R: opcode|rs|rt|rd|shamt|funct   I: opcode|rs|rt|imm16   J: opcode|target26 (target = byte address)"""
    info = INSTR_TABLE.get(op)
    if info is None or info["kind"] == "SIM":
        raise ValueError(f"{op} has no machine code")
    opc = info["opcode"]
    if kind == 'R':
        word = (opc << 26) | ((rs & 31) << 21) | ((rt & 31) << 16) | ((rd & 31) << 11) \
               | ((shamt & 31) << 6) | info["funct"]
    elif kind == 'I':
        word = (opc << 26) | ((rs & 31) << 21) | ((rt & 31) << 16) | (imm & 0xFFFF)
    elif kind == 'J':
        word = (opc << 26) | ((target >> 2) & 0x3FFFFFF)
    else:
        raise ValueError(f"invalid kind: {kind}")
    return f"{word:08x}", f"{word:032b}"


# ---------- decode ----------
_BY_OPCODE = {}
_BY_FUNCT = {}
for _op, _info in INSTR_TABLE.items():
    if _info["kind"] == 'R':
        _BY_FUNCT[_info["funct"]] = _op
    elif _info["kind"] in ('I', 'J'):
        _BY_OPCODE[_info["opcode"]] = _op


def decode_word(word: int) -> dict:
    """ถอด machine code 32 บิต -> {"kind","op","rs","rt","rd","shamt","funct","imm","target"}
    imm เป็นค่า signed ยกเว้น ANDI/ORI/LUI (zero-extend); target เป็น byte address (บิต 31-28 = 0)
    คำสั่งที่ไม่รู้จัก -> op = None"""
    word &= 0xFFFFFFFF
    opc = word >> 26
    funct = word & 0x3F
    raw_imm = word & 0xFFFF
    if opc == 0:
        op = _BY_FUNCT.get(funct)
        kind = 'R'
    else:
        op = _BY_OPCODE.get(opc)
        kind = INSTR_TABLE[op]["kind"] if op else None
    imm = raw_imm if op in ZERO_EXT_IMM else (raw_imm - 0x10000 if raw_imm & 0x8000 else raw_imm)
    return {
        "kind": kind, "op": op,
        "rs": (word >> 21) & 31, "rt": (word >> 16) & 31, "rd": (word >> 11) & 31,
        "shamt": (word >> 6) & 31, "funct": funct,
        "imm": imm, "target": (word & 0x3FFFFFF) << 2,
    }
