# NEW -- Assembler แบบ 2 pass (แทน Instruction.decode/decode2/decode3 ของ cpuSimV7)
#   แก้บัค: ไม่มี label (#5), รับแค่ $<ตัวเลข> (#4), ไม่มี .ORG แล้ว crash (#8 -> ใช้ TEXT_BASE)
#   คงแนวคิดเดิมของอาจารย์: directive .ORG, immediate ทศนิยม/0x, คำสั่งตัวพิมพ์ใหญ่หรือเล็กก็ได้,
#   เขียนคั่นด้วยเว้นวรรค (แบบเดิม) หรือ comma ก็ได้, BEQ/BNE/J ใส่ตัวเลขตรงๆ ได้เหมือนเดิม
"""simulator/assembler.py -- แปลงข้อความ .asm เป็น Program (list ของ Instr + machine code)

Pass 1 : อ่านทีละบรรทัด ตัด comment, เก็บ .ORG, จด label -> address, เก็บคำสั่งไว้
Pass 2 : แยก operand ตาม form ของคำสั่ง, แปลง label เป็น offset/address, ตรวจช่วงค่า, encode
"""
from __future__ import annotations

import os
import re

from simulator.contract import AsmError, Instr, MEM_SIZE, Program, TEXT_BASE
from simulator.isa import INSTR_TABLE, ZERO_EXT_IMM, encode, reg_number

_LABEL_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_.]*)\s*:')
_MEM_RE = re.compile(r'^([^()]*)\((\$?\w+)\)$')
_IDENT_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_.]*$')


def _parse_int(tok: str, line_no: int, what: str = "immediate") -> int:
    t = tok.strip()
    try:
        return int(t, 0)               # 10, -3, 0x2000, -0x10, 0b101
    except ValueError:
        pass
    try:
        return int(t, 10)              # 010 (เลขนำหน้าด้วย 0)
    except ValueError:
        raise AsmError(line_no, f"invalid {what}: '{tok}'") from None


def _reg(tok: str, line_no: int) -> int:
    try:
        return reg_number(tok)
    except AsmError as e:
        raise AsmError(line_no, e.message) from None


def _imm16(op: str, value: int, line_no: int) -> int:
    """รับค่าที่ใส่ใน 16 บิตได้ (-32768..65535) แล้วคืนค่าตามความหมายของคำสั่ง
    ANDI/ORI/LUI -> 0..65535 (zero-extend) ; คำสั่งอื่น -> -32768..32767 (sign-extend)"""
    if not -0x8000 <= value <= 0xFFFF:
        raise AsmError(line_no, f"immediate {value} does not fit in 16 bits (allowed -32768..65535)")
    v = value & 0xFFFF
    if op in ZERO_EXT_IMM:
        return v
    return v - 0x10000 if v & 0x8000 else v


_NUM_RE = re.compile(r'^[+-]?(0x[0-9a-f]+|0b[01]+|\d+)$', re.IGNORECASE)


def _split_operands(text: str) -> list[str]:
    text = re.sub(r'\(\s*', '(', text)         # "( $sp )" -> "($sp)"
    text = re.sub(r'\s*\)', ')', text)
    out: list[str] = []
    for t in re.split(r'[\s,]+', text.strip()):
        if not t:
            continue
        if t.startswith('(') and out and _NUM_RE.match(out[-1]):
            out[-1] += t                        # "4 ($sp)" -> "4($sp)"
        else:
            out.append(t)
    return out


def assemble(source: str, name: str = "program") -> Program:
    """2 ผ่าน; ผิด -> AsmError(line_no, message)"""
    # ------------------------------------------------------------ pass 1
    text_base = TEXT_BASE
    labels: dict[str, int] = {}
    label_line: dict[str, int] = {}
    pending = []                     # (line_no, raw, labels_here)
    labels_here: list[str] = []

    for line_no, line in enumerate(source.splitlines(), 1):
        code = line.split('#', 1)[0].strip()
        # label อาจมีหลายตัว และอาจอยู่บรรทัดเดียวกับคำสั่ง
        while True:
            m = _LABEL_RE.match(code)
            if not m:
                break
            lab = m.group(1)
            if lab in labels:
                raise AsmError(line_no, f"duplicate label '{lab}' (already defined on line {label_line[lab]})")
            labels[lab] = text_base + 4 * len(pending)
            label_line[lab] = line_no
            labels_here.append(lab)
            code = code[m.end():].strip()
        if not code:
            continue
        if code.split()[0].upper() == '.ORG':
            parts = _split_operands(code)
            if len(parts) != 2:
                raise AsmError(line_no, ".ORG needs exactly one address, e.g. .ORG 0x2000")
            if pending or labels_here:
                raise AsmError(line_no, ".ORG must come before the first instruction or label")
            addr = _parse_int(parts[1], line_no, "address")
            if addr % 4 or not 0 <= addr < MEM_SIZE:
                raise AsmError(line_no, f".ORG 0x{addr:x} must be a multiple of 4 and inside memory")
            text_base = addr
            continue
        pending.append((line_no, code, labels_here))
        labels_here = []

    # ------------------------------------------------------------ pass 2
    instrs: list[Instr] = []
    for index, (line_no, raw, labs) in enumerate(pending):
        addr = text_base + 4 * index
        parts = _split_operands(raw)
        op = parts[0].upper()
        args = parts[1:]
        info = INSTR_TABLE.get(op)
        if info is None:
            raise AsmError(line_no, f"unknown instruction '{parts[0]}'")
        if info["status"] == "UNSUPPORTED":
            raise AsmError(line_no, f"unsupported instruction: {op} (not implemented in this simulator)")
        form = info["form"]
        need = {'R3': 3, 'SHIFT': 3, 'JR': 1, 'I3': 3, 'LUI': 2, 'BR': 3, 'MEM': 2, 'JUMP': 1, 'NONE': 0}[form]
        if len(args) != need:
            raise AsmError(line_no, f"{op} expects {need} operand(s), got {len(args)}")

        f = dict(rd=0, rs=0, rt=0, shamt=0, imm=0, target=0)
        if form == 'R3':                                     # OP rd rs rt
            f['rd'], f['rs'], f['rt'] = (_reg(a, line_no) for a in args)
        elif form == 'SHIFT':                                # OP rd rt shamt
            f['rd'], f['rt'] = _reg(args[0], line_no), _reg(args[1], line_no)
            sh = _parse_int(args[2], line_no, "shamt")
            if not 0 <= sh <= 31:
                raise AsmError(line_no, f"shamt {sh} must be in 0..31")
            f['shamt'] = sh
        elif form == 'JR':                                   # OP rs
            f['rs'] = _reg(args[0], line_no)
        elif form == 'I3':                                   # OP rt rs imm
            f['rt'], f['rs'] = _reg(args[0], line_no), _reg(args[1], line_no)
            f['imm'] = _imm16(op, _parse_int(args[2], line_no), line_no)
        elif form == 'LUI':                                  # OP rt imm
            f['rt'] = _reg(args[0], line_no)
            f['imm'] = _imm16(op, _parse_int(args[1], line_no), line_no)
        elif form == 'BR':                                   # OP rs rt label|offset
            f['rs'], f['rt'] = _reg(args[0], line_no), _reg(args[1], line_no)
            tok = args[2]
            if _IDENT_RE.match(tok):
                if tok not in labels:
                    raise AsmError(line_no, f"undefined label '{tok}'")
                off = (labels[tok] - (addr + 4)) // 4       # นับเป็นจำนวนคำสั่งจากคำสั่งถัดไป
            else:
                off = _parse_int(tok, line_no, "offset")
            if not -0x8000 <= off <= 0x7FFF:
                raise AsmError(line_no, f"branch offset {off} does not fit in 16 bits")
            f['imm'] = off
        elif form == 'MEM':                                  # OP rt off(rs)
            f['rt'] = _reg(args[0], line_no)
            m = _MEM_RE.match(args[1])
            if not m:
                raise AsmError(line_no, f"expected offset($reg), e.g. 4($sp) (got '{args[1]}')")
            f['rs'] = _reg(m.group(2), line_no)
            f['imm'] = _imm16(op, _parse_int(m.group(1) or "0", line_no, "offset"), line_no)
        elif form == 'JUMP':                                 # OP label|address
            tok = args[0]
            if _IDENT_RE.match(tok):
                if tok not in labels:
                    raise AsmError(line_no, f"undefined label '{tok}'")
                tgt = labels[tok]
            else:
                tgt = _parse_int(tok, line_no, "address")
            if tgt % 4 or not 0 <= tgt < MEM_SIZE:
                raise AsmError(line_no, f"jump target 0x{tgt & 0xFFFFFFFF:x} must be a multiple of 4 and inside memory")
            if (tgt & 0xF0000000) != ((addr + 4) & 0xF0000000):
                raise AsmError(line_no, "J/JAL cannot jump across a 256 MB region")
            f['target'] = tgt

        kind = info["kind"]
        if kind == 'SIM':
            hx = bn = None
        else:
            hx, bn = encode(op, kind, **f)
        instrs.append(Instr(index=index, addr=addr, line_no=line_no, raw=raw,
                            label=labs[0] if labs else None, op=op, kind=kind,
                            hex8=hx, bin32=bn, **f))

    return Program(name=name, text_base=text_base, instrs=instrs, labels=labels,
                   source=source, entry=labels.get('main', text_base))


def assemble_file(path: str) -> Program:
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    return assemble(source, os.path.splitext(os.path.basename(path))[0])
