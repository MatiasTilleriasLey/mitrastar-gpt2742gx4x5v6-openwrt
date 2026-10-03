#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Flashea la imagen al slot slave desde el Linux de FABRICA, por serie.

Loguea en la CLI de fabrica (usuario supervisor), escapa a shell, baja la
imagen desde un server HTTP de tu PC y la escribe en la particion del slave
con la herramienta 'mtd' del propio firmware. Despues rebootea: el zloader
elige el slave (imageSequence mas alto) y bootea OpenWrt.

Necesitas estar en el Linux de fabrica (bootea el main con el fixer BL2, ver
docs/02-unbrick-bootrom.md) y servir la imagen:  python3 -m http.server 8188

Credenciales: el usuario/clave del supervisor NO van hardcodeados. Pasalos por
env (FACTORY_USER / FACTORY_PASS) o --user/--pass. La clave es derivada del
serial del equipo; averigua la tuya (no se publica aca).

Uso:
  FACTORY_PASS=xxxx ./flash-from-factory.py --url http://192.168.1.117:8188/owrt-final.bin
"""
import serial, time, re, sys, os, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--port", default="/dev/ttyUSB0")
ap.add_argument("--baud", type=int, default=115200)
ap.add_argument("--url", required=True, help="URL HTTP de la imagen owrt-final.bin")
ap.add_argument("--size", type=int, default=0, help="tamano exacto en bytes (0 = no verificar)")
ap.add_argument("--part", default="tclinux_slave", help="particion mtd destino (nombre de fabrica)")
ap.add_argument("--user", default=os.environ.get("FACTORY_USER", "Support"))
ap.add_argument("--pw", default=os.environ.get("FACTORY_PASS", ""))
a = ap.parse_args()
if not a.pw:
    sys.exit("falta la clave: FACTORY_PASS=... o --pw")

s = serial.Serial(); s.port = a.port; s.baudrate = a.baud; s.timeout = 0
s.dtr = False; s.rts = False; s.open(); buf = b""

def rd(t):
    global buf; e = time.time() + t
    while time.time() < e:
        d = s.read(8192)
        if d: buf += d
        time.sleep(0.02)
def tx(x):
    s.reset_input_buffer()
    for ch in x: s.write(ch.encode()); time.sleep(0.008)
    s.write(b"\r")
def tail(n=500): return re.sub(b'\r', b'', buf[-9000:]).decode('latin-1', 'replace')[-n:]
def wait(pats, t):
    e = time.time() + t
    while time.time() < e:
        rd(0.25)
        for p in pats:
            if p in tail(): return p
    return None

rd(0.6); tx(""); rd(0.8)
if "#" not in tail(30):
    for _ in range(8):
        tx("")
        w = wait(["ogin:", "#", ">"], 6)
        if w == "#": break
        if w == ">": tx("sh")
        if wait(["ogin:"], 1):
            tx(a.user); wait(["assword", "PASSWORD"], 6); tx(a.pw)
            if wait([">"], 6): tx("sh")
            if wait(["#"], 4): break
if "#" not in tail(30):
    sys.exit("NO_SHELL (login fallo)")
print("SHELL OK", flush=True)

chk = f" && test $(wc -c <o.bin) = {a.size}" if a.size else ""
echo_sz = a.size or "$(wc -c <o.bin)"
cmd = (f"cd /tmp && wget -q -O o.bin {a.url}{chk} && echo DLOK"
       f" && /userfs/bin/mtd -f -e {a.part} write o.bin {echo_sz} 0 {a.part} >/tmp/w.log 2>&1"
       f" && echo FLASHOK && sync && sleep 1 && reboot")
buf = b""; tx(cmd)
e = time.time() + 220
while time.time() < e:
    rd(0.2)
    if b"FLASHOK" in buf: break
print("RESULT:", re.sub(b'\r', b'\n', buf[-400:]).decode('latin1', 'replace'), flush=True)
