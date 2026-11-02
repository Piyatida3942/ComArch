# NEW (GUI only): แปลงข้อมูลของ StepResult / ViewState เป็นภาษาคน (English / ไทย)
# เป็นโค้ดล้วน (ไม่ import tkinter) จึงทดสอบได้โดยไม่ต้องเปิดหน้าต่าง
# อ่านข้อมูลจาก Engine อย่างเดียว ไม่เขียนกลับ ไม่เรียกฟังก์ชันคำนวณเอง
import re
from simulator.contract import REG_NAMES, s32

DEFAULT_LANG = 'en'

# ------------------------------------------------------------------ ข้อความทั้งหมด (en / th)
TX = {
    'en': {
        # op titles
        'op.ADD': 'Add', 'op.ADDU': 'Add', 'op.ADDI': 'Add a constant', 'op.ADDIU': 'Add a constant',
        'op.SUB': 'Subtract', 'op.SUBU': 'Subtract', 'op.AND': 'AND', 'op.OR': 'OR', 'op.NOR': 'NOR',
        'op.ANDI': 'AND a constant', 'op.ORI': 'OR a constant',
        'op.SLT': 'Compare (<)', 'op.SLTU': 'Compare (<)', 'op.SLTI': 'Compare (<)', 'op.SLTIU': 'Compare (<)',
        'op.LUI': 'Set upper half', 'op.SLL': 'Shift left', 'op.SRL': 'Shift right',
        'op.BEQ': 'Jump if equal', 'op.BNE': 'Jump if not equal', 'op.J': 'Jump',
        'op.JAL': 'Call function', 'op.JR': 'Return from function',
        'op.LW': 'Load from memory', 'op.SW': 'Store to memory', 'op.HALT': 'Stop',
        't.clear': 'Clear to 0', 't.copy': 'Copy value', 't.set': 'Set value', 't.inc': 'Increase', 't.dec': 'Decrease',
        'title.error': 'Error',
        # sentences
        's.generic': 'Run {op}.',
        's.cmp': 'Is {rs} ({a}) less than {rhs}? {truth}, so {dn} gets {v}.',
        'yes': 'Yes', 'no': 'No',
        's.clear': 'Clear {dn} to 0.',
        's.copy': 'Copy the value of {src} ({v}) into {dn}.',
        's.set': 'Set {dn} to {v}.',
        's.inc': '{dn} goes up by {n}: from {a} to {v}.',
        's.dec': '{dn} goes down by {n}: from {a} to {v}.',
        's.alu_r': 'Take {rs} ({a}) {sym} {rt} ({b}) = {v}, and store it in {dn}.',
        's.alu_i': 'Take {rs} ({a}) {sym} {b} = {v}, and store it in {dn}.',
        's.shift': 'Shift the bits of {rt} {way} by {n} place(s)',
        's.shift_to': ', giving {new}, stored in {dn}.',
        'left': 'left', 'right': 'right',
        's.lui': 'Put {imm} in the upper half of {d}',
        's.lui_to': ', giving {new}.',
        's.zero_note': ' (Writing to $zero does nothing.)',
        's.br_vals': 'Compare {rs} ({a}) with {rt} ({b}): they are {real}. This instruction jumps when they are {rule}',
        's.br_novals': 'Compare {rs} with {rt}. This instruction jumps when they are {rule}',
        'equal': 'equal', 'different': 'different',
        's.br_taken': ', so it jumps to {addr}.',
        's.br_not': ', so it does not jump and goes on to the next instruction.',
        's.j': 'Jump straight to the instruction at {addr}.',
        's.jal': 'Call the function at {addr}, and remember where to come back to ({back}) in $ra.',
        'next_instr': 'the next instruction',
        's.jr': 'Return from the function and continue at {addr}.',
        's.lw': 'Load the value{val} from memory address {addr} into {rt}.',
        's.lw_any': 'Load a value from memory into {rt}.',
        's.sw': 'Store the value {v} of {rt} into memory address {addr}.',
        's.sw_any': 'Store the value of {rt} into memory.',
        's.halt': 'Stop the program. The final answer is in $v0',
        's.halt_v': ' (it holds {v} right now).',
        's.halt_end': '.',
        # short results
        'r.jump': 'jump to {addr}', 'r.nojump': 'no jump', 'r.go': '→ {addr}', 'r.stop': 'stop',
        'r.read': 'loaded', 'r.fail': 'stopped',
        # errors
        'e.OVERFLOW': 'The result is too big for the CPU’s 32-bit numbers (about ±2.1 billion), so the CPU stopped instead of giving a wrong answer.',
        'e.BAD_MEMORY': 'The program tried to use a memory address that does not exist.',
        'e.BAD_OPCODE': 'The simulator met an instruction it does not support.',
        'e.BAD_PC': 'The program counter points to a place with no instruction.',
        'e.MAX_STEPS': 'The program ran for too many steps (it may be stuck in a loop).',
        'e.generic': 'Something went wrong while running.',
        # next-instruction hint
        'n.uses': 'uses {parts}', 'n.and': ' and ',
        # CPU stages (name, subtitle, short)
        'st.0': 'Program Counter', 'st.0.sub': 'Which instruction?', 'st.0.short': 'PC',
        'st.1': 'Fetch', 'st.1.sub': 'Get the instruction', 'st.1.short': 'Fetch',
        'st.2': 'Decode', 'st.2.sub': 'Understand it', 'st.2.short': 'Decode',
        'st.3': 'ALU', 'st.3.sub': 'Do the math', 'st.3.short': 'ALU',
        'st.4': 'Write-back', 'st.4.sub': 'Save the result', 'st.4.short': 'Write',
        'c.jump': 'jump', 'c.nojump': 'no jump', 'c.addr': 'address {addr}', 'c.skipped': 'not used',
        'k.R': 'R-type', 'k.I': 'I-type', 'k.J': 'J-type', 'k.SIM': 'special',
        # modes
        'm.idle': 'Not started', 'm.ready': 'Ready', 'm.running': 'Running', 'm.paused': 'Paused',
        'm.finished': 'Finished', 'm.error': 'Error',
        # calculate outcome
        'k.bad_range': 'These numbers are outside the range this program supports.',
        'k.div0': 'A division by zero happened.',
    },
    'th': {
        'op.ADD': 'บวก', 'op.ADDU': 'บวก', 'op.ADDI': 'บวกค่าคงที่', 'op.ADDIU': 'บวกค่าคงที่',
        'op.SUB': 'ลบ', 'op.SUBU': 'ลบ', 'op.AND': 'AND', 'op.OR': 'OR', 'op.NOR': 'NOR',
        'op.ANDI': 'AND ค่าคงที่', 'op.ORI': 'OR ค่าคงที่',
        'op.SLT': 'เปรียบเทียบ (<)', 'op.SLTU': 'เปรียบเทียบ (<)', 'op.SLTI': 'เปรียบเทียบ (<)', 'op.SLTIU': 'เปรียบเทียบ (<)',
        'op.LUI': 'ตั้งค่าครึ่งบน', 'op.SLL': 'เลื่อนบิตซ้าย', 'op.SRL': 'เลื่อนบิตขวา',
        'op.BEQ': 'ถ้าเท่ากัน กระโดด', 'op.BNE': 'ถ้าไม่เท่ากัน กระโดด', 'op.J': 'กระโดด',
        'op.JAL': 'เรียกฟังก์ชัน', 'op.JR': 'กลับจากฟังก์ชัน',
        'op.LW': 'อ่านหน่วยความจำ', 'op.SW': 'เขียนหน่วยความจำ', 'op.HALT': 'จบโปรแกรม',
        't.clear': 'ล้างค่าเป็น 0', 't.copy': 'คัดลอกค่า', 't.set': 'ตั้งค่า', 't.inc': 'เพิ่มค่า', 't.dec': 'ลดค่า',
        'title.error': 'เกิดข้อผิดพลาด',
        's.generic': 'ทำคำสั่ง {op}',
        's.cmp': 'เปรียบเทียบว่า {rs} ({a}) น้อยกว่า {rhs} หรือไม่ → {truth} จึงเก็บ {v} ไว้ใน {dn}',
        'yes': 'จริง', 'no': 'เท็จ',
        's.clear': 'ล้างค่า {dn} ให้เป็น 0',
        's.copy': 'คัดลอกค่า {src} ({v}) ไปใส่ใน {dn}',
        's.set': 'ตั้งค่า {dn} ให้เป็น {v}',
        's.inc': '{dn} เพิ่มขึ้น {n}: จาก {a} เป็น {v}',
        's.dec': '{dn} ลดลง {n}: จาก {a} เป็น {v}',
        's.alu_r': 'นำค่าใน {rs} ({a}) {sym} ค่าใน {rt} ({b}) ได้ {v} แล้วเก็บไว้ใน {dn}',
        's.alu_i': 'นำค่าใน {rs} ({a}) {sym} {b} ได้ {v} แล้วเก็บไว้ใน {dn}',
        's.shift': 'เลื่อนบิตของ {rt} ไป{way} {n} ตำแหน่ง',
        's.shift_to': ' ได้ {new} เก็บไว้ใน {dn}',
        'left': 'ซ้าย', 'right': 'ขวา',
        's.lui': 'ใส่ค่า {imm} ไว้ที่ครึ่งบนของ {d}',
        's.lui_to': ' ได้ {new}',
        's.zero_note': ' (เขียนลง $zero จึงไม่มีผล)',
        's.br_vals': 'เทียบ {rs} ({a}) กับ {rt} ({b}) → {real} (คำสั่งนี้กระโดดเมื่อ{rule})',
        's.br_novals': 'เทียบ {rs} กับ {rt} (คำสั่งนี้กระโดดเมื่อ{rule})',
        'equal': 'เท่ากัน', 'different': 'ไม่เท่ากัน',
        's.br_taken': ' จึงกระโดดไปที่ {addr}',
        's.br_not': ' จึงไม่กระโดด ทำคำสั่งถัดไปต่อ',
        's.j': 'กระโดดไปทำคำสั่งที่ {addr} ทันที',
        's.jal': 'เรียกฟังก์ชันที่ {addr} และจำที่อยู่ที่ต้องกลับมา ({back}) ไว้ใน $ra',
        'next_instr': 'คำสั่งถัดไป',
        's.jr': 'จบฟังก์ชัน กลับไปทำต่อที่ {addr}',
        's.lw': 'อ่านค่า{val} จากหน่วยความจำที่ {addr} มาใส่ใน {rt}',
        's.lw_any': 'อ่านค่าจากหน่วยความจำมาใส่ใน {rt}',
        's.sw': 'เก็บค่า {v} ของ {rt} ลงหน่วยความจำที่ {addr}',
        's.sw_any': 'เก็บค่าของ {rt} ลงหน่วยความจำ',
        's.halt': 'จบโปรแกรม ผลลัพธ์สุดท้ายอยู่ใน $v0',
        's.halt_v': ' (ตอนนี้เท่ากับ {v})',
        's.halt_end': '',
        'r.jump': 'กระโดดไป {addr}', 'r.nojump': 'ไม่กระโดด', 'r.go': '→ {addr}', 'r.stop': 'จบ',
        'r.read': 'อ่านแล้ว', 'r.fail': 'หยุดทำงาน',
        'e.OVERFLOW': 'ผลลัพธ์ใหญ่เกินช่วงตัวเลข 32 บิตของ CPU (ประมาณ ±2,147,483,647) CPU จึงหยุดเพื่อไม่ให้ได้คำตอบที่ผิด',
        'e.BAD_MEMORY': 'โปรแกรมพยายามเข้าถึงหน่วยความจำผิดตำแหน่ง',
        'e.BAD_OPCODE': 'พบคำสั่งที่ Simulator ยังไม่รองรับ',
        'e.BAD_PC': 'ตัวนับคำสั่ง (PC) ชี้ไปตำแหน่งที่ไม่มีคำสั่ง',
        'e.MAX_STEPS': 'ทำงานเกินจำนวนคำสั่งสูงสุดที่กำหนดไว้ (อาจวนลูปไม่จบ)',
        'e.generic': 'เกิดข้อผิดพลาดระหว่างทำงาน',
        'n.uses': 'ใช้ {parts}', 'n.and': ' และ ',
        'st.0': 'Program Counter', 'st.0.sub': 'คำสั่งไหนต่อไป', 'st.0.short': 'PC',
        'st.1': 'Fetch', 'st.1.sub': 'ดึงคำสั่ง', 'st.1.short': 'Fetch',
        'st.2': 'Decode', 'st.2.sub': 'แปลคำสั่ง', 'st.2.short': 'Decode',
        'st.3': 'ALU', 'st.3.sub': 'คำนวณ', 'st.3.short': 'ALU',
        'st.4': 'Write-back', 'st.4.sub': 'บันทึกผล', 'st.4.short': 'Write',
        'c.jump': 'กระโดด', 'c.nojump': 'ไม่กระโดด', 'c.addr': 'ที่อยู่ {addr}', 'c.skipped': 'ข้ามขั้นนี้',
        'k.R': 'R-type', 'k.I': 'I-type', 'k.J': 'J-type', 'k.SIM': 'พิเศษ',
        'm.idle': 'ยังไม่เริ่ม', 'm.ready': 'พร้อม', 'm.running': 'กำลังรัน', 'm.paused': 'หยุดชั่วคราว',
        'm.finished': 'เสร็จแล้ว', 'm.error': 'ผิดพลาด',
        'k.bad_range': 'ตัวเลขอยู่นอกช่วงที่โปรแกรมนี้รองรับ',
        'k.div0': 'เกิดการหารด้วยศูนย์',
    },
}


def tx(lang, key, **kw):
    s = TX.get(lang, TX['en']).get(key)
    if s is None:
        s = TX['en'][key]
    return s.format(**kw) if kw else s


# ------------------------------------------------------------------ ชื่อ / สัญลักษณ์
def rn(i):
    return '$' + REG_NAMES[i]


def hx(v):
    return f'0x{v & 0xFFFFFFFF:08X}'


def clean(raw):
    """ตัดช่องว่างซ้ำในข้อความคำสั่ง (ต้นฉบับ .asm จัดแนวด้วยช่องว่างหลายตัว)"""
    return ' '.join(str(raw).split())


def sign_pair(sym, b):
    """'+' กับเลขติดลบ -> '−' กับเลขบวก  (เช่น + -32  ->  − 32)"""
    if sym == '+' and b < 0:
        return '−', -b
    return sym, b


SYMBOL = {'ADD': '+', 'ADDU': '+', 'ADDI': '+', 'ADDIU': '+', 'SUB': '−', 'SUBU': '−',
          'AND': 'AND', 'ANDI': 'AND', 'OR': 'OR', 'ORI': 'OR', 'NOR': 'NOR',
          'SLT': '<', 'SLTU': '<', 'SLTI': '<', 'SLTIU': '<'}
R_DEST = {'ADD', 'ADDU', 'SUB', 'SUBU', 'AND', 'OR', 'NOR', 'SLT', 'SLTU', 'SLL', 'SRL'}   # เขียนลง rd
I_DEST = {'ADDI', 'ADDIU', 'ANDI', 'ORI', 'SLTI', 'SLTIU', 'LUI', 'LW'}                   # เขียนลง rt
BRANCH = {'BEQ', 'BNE'}
COMPARE = {'SLT', 'SLTU', 'SLTI', 'SLTIU'}
ALU_RE = re.compile(r'^(-?\d+) (\w+) (-?\d+) = (-?\d+)$')


def dest_reg(ins):
    if ins.op in R_DEST:
        return ins.rd
    if ins.op in I_DEST:
        return ins.rt
    if ins.op == 'JAL':
        return 31
    return None


def op_title(ins, lang=DEFAULT_LANG):
    """ชื่อที่คนทั่วไปเข้าใจ (แยกรูปแบบยอดนิยม เช่น คัดลอก/ตั้งค่า/เพิ่มค่า)"""
    op = ins.op
    if op in ('ADD', 'ADDU'):
        if ins.rs == 0 and ins.rt == 0:
            return tx(lang, 't.clear')
        if ins.rs == 0 or ins.rt == 0:
            return tx(lang, 't.copy')
    if op in ('ADDI', 'ADDIU'):
        if ins.rs == 0:
            return tx(lang, 't.set')
        if ins.rs == ins.rt and ins.imm > 0:
            return tx(lang, 't.inc')
        if ins.rs == ins.rt and ins.imm < 0:
            return tx(lang, 't.dec')
    key = 'op.' + op
    return tx(lang, key) if key in TX['en'] else op


def parse_alu(text):
    if not text:
        return None
    m = ALU_RE.match(text)
    if not m:
        return None
    return int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))


def _changes(step):
    return [(rn(i), old, new) for i, (old, new) in sorted(step.reg_changes.items())]


# ------------------------------------------------------------------ คำอธิบายรายขั้น
def explain_step(step, regs=None, lang=DEFAULT_LANG):
    """คืน dict: title, sentence, result, changes, tone
    regs = ค่า register หลังจบ step นี้ (ใส่ได้เฉพาะ step ล่าสุด ใช้แสดงค่าที่เปรียบเทียบในคำสั่ง branch)"""
    T = lambda k, **kw: tx(lang, k, **kw)                                  # noqa: E731
    ins = step.instr
    op = ins.op
    changes = _changes(step)
    title = op_title(ins, lang)
    alu = parse_alu(step.alu_text)

    if not step.completed:
        return dict(title=T('title.error'), tone='error', changes=[],
                    sentence=friendly_error(step.status, step.error, lang), result=T('r.fail'))

    tone, sentence, result = 'alu', T('s.generic', op=op), ''

    if op in R_DEST or (op in I_DEST and op not in ('LW', 'LUI')):
        d = dest_reg(ins)
        dn = rn(d) if d is not None else '?'
        if alu:
            a, _, b, v = alu
            if op in COMPARE:
                rhs = f'{rn(ins.rt)} ({b})' if op in ('SLT', 'SLTU') else f'{b}'
                sentence = T('s.cmp', rs=rn(ins.rs), a=a, rhs=rhs, truth=T('yes' if v else 'no'), v=v, dn=dn)
            elif op in ('ADD', 'ADDU') and (ins.rs == 0 or ins.rt == 0):
                if ins.rs == 0 and ins.rt == 0:
                    sentence = T('s.clear', dn=dn)
                else:
                    src = ins.rt if ins.rs == 0 else ins.rs
                    sentence = T('s.copy', src=rn(src), v=v, dn=dn)
            elif op in ('ADDI', 'ADDIU') and ins.rs == 0:
                sentence = T('s.set', dn=dn, v=v)
            elif op in ('ADDI', 'ADDIU') and ins.rs == ins.rt and ins.imm != 0:
                sentence = T('s.inc' if ins.imm > 0 else 's.dec', dn=dn, n=abs(ins.imm), a=a, v=v)
            else:
                sym, bb = sign_pair(SYMBOL.get(op, op), b)
                if op in R_DEST:
                    sentence = T('s.alu_r', rs=rn(ins.rs), a=a, sym=SYMBOL.get(op, op), rt=rn(ins.rt), b=b, v=v, dn=dn)
                else:
                    sentence = T('s.alu_i', rs=rn(ins.rs), a=a, sym=sym, b=bb, v=v, dn=dn)
            result = f'{dn} = {v}' if d else f'= {v}'
        else:   # SLL / SRL
            new = step.reg_changes.get(d, (None, None))[1] if d is not None else None
            way = T('left' if op == 'SLL' else 'right')
            sentence = T('s.shift', rt=rn(ins.rt), way=way, n=ins.shamt)
            if new is not None:
                sentence += T('s.shift_to', new=new, dn=dn)
                result = f'{dn} = {new}'
        if d == 0:
            sentence += T('s.zero_note')
    elif op == 'LUI':
        d = rn(ins.rt)
        new = step.reg_changes.get(ins.rt, (None, None))[1]
        sentence = T('s.lui', imm=ins.imm & 0xFFFF, d=d)
        if new is not None:
            sentence += T('s.lui_to', new=new)
            result = f'{d} = {new}'
    elif op in BRANCH:
        tone = 'branch'
        taken = bool(step.branch_taken)
        rule = T('equal' if op == 'BEQ' else 'different')
        if regs is not None:
            a, b = s32(regs[ins.rs]), s32(regs[ins.rt])
            real = T('equal' if a == b else 'different')
            sentence = T('s.br_vals', rs=rn(ins.rs), a=a, rt=rn(ins.rt), b=b, real=real, rule=rule)
        else:
            sentence = T('s.br_novals', rs=rn(ins.rs), rt=rn(ins.rt), rule=rule)
        if taken:
            sentence += T('s.br_taken', addr=hx(step.pc_after))
            result = T('r.jump', addr=hx(step.pc_after))
        else:
            sentence += T('s.br_not')
            result = T('r.nojump')
    elif op == 'J':
        tone = 'jump'
        sentence = T('s.j', addr=hx(step.pc_after))
        result = T('r.go', addr=hx(step.pc_after))
    elif op == 'JAL':
        tone = 'jump'
        ra = step.reg_changes.get(31, (None, None))[1]
        back = hx(ra) if ra is not None else T('next_instr')
        sentence = T('s.jal', addr=hx(step.pc_after), back=back)
        result = T('r.go', addr=hx(step.pc_after))
    elif op == 'JR':
        tone = 'jump'
        sentence = T('s.jr', addr=hx(step.pc_after))
        result = T('r.go', addr=hx(step.pc_after))
    elif op == 'LW':
        tone = 'mem'
        addr = step.mem_reads[0] if step.mem_reads else None
        new = step.reg_changes.get(ins.rt, (None, None))[1]
        if new is None and regs is not None:
            new = regs[ins.rt]
        if addr is not None:
            sentence = T('s.lw', val=(f' {new}' if new is not None else ''), addr=hx(addr), rt=rn(ins.rt))
        else:
            sentence = T('s.lw_any', rt=rn(ins.rt))
        result = f'{rn(ins.rt)} = {new}' if new is not None else T('r.read')
    elif op == 'SW':
        tone = 'mem'
        if step.mem_writes:
            addr, val = step.mem_writes[0]
            sentence = T('s.sw', v=s32(val), rt=rn(ins.rt), addr=hx(addr))
            result = f'mem[{hx(addr)}] = {s32(val)}'
        else:
            sentence = T('s.sw_any', rt=rn(ins.rt))
    elif op == 'HALT':
        tone = 'halt'
        sentence = T('s.halt')
        if regs is not None:
            sentence += T('s.halt_v', v=s32(regs[2]))
            result = f'$v0 = {s32(regs[2])}'
        else:
            sentence += T('s.halt_end')
            result = T('r.stop')
    return dict(title=title, sentence=sentence, result=result, changes=changes, tone=tone)


def friendly_error(status, error=None, lang=DEFAULT_LANG):
    key = 'e.' + str(status)
    if key in TX['en']:
        return tx(lang, key)
    return error or tx(lang, 'e.generic')


def explain_next(ins, regs=None, lang=DEFAULT_LANG):
    """บรรทัด 'Next' : ชื่อการกระทำ + ค่าปัจจุบันของ register ที่คำสั่งจะใช้ (ยังไม่คำนวณผล)"""
    srcs = []
    if ins.op in ('ADD', 'ADDU', 'SUB', 'SUBU', 'AND', 'OR', 'NOR', 'SLT', 'SLTU', 'BEQ', 'BNE'):
        srcs = [ins.rs, ins.rt]
    elif ins.op in ('ADDI', 'ADDIU', 'ANDI', 'ORI', 'SLTI', 'SLTIU', 'LW'):
        srcs = [ins.rs]
    elif ins.op == 'SW':
        srcs = [ins.rt, ins.rs]
    elif ins.op in ('SLL', 'SRL'):
        srcs = [ins.rt]
    elif ins.op == 'JR':
        srcs = [ins.rs]
    detail = ''
    if regs is not None and srcs:
        seen, parts = set(), []
        for i in srcs:
            if i in seen or i == 0:
                continue
            seen.add(i)
            parts.append(f'{rn(i)} = {s32(regs[i])}')
        if parts:
            detail = tx(lang, 'n.uses', parts=tx(lang, 'n.and').join(parts))
    return op_title(ins, lang), detail


# ------------------------------------------------------------------ CPU Execution Path
def _short(text, n=26):
    text = str(text)
    return text if len(text) <= n else text[:n - 1] + '…'


def stage_info(step, lang=DEFAULT_LANG):
    """รายการ 5 ขั้น: {name, sub, short, caption, used}"""
    out = [dict(name=tx(lang, f'st.{i}'), sub=tx(lang, f'st.{i}.sub'), short=tx(lang, f'st.{i}.short'),
                caption='—', used=False) for i in range(5)]
    if step is None:
        return out
    ins = step.instr
    op = ins.op
    alu = parse_alu(step.alu_text)
    out[0].update(used=True, caption=hx(step.pc_before))
    out[1].update(used=True, caption=clean(ins.raw))
    out[2].update(used=True, caption=f'{op} · {tx(lang, "k." + ins.kind) if ("k." + ins.kind) in TX["en"] else ins.kind}')
    if not step.completed:
        out[3].update(used=True, caption=_short(step.status))
        return out
    mem = bool(step.mem_reads or step.mem_writes)
    if alu:
        a, _, b, v = alu
        sym, bb = sign_pair(SYMBOL.get(alu[1], alu[1]), b)
        out[3].update(used=True, caption=f'{a} {sym} {bb} = {v}')
    elif op in BRANCH:
        out[3].update(used=True, caption=tx(lang, 'c.jump' if step.branch_taken else 'c.nojump'))
    elif mem:
        addr = step.mem_reads[0] if step.mem_reads else step.mem_writes[0][0]
        out[3].update(used=True, caption=tx(lang, 'c.addr', addr=hx(addr)))
    d = dest_reg(ins)
    if step.mem_writes:
        addr, val = step.mem_writes[0]
        out[4].update(used=True, caption=f'mem ← {s32(val)}')
    elif d:
        new = step.reg_changes.get(d, (None, None))[1]
        if new is None and alu:
            new = alu[3]
        shown = hx(new) if (d == 31 and new is not None) else new
        out[4].update(used=True, caption=f'{rn(d)} ← {shown}' if new is not None else rn(d))
    return out


# ------------------------------------------------------------------ Execution History
def history_row(step, lang=DEFAULT_LANG):
    """(step_no, instruction, what, result, tag)"""
    ins = step.instr
    if not step.completed:
        return (f'{step.step_no:,}', clean(ins.raw), tx(lang, 'title.error'), tx(lang, 'r.fail'), 'error')
    e = explain_step(step, None, lang)
    return (f'{step.step_no:,}', clean(ins.raw), e['title'], e['result'] or '—', e['tone'])


# ------------------------------------------------------------------ ตัวเลขที่กำลังใช้ (chips)
ORDER = [2, 4, 5] + list(range(8, 16)) + [24, 25] + list(range(16, 24)) + [3, 31, 29]
STACK_INIT = 0x1FFFC

ROLES = {
    'en': {
        'factorial': {
            4: 'n (your input)', 2: 'running product (final = n!)', 3: 'status (0 = OK)',
            8: 'multiplier i (counts 2 → n)', 9: 'comparison (1 = true)',
            10: 'temporary sum', 11: 'inner counter j', 31: 'return address',
        },
        'ncr_factorial': {
            4: 'value passed to function (1)', 5: 'value passed to function (2)',
            2: 'result of the last function', 3: 'status (0 = OK)',
            16: 'n', 17: 'r', 18: 'n − r', 19: 'n!',
            20: 'bigger divisor (r! or (n−r)!)', 21: 'smaller divisor',
            8: 'counter i / running sum when dividing', 9: 'comparison (1 = true)',
            10: 'temporary sum', 11: 'inner counter j', 31: 'return address',
        },
        'nck_optimized': {
            4: 'n (your input)', 5: 'k = r (your input)',
            2: 'running product n(n−1)…(b+1) → result', 3: 'status (0 = OK)',
            8: 'n − k', 9: 'comparison (1 = true)',
            10: 'a = smaller of (k, n−k)', 11: 'b = larger of (k, n−k)',
            12: 'counter i / quotient', 13: 'comparison (1 = true)',
            14: 'temporary sum', 15: 'inner counter j',
            24: 'a! (the divisor)', 25: 'running sum of the divisor', 31: 'return address',
        },
    },
    'th': {
        'factorial': {
            4: 'n (ตัวเลขที่ใส่)', 2: 'ผลคูณสะสม (ตอนจบ = n!)', 3: 'สถานะ (0 = ปกติ)',
            8: 'ตัวคูณ i (นับ 2 → n)', 9: 'ผลเปรียบเทียบ (1 = จริง)',
            10: 'ผลบวกชั่วคราว', 11: 'ตัวนับรอบบวก j', 31: 'ที่อยู่ที่ต้องกลับ',
        },
        'ncr_factorial': {
            4: 'ค่าที่ส่งเข้าฟังก์ชัน (1)', 5: 'ค่าที่ส่งเข้าฟังก์ชัน (2)',
            2: 'ผลของฟังก์ชันล่าสุด', 3: 'สถานะ (0 = ปกติ)',
            16: 'n', 17: 'r', 18: 'n − r', 19: 'n!',
            20: 'ตัวหารตัวใหญ่ (r! หรือ (n−r)!)', 21: 'ตัวหารตัวเล็ก',
            8: 'ตัวนับ i / ผลบวกสะสมตอนหาร', 9: 'ผลเปรียบเทียบ (1 = จริง)',
            10: 'ผลบวกชั่วคราว', 11: 'ตัวนับรอบบวก j', 31: 'ที่อยู่ที่ต้องกลับ',
        },
        'nck_optimized': {
            4: 'n (ตัวเลขที่ใส่)', 5: 'k = r (ตัวเลขที่ใส่)',
            2: 'ผลคูณสะสม n(n−1)…(b+1) → ผลลัพธ์', 3: 'สถานะ (0 = ปกติ)',
            8: 'n − k', 9: 'ผลเปรียบเทียบ (1 = จริง)',
            10: 'a = ตัวน้อยของ (k, n−k)', 11: 'b = ตัวใหญ่ของ (k, n−k)',
            12: 'ตัวนับ i / ผลหาร', 13: 'ผลเปรียบเทียบ (1 = จริง)',
            14: 'ผลบวกชั่วคราว', 15: 'ตัวนับรอบบวก j',
            24: 'a! (ตัวหาร)', 25: 'ผลบวกสะสมของตัวหาร', 31: 'ที่อยู่ที่ต้องกลับ',
        },
    },
}


def roles_for(skey, lang=DEFAULT_LANG):
    return ROLES.get(lang, ROLES['en']).get(skey, {})


def live_registers(regs, changes, roles, always=()):
    """chips ของ register ที่น่าสนใจ ณ ตอนนี้: เปลี่ยนในขั้นล่าสุด หรือมีค่าไม่ใช่ 0 (หรืออยู่ใน always)"""
    chips = []
    for i in ORDER:
        v = s32(regs[i])
        ch = changes.get(i)
        if i == 29 and not ch and v == s32(STACK_INIT):
            continue
        if not ch and v == 0 and i not in always:
            continue
        chips.append(dict(idx=i, name=rn(i), role=roles.get(i, ''), value=v,
                          changed=bool(ch), old=s32(ch[0]) if ch else None))
    return chips


# ------------------------------------------------------------------ Calculate (ผลลัพธ์ด่วน)
def formula_text(kind, n, r=None):
    if kind == 'factorial':
        if n <= 1:
            return f'{n}! = 1'
        if n <= 7:
            return f'{n}! = ' + ' × '.join(str(i) for i in range(n, 0, -1))
        return f'{n}! = {n} × {n - 1} × {n - 2} × … × 2 × 1'
    return f'{n}C{r} = {n}! ÷ ({r}! × {n - r}!)'


def division_rounds(n, r):
    """ประมาณจำนวนรอบหารของวิธี Factorial-Based (= n!/b!) ใช้ตัดสินว่าควรคำนวณอัตโนมัติหรือรอให้กดปุ่ม"""
    b = max(r, n - r)
    p = 1
    for i in range(b + 1, n + 1):
        p *= i
    return p


def calc_outcome(row, lang=DEFAULT_LANG):
    """แปลงผล CompareRow (จาก Controller.run_headless) เป็นข้อความที่ผู้ใช้เข้าใจ"""
    instr = row.counters.get('instr', 0) if row.counters else 0
    if row.status == 'HALTED' and row.prog_status == 0 and row.result is not None:
        return dict(ok=True, value=row.result, instr=instr, verified=row.matches_reference, message='')
    if row.status == 'HALTED' and row.prog_status == 3:
        return dict(ok=False, instr=instr, message=tx(lang, 'k.bad_range'))
    if row.status == 'HALTED' and row.prog_status == 2:
        return dict(ok=False, instr=instr, message=tx(lang, 'k.div0'))
    return dict(ok=False, instr=instr, message=friendly_error(row.status, None, lang))


def mode_name(mode, lang=DEFAULT_LANG):
    key = 'm.' + str(mode)
    return tx(lang, key) if key in TX['en'] else str(mode)
