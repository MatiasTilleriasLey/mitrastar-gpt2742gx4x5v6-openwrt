.syntax unified
.thumb
.text
.global _start
_start:
    @ read slave block0 -> buf
    ldr r0, =0x05ac0000
    ldr r1, =0x00020000
    ldr r2, =0x81800000
    ldr r3, =0x08001a2d
    blx r3
    @ print seq FIRST (proves reached code + read OK + offset)
    ldr r3, =0x81800040
    ldr r1, [r3]
    ldr r0, =fmt
    ldr r3, =0x08014658
    blx r3
    @ lower seq in buf
    ldr r3, =0x81800040
    ldr r0, =0x01000000
    str r0, [r3]
    @ erase slave block0
    ldr r0, =0x05ac0000
    ldr r1, =0x00020000
    ldr r3, =0x08001a89
    blx r3
    @ write buf back (seq lowered)
    ldr r0, =0x05ac0000
    ldr r1, =0x00020000
    ldr r2, =0x81800000
    ldr r3, =0x08001aa9
    blx r3
    @ print DONE marker
    ldr r0, =fmd
    ldr r3, =0x08014658
    blx r3
hang:
    b hang
.align 2
fmt: .asciz "S=%08x\n"
.align 2
fmd: .asciz "D\n"
.align 2
