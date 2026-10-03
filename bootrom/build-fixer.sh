#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Ensambla el fixer BL2 (Thumb) y lo inyecta en TU dump del FIP preloader.
#
# IMPORTANTE: el .bin resultante contiene el BL2 de FABRICA (propiedad del
# fabricante). NO lo redistribuyas. Lo generas desde TU propio dump.
#
# Requisitos: arm-none-eabi-{as,ld,objcopy}  (gcc-arm-none-eabi)
set -euo pipefail

SRC="${1:-fixer_pw.s}"              # fixer_pw.s (escritura) o fixer_diag.s (read-only)
FIP="${2:?Uso: build-fixer.sh <fixer.s> <preloader_fip.bin> [salida.bin]}"
OUT="${3:-preloader_fixer.bin}"

# El parche vive en vaddr 0x08000b68 (sobre la rutina de recovery del BL2).
# En el archivo del FIP eso cae en el offset 0xf66 (2 bytes de padding + codigo).
LINK=0x08000b68
FILE_OFF=$((0xf66))
BUDGET=88                           # presupuesto real: 0x8000b68..0x8000bc0

arm-none-eabi-as -mthumb -mcpu=cortex-a53 "$SRC" -o /tmp/fixer.o
arm-none-eabi-ld -Ttext=$LINK /tmp/fixer.o -o /tmp/fixer.elf
arm-none-eabi-objcopy -O binary /tmp/fixer.elf /tmp/fixer.bin

SZ=$(stat -c%s /tmp/fixer.bin)
echo "[*] fixer: $SZ bytes (presupuesto $BUDGET)"
[ "$SZ" -le "$BUDGET" ] || { echo "[!] el fixer excede $BUDGET bytes: pisaria el literal del buffer en 0x8000bcc"; exit 1; }

cp "$FIP" "$OUT"
dd if=/tmp/fixer.bin of="$OUT" bs=1 seek=$FILE_OFF conv=notrunc status=none
echo "[+] inyectado en $OUT @ offset $(printf 0x%x $FILE_OFF)"
echo "    subilo con:  ./bromflash.py $OUT"
