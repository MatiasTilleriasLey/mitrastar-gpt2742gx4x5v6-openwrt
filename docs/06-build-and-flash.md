# 06 — Build de punta a punta y flasheo

## 1. OpenWrt
Base: OpenWrt con el target **airoha / en7523** y kernel **6.18**. Partimos de
un port comunitario del EN7523 y rebasamos los parches al mainline (quilt).

Aplica los simbolos de `openwrt/config-fragment.txt` a los config fragments del
target. En resumen:
- `CONFIG_NET_DSA=y` (switch).
- `CONFIG_CMDLINE_FORCE=y` + el `CONFIG_CMDLINE` + los disables del choice (rootfs).
- `CONFIG_CFG80211_HEADERS=y` (WiFi; ya suele venir de upstream).

Build:
```sh
make -j$(nproc)
```
De ahi salen: `vmlinux`, el DTB, y `root.squashfs` (con los modulos WiFi
recompilados — ver `docs/05`).

## 2. Comprimir el kernel
El zloader espera el kernel en **lzma** (magic `0x6d`):
```sh
arm-openwrt-linux-muslgnueabi-objcopy -O binary -S vmlinux Image
staging_dir/host/bin/lzma e Image kernel.lzma -lc1 -lp2 -pb2
```

## 3. Ensamblar la imagen
```sh
image/build-image.py \
  --dtb         en7523-mitrastar-gpt-2742gx4x5v6.dtb \
  --kernel-lzma kernel.lzma \
  --squashfs    root.squashfs \
  --factory-dump mi_tclinux_dump.bin \
  --mkimage     staging_dir/host/bin/mkimage \
  -o owrt-final.bin
```
El `--factory-dump` es un volcado de un slot de fabrica (de TU equipo): se usan
sus primeros `0x274` bytes como header. El DTB tiene que tener la particion del
slot labeleada `"firmware"` con `openwrt,fit-offset = <0x274>`.

## 4. Flashear
- **Primera vez** (o si brickeaste): por el BootROM. Baja el `imageSequence`
  del slave con el fixer, bootea el main de fabrica, y flashea el slave desde
  ahi con `flash/flash-from-factory.py`. Ver `docs/02`.
- **Despues**: en caliente desde OpenWrt (`flash/flash-in-place.md`), ya sin
  BootROM.

## 5. Configurar
`http://192.168.1.1` (LuCI) o uci. Para el AP:
```sh
uci set wireless.radio0.disabled='0'
uci set wireless.default_radio0.ssid='MiRed'
uci set wireless.default_radio0.encryption='psk2'
uci set wireless.default_radio0.key='<password>'
uci commit wireless && wifi up
```
(idem radio1). Las dos radios salen en 5 GHz; para no auto-interferir, poneles
canales distintos (p.ej. 36 y 149).
