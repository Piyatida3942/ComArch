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
