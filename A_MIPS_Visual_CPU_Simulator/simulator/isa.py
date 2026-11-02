# NEW: MIPS32 instruction metadata and encoding
from .contract import REG_NAMES,AsmError,hex8,bin32
OPS={'ADD':('R',0,32,'rd rs rt'),'ADDU':('R',0,33,'rd rs rt'),'SUB':('R',0,34,'rd rs rt'),'SUBU':('R',0,35,'rd rs rt'),'AND':('R',0,36,'rd rs rt'),'OR':('R',0,37,'rd rs rt'),'NOR':('R',0,39,'rd rs rt'),'SLT':('R',0,42,'rd rs rt'),'SLTU':('R',0,43,'rd rs rt'),'SLL':('R',0,0,'rd rt shamt'),'SRL':('R',0,2,'rd rt shamt'),'JR':('R',0,8,'rs'),'ADDI':('I',8,0,'rt rs imm'),'ADDIU':('I',9,0,'rt rs imm'),'ANDI':('I',12,0,'rt rs imm'),'ORI':('I',13,0,'rt rs imm'),'SLTI':('I',10,0,'rt rs imm'),'SLTIU':('I',11,0,'rt rs imm'),'LUI':('I',15,0,'rt imm'),'LW':('I',35,0,'rt off(rs)'),'SW':('I',43,0,'rt off(rs)'),'BEQ':('I',4,0,'rs rt imm'),'BNE':('I',5,0,'rs rt imm'),'J':('J',2,0,'target'),'JAL':('J',3,0,'target'),'HALT':('SIM',0,0,'')}
INSTR_TABLE={k:{'kind':v[0],'opcode':v[1],'funct':v[2],'status':'EXEC','form':v[3]} for k,v in OPS.items()}
for k in ('LBU','LHU','LL','SB','SC','SH'): INSTR_TABLE[k]={'kind':'I','opcode':0,'funct':0,'status':'UNSUPPORTED','form':''}
def reg_number(token):
    t=token.strip().lower().lstrip('$')
    if t.isdecimal() and 0<=int(t)<32:return int(t)
    if t in REG_NAMES:return REG_NAMES.index(t)
    raise AsmError(0,f'invalid register {token}')
def encode(op,kind,rd=0,rs=0,rt=0,shamt=0,imm=0,target=0):
    if kind=='SIM':return None,None
    entry=INSTR_TABLE[op];code=entry['opcode']<<26
    if kind=='R':code|=(rs<<21)|(rt<<16)|(rd<<11)|(shamt<<6)|entry['funct']
    elif kind=='I':code|=(rs<<21)|(rt<<16)|(imm&65535)
    else:code|=(target>>2)&0x3ffffff
    return hex8(code),bin32(code)
def decode_word(word):
    opcode=(word>>26)&63; rs=(word>>21)&31;rt=(word>>16)&31;rd=(word>>11)&31;shamt=(word>>6)&31;funct=word&63
    op=next((k for k,v in OPS.items() if v[1]==opcode and (v[0]!='R' or v[2]==funct)),None)
    kind=OPS[op][0] if op else None
    imm=word&65535
    if imm&32768:imm-=65536
    return {'kind':kind,'op':op,'rs':rs,'rt':rt,'rd':rd,'shamt':shamt,'funct':funct,'imm':imm,'target':(word&0x3ffffff)<<2}
