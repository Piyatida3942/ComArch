# MODIFIED from cpuSimV7 memory.py
#   เดิม: dict เก็บค่าอะไรก็ได้ต่อ key เดียว (SW เก็บทั้ง word ที่ key เดียว แต่ text เก็บทีละ byte -> บัค #10)
#   ใหม่: byte-addressed ทั้งหมด, word = 4 byte Big-endian, ตรวจช่วงที่อยู่และ alignment
#   คงแนวคิดเดิม: ใช้ dict, ที่อยู่ที่ไม่เคยเขียนอ่านได้ 0, มี dump() ไว้ debug แบบเดิม
"""simulator/memory.py -- หน่วยความจำแบบ byte-addressed (Big-endian, word = 4 byte)"""
from __future__ import annotations

from simulator.contract import MEM_SIZE


class MemoryAccessError(Exception):
    """เข้าถึงนอกช่วง 0..MEM_SIZE-1 หรือ word ไม่ align 4"""


class Memory:
    def __init__(self) -> None:
        self.data: dict[int, int] = {}          # byte address -> byte (0..255)

    # ---------- byte ----------
    def read_byte(self, addr: int) -> int:
        if not 0 <= addr < MEM_SIZE:
            raise MemoryAccessError(f"address 0x{addr & 0xFFFFFFFF:08x} is out of memory range")
        return self.data.get(addr, 0)

    def write_byte(self, addr: int, value: int) -> None:
        if not 0 <= addr < MEM_SIZE:
            raise MemoryAccessError(f"address 0x{addr & 0xFFFFFFFF:08x} is out of memory range")
        self.data[addr] = value & 0xFF

    # ---------- word (Big-endian: byte ที่ addr คือบิตสูงสุด) ----------
    def _check_word(self, addr: int) -> None:
        if not 0 <= addr <= MEM_SIZE - 4:
            raise MemoryAccessError(f"address 0x{addr & 0xFFFFFFFF:08x} is out of memory range")
        if addr & 3:
            raise MemoryAccessError(f"address 0x{addr:08x} is not word-aligned (must be a multiple of 4)")

    def read_word(self, addr: int) -> int:
        """คืนค่า unsigned 0..2**32-1"""
        self._check_word(addr)
        g = self.data.get
        return (g(addr, 0) << 24) | (g(addr + 1, 0) << 16) | (g(addr + 2, 0) << 8) | g(addr + 3, 0)

    def write_word(self, addr: int, value: int) -> None:
        self._check_word(addr)
        value &= 0xFFFFFFFF
        d = self.data
        d[addr] = value >> 24
        d[addr + 1] = (value >> 16) & 0xFF
        d[addr + 2] = (value >> 8) & 0xFF
        d[addr + 3] = value & 0xFF

    # ---------- อื่นๆ ----------
    def snapshot(self) -> dict[int, int]:
        return dict(self.data)

    def clear(self) -> None:
        self.data.clear()

    def dump(self, start: int = 0, length: int = 100, width: int = 20) -> str:
        """ข้อความตาราง hex แบบ dump() ของ cpuSimV7 (ใช้ debug ใน console)"""
        lines = []
        for row in range(start, start + length, width):
            cells = " ".join(f"{self.data.get(a, 0):02x}" for a in range(row, min(row + width, start + length)))
            lines.append(f"{row:>8x}: {cells}")
        return "\n".join(lines)
