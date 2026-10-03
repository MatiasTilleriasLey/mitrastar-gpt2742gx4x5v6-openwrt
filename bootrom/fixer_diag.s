.syntax unified
.thumb
.text
.global _start
_start:
    ldr r0, =0x05ac0000
    ldr r1, =0x00020000
    ldr r2, =0x81800000
    ldr r3, =0x08001a2d      @ flash_read Thumb
    blx r3
    ldr r3, =0x81800040
    ldr r1, [r3]
    ldr r0, =fmt_r
    ldr r3, =0x08014658      @ printf ARM
    blx r3
    ldr r0, =0x05ac0000
    ldr r1, =0x00020000
    ldr r3, =0x08001a89      @ flash_erase Thumb
    blx r3
    ldr r0, =0x05ac0000
    ldr r1, =0x00000800
    ldr r2, =0x81900000
    ldr r3, =0x08001a2d
    blx r3
    ldr r3, =0x81900040
    ldr r1, [r3]
    ldr r0, =fmt_e
    ldr r3, =0x08014658
    blx r3
    ldr r3, =0x81800040
    ldr r0, =0x01000000
    str r0, [r3]
    ldr r0, =0x05ac0000
    ldr r1, =0x00020000
    ldr r2, =0x81800000
    ldr r3, =0x08001aa9      @ flash_write Thumb
    blx r3
    ldr r0, =0x05ac0000
    ldr r1, =0x00000800
    ldr r2, =0x81a00000
    ldr r3, =0x08001a2d
    blx r3
    ldr r3, =0x81a00040
    ldr r1, [r3]
    ldr r0, =fmt_w
    ldr r3, =0x08014658
    blx r3
hang:
    b hang
.align 2
fmt_r: .asciz "FIX_R=%08x\n"
.align 2
fmt_e: .asciz "FIX_E=%08x\n"
.align 2
fmt_w: .asciz "FIX_W=%08x\n"
.align 2
