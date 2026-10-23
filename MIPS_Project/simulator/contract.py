"""simulator/contract.py -- ข้อตกลงกลางของโปรเจกต์ (ทุกโมดูล import จากไฟล์นี้)
ห้ามแก้โดยไม่แจ้งสมาชิกทั้ง 4 คน (แก้ผ่าน Pull Request ที่ทุกคนอนุมัติเท่านั้น)
ไม่มี network / API ใดๆ: ทุกโมดูลเรียกกันด้วย Python import และเรียกฟังก์ชันตรงๆ
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ---------- ค่าคงที่ ----------
TEXT_BASE = 0x00002000          # ที่อยู่เริ่มต้นของโค้ด (.ORG ตาม cpuSimV7)
DATA_BASE = 0x00010000
STACK_TOP = 0x0001FFFC          # ค่าเริ่มต้นของ $sp (stack โตลง)
MEM_SIZE = 0x00100000           # 1 MiB; เข้าถึงนอกช่วง = BAD_MEMORY
DEFAULT_MAX_STEPS = 10_000_000  # 12C6 แบบ Factorial-Based ใช้ ~3.3 ล้านคำสั่ง
TRACE_LIMIT = 5000              # ring buffer ของ Trace (เก็บล่าสุด N แถว)

REG_NAMES = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
             "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
             "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
             "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]
REG_V0, REG_V1, REG_A0, REG_A1, REG_SP, REG_RA = 2, 3, 4, 5, 29, 31

COUNTER_KEYS = ("instr", "branch", "branch_taken", "arith",
                "mem_read", "mem_write", "call")


class Status:                    # สถานะของ CPU (ใช้เป็น str)
    READY = "READY"
    RUNNING = "RUNNING"
    HALTED = "HALTED"            # จบปกติด้วย HALT
    OVERFLOW = "OVERFLOW"        # ADD/ADDI/SUB เกิน signed 32-bit (trap)
    BAD_OPCODE = "BAD_OPCODE"
    BAD_REGISTER = "BAD_REGISTER"
    BAD_MEMORY = "BAD_MEMORY"    # นอกช่วงหรือไม่ align 4
    BAD_PC = "BAD_PC"
    MAX_STEPS = "MAX_STEPS"
    FINISHED = (HALTED,)
    ERRORS = (OVERFLOW, BAD_OPCODE, BAD_REGISTER, BAD_MEMORY, BAD_PC, MAX_STEPS)


class ProgStatus:                # รหัสสถานะที่โปรแกรม MIPS คืนใน $v1
    OK = 0
    DIV_ZERO = 2
    BAD_INPUT = 3


# ---------- ตัวช่วยแปลงค่า (register เก็บเป็น signed int32) ----------
def s32(x: int) -> int:
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x >> 31 else x

def u32(x: int) -> int:
    return x & 0xFFFFFFFF

def hex8(x: int) -> str:
    return f"{u32(x):08x}"

def bin32(x: int) -> str:
    return f"{u32(x):032b}"


class AsmError(Exception):
    """ข้อผิดพลาดตอน assemble (ภาษา/label/immediate)"""
    def __init__(self, line_no: int, message: str):
        super().__init__(f"line {line_no}: {message}")
        self.line_no, self.message = line_no, message


# ---------- ข้อมูลที่ไหลระหว่างโมดูล ----------
@dataclass(frozen=True)
class Instr:                     # สร้างโดย assembler (isa.py), อ่านโดย cpu.py และ GUI
    index: int                   # ลำดับในโปรแกรม
    addr: int                    # byte address
    line_no: int                 # บรรทัดในไฟล์ .asm
    raw: str                     # ข้อความเดิม (ไม่รวม comment/label)
    label: Optional[str]         # label ที่ชี้มาที่คำสั่งนี้ (ถ้ามี)
    op: str                      # 'ADD', 'ADDI', 'JAL', 'HALT' ...
    kind: str                    # 'R' | 'I' | 'J' | 'SIM'  (SIM = HALT/.ORG ไม่ใช่ MIPS มาตรฐาน)
    rd: int = 0
    rs: int = 0
    rt: int = 0
    shamt: int = 0
    imm: int = 0                 # signed; BEQ/BNE = offset เป็นจำนวนคำสั่งนับจากคำสั่งถัดไป
    target: int = 0              # J/JAL = byte address ปลายทาง
    hex8: Optional[str] = None   # None เมื่อ kind == 'SIM'
    bin32: Optional[str] = None


@dataclass
class Program:
    name: str
    text_base: int
    instrs: list[Instr]
    labels: dict[str, int]       # label -> byte address
    source: str                  # ข้อความ .asm ทั้งไฟล์ (ให้ GUI แสดง)
    entry: int = TEXT_BASE       # = label 'main' ถ้ามี ไม่งั้น text_base


@dataclass
class StepResult:                # ผลของ cpu.step() หนึ่งครั้ง
    step_no: int                 # ลำดับ (นับเฉพาะคำสั่งที่ทำสำเร็จ; trap ใช้เลขถัดไป)
    pc_before: int
    pc_after: int
    instr: Instr
    completed: bool              # False เมื่อ trap (เช่น OVERFLOW) -> ไม่นับใน counter
    reg_changes: dict[int, tuple[int, int]] = field(default_factory=dict)  # idx -> (old, new)
    mem_reads: list[int] = field(default_factory=list)                     # byte address
    mem_writes: list[tuple[int, int]] = field(default_factory=list)        # (addr, word)
    alu_text: Optional[str] = None       # เช่น "5 + 7 = 12" หรือ "3 < 9 -> 1"
    branch_taken: Optional[bool] = None  # None = ไม่ใช่ branch
    status: str = Status.RUNNING
    error: Optional[str] = None


@dataclass
class CPUState:                  # snapshot สำหรับ GUI (คัดลอกมา ไม่ใช่ reference)
    pc: int
    regs: list[int]              # 32 ตัว signed int32
    memory: dict[int, int]       # byte address -> byte (เฉพาะที่ถูกเขียน รวมโซน text)
    counters: dict[str, int]     # key ตาม COUNTER_KEYS
    status: str
    error: Optional[str] = None


@dataclass
class RunResult:
    finished: bool               # True = CPU หยุดแล้ว (HALTED หรือ error)
    status: str
    steps_executed: int          # จำนวนคำสั่งที่ทำในการเรียก run() นี้
    state: CPUState


# ---------- ข้อมูลโปรแกรม MIPS ที่ GUI เลือกได้ ----------
@dataclass(frozen=True)
class ProgramSpec:
    key: str
    title: str
    asm_path: str
    uses_r: bool
    n_min: int
    n_max: int                   # ขอบเขตที่รับประกัน/ตรวจใน GUI
    reference: str               # ชื่อฟังก์ชันใน reference/reference.py

PROGRAM_SPECS: dict[str, ProgramSpec] = {
    "factorial": ProgramSpec("factorial", "Factorial n! (Repeated Addition)",
                             "programs/factorial.asm", False, 0, 12, "factorial_ref"),
    "ncr_factorial": ProgramSpec("ncr_factorial", "nCr แบบ Factorial-Based (เรียก fact 3 ครั้ง)",
                                 "programs/ncr_factorial.asm", True, 0, 12, "ncr_ref"),
    "nck_optimized": ProgramSpec("nck_optimized", "nCk แบบ Optimized (ฐานจาก nCkbound.py)",
                                 "programs/nck_optimized.asm", True, 0, 26, "ncr_ref"),
}

def spec_key(kind: str, algo: Optional[str]) -> str:
    """kind: 'factorial' | 'ncr'; algo: 'optimized' | 'factorial_based' (ใช้เมื่อ kind == 'ncr')"""
    if kind == "factorial":
        return "factorial"
    return "nck_optimized" if algo == "optimized" else "ncr_factorial"


# ---------- ข้อมูลที่ Controller ส่งให้ GUI ----------
@dataclass
class ViewState:
    mode: str                    # 'idle' | 'ready' | 'running' | 'paused' | 'finished' | 'error'
    program: Optional[Program]
    cpu: Optional[CPUState]
    last_step: Optional[StepResult]
    trace_tail: list[StepResult]         # ล่าสุดไม่เกิน TRACE_LIMIT
    result: Optional[int] = None         # ค่าใน $v0 เมื่อ finished และ prog_status == OK
    prog_status: Optional[int] = None    # ค่าใน $v1 เมื่อ finished
    message: str = ""
    turbo: bool = False                  # True = ข้ามการบันทึก trace รายคำสั่ง

@dataclass
class CompareRow:
    n: int
    r: int
    method: str                  # key ใน PROGRAM_SPECS
    result: Optional[int]
    status: str
    prog_status: Optional[int]
    counters: dict[str, int]
    matches_reference: Optional[bool]
