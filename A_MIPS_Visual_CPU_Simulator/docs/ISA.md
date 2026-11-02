# MIPS ISA — project subset

## Executable (MUST)

| Instruction | Meaning |
|---|---|
| ADD, ADDI | Signed addition with overflow trap |
| ADDU, ADDIU | 32-bit wrapping addition |
| SUB, SUBU | Subtraction, signed-trapping / wrapping |
| AND, ANDI, OR, ORI | Bitwise logic |
| SLT, SLTI | Signed less-than comparison |
| SLTU, SLTIU | Unsigned less-than comparison |
| LUI | Load upper immediate |
| LW, SW | Load/store aligned 32-bit word |
| BEQ, BNE | Conditional branch relative to next instruction |
| J, JAL | Absolute jump; JAL saves return PC in `$ra` |
| JR | Jump to address stored in register |
| HALT | Simulator-only stop instruction; no MIPS encoding |

SHOULD: SLL, SRL, NOR. Unsupported: LBU, LHU, LL, SB, SC, SH. Directive `.ORG` sets code origin.

## Encoding example

`ADD $t2 $t0 $t1`: opcode `000000`, rs `01000`, rt `01001`, rd `01010`, shamt `00000`, funct `100000` → `0x01095020`.

`ADDI $t0 $zero 5`: opcode `001000`, rs `00000`, rt `01000`, immediate `0000000000000101` → `0x20080005`.

`JAL 0x2008`: opcode `000011`, target `(0x2008 >> 2)` → `0x0c000802`.

Golden values in `tests/golden_hex.json` are transcribed from the supplied project specification; **independent MARS/QtSpim verification is still required**.

## Golden-vector corrections (independently checked)

The seed specification lists `BEQ $t0 $t1 3` as `11280003` and `BNE $t1 $zero -2` as `1409fffe`. Those hex words encode *different operand orders*. The corrected encodings for the written assembly operands are `11090003` and `1520fffe`, respectively. `tests/golden_hex.json` uses the corrected versions. Confirm with MARS/QtSpim before final team sign-off.
