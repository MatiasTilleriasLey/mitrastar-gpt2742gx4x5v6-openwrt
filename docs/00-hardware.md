# 00 — Hardware y cadena de boot

## SoC y perifericos
- **Airoha/EcoNet EN7523**: 2× Cortex-A53. El kernel corre en modo aarch32
  (ARMv7, build cortex-a7).
- 512 MB RAM, base fisica `0x80000000`.
- SPI NAND **W25N02KV** (256 MB), erase block `0x20000` (128 KiB), page 2 KiB.
- 2× **MT7915** por PCIe (`1fa91000.pcie`, `1fa92000.pcie`), Wi-Fi 6.
- Switch **GSW** integrado: 4 PHYs internos, puerto CPU interno a 10 Gbps.
- Consola serie: ns16550 en `0x1fbf0000` (reg-shift 2, io-width 4,
  clock 1843200), **115200 8N1**.

## Esquema A/B (dual boot)
Dos slots de firmware. El bootloader elige el de `imageSequence` mas alto:

| slot | mtd (fabrica) | offset flash |
|---|---|---|
| `tclinux` (main)  | mtd4 | `0xc0000` |
| `tclinux_slave`   | mtd7 | `0x5ac0000` |

El tag `imageSequence` vive en el header de cada slot en el offset `+0x40`.
Flasheamos OpenWrt en el **slave** y dejamos el main de fabrica como red de
seguridad.

> **Leccion cara**: al probar un firmware nuevo, flashealo con `imageSequence`
> MENOR que el bueno. El zloader NO tiene fallback: si el slot elegido no
> bootea, se cuelga (no prueba el otro). Al reves, un fallo = ladrillo.

## Cadena de boot
```
BROM (silicio)
 -> BL2            0x08000000   (init DRAM, lee NAND)
 -> BL31           0x80000000..0x80200000 (monitor seguro / PSCI)  <- memreserve!
 -> U-Boot BL33    0x81E00000
 -> zloader ZyXEL  (standalone 'zld-2.0', cargado de flash a 0x81700000)
 -> FIT boot       (parser propio de ZyXEL, NO libfdt estandar)
```

El **trusted boot no esta forzado**: el BROM corre un BL2 sin firmar. Eso es lo
que permite el rescate (subir nuestro propio codigo). Ver `02-unbrick-bootrom.md`.

Funciones de flash del BL2 (reverseadas, reusadas por el fixer):

| funcion | direccion | ISA | convencion |
|---|---|---|---|
| flash_read  | `0x08001a2c` | Thumb | r0=from, r1=len, r2=buf |
| flash_erase | `0x08001a88` | Thumb | r0=addr, r1=size |
| flash_write | `0x08001aa8` | Thumb | r0=to, r1=len, r2=buf |
| printf      | `0x08014658` | **ARM** | variadica, r0=fmt |

> ARM/Thumb interworking: en `blx`, direccion impar = Thumb, par = ARM. Las
> funciones de flash se llaman con `+1` (impar); `printf` es ARM (par). Llamar
> `printf` como Thumb no imprime nada.
