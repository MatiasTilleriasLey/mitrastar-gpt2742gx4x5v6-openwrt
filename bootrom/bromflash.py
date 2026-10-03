#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Airoha BootROM XMODEM-CRC uploader.

Espera el prompt "Press x" del BootROM, manda una 'x', y sube el archivo
por XMODEM-CRC (bloques de 128 B). Se usa para inyectar el fixer BL2 cuando
el equipo esta brickeado.

Uso:  bromflash.py <archivo> [--port /dev/ttyUSB0] [--1k]
Flujo: ejecuta el script, despues mante RESET y da corriente al equipo.
"""
import serial, time, sys, re, argparse

def crc16(data):               # CRC16/XMODEM
    c = 0
    for b in data:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) if (c & 0x8000) else (c << 1)
            c &= 0xffff
    return c

SOH, STX, EOT, ACK, NAK, C = 0x01, 0x02, 0x04, 0x06, 0x15, 0x43

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--port", default="/dev/ttyUSB0")
ap.add_argument("--baud", type=int, default=115200)
ap.add_argument("--1k", dest="k1", action="store_true", help="bloques de 1024 B")
ap.add_argument("--timeout", type=int, default=600, help="espera del 'Press x' (s)")
a = ap.parse_args()

data = open(a.file, "rb").read()
bs = 1024 if a.k1 else 128
s = serial.Serial(); s.port = a.port; s.baudrate = a.baud; s.timeout = 0
s.dtr = False; s.rts = False; s.open()

print(f"[*] espera 'Press x' (mante RESET + da corriente). {a.file} {len(data)}B blk={bs}", flush=True)
buf = b""; got_C = False; t0 = time.time(); last_x = 0; xcount = 0
while time.time() - t0 < a.timeout:
    d = s.read(256)
    if d:
        buf += d
    now = time.time()
    seen_prompt = (b'ress' in buf) or (b'rmwar' in buf)   # "Press x" / "firmware"
    if seen_prompt and buf.count(bytes([C])) < 3 and now - last_x > 2.0 and xcount < 1:
        s.write(b"x"); last_x = now; xcount += 1
    if buf.count(bytes([C])) >= 3:
        got_C = True
        print(f"[+] flood de 'C' tras {xcount} 'x' -> XMODEM", flush=True)
        time.sleep(0.1); s.read(4096); break
    time.sleep(0.01)
if not got_C:
    print("[!] no llegue al handshake 'C'", flush=True); sys.exit(1)

time.sleep(0.1); s.read(4096)
blk = 1; off = 0; s.timeout = 1
while off < len(data):
    chunk = data[off:off + bs]
    chunk = chunk + bytes([0x1a] * (bs - len(chunk)))
    pkt = bytes([STX if bs == 1024 else SOH, blk & 0xff, (~blk) & 0xff]) + chunk
    cc = crc16(chunk); pkt += bytes([cc >> 8, cc & 0xff])
    ok = False
    for _ in range(25):
        s.write(pkt); r = s.read(1)
        if r and r[0] == ACK: ok = True; break
        if r and r[0] in (NAK, C): time.sleep(0.01); continue
        time.sleep(0.01)
    if not ok:
        if off >= len(data) - 2048:          # buffer del BROM lleno: cerrar
            print(f"[i] fin del buffer BROM en 0x{off:x} -> EOT", flush=True); break
        print(f"[!] GLITCH en blk {blk} (0x{off:x}) -> abort (reintenta)", flush=True)
        sys.exit(3)
    off += bs; blk += 1
    if blk % 128 == 0: print(f"  {off}/{len(data)}", flush=True)

for _ in range(6):
    s.write(bytes([EOT])); r = s.read(1)
    if r and r[0] == ACK: break
print("[+] EOT ACK - upload completo", flush=True)
s.timeout = 0; end = time.time() + 45; out = b""
while time.time() < end:
    dd = s.read(256); out += dd or b""
print("=== salida post-upload ===", flush=True)
print(re.sub(b'\r', b'\n', out).decode('latin1', 'replace')[:1800], flush=True)
