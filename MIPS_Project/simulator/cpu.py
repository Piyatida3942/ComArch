# MODIFIED from cpuSimV7 cpu.py
#   คงแนวคิดเดิม: วงจร fetch -> execute แยกตาม opcode, .ORG กำหนด address เริ่ม, validate(), debug()
#   แก้บัค/เพิ่ม:
#     #2  JAL/JR/SLL/SRL ไม่มีโค้ด execute -> ทำครบ (รวม AND/OR/NOR/SLT/SLTU/ADDU/SUBU/ANDI)
#     #6  ไม่มี Max Steps -> status MAX_STEPS
#     #7  ไม่ตรวจ overflow / validate() แปลง hex ผิด -> ADD/ADDI/SUB trap OVERFLOW, ...U wrap 32 บิต
#     #9  SLTI/SLTIU เขียนทับ rs -> ไม่แตะ rs
#     #10 memory 2 รูปแบบปนกัน -> byte-addressed ทั้งหมด (memory.py)
#     #11 PC เป็น index -> API ใช้ byte address เสมอ
#     เพิ่ม step()/run()/reset()/get_state(), trace ring buffer, counters, error เป็น status แทน exit()
#   Execute จากออบเจ็กต์ Instr ที่ assemble แล้ว (machine code ใน memory ใช้แสดงผล)
"""simulator/cpu.py -- Functional single-cycle MIPS CPU (ไม่มี pipeline / delay slot / timing model)"""
from __future__ import annotations

from collections import deque

from simulator.contract import (
    COUNTER_KEYS, CPUState, DEFAULT_MAX_STEPS, Instr, Program, REG_NAMES, REG_RA, REG_SP,
    RunResult, STACK_TOP, Status, StepResult, TRACE_LIMIT, s32, u32,
)
from simulator.memory import Memory, MemoryAccessError

_MIN32, _MAX32 = -(1 << 31), (1 << 31) - 1

# รหัสภายในของแต่ละคำสั่ง (ใช้เป็น index ของ counter และเลือกทางใน execute)
_OPS = ["ADD", "ADDI", "SLT", "SLTI", "BEQ", "BNE", "J", "JAL", "JR", "SUB", "LW", "SW",
        "ADDU", "ADDIU", "SUBU", "AND", "ANDI", "OR", "ORI", "NOR", "SLTU", "SLTIU",
        "LUI", "SLL", "SRL", "HALT"]
_OPID = {name: i for i, name in enumerate(_OPS)}
(ADD, ADDI, SLT, SLTI, BEQ, BNE, J, JAL, JR, SUB, LW, SW, ADDU, ADDIU, SUBU, AND, ANDI,
 OR, ORI, NOR, SLTU, SLTIU, LUI, SLL, SRL, HALT) = range(len(_OPS))
_ARITH = (ADD, ADDI, ADDU, ADDIU, SUB, SUBU, AND, ANDI, OR, ORI, NOR,
          SLT, SLTI, SLTU, SLTIU, LUI, SLL, SRL)
_SYM = {ADD: '+', ADDU: '+', ADDI: '+', ADDIU: '+', SUB: '-', SUBU: '-',
        AND: '&', ANDI: '&', OR: '|', ORI: '|', NOR: 'NOR', SLT: '<', SLTI: '<', SLTU: '<u', SLTIU: '<u'}


class _Trap(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status, self.message = status, message


class CPU:
    def __init__(self, memory: "Memory | None" = None, max_steps: int = DEFAULT_MAX_STEPS) -> None:
        self.memory = memory if memory is not None else Memory()
        self.max_steps = max_steps
        self._program: Program | None = None
        self._init_regs: dict[int, int] = {}
        self._r = [0] * 32
        self._pc = 0
        self._status = Status.READY
        self._error: str | None = None
        self._codes: list[tuple] = []
        self._opcount = [0] * len(_OPS)
        self._taken = 0
        self._trace: deque[StepResult] = deque(maxlen=TRACE_LIMIT)
        self._last: StepResult | None = None
        self._track = False
        self._mr: list[int] = []
        self._mw: list[tuple[int, int]] = []

    # ================================================================ load / reset
    def load(self, program: Program, init_regs: "dict[int, int] | None" = None) -> None:
        """เขียน machine code ลง memory ที่ text_base, regs = 0, $sp = STACK_TOP, ตั้ง init_regs, PC = entry"""
        self._program = program
        self._init_regs = dict(init_regs or {})
        self.memory.clear()
        for ins in program.instrs:
            if ins.hex8 is not None:
                self.memory.write_word(ins.addr, int(ins.hex8, 16))
        self._r = [0] * 32
        self._r[REG_SP] = STACK_TOP
        for idx, val in self._init_regs.items():
            self.set_reg(idx, val)
        self._pc = program.entry
        self._status = Status.READY
        self._error = None
        self._opcount = [0] * len(_OPS)
        self._taken = 0
        self._trace.clear()
        self._last = None
        # แปลง Instr เป็น tuple เพื่อให้ execute เร็ว: (opid, rd, rs, rt, imm, target, shamt)
        #   คำสั่งที่ไม่มีโค้ด execute ได้ opid = -1 -> BAD_OPCODE ตอนรัน
        self._codes = [(_OPID.get(i.op, -1), i.rd, i.rs, i.rt, i.imm, i.target, i.shamt) for i in program.instrs]

    def reset(self) -> None:
        """คืนสถานะ 'หลัง load' (รวม init_regs เดิม)"""
        if self._program is None:
            raise RuntimeError("no program loaded (call load() first)")
        self.load(self._program, self._init_regs)

    def set_reg(self, idx: int, value: int) -> None:
        if not 0 <= idx < 32:
            raise ValueError(f"register {idx} does not exist (must be 0..31)")
        if idx != 0:                        # $zero เป็น 0 เสมอ
            self._r[idx] = s32(value)

    # ================================================================ execute (1 คำสั่ง)
    def _execute(self, c: tuple, pc: int) -> int:
        """ทำคำสั่งเดียว คืน PC ถัดไป ; ผิดพลาด -> _Trap ก่อนเขียน register/memory ใดๆ"""
        op, rd, rs, rt, imm, target, sh = c
        R = self._r
        if op == ADD:
            v = R[rs] + R[rt]
            if v > _MAX32 or v < _MIN32:
                raise _Trap(Status.OVERFLOW, f"ADD overflow: {R[rs]} + {R[rt]} = {v} exceeds signed 32-bit")
            if rd: R[rd] = v
        elif op == ADDI:
            v = R[rs] + imm
            if v > _MAX32 or v < _MIN32:
                raise _Trap(Status.OVERFLOW, f"ADDI overflow: {R[rs]} + {imm} = {v} exceeds signed 32-bit")
            if rt: R[rt] = v
        elif op == SLT:
            if rd: R[rd] = 1 if R[rs] < R[rt] else 0
        elif op == BEQ:
            if R[rs] == R[rt]:
                self._taken += 1
                return pc + 4 + (imm << 2)
        elif op == BNE:
            if R[rs] != R[rt]:
                self._taken += 1
                return pc + 4 + (imm << 2)
        elif op == J:
            return target
        elif op == SLTI:
            if rt: R[rt] = 1 if R[rs] < imm else 0
        elif op == JAL:
            R[REG_RA] = pc + 4
            return target
        elif op == JR:
            return R[rs] & 0xFFFFFFFF
        elif op == SUB:
            v = R[rs] - R[rt]
            if v > _MAX32 or v < _MIN32:
                raise _Trap(Status.OVERFLOW, f"SUB overflow: {R[rs]} - {R[rt]} = {v} exceeds signed 32-bit")
            if rd: R[rd] = v
        elif op == LW:
            addr = R[rs] + imm
            try:
                v = self.memory.read_word(addr)
            except MemoryAccessError as e:
                raise _Trap(Status.BAD_MEMORY, f"LW: {e}") from None
            if self._track: self._mr.append(addr)
            if rt: R[rt] = v - 0x100000000 if v & 0x80000000 else v
        elif op == SW:
            addr = R[rs] + imm
            try:
                self.memory.write_word(addr, R[rt])
            except MemoryAccessError as e:
                raise _Trap(Status.BAD_MEMORY, f"SW: {e}") from None
            if self._track: self._mw.append((addr, R[rt] & 0xFFFFFFFF))
        elif op == HALT:
            self._status = Status.HALTED
            return pc                                   # PC ไม่เลื่อน
        elif op == ADDU:
            if rd: R[rd] = s32(R[rs] + R[rt])
        elif op == ADDIU:
            if rt: R[rt] = s32(R[rs] + imm)
        elif op == SUBU:
            if rd: R[rd] = s32(R[rs] - R[rt])
        elif op == AND:
            if rd: R[rd] = s32(R[rs] & R[rt])
        elif op == ANDI:
            if rt: R[rt] = R[rs] & imm                  # imm เป็น 0..65535 (zero-extend)
        elif op == OR:
            if rd: R[rd] = s32(R[rs] | R[rt])
        elif op == ORI:
            if rt: R[rt] = s32((R[rs] & 0xFFFFFFFF) | imm)
        elif op == NOR:
            if rd: R[rd] = s32(~(R[rs] | R[rt]))
        elif op == SLTU:
            if rd: R[rd] = 1 if (R[rs] & 0xFFFFFFFF) < (R[rt] & 0xFFFFFFFF) else 0
        elif op == SLTIU:                               # imm sign-extend แล้วเทียบแบบ unsigned (ตาม MIPS)
            if rt: R[rt] = 1 if (R[rs] & 0xFFFFFFFF) < (imm & 0xFFFFFFFF) else 0
        elif op == LUI:
            if rt: R[rt] = s32(imm << 16)
        elif op == SLL:
            if rd: R[rd] = s32(R[rt] << sh)
        elif op == SRL:
            if rd: R[rd] = s32((R[rt] & 0xFFFFFFFF) >> sh)
        else:
            raise _Trap(Status.BAD_OPCODE, "instruction has no execute implementation in this simulator")
        return pc + 4

    def _fetch_index(self, pc: int) -> int:
        """byte address -> index ของคำสั่ง ; นอกโปรแกรม -> -1"""
        off = pc - self._program.text_base
        if off < 0 or off & 3:
            return -1
        idx = off >> 2
        return idx if idx < len(self._codes) else -1

    # ================================================================ step
    def step(self) -> StepResult:
        """ทำ 1 คำสั่งพอดี บันทึกลง trace เสมอ ; ถ้า CPU หยุดแล้ว คืน StepResult เดิมโดยไม่ทำอะไร"""
        if self._program is None:
            raise RuntimeError("no program loaded (call load() first)")
        if self._status in Status.FINISHED or self._status in Status.ERRORS:
            return self._last
        self._status = Status.RUNNING
        pc = self._pc
        idx = self._fetch_index(pc)
        done = sum(self._opcount)
        ins = self._program.instrs[idx] if idx >= 0 else Instr(
            index=-1, addr=pc, line_no=0, raw="(no instruction at this address)", label=None, op="?", kind="SIM")

        if done >= self.max_steps:
            return self._trap(pc, ins, done, Status.MAX_STEPS,
                              f"reached {self.max_steps:,} instructions without HALT (infinite loop?)")
        if idx < 0:
            return self._trap(pc, ins, done, Status.BAD_PC,
                              f"PC = 0x{pc & 0xFFFFFFFF:08x} does not point to an instruction (missing HALT or bad JR target?)")

        c = self._codes[idx]
        before = list(self._r)
        taken_before = self._taken
        self._mr, self._mw, self._track = [], [], True
        try:
            new_pc = self._execute(c, pc)
        except _Trap as t:
            self._track = False
            return self._trap(pc, ins, done, t.status, t.message, before)
        self._track = False
        self._opcount[c[0]] += 1
        self._pc = new_pc

        changes = {i: (before[i], v) for i, v in enumerate(self._r) if v != before[i]}
        op = c[0]
        res = StepResult(
            step_no=done + 1, pc_before=pc, pc_after=new_pc, instr=ins, completed=True,
            reg_changes=changes, mem_reads=self._mr, mem_writes=self._mw,
            alu_text=self._alu_text(c, before, self._r),
            branch_taken=(self._taken != taken_before) if op in (BEQ, BNE) else None,
            status=self._status,
        )
        self._trace.append(res)
        self._last = res
        return res

    def _trap(self, pc, ins, done, status, message, before=None) -> StepResult:
        where = f" at 0x{pc & 0xFFFFFFFF:08x}"
        if ins.line_no:
            where += f" (line {ins.line_no}: {ins.raw})"
        self._status = status
        self._error = message + where
        alu = None
        if status == Status.OVERFLOW and before is not None:
            alu = self._alu_text(self._codes[ins.index], before, None)
        res = StepResult(step_no=done + 1, pc_before=pc, pc_after=pc, instr=ins, completed=False,
                         alu_text=alu, status=status, error=self._error)
        self._trace.append(res)
        self._last = res
        return res

    @staticmethod
    def _alu_text(c: tuple, before: list[int], after: "list[int] | None") -> "str | None":
        """ข้อความอธิบายสิ่งที่ ALU คำนวณ (None = คำสั่งนี้ไม่ใช้ ALU)"""
        op, rd, rs, rt, imm, target, sh = c
        a = before[rs]
        res = (lambda reg: "overflow" if after is None else str(after[reg]))
        if op in (ADD, ADDU, SUB, SUBU, AND, OR, NOR):
            return f"{a} {_SYM[op]} {before[rt]} = {res(rd)}"
        if op in (SLT, SLTU):
            return f"{a} {_SYM[op]} {before[rt]} -> {res(rd)}"
        if op in (ADDI, ADDIU, ANDI, ORI):
            return f"{a} {_SYM[op]} {imm} = {res(rt)}"
        if op in (SLTI, SLTIU):
            return f"{a} {_SYM[op]} {imm} -> {res(rt)}"
        if op == LUI:
            return f"{imm} << 16 = {res(rt)}"
        if op in (SLL, SRL):
            return f"{before[rt]} {'<<' if op == SLL else '>>'} {sh} = {res(rd)}"
        if op in (LW, SW):
            return f"address = 0x{u32(a):x} + {imm} = 0x{u32(a + imm):x}"
        if op in (BEQ, BNE):
            return f"{a} - {before[rt]} = {a - before[rt]} -> {'equal' if a == before[rt] else 'not equal'}"
        return None

    # ================================================================ run
    def run(self, stop_after: "int | None" = None, record_trace: bool = False) -> RunResult:
        """ทำงานจน HALT / error / ครบ stop_after (เรียกซ้ำเพื่อทำต่อได้)
        record_trace=False -> fast path ไม่สร้าง StepResult (counter ยังถูกต้อง)"""
        if self._program is None:
            raise RuntimeError("no program loaded (call load() first)")
        if self._status in Status.FINISHED or self._status in Status.ERRORS:
            return RunResult(True, self._status, 0, self.get_state())
        start = sum(self._opcount)
        limit = float('inf') if stop_after is None else stop_after

        if record_trace:
            n = 0
            while n < limit:
                r = self.step()
                if r.completed:
                    n += 1
                if self._status != Status.RUNNING:
                    break
        else:
            self._fast(limit, start)

        finished = self._status != Status.RUNNING and self._status != Status.READY
        return RunResult(finished, self._status, sum(self._opcount) - start, self.get_state())

    def _fast(self, limit, start: int) -> None:
        """ลูปเร็ว: ไม่สร้าง StepResult ; เจอเหตุผิดปกติเมื่อไร ส่งต่อให้ step() ทำคำสั่งนั้น (บันทึก trap ลง trace)"""
        self._status = Status.RUNNING
        budget = self.max_steps - start
        n_max = budget if limit > budget else int(limit)
        codes, base, ncode = self._codes, self._program.text_base, len(self._codes)
        execute, oc = self._execute, self._opcount
        pc = self._pc
        n = 0
        try:
            while n < n_max:
                off = pc - base
                idx = off >> 2
                if off < 0 or off & 3 or idx >= ncode:
                    break                               # BAD_PC -> ให้ step() รายงาน
                c = codes[idx]
                pc = execute(c, pc)
                oc[c[0]] += 1
                n += 1
                if c[0] == HALT:
                    break
        except _Trap:
            pass                                        # ไม่มีอะไรถูกเขียน -> step() จะทำซ้ำและบันทึก trap
        self._pc = pc
        if self._status == Status.HALTED:
            return
        if n < n_max or n >= budget:                    # ออกเพราะเหตุผิดปกติ หรือครบ max_steps
            self.step()

    # ================================================================ state
    def _counters(self) -> dict[str, int]:
        oc = self._opcount
        return {
            "instr": sum(oc),
            "branch": oc[BEQ] + oc[BNE],
            "branch_taken": self._taken,
            "arith": sum(oc[i] for i in _ARITH),
            "mem_read": oc[LW],
            "mem_write": oc[SW],
            "call": oc[JAL],
        }

    def get_state(self) -> CPUState:
        cnt = self._counters()
        assert tuple(cnt) == COUNTER_KEYS
        return CPUState(pc=self._pc, regs=list(self._r), memory=self.memory.snapshot(),
                        counters=cnt, status=self._status, error=self._error)

    @property
    def trace(self) -> list[StepResult]:
        return list(self._trace)

    # ================================================================ แนวคิดเดิมของอาจารย์
    def validate(self) -> list[str]:
        """ตรวจสถานะ CPU (เดิม: เตือนเมื่อ $0 ไม่เป็น 0 หรือค่าเกิน 32 บิต) คืนรายการปัญหา (ว่าง = ปกติ)"""
        problems = []
        if self._r[0] != 0:
            problems.append("register $zero must always be 0")
        problems += [f"${REG_NAMES[i]} = {v} exceeds signed 32-bit" for i, v in enumerate(self._r)
                     if not _MIN32 <= v <= _MAX32]
        return problems

    def debug(self, hex_format: bool = True) -> str:
        """แสดง register ทั้ง 32 ตัวแบบ debug() ของ cpuSimV7 (5 ตัวต่อแถว)"""
        lines = [f"PC = 0x{self._pc:08x}  status = {self._status}"]
        for row in range(0, 32, 5):
            cells = []
            for i in range(row, min(row + 5, 32)):
                v = self._r[i]
                cells.append(f"{u32(v):08x}" if hex_format else f"{v:>11}")
            lines.append(f"{row:>2}-{min(row + 4, 31):>2} " + "  ".join(f"{c:>10}" for c in cells))
        return "\n".join(lines)
