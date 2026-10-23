# NEW -- tests for simulator/memory.py (Member 3)
import pytest

from simulator.contract import MEM_SIZE
from simulator.memory import Memory, MemoryAccessError


def test_unwritten_reads_zero():
    m = Memory()
    assert m.read_byte(0x100) == 0
    assert m.read_word(0x100) == 0


def test_byte_roundtrip_and_mask():
    m = Memory()
    m.write_byte(5, 0x1AB)
    assert m.read_byte(5) == 0xAB


def test_word_is_big_endian():
    m = Memory()
    m.write_word(0x2000, 0x12345678)
    assert [m.read_byte(0x2000 + i) for i in range(4)] == [0x12, 0x34, 0x56, 0x78]
    assert m.read_word(0x2000) == 0x12345678


def test_word_negative_stored_as_unsigned():
    m = Memory()
    m.write_word(0x10000, -1)
    assert m.read_word(0x10000) == 0xFFFFFFFF


@pytest.mark.parametrize("addr", [1, 2, 3, 0x2002])
def test_word_must_be_aligned(addr):
    m = Memory()
    with pytest.raises(MemoryAccessError):
        m.read_word(addr)
    with pytest.raises(MemoryAccessError):
        m.write_word(addr, 1)


@pytest.mark.parametrize("addr", [-4, MEM_SIZE, MEM_SIZE - 2])
def test_out_of_range(addr):
    m = Memory()
    with pytest.raises(MemoryAccessError):
        m.read_word(addr)
    with pytest.raises(MemoryAccessError):
        m.write_byte(addr if addr != MEM_SIZE - 2 else MEM_SIZE, 1)


def test_last_word_ok():
    m = Memory()
    m.write_word(MEM_SIZE - 4, 7)
    assert m.read_word(MEM_SIZE - 4) == 7


def test_snapshot_is_copy_and_clear():
    m = Memory()
    m.write_word(0, 0x01020304)
    snap = m.snapshot()
    snap[0] = 99
    assert m.read_byte(0) == 1
    assert snap.keys() == {0, 1, 2, 3}
    m.clear()
    assert m.snapshot() == {}
