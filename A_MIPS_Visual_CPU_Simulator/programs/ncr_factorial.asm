# NEW: adapted from project specification appendix
# ncr_factorial.asm -- C(n,r) = n! / (r! (n-r)!)  calls fact 3 times, divides by repeated addition

# IN : $a0 = n (0..12), $a1 = r (0..n)

# OUT: $v0 = C(n,r)   $v1 = 0 ok | 2 divide by zero | 3 invalid input

.ORG 0x2000

main:

    JAL  ncr_fact

    HALT



ncr_fact:

    ADD  $v1 $zero $zero

    SLT  $t0 $a0 $zero

    BNE  $t0 $zero ncr_bad

    SLT  $t0 $a1 $zero

    BNE  $t0 $zero ncr_bad

    SLT  $t0 $a0 $a1            # n < r ?

    BNE  $t0 $zero ncr_bad

    SLTI $t0 $a0 13             # n <= 12 ?

    BEQ  $t0 $zero ncr_bad

    ADDI $sp $sp -32            # frame: save $ra,$s0-$s5

    SW   $ra 28($sp)

    SW   $s0 24($sp)

    SW   $s1 20($sp)

    SW   $s2 16($sp)

    SW   $s3 12($sp)

    SW   $s4 8($sp)

    SW   $s5 4($sp)

    ADD  $s0 $zero $a0          # s0 = n

    ADD  $s1 $zero $a1          # s1 = r

    SUB  $s2 $s0 $s1            # s2 = n-r

    ADD  $a0 $zero $s0

    JAL  fact

    ADD  $s3 $zero $v0          # s3 = n!

    ADD  $a0 $zero $s1

    JAL  fact

    ADD  $s4 $zero $v0          # s4 = r!

    ADD  $a0 $zero $s2

    JAL  fact

    ADD  $s5 $zero $v0          # s5 = (n-r)!

    SLT  $t0 $s4 $s5            # make s4 the larger factorial (smaller quotient 1st)

    BEQ  $t0 $zero ncr_noswap

    ADD  $t1 $zero $s4

    ADD  $s4 $zero $s5

    ADD  $s5 $zero $t1

ncr_noswap:

    ADD  $a0 $zero $s3

    ADD  $a1 $zero $s4

    JAL  div_add                # q1 = n! / larger

    BNE  $v1 $zero ncr_exit

    ADD  $a0 $zero $v0

    ADD  $a1 $zero $s5

    JAL  div_add                # q2 = q1 / smaller

ncr_exit:

    LW   $s5 4($sp)

    LW   $s4 8($sp)

    LW   $s3 12($sp)

    LW   $s2 16($sp)

    LW   $s1 20($sp)

    LW   $s0 24($sp)

    LW   $ra 28($sp)

    ADDI $sp $sp 32

    JR   $ra

ncr_bad:

    ADDI $v1 $zero 3

    ADD  $v0 $zero $zero

    JR   $ra



div_add:                        # $a0 / $a1 by repeated addition (exact division assumed)

    BNE  $a1 $zero div_ok

    ADDI $v1 $zero 2

    ADD  $v0 $zero $zero

    JR   $ra

div_ok:

    ADD  $t0 $zero $a1          # tmm = divisor

    ADDI $v0 $zero 1            # q = 1

div_loop:

    SLT  $t1 $t0 $a0            # tmm < dividend ?

    BEQ  $t1 $zero div_done

    ADD  $t0 $t0 $a1

    ADDI $v0 $v0 1

    J    div_loop

div_done:

    JR   $ra



fact:                           # same routine as factorial.asm (keep identical!)

    ADDI $v0 $zero 1

    ADDI $t0 $zero 2

fact_outer:

    SLT  $t1 $a0 $t0

    BNE  $t1 $zero fact_done

    ADD  $t2 $zero $zero

    ADD  $t3 $zero $zero

fact_inner:

    SLT  $t1 $t3 $t0

    BEQ  $t1 $zero fact_inner_end

    ADD  $t2 $t2 $v0

    ADDI $t3 $t3 1

    J    fact_inner

fact_inner_end:

    ADD  $v0 $zero $t2

    ADDI $t0 $t0 1

    J    fact_outer

fact_done:

    JR   $ra
