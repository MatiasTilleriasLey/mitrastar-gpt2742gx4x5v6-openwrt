#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Ensambla la imagen flasheable para el MitraStar GPT-2742GX4X5v6.

Layout final (lo que lee el zloader ZyXEL + lo que parte mtdsplit):

    [ header MitraStar 0x274 ][ FIT embebido ][ padding 0xFF ][ squashfs crudo ]
      ^ del dump de fabrica     ^ fdt+kernel    a borde de        ^ lo monta como
        con 3 campos tocados      +filesystem   erase-block (128K)   rootfs via mtdsplit

Campos del header que se recalculan:
    [0x24] = tamano del FIT            (4 B LE)
    [0x40] = imageSequence             (4 B LE; mas alto que el main para bootear el slave)
    [0x84] = zlib.crc32(FIT) ^ 0xFFFFFFFF   (el "verify kernel" del bootloader BL33)

El squashfs se pega en roundup_eb(0x274 + FITsize) porque mtdsplit_fit escanea
en limites de erase-block desde ahi (ver docs/03-image-fit-wrapper.md).

El DTB debe tener la particion del slot labeleada "firmware" con
'openwrt,fit-offset = <0x274>' para que mtdsplit halle el FIT tras el header.
"""
import argparse, os, shutil, subprocess, tempfile, zlib

EB = 0x20000          # erase block de la W25N02KV (128 KiB)
HDR = 0x274           # header MitraStar
MAGIC = b"\x9c\xfc\xd0\x04"

def roundup_eb(x):
    return x if x % EB == 0 else ((x // EB) + 1) * EB

ap = argparse.ArgumentParser()
ap.add_argument("--dtb", required=True, help="device tree blob (.dtb) del kernel")
ap.add_argument("--kernel-lzma", required=True, help="Image del kernel comprimida con lzma (magic 0x6d)")
ap.add_argument("--squashfs", required=True, help="root squashfs (xz, block 256K)")
ap.add_argument("--factory-dump", required=True,
                help="dump de un slot de fabrica (p.ej. mtd de tclinux): se usan sus primeros 0x274 B")
ap.add_argument("--its", default=os.path.join(os.path.dirname(__file__), "fit.its"))
ap.add_argument("--mkimage", default="mkimage", help="path a mkimage (staging_dir/host/bin/mkimage de OpenWrt)")
ap.add_argument("--seq", type=lambda s: int(s, 0), default=0x01000007)
ap.add_argument("-o", "--out", default="owrt-final.bin")
a = ap.parse_args()

with tempfile.TemporaryDirectory() as td:
    # el .its hace /incbin/ de estos nombres exactos
    shutil.copy(a.dtb,         os.path.join(td, "fit_dtb_fitblk.bin"))
    shutil.copy(a.kernel_lzma, os.path.join(td, "kernel_lzma_fitblk.bin"))
    shutil.copy(a.squashfs,    os.path.join(td, "root.squashfs"))
    its = os.path.join(td, "fit.its"); shutil.copy(a.its, its)
    itb = os.path.join(td, "fit.itb")
    subprocess.run([a.mkimage, "-f", its, itb], cwd=td, check=True,
                   stdout=subprocess.DEVNULL)
    fit = open(itb, "rb").read()

sq = open(a.squashfs, "rb").read()
hdr = bytearray(open(a.factory_dump, "rb").read(HDR))
assert bytes(hdr[:4]) == MAGIC, "el factory-dump no arranca con el magic MitraStar 9cfcd004"

fs = len(fit)
sq_off = roundup_eb(HDR + fs)
img = bytearray(b"\xff" * (sq_off + len(sq)))
img[0:HDR] = hdr
img[HDR:HDR + fs] = fit
img[sq_off:sq_off + len(sq)] = sq
img[0x24:0x28] = fs.to_bytes(4, "little")
img[0x40:0x44] = a.seq.to_bytes(4, "little")
crc = (zlib.crc32(fit) ^ 0xFFFFFFFF) & 0xFFFFFFFF
img[0x84:0x88] = crc.to_bytes(4, "little")

# chequeos (si algo de esto falla, el bootloader rechaza o no montea)
assert img[HDR:HDR + 4] == b"\xd0\x0d\xfe\xed", "FIT magic ausente en 0x274"
assert bytes(img[sq_off:sq_off + 4]) == b"hsqs", "squashfs mal alineado"
assert (zlib.crc32(bytes(img[HDR:HDR + fs])) ^ 0xFFFFFFFF) & 0xFFFFFFFF == crc

open(a.out, "wb").write(img)
print(f"{a.out}: {len(img)} B  FIT={fs} (0x{fs:x})  squashfs@0x{sq_off:x}  "
      f"seq=0x{a.seq:08x}  crc@0x84=0x{crc:08x}")
