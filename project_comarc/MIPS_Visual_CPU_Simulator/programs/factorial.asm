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
