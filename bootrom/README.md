# bootrom — rescate por BootROM

- `fixer_pw.s` / `fixer_diag.s` — parche Thumb para el BL2 (escritura / read-only).
- `build-fixer.sh` — ensambla el fixer e inyecta en TU dump del FIP (offset 0xf66).
- `bromflash.py` — uploader XMODEM-CRC al BootROM.

Ver `../docs/02-unbrick-bootrom.md`. **El .bin del fixer contiene BL2 de
fabrica: no lo redistribuyas.**
