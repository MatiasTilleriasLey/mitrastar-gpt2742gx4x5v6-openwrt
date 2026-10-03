# image — ensamblado de la imagen

- `en7523-mitrastar-gpt-2742gx4x5v6.dts` — el Device Tree que embebemos (slot
  "firmware" con `openwrt,fit-offset=<0x274>`, memoria en 0x80200000, switch en
  polling, nodos WiFi con nvmem).
- `fit.its` — topologia del FIT (fdt@1 primero, kernel lzma load 0x80208000,
  filesystem@1).
- `build-image.py` — FIT (mkimage) + wrapper MitraStar + CRC + append squashfs.

Ver `../docs/03-image-fit-wrapper.md`.
