# OpenWrt en el MitraStar GPT-2742GX4X5v6 (Airoha EN7523)

Port no oficial de OpenWrt a una ONT MitraStar GPT-2742GX4X5v6 — la caja blanca
que Movistar Chile deja cuando instala fibra. Convertida en **access point
Wi-Fi 6 + switch gestionado** corriendo OpenWrt.

No hay soporte oficial de OpenWrt para este equipo. Partimos de un port
comunitario para otra placa con el mismo SoC y armamos el nuestro. Esto
documenta todo el camino: revivir el equipo por el BootROM, armar una imagen
que el bootloader propietario acepte, prender el switch, y arreglar el crash de
WiFi del kernel 6.18.

> **Resultado**: 4 puertos LAN (DSA) + 2 radios MT7915 Wi-Fi 6, todo en un
> `br-lan`, con LuCI. Se flashea en caliente desde el propio OpenWrt.

## ⚠️ Disclaimer

- **Riesgo de brick.** Escribir la NAND mal te deja el equipo colgado. Hay red
  de seguridad (el BootROM por UART recupera), pero vas bajo tu responsabilidad.
- **Voidea la garantia** y probablemente los terminos con tu ISP.
- El **firmware de fabrica, el BL2/FIP y todo binario del fabricante o del ISP**
  son propiedad de sus duenos. Este repo **no los incluye**; los generas/extraes
  de TU propio equipo. La licencia MIT cubre solo nuestros scripts y docs.
- Credenciales (supervisor, claves del config, del ISP) **no se publican**. Los
  scripts las toman por variable de entorno.

## Hardware

| | |
|---|---|
| SoC | Airoha / EcoNet **EN7523**, 2× Cortex-A53 (kernel ARM aarch32) |
| RAM | 512 MB (base `0x80000000`) |
| Flash | SPI NAND **W25N02KV** 256 MB, erase block 128 KiB |
| WiFi | 2× MediaTek **MT7915** (Wi-Fi 6, por PCIe) |
| Switch | GSW integrado, 4 puertos (DSA via `mt7530-mmio`) |
| Telefonia/GPON | Lantiq PEF32001 + PON EcoNet (drivers cerrados, **no portados**) |
| Boot | BROM → BL2 (`0x08000000`) → BL31 → U-Boot/zloader ZyXEL → FIT |

## Quickstart

1. **Dump** de tu equipo (necesitas serie + root; ver `docs/01-uart-recon.md`).
2. **Build** de OpenWrt con el target airoha/en7523 + los simbolos de
   `openwrt/config-fragment.txt`.
3. **Ensambla** la imagen: `image/build-image.py` (FIT + wrapper MitraStar + squashfs).
4. **Flashea**: la primera vez por el BootROM (`bootrom/`), despues en caliente
   (`flash/flash-in-place.md`).
5. **Configura** por LuCI (`http://192.168.1.1`) o uci.

## Indice de documentacion

| Doc | Tema |
|---|---|
| [00-hardware](docs/00-hardware.md) | SoC, flash, cadena de boot, esquema A/B |
| [01-uart-recon](docs/01-uart-recon.md) | Puente UART (ESP32/CP2102), recon, root |
| [02-unbrick-bootrom](docs/02-unbrick-bootrom.md) | Rescate por BootROM, el fixer BL2 de 88 bytes |
| [03-image-fit-wrapper](docs/03-image-fit-wrapper.md) | FIT, wrapper MitraStar, CRC, load address, rootfs |
| [04-switch-dsa](docs/04-switch-dsa.md) | Switch DSA (el typo de config que lo apagaba) |
| [05-wifi-cfg80211](docs/05-wifi-cfg80211.md) | El crash de 12 bytes de cfg80211 en 6.18 |
| [06-build-and-flash](docs/06-build-and-flash.md) | Build de punta a punta y flasheo |

## Estructura

```
bootrom/   rescate BROM: fixer BL2 (asm) + uploader XMODEM
image/     DTS, .its del FIT, build-image.py (ensamblador de la imagen)
openwrt/   simbolos de config del kernel que agregamos
flash/     flasheo desde fabrica y en caliente
tools/     generador de "capturas" de terminal
docs/      la historia completa, de bajo nivel
```
