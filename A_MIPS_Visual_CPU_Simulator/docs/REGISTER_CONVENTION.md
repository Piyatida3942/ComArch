# Register Convention — Member 1

- `$zero` (0): always 0.
- `$v0` (2): factorial result; `$v1` (3): status, 0 success, 3 invalid input.
- `$a0` (4): input n, preserved by `fact`.
- `$t0` (8): outer loop i; `$t1` (9): comparison; `$t2` (10): temp; `$t3` (11): inner loop j. These are caller-saved.
- `$sp` (29): stack pointer, initially `0x1FFFC`; `$ra` (31): return address for `JAL`/`JR`.
- `$s0`–`$s7` (16–23): callee-saved, untouched by `fact`.
- Register values use signed int32; overflow traps on ADD/ADDI/SUB.

`fact` is a leaf subroutine and does not modify `$a0`, `$s*`, `$sp`, or `$ra`. Member 2 must copy the same `fact:` block into `ncr_factorial.asm`.
