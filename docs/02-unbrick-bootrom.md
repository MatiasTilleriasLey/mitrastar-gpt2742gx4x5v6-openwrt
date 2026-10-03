# 02 — Rescate por BootROM (unbrick)

Si flasheaste el slave con `imageSequence` alto y no bootea, el zloader se
cuelga (sin fallback) y la red del bootloader esta muerta (`Not found TC Phy`,
no hay TFTP). Queda una via: el **BootROM** en silicio.

## El modo recovery
1. Apreta **RESET** y mantenelo mientras das corriente.
2. El BROM imprime `Press x`.
3. Manda una `x` -> responde con un flood de `C` (handshake XMODEM-CRC).
4. Subis un payload por XMODEM.

`bromflash.py` automatiza el handshake y el XMODEM (bloques de 128 B, CRC16).

## El fixer BL2
No reescribimos un driver NAND: **reusamos las funciones de flash del BL2 de
fabrica**. El fixer es un parche Thumb que se inyecta sobre la rutina de
recovery del BL2 (vaddr `0x08000b68`, offset `0xf66` en el FIP).

Dos variantes (`bootrom/`):
- `fixer_diag.s` — **read-only**: lee el bloque 0 del slave e imprime el
  `imageSequence`. Valida offset y funciones sin escribir nada.
- `fixer_pw.s` — **escritura**: lee el bloque, baja el `imageSequence` a
  `0x01000000`, borra y reescribe. Imprime `D` al terminar.

### El bug del presupuesto (el cazabugs)
El fixer de escritura se moria MUDO despues del init de DRAM. Causa: el codigo
ANTES del parche, en `0x8000b44`, carga un literal desde `0x8000bcc` (= el
puntero al buffer de `flash_read`). Los fixers largos **pisaban `0x8000bcc`** ->
`flash_read` escribia a basura -> fault silencioso.

> **Presupuesto real: `0x8000b68` .. `0x8000bc0` = 88 bytes.** Ni uno mas, o
> pisas el literal del buffer. `build-fixer.sh` lo chequea.

## Uso
```sh
# 1) arma el fixer sobre TU dump del FIP (mtd0 / bootloader):
./build-fixer.sh fixer_pw.s mi_preloader_fip.bin preloader_fixer.bin

# 2) subilo por el BootROM (corre el script, despues RESET + corriente):
./bromflash.py preloader_fixer.bin
#    ... DRAM size=512MB
#    D                <- erase+write OK, imageSequence del slave bajado

# 3) power-cycle NORMAL (sin RESET): el zloader elige el main de fabrica.
```

Todo corre desde RAM: en el peor caso, un power-cycle vuelve al estado anterior.
El main nunca se toca.

> Glitch conocido: a veces el XMODEM falla en el bloque 1 (`exit 3`). Reintenta
> con entrada limpia (corta corriente del todo antes del RESET dance).
