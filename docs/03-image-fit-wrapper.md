# 03 — Imagen: FIT, wrapper MitraStar y rootfs

El zloader de ZyXEL no bootea una imagen generica de OpenWrt. Hay tres muros.

## Muro 1: topologia del FIT
El parser FIT del zloader es **propio** (no libfdt). Exige la topologia de
fabrica: nodo `fdt@1` **primero**, un `kernel@1`, y un `filesystem@1` con el
rootfs adentro; `conf@1` referencia los tres. Naming con `@` (no `-1`), hashes
crc32+sha1. Ver `image/fit.its`.

Una imagen generica (kernel primero, 2 nodos) da `FDT_ERR_BADSTRUCTURE`.

## Muro 2: el wrapper MitraStar y el CRC
El slot no empieza con el FIT, sino con un **header propietario de 0x274 bytes**
(magic `9cfc d004`). Campos que importan:

| offset | campo |
|---|---|
| `0x24` | tamano del FIT |
| `0x40` | `imageSequence` (mas alto que el main para bootear el slave) |
| `0x84` | CRC del FIT (el "verify kernel" del BL33) |

El BL33 (U-Boot, base `0x81E00000`) tiene en `0x81e1f200` un CRC32 sobre el FIT
(init `0xFFFFFFFF`, **sin** XOR final) comparado contra `[0x84]`. En Python:

    crc = zlib.crc32(FIT) ^ 0xFFFFFFFF

`build-image.py` recalcula los tres campos. Validado contra la imagen de
fabrica (coincide al bit).

## Muro 3: load address y el rootfs
- **Load address**: el kernel ARM se descomprime con `TEXT_OFFSET=0x8000`.
  Pero `BL31` vive en el memreserve `0x80000000..0x80200000`. Cargar en
  `0x80008000` lo pisa -> cuelga en `psci: probing...`. Solucion: base de
  memoria del DTB en `0x80200000`, kernel en **`0x80208000`** (en `fit.its`).
- **Rootfs**: el zloader inyecta `root=/dev/mtdblock6` en el cmdline (una
  particion vacia). Dos piezas lo arreglan:
  1. **mtdsplit**: la particion del slot se labelea `"firmware"` y lleva
     `openwrt,fit-offset = <0x274>` (para saltar el header). mtdsplit_fit halla
     el FIT, y busca el squashfs **appendeado despues del FIT**, en el proximo
     borde de erase-block. Crea las particiones `kernel` y `rootfs`.
  2. **`CONFIG_CMDLINE_FORCE`**: borra el `root=` del zloader, para que
     `mtdcore` auto-montee la particion llamada `rootfs`
     (`CONFIG_MTD_ROOTFS_ROOT_DEV`).

El layout final que arma `build-image.py`:
```
[ header 0x274 ][ FIT (fdt+kernel+filesystem) ][ 0xFF... ][ squashfs crudo ]
                                                 ^ pad a   ^ roundup_eb(0x274+FITsize)
                                                   128 KiB    = donde mtdsplit lo busca
```
