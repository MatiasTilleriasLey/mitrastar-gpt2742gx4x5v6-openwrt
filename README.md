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

## Instalacion paso a paso

Flujo completo, de equipo de fabrica a OpenWrt. El detalle de cada muro esta en
`docs/`; aca va el orden y los comandos.

### 0. Prerequisitos

- **Hardware**: un adaptador **USB-UART 3.3V** (sirve el CP2102 de una ESP32 con
  `EN`→GND). TX/RX/GND a los pads del equipo. Una PC con Linux.
- **Software en la PC**:
  - Toolchain bare-metal: `arm-none-eabi-binutils` (`as`, `ld`, `objcopy`, `objdump`).
  - `python3` + `pyserial`  ·  `dtc`  ·  `squashfs-tools` (`mksquashfs`/`unsquashfs`).
  - `mkimage` (de `u-boot-tools`, o el de `staging_dir/host/bin` del build OpenWrt).
  - El **build system de OpenWrt** (ver [build oficial](https://openwrt.org/docs/guide-developer/toolchain/use-buildsystem)).
- **UART**: `/dev/ttyUSB0`, **115200 8N1**.

### 1. Root en el firmware de fabrica (UART)

Enchufa la UART, abri la consola (`picocom -b 115200 /dev/ttyUSB0`), energiza y
logueate. En la consola **serie** (no la de SSH) el usuario de soporte puede
escapar a un shell con `sh` → caes en BusyBox como `uid=0`.  Detalle:
[`docs/01-uart-recon.md`](docs/01-uart-recon.md).

### 2. Dump del firmware de fabrica

Necesitas tu propio dump para dos cosas: la **cabecera MitraStar** (`0x274`) que
el bootloader valida, y el **FIP/BL2** sobre el que se construye el fixer.
Con root, exfiltra las particiones por red (este BusyBox no trae `dd`):

```sh
# en la PC:        nc -lnp 9000 > mtd4_tclinux.bin
# en el equipo:    cat /dev/mtdblock4 | nc <ip-pc> 9000     # slot main (header + FIT)
#                  cat /dev/mtdblock0 | nc <ip-pc> 9000     # bootloader (FIP/BL2 para el fixer)
```

Guarda tambien un `mtd4` completo: de ahi salen los primeros `0x274` bytes para
el wrapper. **Verifica por tamano y `sha256`.** Ver [`docs/02-unbrick-bootrom.md`](docs/02-unbrick-bootrom.md).

### 3. Build de OpenWrt

Sobre OpenWrt `main` (SNAPSHOT — el EN7523 y el kernel 6.18 solo estan ahi) con
el target **airoha/en7523**. Aplica los simbolos de kernel de este repo:

```sh
git clone https://github.com/openwrt/openwrt && cd openwrt
./scripts/feeds update -a && ./scripts/feeds install -a
# target airoha/en7523 (+ el device mitrastar; ver openwrt/README.md)
# agrega al fragment del kernel los simbolos de:
cat /ruta/a/este-repo/openwrt/config-fragment.txt   # NET_DSA, CMDLINE_FORCE, CFG80211_HEADERS
make defconfig
make -j$(nproc)
```

Salen `vmlinux` y `root.squashfs`. Ojo: `CONFIG_CMDLINE_FORCE` se pierde si
regeneras el `.config` — mira la nota en `openwrt/README.md`. Detalle del por que
de cada simbolo: [`docs/04-switch-dsa.md`](docs/04-switch-dsa.md) y
[`docs/05-wifi-cfg80211.md`](docs/05-wifi-cfg80211.md).

### 4. Ensamblar la imagen flasheable

El bootloader propietario no acepta una imagen OpenWrt generica: hay que envolver
el FIT en el wrapper MitraStar con el CRC correcto y appendear el squashfs para
que `mtdsplit` lo monte. Eso lo hace `image/build-image.py`:

```sh
# compila el DTB (image/en7523-mitrastar-gpt-2742gx4x5v6.dts) y el kernel lzma, y:
python3 image/build-image.py \
    --its image/fit.its \
    --header-source mtd4_tclinux.bin \   # TU dump: aporta el header 0x274
    --squashfs root.squashfs \
    --seq 0x01000007 \                   # > el imageSequence del slot bueno
    --out owrt-final.bin
```

El script arma el FIT (`mkimage`), le pone el header, calcula
`[0x84] = zlib.crc32(FIT) ^ 0xFFFFFFFF`, y appendea el squashfs en
`roundup_eb(0x274 + FITsize)`. Detalle: [`docs/03-image-fit-wrapper.md`](docs/03-image-fit-wrapper.md).

### 5. Primer flasheo (por BootROM)

Como el equipo sale de fabrica, el primer flasheo va por el BootROM (red de
seguridad: si algo sale mal, se recupera por el mismo camino).

```sh
# a) construi el fixer e inyectalo en TU dump del FIP (offset 0xf66):
bash bootrom/build-fixer.sh            # produce el .bin del parche de 88 bytes
# b) con el equipo apagado: manten RESET, da corriente, soltalo. Aparece "Press x".
python3 bootrom/bromflash.py preloader_fixer_wd.bin   # sube el fixer por XMODEM
#    -> imprime "D": bajo el imageSequence del slot slave.
```

Un power-cycle normal arranca el **Linux de fabrica** (ahora el main gana). Desde
ahi, con red, flashea OpenWrt al slot slave:

```sh
FACTORY_PASS=<tu-pass-supervisor> \
python3 flash/flash-from-factory.py \
    --host <ip-pc> --image owrt-final.bin --partition tclinux_slave
```

Reboot, y el zloader elige el slot nuevo → **arranca OpenWrt**. Paso a paso:
[`docs/06-build-and-flash.md`](docs/06-build-and-flash.md).

### 6. Primer arranque y configuracion

OpenWrt levanta en **`192.168.1.1`** con los 4 puertos LAN en `br-lan`. Abri
**LuCI** en `http://192.168.1.1` (usuario `root`, sin password — ponele una ya).
El WiFi se habilita en *Network → Wireless* (Edit en cada radio: SSID, WPA2/WPA3,
Enable), o por uci.

### 7. Updates posteriores (en caliente, sin BootROM)

Una vez que OpenWrt tiene red, ya no hace falta el baile de RESET. Flasheas en
caliente desde el propio equipo:

```sh
# en el equipo (via ssh/uart):
cd /tmp && wget http://<ip-pc>/owrt-final.bin -O o.bin
mtd -r write o.bin firmware      # reescribe el slot y rebootea solo
```

Ver [`flash/flash-in-place.md`](flash/flash-in-place.md).

## Unbrick — la red de seguridad

**Este equipo es practicamente imposible de brickear de forma permanente**, y eso
es lo que vuelve seguro todo el resto. El hallazgo clave:

- Todos los SoC Airoha/EcoNet tienen un **BootROM en silicio** con recovery por
  UART, y en esta unidad **el arranque seguro (trusted boot) NO esta forzado**:
  el BootROM corre un BL2 sin firmar → podes subir y ejecutar tu propio codigo.
- O sea: pase lo que pase con la NAND, un cable UART de 3 dolares lo revive.
  Sin JTAG, sin programador, sin abrir la caja.

### Como se dispara

```
1. Equipo apagado. Manten RESET apretado.
2. Da corriente (sin soltar RESET).
3. El BROM imprime  "Press x"
4. Manda una 'x'  ->  responde con un flood de 'C' (handshake XMODEM-CRC)
5. Subis un payload por XMODEM (bromflash.py lo hace)
```

### El fixer: recuperar sin driver de NAND propio

El bug clasico es flashear el slot de prueba con `imageSequence` **mayor** que el
bueno: el zloader elige el roto y **no tiene fallback automatico** → bucle de
muerte. La cura es bajarle el `imageSequence` al slot roto para que el zloader
vuelva a elegir el bueno.

En vez de escribir un driver SPI-NAND desde cero, **reverseamos el BL2 de fabrica
y reusamos sus propias funciones de flash** (`flash_read`/`flash_erase`/
`flash_write`, mas `printf`). El fixer es un parche **Thumb de 88 bytes**
inyectado en el FIP (offset de archivo `0xf66`, vaddr `0x08000b68`) que: lee el
bloque 0 del slot roto → baja el `imageSequence` a `0x01000000` → borra y
reescribe.

> ⚠️ **El presupuesto es exactamente 88 bytes** (`0x8000b68`…`0x8000bc0`). Pasarte
> pisa el literal en `0x8000bcc` (el puntero al buffer de `flash_read`) y el fixer
> muere **mudo** justo despues del init de DRAM. Nos costo tres noches. El fixer
> read-only (`fixer_diag.s`) es mas corto y sirve para validar offsets sin escribir.

Cuando el fixer imprime **`D`**, termino bien. Power-cycle normal → arranca el
slot sano. Fuentes del parche en [`bootrom/`](bootrom/), historia completa en
[`docs/02-unbrick-bootrom.md`](docs/02-unbrick-bootrom.md).

> **Regla de oro A/B**: flashea el slot de prueba con `imageSequence` **MENOR** que
> el bueno. Si falla, el bootloader cae solo al estable. Al reves, un fallo = (casi)
> ladrillo.

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
