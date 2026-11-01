# MASTER PROJECT PROMPT (v3 — Build Edition)
## MIPS Factorial & nCr Visual CPU Architecture Simulator
### Python 3.10+ · VS Code · Tkinter GUI · รันด้วย `python main.py` · ไม่มี API ทุกโมดูลเรียกกันด้วย `import`

> **วิธีใช้:** เปิดแชตใหม่ แนบ `Comarch.zip` (ไฟล์อาจารย์) แล้ววางพรอมพ์นี้ทั้งฉบับ จากนั้นพิมพ์บรรทัดสั่งงาน เช่น `BUILD MEMBER 3`
> ทั้ง 4 คนใช้พรอมพ์ **ฉบับเดียวกันทุกตัวอักษร** (สำคัญมาก เพราะ Contract ในข้อ 5 และภาคผนวกต้องตรงกัน) ต่างกันแค่บรรทัดสั่งงาน
> ระดับความต้องการ: **MUST** = ต้องมี · **SHOULD** = ควรมีหลัง MVP · **MAY** = ทำถ้ามีเวลา

---

## 0. โหมดสั่งงาน (AI ต้องทำตามบรรทัดสั่งงานที่ผู้ใช้พิมพ์หลังพรอมพ์นี้)

| คำสั่ง | AI ต้องทำอะไร |
|---|---|
| `BUILD MEMBER n` (n = 1–4) | สร้าง**ไฟล์ทั้งหมดของ Member n** ตามข้อ 10 ให้ครบ ใช้งานได้ ไม่มี `...` หรือ TODO เว้นว่าง พร้อมไฟล์ทดสอบ วิธีรัน และผลที่คาดหวัง |
| `BUILD INTEGRATION` | ตรวจและประกอบทุกโมดูลเข้าด้วยกัน รัน `python main.py --selftest` และ Integration Checklist (ข้อ 12) แล้วรายงานผล |
| `REVIEW <path>` | อ่านไฟล์ที่ผู้ใช้วาง ตรวจกับ Contract (ข้อ 5–6) และกติกา ชี้จุดที่ไม่ตรงพร้อมโค้ดที่แก้ |
| `TEACH <Phase n>` | โหมดสอนทีละ Phase (ข้อ 13) อธิบายหลักการ + ทำ + ทดสอบ แล้วหยุดรอผล |
| `FIX <ข้อความ error>` | วิเคราะห์สาเหตุจาก error ที่ผู้ใช้วาง แก้เฉพาะจุด และบอกว่ากระทบโมดูลของใครบ้าง |

**กติกาของ AI ในทุกโหมด**

1. ใช้ชื่อไฟล์ ชื่อฟังก์ชัน ชื่อคลาส ชื่อ field **ตรงตามข้อ 5–6 และภาคผนวก B ทุกตัวอักษร** ห้ามเพิ่มโมดูลใหม่ ห้ามเปลี่ยนลายเซ็นฟังก์ชันเอง ถ้า Contract ขัดขวางงานให้บอกผู้ใช้แล้วหยุด ไม่แก้ Contract เอง
2. **ห้ามอ้างว่าโค้ดทำงานได้ถ้ายังไม่ได้รัน** ถ้ารันไม่ได้ในสภาพแวดล้อมนี้ ให้เขียนว่า "ยังไม่ได้รัน" และให้คำสั่งทดสอบกับผลที่คาดหวัง (ตัวเลขในข้อ 9.3 ใช้ตรวจได้)
3. ถ้ามีเครื่องมือสร้างไฟล์ ให้สร้างไฟล์จริงตาม path ถ้าไม่มี ให้ใส่ code block แยกต่อไฟล์ พร้อมบรรทัดแรกเป็น path
4. ทุกไฟล์ Python ต้องมี header บอกที่มา: `ORIGINAL` (ของอาจารย์ไม่แก้), `MODIFIED` (แก้จากอาจารย์ พร้อมเหตุผล), `NEW` (เขียนใหม่)
5. ตอบเป็นภาษาไทย ศัพท์เทคนิคภาษาอังกฤษตามเดิม คอมเมนต์ในโค้ดเป็นไทยหรืออังกฤษก็ได้แต่ให้สม่ำเสมอ
6. ท้ายทุกคำตอบของ `BUILD` ให้สรุป: ไฟล์ที่สร้าง · ฟังก์ชันที่โมดูลอื่นเรียกใช้ · สิ่งที่ต้องรอจากสมาชิกคนอื่น · วิธีทดสอบ
7. ห้ามใช้ `math.factorial()`/`math.comb()` ที่ไหนก็ตามนอก `reference/`, `tests/`, `tools/`

---

## 1. โปรเจกต์ และ "คำตัดสิน" เรื่องวิธีคำนวณ nCr

โปรแกรมจำลอง CPU แบบ MIPS ด้วย Python + Tkinter เปิดด้วย `python main.py` ผู้ใช้เลือก **Factorial** หรือ **nCr** กรอก n, r แล้ว Run หรือ Step ดูการทำงานทีละคำสั่ง (PC, Registers, ALU, Memory, Machine Code, Trace) การคำนวณทุกครั้งเกิดจากการ Execute โปรแกรม MIPS (`programs/*.asm`) บน Simulator จริง

### คำตัดสิน (ล็อกแล้ว ไม่ต้องถกอีก)

| หัวข้อ | ตัดสินใจ | เหตุผล |
|---|---|---|
| วิธีหลัก (ค่าเริ่มต้นใน GUI) | **Optimized nCk** — ฐานจาก `nCkbound.py` ของอาจารย์ | ใช้ Instruction น้อยกว่ามาก (12C6: 5,063 เทียบ 3,331,860 หรือ ~658 เท่า) Step ดูได้จริงในหลักพันคำสั่ง ช่วงที่ปลอดภัยกว้างกว่า (n ≤ 17 ทุก r เทียบ n ≤ 12) |
| วิธีเปรียบเทียบ | **Factorial-Based** — เรียก `fact` 3 ครั้ง + หารด้วยการบวกสะสม | จำเป็นต่อโจทย์ (Subroutine, JAL/JR, Stack, เปรียบเทียบอัลกอริทึม) และให้เห็นว่าทำไมวิธีนี้แพง |
| Factorial เดี่ยว | `factorial.asm` ใช้ Repeated Addition ตาม `factorial_no_mul_2.py` | ของอาจารย์ แปลงตรงๆ และถูกใช้ซ้ำเป็น Subroutine `fact` |
| วิธีที่ 3 (Stepwise) | **ไม่ทำใน MVP** (MAY) | ครอบคลุม n ≤ 26 ทุก r ได้ (ค่ากลางสูงสุด 135,207,800 ใน 32-bit) ทำเมื่อเสร็จหมดแล้วเท่านั้น |
| nC0 ในโค้ดอาจารย์ | **แก้บัค** | `nCkNoMulDiv(n,0)` ของอาจารย์ตอบ n แทน 1 (ผิด 25 กรณีสำหรับ n ≤ 26) เพราะชุดทดสอบของอาจารย์เริ่มที่ k=1 ใน MIPS แก้ด้วยการคืน 1 เมื่อ a = 0 |

### ขอบเขตค่า n ของแต่ละโปรแกรม (ตรวจแล้วด้วยการรันจริงบนตัวแปลอิสระ)
- `factorial`: n = 0..12 (13! = 6,227,020,800 เกิน signed 32-bit → โปรแกรมคืน `$v1 = 3`)
- `ncr_factorial`: n = 0..12, r = 0..n
- `nck_optimized`: n = 0..26, r = 0..n **แต่** ค่ากลาง n!/b! โตเกิน 32-bit ได้: ทุก r ปลอดภัยเมื่อ n ≤ 17; ตั้งแต่ n = 18 เป็นต้นไปบางคู่ (n, r) จะเกิด **OVERFLOW trap** จากเอนจิน (ทั้งหมด 65 จาก 378 คู่ที่ n ≤ 26 เช่น 18C9, 26C13) GUI ต้องแสดงข้อความ Overflow ชัดเจน **ห้ามตอบผิดเงียบๆ** และนำมาเป็นตัวอย่างสอนในการสาธิตได้

---

## 2. ข้อกำหนดบังคับ (MUST) แบบสรุป

1. คำนวณผ่านโปรแกรม MIPS บน Simulator เท่านั้น ใช้ Python Reference เพื่อตรวจคำตอบ (ป้าย ✔) ห้ามนำมาแสดงเป็นผลลัพธ์
2. Simulator: `step()` ทำ 1 คำสั่งพอดี, `reset()`, `get_state()`, Run/Pause ผ่าน Controller, Max Steps, Instruction Counter (Dynamic), Error handling (Overflow, Bad Opcode/Register/Memory, Max Steps)
3. ISA: Assembler 2 ผ่าน (รองรับ label), Encode Machine Code R/I/J ถูกต้อง (Binary 32-bit + Hex 8 หลัก), ถอด field ได้, JAL/JR/SLT/SUB/ADD ทำงานจริง
4. GUI Tkinter: Input / Control (Run, Pause, Step, Reset) / Instruction / Register 32 ตัว / Memory / Output / Performance (ตาราง + กราฟ Matplotlib) / Trace
5. เปรียบเทียบ 2 วิธีบน Input เดียวกัน ด้วย Dynamic Instruction Count (ไม่ใช่เวลา/Clock Cycles จริง) และตรวจว่าผลตรงกันก่อนพล็อต
6. เปิดด้วย `python main.py` เรียกกันด้วย `import` และเรียกฟังก์ชัน Python ตรงๆ **ไม่มีเซิร์ฟเวอร์ ไม่มี HTTP API ไม่มี thread ที่แตะ widget**
7. Unit + Integration tests, README, รายงาน, Flowchart, Architecture Diagram

**ข้อจำกัดที่ต้องเขียนในเอกสารและ GUI ตามความจริง:** เป็น Functional Single-Cycle Simulator ไม่มี Branch Delay Slot ไม่ใช่ Pipeline ไม่มี Timing Model; MVP Execute จากออบเจ็กต์ `Instr` ที่ Assemble แล้ว (Machine Code เป็นข้อมูลแสดงผลที่ Encode จากคำสั่งเดียวกัน)

---

## 3. ฐานจากอาจารย์ และบัคที่ยืนยันแล้ว

ไฟล์ที่ได้รับ: `cpu.py`, `isa.py`, `memory.py`, `main.py`, `instructions.txt`, `test.py`, `Readme3-7.txt` (cpuSimV7), `nCkbound.py`, `factorial_no_mul_1.py`, `factorial_no_mul_2.py`

**กฎการใช้ไฟล์อาจารย์:** เก็บต้นฉบับไว้ไม่แก้ที่ `references/original_cpuSimV7/` (ORIGINAL) แล้วสร้างฉบับใช้งานใน `simulator/` โดยรักษาแนวคิดเดิม (execute แยกตาม opcode, `.ORG`, `validate()`, `debug()`) และติดป้าย MODIFIED/NEW ต้องมี Regression Test ว่า `instructions.txt` เดิมยังได้ผลเดิม (ค่า register สุดท้ายเทียบกับที่รันบน cpuSimV7 ต้นฉบับ)

| # | บัคใน cpuSimV7 (ยืนยันด้วยการรัน) | ผลที่เห็น | แก้โดย |
|---|---|---|---|
| 1 | `ADD` อ่าน `ops[3]` ทั้งที่มี 3 operands | `IndexError` | Member 3 |
| 2 | `JAL`, `JR`, `SLL`, `SRL` ไม่มีโค้ด execute | รันผ่านโดยไม่ทำอะไร ไม่แจ้ง error | Member 3 |
| 3 | R-type ถูก Encode เป็น `00000000` (`J`, `ADDI` ถูกแล้ว) | Machine Code ผิด | Member 3 |
| 4 | Parser รับแค่ `$<ตัวเลข>` | `$a0`, `$sp` ทำให้ crash | Member 3 |
| 5 | ไม่มี label ต้องนับ offset เอง | เขียน loop ซ้อนยาก/ผิดง่าย | Member 3 |
| 6 | ไม่มี Max Steps | loop ไม่จบ = โปรแกรมค้าง | Member 3 |
| 7 | ADD/ADDI ไม่ตรวจ/ไม่ wrap 32-bit; `validate()` ใช้ `int(hex(..)[-8:])` แปลง hex เป็นฐาน 10 ผิด | `0x7fffffff+1` ได้ `2147483648` | Member 3 |
| 8 | ไม่มี `.ORG` บรรทัดแรก | `UnboundLocalError` | Member 3 |
| 9 | `SLTI`/`SLTIU` เขียนทับ `rs` | ค่าต้นทางถูกเปลี่ยน | Member 3 |
| 10 | `SW` เก็บทั้ง word ที่ key เดียว แต่ instruction memory เก็บทีละ byte | Memory 2 รูปแบบปนกัน | Member 3 |
| 11 | PC เก็บเป็น index (address÷4) + `BASE_PC` | สับสนเมื่อ GUI ต้องใช้ address จริง | Member 3 |
| 12 | `nCkNoMulDiv(n,0)` ตอบ n แทน 1 | ผิด 25 กรณี (n 2..26) | Member 2 (ใน asm) |
| 13 | คำสั่งใน `cmdDict` (LBU, LHU, LL, SB, SC, SH) ไม่มี execute | ไม่ชัดว่ารองรับหรือไม่ | Member 3 (ประกาศ Unsupported) |

---

## 4. สถาปัตยกรรม: ทุกอย่างเรียกกันด้วย `import`

```
python main.py
 └─ interface/gui.py : App(tk.Tk)         ← สร้าง Controller เอง: Controller(scheduler=self.after, on_update=self.render)
      │  import
      ▼
    integration/controller.py : Controller   ← เป็นจุดเดียวที่ GUI คุยกับระบบ
      ├─ simulator/assembler.py  assemble_file() → Program
      ├─ simulator/cpu.py        CPU.load/step/run/reset/get_state
      │        └─ simulator/memory.py, simulator/isa.py
      ├─ programs/*.asm          (อ่านเป็นไฟล์ข้อความ)
      └─ reference/reference.py  (ตรวจคำตอบ → ป้าย ✔ เท่านั้น)
ทุกโมดูล import ชนิดข้อมูลจาก simulator/contract.py
```

**กฎการ import (ตรวจใน Integration Checklist):**
- `simulator/` ห้าม import `interface/`, `integration/`, `reference/`
- `interface/` import ได้เฉพาะ `integration.controller` และ `simulator.contract` (ห้าม import `simulator.cpu` ตรงๆ)
- `integration/` import `simulator/*`, `reference/*`, `simulator.contract` ได้
- รันเทสต์ด้วย `python -m pytest` จาก root ของโปรเจกต์ (ทุกโฟลเดอร์มี `__init__.py`)
- `main.py`: `python main.py` เปิด GUI · `python main.py --selftest` รัน Acceptance Table (ข้อ 9.3) แบบไม่เปิด GUI แล้วพิมพ์ PASS/FAIL

**ไม่ใช้ thread กับ GUI:** Run ใช้ `root.after()` เรียก `step()`/`run(stop_after=k)` เป็นช่วงสั้นๆ ผ่าน `scheduler` ที่ส่งเข้า `Controller` เพื่อให้ Controller ทดสอบได้โดยไม่ต้องมี Tkinter

---

## 5. Contract กลาง — `simulator/contract.py` (ฉบับสมบูรณ์ ทดสอบ import ผ่านแล้ว)

ทุกคนต้องวางไฟล์นี้ตามที่เป็นอยู่ ห้ามแก้ (Member 3 เป็นผู้ commit ลง repo)

```python
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
```

---

## 6. ลายเซ็นฟังก์ชันของแต่ละโมดูล (ต้องตรงทุกตัวอักษร)

```python
# ---- simulator/memory.py  (Member 3)
class MemoryAccessError(Exception): ...
class Memory:
    def __init__(self) -> None: ...
    def read_byte(self, addr: int) -> int: ...
    def write_byte(self, addr: int, value: int) -> None: ...
    def read_word(self, addr: int) -> int: ...          # unsigned 0..2**32-1, Big-endian, addr % 4 == 0 ไม่งั้น MemoryAccessError
    def write_word(self, addr: int, value: int) -> None: ...
    def snapshot(self) -> dict[int, int]: ...            # byte address -> byte (เฉพาะที่เคยเขียน)
    def clear(self) -> None: ...
    # ช่วง 0 <= addr < MEM_SIZE เท่านั้น นอกช่วง = MemoryAccessError

# ---- simulator/isa.py  (Member 3)
INSTR_TABLE: dict[str, dict]   # op -> {"kind","opcode","funct","status"("EXEC"|"UNSUPPORTED"),"form"}
def reg_number(token: str) -> int: ...                  # "$a0" / "a0" / "$4" -> 4 ; ผิดรูป -> AsmError
def encode(op: str, kind: str, rd=0, rs=0, rt=0, shamt=0, imm=0, target=0) -> tuple[str, str]: ...  # (hex8, bin32)
def decode_word(word: int) -> dict: ...                 # {"kind","op","rs","rt","rd","shamt","funct","imm","target"}

# ---- simulator/assembler.py  (Member 3)
def assemble(source: str, name: str = "program") -> Program: ...        # 2 ผ่าน; ผิด -> AsmError(line_no, message)
def assemble_file(path: str) -> Program: ...

# ---- simulator/cpu.py  (Member 3)
class CPU:
    def __init__(self, memory: "Memory | None" = None, max_steps: int = DEFAULT_MAX_STEPS) -> None: ...
    def load(self, program: Program, init_regs: "dict[int, int] | None" = None) -> None: ...
        # เขียน machine code ลง memory ที่ text_base, ตั้ง regs=0, $sp=STACK_TOP, regs ตาม init_regs, PC=program.entry
        # reset() ต้องคืนสถานะ "หลัง load" เดิม (รวม init_regs)
    def reset(self) -> None: ...
    def step(self) -> StepResult: ...                    # ทำ 1 คำสั่งพอดี บันทึกลง trace ring buffer เสมอ
    def run(self, stop_after: "int | None" = None, record_trace: bool = False) -> RunResult: ...
        # fast path: ไม่สร้าง StepResult ถ้า record_trace=False ; เรียกซ้ำเพื่อทำต่อได้ ; เป้า >= 300,000 คำสั่ง/วินาที
    def get_state(self) -> CPUState: ...                 # snapshot (คัดลอก)
    def set_reg(self, idx: int, value: int) -> None: ...
    @property
    def trace(self) -> list[StepResult]: ...             # ล่าสุดไม่เกิน TRACE_LIMIT

# ---- reference/reference.py  (Member 2)  -- ใช้ math ได้ที่นี่เท่านั้น
def factorial_ref(n: int) -> int: ...
def ncr_ref(n: int, r: int) -> int: ...

# ---- integration/runner.py  (Member 2)
def run_asm(path: str, a0: int, a1: int = 0, max_steps: int = DEFAULT_MAX_STEPS) -> RunResult: ...
    # assemble_file -> CPU.load(init_regs={4:a0, 5:a1}) -> cpu.run() ทั้งหมดจนจบ (ไม่บันทึก trace)

# ---- integration/controller.py  (Member 4)
class Controller:
    def __init__(self, scheduler=None, on_update=None) -> None: ...
        # scheduler(ms: int, fn: Callable) -> handle   (GUI ส่ง root.after มา; None = เรียกตรงไม่หน่วง)
        # on_update(view: ViewState) -> None
    def validate_input(self, kind: str, algo: "str | None", n_text: str, r_text: str
                       ) -> "tuple[bool, str, tuple[int, int | None] | None]": ...   # (ok, ข้อความไทย, (n, r))
    def load(self, kind: str, algo: "str | None", n: int, r: "int | None") -> ViewState: ...
    def step(self) -> ViewState: ...
    def run(self, steps_per_tick: int = 20, delay_ms: int = 20) -> None: ...   # เริ่มลูปด้วย scheduler จนจบ/pause
    def pause(self) -> None: ...
    def reset(self) -> ViewState: ...
    def get_view(self) -> ViewState: ...
    def run_headless(self, kind: str, algo: "str | None", n: int, r: "int | None") -> CompareRow: ...
    def compare(self, cases: "list[tuple[int, int]]", methods: "list[str]") -> "list[CompareRow]": ...   # ซิงค์ ใช้ใน test/benchmark
    def compare_async(self, cases, methods, on_progress, on_done) -> None: ...   # แบ่งช่วงด้วย scheduler (cpu.run(stop_after=50_000))

# ---- interface/*.py  (Member 4)
class App(tk.Tk): ...                      # __init__(self) สร้าง Controller เอง
class CPUDiagram(tk.Canvas):               # cpu_visualizer.py
    def show_step(self, step: "StepResult | None") -> None: ...
class PerformanceChart(ttk.Frame):         # performance_chart.py
    def show(self, rows: "list[CompareRow]", metric: str = "instr", log_scale: bool = True) -> None: ...
```

**ข้อตกลงความหมาย (ทุกคนต้องเข้าใจตรงกัน)**
- Register เก็บเป็น **signed int32** (`s32`) แสดง Hex ด้วย `hex8()`; Memory word เป็น unsigned; `LW` แปลงด้วย `s32`
- **PC ในทุก API เป็น byte address** (ภายใน `cpu.py` เก็บเป็น index ก็ได้แต่ห้ามรั่วออกนอกไฟล์)
- `Instr.imm` ของ BEQ/BNE = offset เป็น**จำนวนคำสั่ง**นับจากคำสั่งถัดไป (`target = addr + 4 + imm*4`) Assembler คำนวณจาก label ให้
- J/JAL: `Instr.target` = byte address, Encode ด้วย `target >> 2`; JAL เก็บ `addr + 4` ลง `$ra`; JR กระโดดไป `$rs`
- HALT: ทำแล้ว status = HALTED PC ไม่เลื่อน (ถูกนับ 1 คำสั่ง) ส่วน `.ORG` ไม่นับและไม่ execute
- **นับ `instr` = ทุกคำสั่งที่ทำสำเร็จ รวม HALT ไม่รวม `.ORG` และคำสั่งที่ trap** ต้องเท่ากับจำนวนแถว `completed=True` ใน trace (ตราบที่ไม่ใช่ Turbo)
- Trap (OVERFLOW, BAD_*): ไม่เขียน register/memory, PC ไม่เลื่อน, status เป็นค่า error, `StepResult.completed=False` (ใส่ใน trace เป็นแถวสุดท้าย) ผู้เรียกต่อไปจะได้ `StepResult` เดิมโดยไม่เกิดผลใดๆ
- ADD/ADDI/SUB: ตรวจ signed overflow แล้ว trap · ADDU/ADDIU/SUBU: wrap 32-bit · เขียน `$zero` = ไม่มีผล (ไม่ error)
- `run()` ที่ครบ `max_steps` โดยยังไม่ HALT → status `MAX_STEPS`

---

## 7. ISA ที่ Simulator รองรับ

| สถานะ | คำสั่ง |
|---|---|
| **Executable (MUST)** | ADD ADDU ADDI ADDIU SUB SUBU AND ANDI OR ORI SLT SLTU SLTI SLTIU LUI LW SW BEQ BNE J JAL JR และ HALT (Simulator-specific) |
| Executable (SHOULD) | SLL SRL NOR |
| **Unsupported** | LBU LHU LL SB SC SH → Assembler แจ้ง `AsmError("unsupported instruction")` ห้ามแสดงว่ารองรับ |
| Directive | `.ORG addr` (Simulator-specific, ไม่มี Machine Code) |

**รูปแบบ Assembly:** `ADD rd rs rt` · `ADDI rt rs imm` · `SLT rd rs rt` · `SLTI rt rs imm` · `BEQ rs rt label` · `J label` · `JAL label` · `JR rs` · `LW rt off(rs)` · `SW rt off(rs)` · `LUI rt imm` · label = `ชื่อ:` · comment = `#` · register ได้ทั้ง `$a0` และ `$4` · immediate ทศนิยม/`0x` · ไม่สนตัวพิมพ์ใหญ่เล็ก · ตัวคั่นเป็นเว้นวรรคหรือ comma · บอกเลขบรรทัดเมื่อ error (label ซ้ำ/ไม่พบ, immediate เกิน 16 บิต, register ผิด)

**Golden Machine Code** (คำนวณจากสูตร MIPS32 และตรวจ 4 ตัวแรกกับค่าที่รู้กันทั่วไป; **Member 1 ต้องยืนยันซ้ำด้วย MARS หรือ QtSpim** แล้วเก็บเป็น `tests/golden_hex.json`)

| Assembly | Hex | | Assembly | Hex |
|---|---|---|---|---|
| `ADD $t2 $t0 $t1` | 01095020 | | `SW $ra 28($sp)` | afbf001c |
| `ADDI $t0 $zero 5` | 20080005 | | `ORI $10 $9 0xfffe` | 352afffe |
| `LW $t0 4($sp)` | 8fa80004 | | `BEQ $t0 $t1 3` | 11280003 |
| `JR $ra` | 03e00008 | | `BNE $t1 $zero -2` | 1409fffe |
| `SUB $s2 $s0 $s1` | 02119022 | | `J 0x2030` | 0800080c |
| `SLT $t1 $a0 $t0` | 0088482a | | `JAL 0x2008` | 0c000802 |
| `SLTI $t0 $a0 13` | 2888000d | | `LUI $9 0xffff` | 3c09ffff |
| `ADDI $sp $sp -32` | 23bdffe0 | | `ADDIU $t0 $t0 1` | 25080001 |

**Memory Model:** byte-addressed, word = 4 byte, Big-endian, `LW/SW` ต้อง align 4, ช่วงที่อยู่ 0 ≤ addr < `MEM_SIZE`; โซน text เริ่ม `0x2000` (เขียน machine code เป็น byte ตอน `load`), data `0x10000`, stack `0x1FFFC` โตลง

**Register Convention:** `$zero`=0 · `$v0`=2 (ผลลัพธ์) · `$v1`=3 (รหัสสถานะโปรแกรม) · `$a0`=4 (n) · `$a1`=5 (r) · `$t0–$t7`=8–15, `$t8–$t9`=24–25 (ใช้อิสระใน leaf routine) · `$s0–$s7`=16–23 (ต้อง save/restore ถ้าใช้) · `$sp`=29 · `$ra`=31
**รหัส `$v1`:** 0 = ปกติ · 2 = หารด้วยศูนย์ · 3 = Input ไม่ถูกต้อง **Controller ใส่ n ใน `$a0` และ r ใน `$a1` ผ่าน `init_regs={4:n, 5:r}`** โปรแกรมเริ่มที่ label `main:`

---

## 8. Instruction Counter และสถิติ
`counters` มี key ตาม `COUNTER_KEYS`: `instr` (ทั้งหมด), `branch` (BEQ/BNE ที่ execute), `branch_taken`, `arith` (ADD/ADDI/ADDU/ADDIU/SUB/SUBU/AND/OR/…/SLT/SLTI/SLTU/SLTIU/LUI/SLL/SRL), `mem_read` (LW), `mem_write` (SW), `call` (JAL) ใช้เปรียบเทียบอัลกอริทึม และต้องตรงกับ Trace

---

## 9. อัลกอริทึม MIPS (โปรแกรมต้นแบบที่ตรวจแล้ว)

### 9.1 หลักการ
- Factorial: Repeated Addition (ลูปซ้อน: `temp += acc` ทำ `i` ครั้งแล้ว `acc = temp`) ตาม `factorial_no_mul_2.py`
- nCr Factorial-Based: `fact` 3 ครั้ง (n!, r!, (n−r)!) เก็บใน `$s3–$s5`, save `$ra`/`$s*` ลง stack, สลับให้ตัวหารตัวแรกเป็น factorial ที่ใหญ่กว่า (ลดจำนวนรอบ), หาร 2 ครั้งด้วยการบวกสะสม (หารทีละตัวเพื่อไม่ต้องคูณ r!·(n−r)!) และคืน `$v1=2` ถ้าหารด้วยศูนย์
- nCr Optimized: ตามอาจารย์ — `a=min(k,n−k)`, `b=max(k,n−k)`, ผลคูณ n(n−1)…(b+1) ด้วย Repeated Addition, a! ด้วย Repeated Addition, หารด้วยการบวกสะสมเมื่อ a! > 1; **เพิ่มการคืน 1 เมื่อ a = 0 (แก้บัค nC0)**

### 9.2 ซอร์สต้นแบบ — อยู่ในภาคผนวก A (factorial.asm, ncr_factorial.asm, nck_optimized.asm)
ตรวจแล้วกับตัวแปลอิสระ (`tools/refsim.py` ภาคผนวก C): factorial ครบ n=0..12; ncr_factorial ครบ 91 คู่ (n ≤ 12) พร้อมตรวจว่า `$s0–$s5` และ `$sp` ถูกคืนค่า; nck_optimized ครบ 378 คู่ (n ≤ 26) ผลถูกทั้ง 313 คู่ที่ไม่ trap และ trap 65 คู่ตรงกับที่วิเคราะห์ไว้ล่วงหน้า **(ยังไม่ได้รันบน cpuSimV7 ที่ปรับปรุงแล้ว นั่นคืองานของทีม)**
กฎ: บล็อก `fact:` … `JR $ra` ใน `factorial.asm` กับ `ncr_factorial.asm` ต้อง**เหมือนกันทุกคำสั่ง (ไม่นับ comment)** เพราะ Assembler ไม่มี `.INCLUDE` Member 2 เขียน test ตรวจ

### 9.3 Acceptance Table (จำนวน Instruction ที่ถูกต้องของโปรแกรมต้นแบบ)
นับตามข้อ 6 (รวม HALT, รวม `JAL main`) ถ้า Simulator ของทีมได้**ตัวเลขตรงเป๊ะ** = หลักฐานว่า Engine + Assembler ถูกต้อง (ถ้าแก้ asm แล้วตัวเลขเปลี่ยน ให้อัปเดตตารางพร้อมเหตุผล)

| Input | Factorial-Based | Optimized | เท่า |
|---|---|---|---|
| `5!` | 118 | — | |
| `12!` | 496 | — | |
| 5C2 = 10 | 387 | 127 | 3.0 |
| 6C3 = 20 | 997 | 234 | 4.3 |
| 8C4 = 70 | 9,198 | 567 | 16.2 |
| 10C5 = 252 | 153,089 | 1,580 | 96.9 |
| 12C6 = 924 | 3,331,860 | 5,063 | 658.1 |
| 12C1 = 12 | 1,088 | 29 | |

`call` ของ Factorial-Based ทุกเคสที่ Input ถูกต้อง = 6 (`main→ncr_fact`, fact×3, div×2), `mem_read` = `mem_write` = 7 (save/restore 7 words)
ข้อสังเกตสำหรับการนำเสนอ: ค่าใช้จ่ายของ Factorial-Based เกือบทั้งหมดมาจากการหารด้วยการบวกสะสม (จำนวนรอบ = ค่าผลหาร) ไม่ใช่การคำนวณ factorial

### 9.4 กรณีทดสอบขั้นต่ำ
Factorial: 0,1,5,10,12 ถูก; 13 และ −1 → `$v1=3` · nCr: nC0=1, nCn=1, 5C2=10, 6C3=20, 8C4=70, 10C5=252, 12C6=924; Input ผิด (n>12, r>n, ติดลบ) → `$v1=3` · Optimized: ทุก (n, r) ที่ n ≤ 17 ตรงกับ `ncr_ref`; (18,9) และ (26,13) → status `OVERFLOW`; 26C1 = 26 ถูก (ไม่ trap)

---

## 10. งานของแต่ละคน (นี่คือสิ่งที่ `BUILD MEMBER n` ต้องสร้าง)

> ไฟล์ที่เป็นเจ้าของ คนอื่นห้ามแก้ตรงๆ ให้เปิด Pull Request ถึงเจ้าของ · Git: Feature Branch ต่อคน, `main` ผ่านเทสต์เท่านั้น

### Member 1 — Factorial & Arithmetic · ตัวตรวจ ISA · เอกสาร
**ไฟล์:** `programs/factorial.asm` (ภาคผนวก A.1 + คอมเมนต์ Register Usage) · `tests/golden_hex.json` (ตารางข้อ 7 ที่ยืนยันกับ MARS/QtSpim แล้ว) · `tests/test_factorial.py` · `docs/REGISTER_CONVENTION.md` · `docs/ISA.md` (ตาราง Executable/Unsupported + ความหมายแต่ละคำสั่ง + ตัวอย่าง Encode) · `docs/FLOWCHARTS/factorial.md` (Mermaid flowchart) · `README.md` (ติดตั้ง/รัน/ตัวอย่าง/ข้อจำกัด) · `requirements.txt` (`matplotlib`, `pytest`)
**`test_factorial.py`:** (1) รัน `programs/factorial.asm` ผ่าน `tools/refsim.py` เทียบ 0!..12! และ 13/−1→`$v1=3` (ทำงานได้ตั้งแต่วันแรก) (2) เมื่อ Engine พร้อม รันผ่าน `integration.runner.run_asm` ตรวจ `5!`=118 คำสั่ง `12!`=496 (3) `fact` ไม่แก้ `$a0`/`$s*`/`$sp`
**พึ่งพา:** ไม่ต้องรอใคร (ใช้ refsim ก่อน) · **ส่งต่อ:** `fact` ให้ Member 2 · golden_hex ให้ Member 3 · **ผ่านเมื่อ:** ทดสอบผ่านบน refsim และ Engine, golden ตรงกับ MARS, README รันตามได้จริง

### Member 2 — nCr, Reference, Benchmark
**ไฟล์:** `programs/ncr_factorial.asm` · `programs/nck_optimized.asm` (ภาคผนวก A.2–A.3) · `reference/__init__.py`, `reference/reference.py` · `tools/refsim.py` (ภาคผนวก C) · `integration/runner.py` · `integration/selftest.py` · `tests/test_combination.py` · `tests/test_programs_refsim.py` · `docs/FLOWCHARTS/ncr.md`, `docs/ALGORITHMS.md` (เปรียบเทียบ 2 วิธีและข้อสังเกตเรื่อง overflow)
**`selftest.py`:** ฟังก์ชัน `run_selftest() -> bool` อ่าน Acceptance Table (ข้อ 9.3) + ผลลัพธ์ จากนั้นรันผ่าน `run_asm` เทียบทั้ง**ผลลัพธ์และจำนวนคำสั่ง**แล้วพิมพ์ PASS/FAIL ต่อแถว
**`test_programs_refsim.py`:** ตรวจทุกคู่ (n, r) ของทุกโปรแกรมบน refsim (ข้อ 9.2) + ตรวจว่าบล็อก `fact` เหมือนกันทั้งสองไฟล์ + Optimized: n ≤ 17 ไม่ trap
**พึ่งพา:** `fact` จาก Member 1 (มีใน seed แล้ว) · Engine+Assembler (Member 3) สำหรับ `runner`/`selftest` · **ผ่านเมื่อ:** ทุกเคสในข้อ 9.4 ผ่าน และ Acceptance Table ตรงเป๊ะบน Engine จริง

### Member 3 — CPU Engine, ISA, Assembler (Critical Path)
**ไฟล์:** `simulator/__init__.py`, `contract.py` (ข้อ 5), `memory.py`, `isa.py`, `assembler.py`, `cpu.py` · `references/original_cpuSimV7/` (สำเนาไฟล์อาจารย์ ห้ามแก้) · `tests/test_memory.py`, `test_isa.py`, `test_assembler.py`, `test_cpu.py`, `test_regression_original.py` · `conftest.py` ว่างที่ root
**ลำดับส่งมอบ (สำคัญ เพราะทุกคนรอ):**
1. **Engine v0.1** (เร็วที่สุด): `contract.py`, Assembler 2 ผ่านพร้อม label และชื่อ register, ADD/ADDI/SUB/SLT/SLTI/BEQ/BNE/J/JAL/JR/LW/SW/HALT, `load/step/run/get_state/reset`, overflow trap, Max Steps — **เกณฑ์ผ่าน:** `run_asm("programs/factorial.asm", 5)` ได้ `$v0=120` และ `instr=118` · `ncr_factorial` 5C2 ได้ 387 · `nck_optimized` 5C2 ได้ 127
2. เติมคำสั่งที่เหลือ (AND/OR/ANDI/ORI/LUI/SLTU/SLTIU/ADDU/ADDIU/SUBU, SLL/SRL/NOR ถ้าทำ) พร้อมเทสต์ทีละคำสั่ง
3. Encode R/I/J ครบ + `decode_word` + เทียบ `golden_hex.json` ทุกตัว
4. Trace ring buffer, counters ครบ, `alu_text`, `reg_changes`, `mem_reads/writes`, ปรับ fast path ให้ ≥ 300,000 คำสั่ง/วินาที (ใช้ dispatch table, ตัวแปรท้องถิ่น, ไม่สร้างออบเจ็กต์ต่อคำสั่งใน `run(record_trace=False)`)
5. `test_regression_original.py`: รัน `instructions.txt` เดิมแล้วเทียบ register สุดท้ายกับค่าอ้างอิงจากการรัน cpuSimV7 ต้นฉบับ
**`test_cpu.py` ต้องมี:** ทุกคำสั่ง Executable อย่างน้อย 1 เทสต์ · `$zero` เขียนไม่ได้ · overflow trap (`0x7fffffff + 1`) · ADDU wrap · SLTI/SLTIU ไม่แก้ rs · branch ไปหน้า/ถอยหลัง · JAL/JR (ค่า `$ra`) · LW/SW align/นอกช่วง (BAD_MEMORY) · Unknown opcode · MAX_STEPS (loop ไม่จบ) · `step()` ทำ 1 คำสั่งพอดี · `reset()` คืนค่า `init_regs` · `len(completed trace) == counters["instr"]`
**`test_assembler.py`:** label (ข้างหน้า/ข้างหลัง) · label ซ้ำ/ไม่พบ · immediate เกินช่วง · ชื่อ register ทั้ง 2 แบบ · Unsupported opcode · ไม่มี `.ORG` ใช้ `TEXT_BASE` · `entry` = `main` ถ้ามี
**ผ่านเมื่อ:** Acceptance Table ตรงเป๊ะทุกแถว, golden_hex ผ่านทั้งหมด, regression ผ่าน

### Member 4 — GUI, Visualization, Controller, main.py
**ไฟล์:** `main.py` · `integration/__init__.py`, `integration/controller.py` · `interface/__init__.py`, `gui.py`, `cpu_visualizer.py`, `performance_chart.py`, `fake_cpu.py` · `tests/test_integration.py`
**`fake_cpu.py`:** `FakeController` เมธอดเหมือน `Controller` ทุกตัว คืน `ViewState` ที่สร้างจากสคริปต์ตายตัว (เช่น 5! ทีละ step) เพื่อให้ทำ GUI ขนานกับ Member 3 ได้ **ห้ามถูกใช้ในการรันจริง** (`App` ใช้ `Controller` เสมอ ยกเว้นส่งพารามิเตอร์ทดสอบ)
**`controller.py`:** ทำตามลายเซ็นข้อ 6 · `load` = `assemble_file` + `CPU.load(init_regs={4:n,5:r})` · `run` ปรับความเร็วด้วย `steps_per_tick`/`delay_ms` (โหมดช้าเรียก `step()` เพื่อเก็บ trace รายคำสั่ง, ตั้งแต่ `steps_per_tick > 50` ใช้ `cpu.run(stop_after=k)` แล้วตั้ง `ViewState.turbo=True`) · เมื่อ CPU จบ: ตั้ง `result` จาก `$v0` และ `prog_status` จาก `$v1` และ**ตรวจกับ `reference` แล้วใส่ข้อความ ✔/✘ ใน `message`** (ใช้เพื่อตรวจเท่านั้น) · `validate_input`: ข้อความไทยสำหรับ ว่าง / ไม่ใช่จำนวนเต็ม / ติดลบ / r > n / เกิน `n_max` ของโปรแกรมที่เลือก · `compare`/`compare_async`: ตรวจว่าผลของทุกวิธี**ตรงกันและตรงกับ reference** ก่อนคืนข้อมูล ถ้าไม่ตรง ให้ `matches_reference=False` และ GUI ต้องไม่พล็อตแถวนั้น
**`test_integration.py`:** `Controller` กับ `scheduler=None`: validate_input ทุกกรณีผิด · load→step ×N→finished→result ถูก · run จนจบ · pause แล้วสถานะไม่หาย · reset กลับมา state หลัง load · `run_headless` ตรง Acceptance Table · overflow case (26,13) ได้ `mode='error'` และข้อความ Overflow · import rule (ข้อ 4) ตรวจด้วยการ scan `import` ในไฟล์
**พึ่งพา:** Engine v0.1 (ก่อนหน้านั้นใช้ `FakeController`) · **ผ่านเมื่อ:** สาธิตตามข้อ 14 ได้จบ

---

## 11. GUI (Member 4) — รายละเอียด

**เค้าโครงหน้าต่างเดียว** (ปรับขนาดได้):
```
┌ Input ──────────────┬ Control ───────────────────────┬ Output ─────────────────────┐
│ ○Factorial ○nCr     │ [โหลด] [Step] [Run] [Pause]    │ $v0 = 10 (0x0000000a)  ✔    │
│ วิธี: ○Optimized     │ [Reset]  ความเร็ว ──●─── Turbo  │ สถานะ: HALTED · $v1=0       │
│       ○Factorial-Based│ รูปแบบเลข: ○Dec ○Hex ○Bin      │ Instruction: 127            │
│ n [  ] r [  ]       │                                │                             │
├ Instruction ────────┼ CPU Diagram ───────────────────┼ Registers (32) ─────────────┤
│ addr  hex8  assembly│ PC → InstrMem → Decoder →       │ $zero..$ra (เปลี่ยน=ไฮไลต์)  │
│ ▶ บรรทัดปัจจุบัน     │ RegFile → ALU → WriteBack/PC    │ PC ก่อน → หลัง              │
│ ฟิลด์: op rs rt ... │                                │                             │
├ Memory ─────────────┼ Trace (เลื่อนย้อนหลัง) ─────────┼ Performance ────────────────┤
│ Text | Data | Stack │ # PC asm hex Δreg mem alu br    │ ตาราง + กราฟ Matplotlib      │
└─────────────────────┴────────────────────────────────┴─────────────────────────────┘
```
- ปุ่ม Step/Run/Pause/Reset ใช้ไม่ได้จนกว่าจะ "โหลด" สำเร็จ · Input ผิด → แสดงข้อความจาก `validate_input` ใต้ช่อง ไม่เปิด dialog
- **Instruction Panel:** ตาราง addr / Hex 8 หลัก / assembly, ไฮไลต์คำสั่งที่ PC ชี้, ใต้ตารางแสดง Binary 32-bit แยกฟิลด์ (opcode|rs|rt|rd|shamt|funct หรือ opcode|rs|rt|imm หรือ opcode|target) ตาม `Instr.kind`; คำสั่ง `SIM` (HALT) แสดง `—` และข้อความ "คำสั่งเฉพาะของ Simulator"
- **Registers:** ไฮไลต์ตัวที่เปลี่ยนใน step ล่าสุดจาก `StepResult.reg_changes` พร้อมค่าก่อน→หลัง
- **Memory:** ตาราง Address/Value (word) 3 มุมมอง Text/Data/Stack ไฮไลต์ address ใน `mem_reads` (สีหนึ่ง) และ `mem_writes` (อีกสี) ของ step ล่าสุด และข้อความแจ้ง Byte order/Alignment
- **Trace:** แสดง `trace_tail` มี scrollbar ย้อนหลังได้ วาดเฉพาะแถวที่มองเห็น; ปุ่ม Export CSV (SHOULD); ใน Turbo แสดงป้าย "Turbo: ไม่บันทึกรายคำสั่ง (counter ยังถูกต้อง)"
- **ความเร็ว:** ระดับ 1, 5, 20, 100, 1000, Turbo (20,000/ครั้ง) → `steps_per_tick`; ต้องไม่ค้างแม้รัน 3.3 ล้านคำสั่ง (แสดงแถบ progress จาก `counters["instr"]`)
- **CPU Diagram (SHOULD):** บล็อก PC, Instruction Memory, Decoder, Register File, ALU, Data Memory, Mux/Write-back ไฮไลต์ตาม `StepResult` จริงเท่านั้น: ALU เมื่อ `alu_text`≠None · Data Memory เมื่อ `mem_reads/writes` · เส้น PC เมื่อ `branch_taken` หรือ J/JAL/JR · Register write เมื่อ `reg_changes` ไม่ว่าง ห้ามมี animation ที่ไม่เกี่ยวกับคำสั่ง และห้ามเขียนว่าเป็น Clock Cycle จริง
- **Output:** แสดงผลลัพธ์ `$v0`, สถานะ CPU, `$v1` ในภาษามนุษย์ (3 = "Input ไม่ถูกต้อง", 2 = "หารด้วยศูนย์"), ✔/✘ จาก reference, และข้อความ `OVERFLOW`/`MAX_STEPS`/`BAD_MEMORY` ที่บอกว่าเกิดที่คำสั่งใด
- **Performance:** ปุ่ม "เปรียบเทียบ" รัน `compare_async` ชุดเริ่มต้น (5,2) (6,3) (8,4) (10,5) พร้อมช่อง "รวม 12C6 (ช้า ~3.3 ล้านคำสั่ง)"; ตารางแสดง instr/branch/arith/mem_read/mem_write ของแต่ละวิธี; กราฟ Bar (เลือก metric) **มีสวิตช์ log scale เปิดเป็นค่าเริ่มต้น** (ค่าต่างกันหลายระดับ); มีข้อความกำกับว่า "Dynamic Instruction Count ไม่ใช่เวลาหรือ Clock Cycles" และ "ไม่ใช่ผลของ Hardware จริง"

---

## 12. การทดสอบและการรวมงาน

**Integration Checklist (ผ่านทุกข้อก่อน merge เข้า `main` และก่อนส่ง):**
- [ ] `python -m pytest` ผ่านทั้งหมด · [ ] `python main.py --selftest` PASS ทุกแถวของข้อ 9.3
- [ ] `python main.py` เปิด GUI ได้ ทำ Demo (ข้อ 14) จบ
- [ ] ไม่มีไฟล์นอก `reference/`, `tests/`, `tools/` ที่ import `math.factorial/comb` หรือ `reference` เพื่อคำนวณคำตอบ
- [ ] กฎ import (ข้อ 4) · [ ] ไม่มี Mock/FakeController ในเส้นทางรันจริง · [ ] `contract.py` ตรงกับข้อ 5
- [ ] GUI ไม่ค้างตอน Run/Turbo · Pause แล้ว Step/Run ต่อได้ ค่า CPU ไม่หาย · Reset คืนสถานะหลังโหลด
- [ ] ทุกเคส error แสดงข้อความไทยชัดเจน (Input ผิด, Overflow, Max Steps, Bad Memory)
- [ ] ทุกไฟล์มีป้าย ORIGINAL/MODIFIED/NEW · [ ] เอกสารระบุข้อจำกัด (ไม่ใช่ Pipeline, ไม่มี Timing Model, Execute จาก parsed Instr)

**กติการ่วม:** ห้ามเปลี่ยนชื่อ API/Register Convention/Contract โดยไม่แจ้งทั้ง 4 คน · เพิ่มคำสั่งใหม่ต้องแก้ ISA + Assembler + Engine + Tests + `docs/ISA.md` ใน PR เดียว · ห้าม merge ฟีเจอร์ก่อนเทสต์ผ่าน

---

## 13. Roadmap (ใช้กับโหมด `TEACH`) — MVP ก่อน

| Phase | เนื้อหา | ผู้ทำ | Gate |
|---|---|---|---|
| 1 | ติดตั้ง Python 3.10+/VS Code/Git, สร้างโครงสร้างและ repo, วาง `contract.py` | ทุกคน | ทุกคน clone แล้ว `python -m pytest` รันได้ |
| 2 | นำเข้า cpuSimV7 เดิม ยืนยันตารางบัค (ข้อ 3) | M3 (+ทุกคนดู) | ยืนยันบัค 1–11 ได้ด้วยการรันเอง |
| 3 | Assembler + label + **Engine v0.1** | M3 · M1/M2 ตรวจ asm ด้วย refsim ขนาน · M4 ทำ FakeController+GUI | `factorial` 5! = 120, 118 คำสั่ง |
| 4 | Factorial บน Simulator + Step ดูทีละคำสั่ง (**MVP**) | M1, M3 | ผ่าน `test_factorial.py` บน Engine จริง |
| 5 | JAL/JR/Stack, Subroutine `fact` | M3, M1 | `$s*`/`$sp` ถูกคืนค่า |
| 6 | nCr Factorial-Based | M2 | 5C2=387 คำสั่ง, 10C5=252 |
| 7 | Optimized nCk | M2 | ตรงทุก (n, r) n ≤ 17; trap ตามข้อ 9.4 |
| 8 | GUI + Controller Run/Pause/Step/Reset | M4 | ไม่ค้างตอน Run |
| 9 | Visualization, Registers, Memory, Trace, Machine Code | M4, M3 (ข้อมูล `StepResult`) | ไฮไลต์ตรงกับ `StepResult` |
| 10 | Counters + Performance + กราฟ | M2, M4 | ตัวเลขตรงข้อ 9.3 |
| 11 | รวมระบบ (`BUILD INTEGRATION`) | ทุกคน | Checklist ข้อ 12 ผ่านหมด |
| 12 | README/รายงาน/Flowchart/Architecture Diagram/ผลทดสอบ/ซ้อม Demo | ทุกคน | อธิบายส่วนของตนได้ |

---

## 14. Demo และสิ่งที่ต้องส่ง

**Demo:** `python main.py` → Factorial n=5 กด Step หลายครั้งให้เห็น Registers/PC/ALU/Machine Code → Run ได้ 120 (118 คำสั่ง) → nCr 5C2 วิธี Factorial-Based เห็นการเรียก `fact` ผ่าน JAL/JR และ stack (Memory Panel) ได้ 10 (387 คำสั่ง) → เปลี่ยนเป็น Optimized ด้วย Input เดิมได้ 10 (127 คำสั่ง) → กด "เปรียบเทียบ" ดูกราฟ log scale → ลอง 26C13 ให้เห็น OVERFLOW ที่รายงานชัดเจน และอธิบายว่าเพราะค่ากลาง n!/b! เกิน 32-bit
**ส่ง:** Source Code, `programs/*.asm`, `requirements.txt`, README, Tests + ผลรัน, Flowcharts, System Architecture Diagram, CPU Execution Diagram, Register Convention, Instruction Set Documentation, ตารางผลเปรียบเทียบ, ตารางสรุปโค้ด ORIGINAL/MODIFIED/NEW และรายงาน/สไลด์ตามที่อาจารย์กำหนด

---

## 15. หมายเหตุสำหรับ AI

- ถ้าผู้ใช้ไม่ได้พิมพ์คำสั่งในข้อ 0 ให้ถามเดียวว่า "คุณคือ Member ไหน และต้องการโหมดอะไร" แล้วรอ
- ถ้าไฟล์ในข้อ 5–6/ภาคผนวกขัดกันเอง ให้แจ้งผู้ใช้ก่อน ไม่เดาเอง
- สอนทุกครั้งที่ใช้ `TEACH`: วัตถุประสงค์ → ใครทำอะไร → ไฟล์ → โค้ด + คำอธิบายหลักการ Computer Architecture (Registers, PC, ALU, ISA, Instruction Format, Branch/Jump, Subroutine, Stack, Memory) → วิธีรันใน VS Code → ผลที่คาดหวัง → ปัญหาที่พบบ่อย → เกณฑ์ผ่าน → งานที่คนอื่นทำขนานได้ แล้วหยุดรอผล
- เป้าหมายสูงสุด: สมาชิกทุกคนเข้าใจโค้ดของตนเอง เข้าใจการเชื่อมต่อของระบบ และอธิบายการทำงานของ MIPS CPU Simulator ได้ถูกต้องในวันนำเสนอ

---

# ภาคผนวก (ซอร์สที่ตรวจแล้ว — คัดลอกไปวางตามที่อยู่ที่ระบุ)

## A.1 `programs/factorial.asm`
```asm
# factorial.asm  -- n! by repeated addition (no MUL)
# IN : $a0 = n (0..12)      OUT: $v0 = n!   $v1 = 0 ok | 3 invalid input
# Subroutine fact: leaf, uses $t0-$t3, preserves $a0, $s*, $sp
.ORG 0x2000
main:
    ADD  $v1 $zero $zero
    SLT  $t0 $a0 $zero          # n < 0 ?
    BNE  $t0 $zero bad_input
    SLTI $t0 $a0 13             # n < 13 ?
    BEQ  $t0 $zero bad_input
    JAL  fact
    HALT
bad_input:
    ADDI $v1 $zero 3
    ADD  $v0 $zero $zero
    HALT

fact:                           # $a0=n -> $v0=n!
    ADDI $v0 $zero 1            # acc = 1
    ADDI $t0 $zero 2            # i = 2
fact_outer:
    SLT  $t1 $a0 $t0            # n < i ?
    BNE  $t1 $zero fact_done
    ADD  $t2 $zero $zero        # temp = 0
    ADD  $t3 $zero $zero        # j = 0
fact_inner:
    SLT  $t1 $t3 $t0            # j < i ?
    BEQ  $t1 $zero fact_inner_end
    ADD  $t2 $t2 $v0            # temp += acc
    ADDI $t3 $t3 1
    J    fact_inner
fact_inner_end:
    ADD  $v0 $zero $t2          # acc = temp
    ADDI $t0 $t0 1
    J    fact_outer
fact_done:
    JR   $ra
```

## A.2 `programs/ncr_factorial.asm`
```asm
# ncr_factorial.asm -- C(n,r) = n! / (r! (n-r)!)  calls fact 3 times, divides by repeated addition
# IN : $a0 = n (0..12), $a1 = r (0..n)
# OUT: $v0 = C(n,r)   $v1 = 0 ok | 2 divide by zero | 3 invalid input
.ORG 0x2000
main:
    JAL  ncr_fact
    HALT

ncr_fact:
    ADD  $v1 $zero $zero
    SLT  $t0 $a0 $zero
    BNE  $t0 $zero ncr_bad
    SLT  $t0 $a1 $zero
    BNE  $t0 $zero ncr_bad
    SLT  $t0 $a0 $a1            # n < r ?
    BNE  $t0 $zero ncr_bad
    SLTI $t0 $a0 13             # n <= 12 ?
    BEQ  $t0 $zero ncr_bad
    ADDI $sp $sp -32            # frame: save $ra,$s0-$s5
    SW   $ra 28($sp)
    SW   $s0 24($sp)
    SW   $s1 20($sp)
    SW   $s2 16($sp)
    SW   $s3 12($sp)
    SW   $s4 8($sp)
    SW   $s5 4($sp)
    ADD  $s0 $zero $a0          # s0 = n
    ADD  $s1 $zero $a1          # s1 = r
    SUB  $s2 $s0 $s1            # s2 = n-r
    ADD  $a0 $zero $s0
    JAL  fact
    ADD  $s3 $zero $v0          # s3 = n!
    ADD  $a0 $zero $s1
    JAL  fact
    ADD  $s4 $zero $v0          # s4 = r!
    ADD  $a0 $zero $s2
    JAL  fact
    ADD  $s5 $zero $v0          # s5 = (n-r)!
    SLT  $t0 $s4 $s5            # make s4 the larger factorial (smaller quotient 1st)
    BEQ  $t0 $zero ncr_noswap
    ADD  $t1 $zero $s4
    ADD  $s4 $zero $s5
    ADD  $s5 $zero $t1
ncr_noswap:
    ADD  $a0 $zero $s3
    ADD  $a1 $zero $s4
    JAL  div_add                # q1 = n! / larger
    BNE  $v1 $zero ncr_exit
    ADD  $a0 $zero $v0
    ADD  $a1 $zero $s5
    JAL  div_add                # q2 = q1 / smaller
ncr_exit:
    LW   $s5 4($sp)
    LW   $s4 8($sp)
    LW   $s3 12($sp)
    LW   $s2 16($sp)
    LW   $s1 20($sp)
    LW   $s0 24($sp)
    LW   $ra 28($sp)
    ADDI $sp $sp 32
    JR   $ra
ncr_bad:
    ADDI $v1 $zero 3
    ADD  $v0 $zero $zero
    JR   $ra

div_add:                        # $a0 / $a1 by repeated addition (exact division assumed)
    BNE  $a1 $zero div_ok
    ADDI $v1 $zero 2
    ADD  $v0 $zero $zero
    JR   $ra
div_ok:
    ADD  $t0 $zero $a1          # tmm = divisor
    ADDI $v0 $zero 1            # q = 1
div_loop:
    SLT  $t1 $t0 $a0            # tmm < dividend ?
    BEQ  $t1 $zero div_done
    ADD  $t0 $t0 $a1
    ADDI $v0 $v0 1
    J    div_loop
div_done:
    JR   $ra

fact:                           # same routine as factorial.asm (keep identical!)
    ADDI $v0 $zero 1
    ADDI $t0 $zero 2
fact_outer:
    SLT  $t1 $a0 $t0
    BNE  $t1 $zero fact_done
    ADD  $t2 $zero $zero
    ADD  $t3 $zero $zero
fact_inner:
    SLT  $t1 $t3 $t0
    BEQ  $t1 $zero fact_inner_end
    ADD  $t2 $t2 $v0
    ADDI $t3 $t3 1
    J    fact_inner
fact_inner_end:
    ADD  $v0 $zero $t2
    ADDI $t0 $t0 1
    J    fact_outer
fact_done:
    JR   $ra
```

## A.3 `programs/nck_optimized.asm`
```asm
# nck_optimized.asm -- C(n,k) without MUL/DIV, from teacher's nCkbound.py (FIXED for k=0)
# IN : $a0 = n (0..26), $a1 = k (0..n)
# OUT: $v0 = C(n,k)   $v1 = 0 ok | 3 invalid input
# Engine traps OVERFLOW if an intermediate n!/b! exceeds signed 32-bit (see docs)
# a = min(k,n-k) -> $t2 ; b = max(k,n-k) -> $t3
.ORG 0x2000
main:
    JAL  nck_opt
    HALT

nck_opt:
    ADD  $v1 $zero $zero
    SLT  $t0 $a0 $zero
    BNE  $t0 $zero nck_bad
    SLT  $t0 $a1 $zero
    BNE  $t0 $zero nck_bad
    SLT  $t0 $a0 $a1            # n < k ?
    BNE  $t0 $zero nck_bad
    SLTI $t0 $a0 27             # n <= 26 ?
    BEQ  $t0 $zero nck_bad
    SUB  $t0 $a0 $a1            # n_k = n-k
    SLT  $t1 $a1 $t0            # k < n_k ?
    BEQ  $t1 $zero nck_k_ge
    ADD  $t2 $zero $a1          # a = k
    ADD  $t3 $zero $t0          # b = n-k
    J    nck_ab_done
nck_k_ge:
    ADD  $t2 $zero $t0          # a = n-k
    ADD  $t3 $zero $a1          # b = k
nck_ab_done:
    BNE  $t2 $zero nck_start    # a == 0  (k==0 or k==n) -> result 1   [FIX k=0]
    ADDI $v0 $zero 1
    JR   $ra
nck_start:
    ADD  $v0 $zero $a0          # nCk = n
    ADDI $t4 $a0 -1             # i = n-1
nck_prod_outer:                 # for i = n-1 down to b+1 : nCk = nCk * i (by addition)
    SLT  $t5 $t3 $t4            # b < i ?
    BEQ  $t5 $zero nck_prod_done
    ADD  $t6 $zero $zero        # tmp = 0
    ADD  $t7 $zero $zero        # j = 0
nck_prod_inner:
    SLT  $t5 $t7 $t4            # j < i ?
    BEQ  $t5 $zero nck_prod_inner_end
    ADD  $t6 $t6 $v0            # tmp += nCk
    ADDI $t7 $t7 1
    J    nck_prod_inner
nck_prod_inner_end:
    ADD  $v0 $zero $t6
    ADDI $t4 $t4 -1
    J    nck_prod_outer
nck_prod_done:
    ADDI $t8 $zero 1            # faca = 1  (a!)
    ADDI $t4 $zero 2            # i = 2
nck_fa_outer:
    SLT  $t5 $t2 $t4            # a < i ?
    BNE  $t5 $zero nck_fa_done
    ADD  $t6 $zero $zero
    ADD  $t7 $zero $zero
nck_fa_inner:
    SLT  $t5 $t7 $t4
    BEQ  $t5 $zero nck_fa_inner_end
    ADD  $t6 $t6 $t8
    ADDI $t7 $t7 1
    J    nck_fa_inner
nck_fa_inner_end:
    ADD  $t8 $zero $t6
    ADDI $t4 $t4 1
    J    nck_fa_outer
nck_fa_done:
    SLTI $t5 $t8 2              # faca < 2 ?  (faca == 1 -> no division needed)
    BNE  $t5 $zero nck_finish
    ADD  $t9 $zero $t8          # tmm = faca
    ADDI $t4 $zero 1            # result = 1
nck_div_loop:
    SLT  $t5 $t9 $v0            # tmm < nCk ?
    BEQ  $t5 $zero nck_div_done
    ADD  $t9 $t9 $t8
    ADDI $t4 $t4 1
    J    nck_div_loop
nck_div_done:
    ADD  $v0 $zero $t4
nck_finish:
    JR   $ra
nck_bad:
    ADDI $v1 $zero 3
    ADD  $v0 $zero $zero
    JR   $ra
```

## B. อ้างอิง Contract
ภาคผนวก B คือไฟล์ `simulator/contract.py` ในข้อ 5 (ฉบับเดียวกัน ไม่ต้องวางซ้ำ)

## C. `tools/refsim.py` (ตัวแปลอิสระสำหรับตรวจ asm ก่อนมี Engine และใช้เทียบจำนวนคำสั่ง)
```python
"""Independent mini MIPS interpreter used ONLY to validate the seed .asm files (not cpuSimV7)."""
import re, math
REGS={'zero':0,'v0':2,'v1':3,'a0':4,'a1':5,'sp':29,'ra':31}
for i in range(8): REGS[f't{i}']=8+i; REGS[f's{i}']=16+i
REGS['t8']=24; REGS['t9']=25
def reg(s):
    s=s.lstrip('$'); return int(s) if s.isdigit() else REGS[s]
def s32(x): x&=0xffffffff; return x-(1<<32) if x>>31 else x
class Overflow(Exception): pass
def assemble(text):
    base=0x2000; lines=[]; labels={}; pc=None
    for raw in text.splitlines():
        l=raw.split('#')[0].strip()
        if not l: continue
        if l.startswith('.ORG'): base=int(l.split()[1],0); pc=base; continue
        if pc is None: pc=base
        m=re.match(r'^(\w+):\s*(.*)$',l)
        if m:
            labels[m.group(1)]=pc; l=m.group(2)
            if not l: continue
        lines.append((pc,l)); pc+=4
    return base,lines,labels
def run(text,a0,a1=0,maxsteps=50_000_000):
    base,lines,labels=assemble(text)
    prog={pc:l for pc,l in lines}
    R=[0]*32; R[4]=a0; R[5]=a1; R[29]=0x1FFFC
    mem={}; pc=base; steps=0; cnt={'branch':0,'mem_r':0,'mem_w':0,'call':0}
    while True:
        l=prog[pc]; p=l.replace(',',' ').split(); op=p[0].upper(); a=p[1:]
        steps+=1
        if steps>maxsteps: raise RuntimeError("max steps")
        npc=pc+4
        def chk(v):
            if not -2**31<=v<2**31: raise Overflow(f"{op} at {pc:#x}")
            return v
        if op=='ADD': R[reg(a[0])]=chk(R[reg(a[1])]+R[reg(a[2])])
        elif op=='SUB': R[reg(a[0])]=chk(R[reg(a[1])]-R[reg(a[2])])
        elif op=='SLT': R[reg(a[0])]=int(R[reg(a[1])]<R[reg(a[2])])
        elif op=='ADDI': R[reg(a[0])]=chk(R[reg(a[1])]+int(a[2],0))
        elif op=='SLTI': R[reg(a[0])]=int(R[reg(a[1])]<int(a[2],0))
        elif op in('BEQ','BNE'):
            cnt['branch']+=1
            eq=R[reg(a[0])]==R[reg(a[1])]
            if eq==(op=='BEQ'): npc=labels[a[2]]
        elif op=='J': npc=labels[a[0]]
        elif op=='JAL': R[31]=pc+4; npc=labels[a[0]]; cnt['call']+=1
        elif op=='JR': npc=R[reg(a[0])]
        elif op in('LW','SW'):
            off,b=re.match(r'(-?\w+)\((\$\w+)\)',a[1]).groups(); ad=R[reg(b)]+int(off,0)
            if op=='LW': R[reg(a[0])]=mem.get(ad,0); cnt['mem_r']+=1
            else: mem[ad]=R[reg(a[0])]; cnt['mem_w']+=1
        elif op=='HALT': break
        else: raise ValueError(op)
        R[0]=0; pc=npc
    return R[2],R[3],steps,cnt,R
```
