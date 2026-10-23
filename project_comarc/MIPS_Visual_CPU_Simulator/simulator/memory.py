# NEW: byte-addressed big-endian memory
from .contract import MEM_SIZE
class MemoryAccessError(Exception): pass
class Memory:
    def __init__(self): self.data={}
    def check(self,a,size=1):
        if not isinstance(a,int) or a<0 or a+size>MEM_SIZE or (size==4 and a%4): raise MemoryAccessError(f'invalid memory address {a}')
    def read_byte(self,addr): self.check(addr);return self.data.get(addr,0)
    def write_byte(self,addr,value): self.check(addr);self.data[addr]=value&255
    def read_word(self,addr):
        self.check(addr,4);return sum(self.read_byte(addr+i)<<(24-8*i) for i in range(4))
    def write_word(self,addr,value):
        self.check(addr,4)
        for i in range(4):self.write_byte(addr+i,value>>(24-8*i))
    def snapshot(self):return self.data.copy()
    def clear(self):self.data.clear()
