import html, subprocess, os, sys, shutil

CAPS = [
 ("cap1-brick.txt",       "cap1-brick.png",        "El brick — red muerta en U-Boot + system halt"),
 ("cap2-brom-pressx.txt", "cap2-brom-pressx.png",  "BootROM Airoha — 'Press x' + handshake XMODEM (CCC)"),
 ("cap3-dram.txt",        "cap3-dram.png",         "BL2 corriendo desde RAM via BootROM — init de DRAM"),
 ("cap4-bl2-disasm.txt",  "cap4-bl2-disasm.png",   "Desensamblado BL2 — el literal 0xbcc (buffer de flash_read)"),
 ("cap5-readonly-seq.txt","cap5-readonly-seq.png", "Fixer read-only — valida el offset del slave"),
 ("cap6-write-D.txt",     "cap6-write-D.png",      "Fixer de escritura (88 bytes) — 'D' = erase+write OK"),
 ("cap7-factory-boot.txt","cap7-factory-boot.png", "Unbrick confirmado — main>slave, factory Linux arranca"),
 ("cap8-openwrt-fail.txt","cap8-openwrt-fail.png", "OpenWrt — elige slave, verifica hashes, FDT_ERR_BADSTRUCTURE"),
 ("cap9-bootflow.txt","cap9-bootflow.png","Boot flow del fallo - Parse second image fail + BADSTRUCTURE"),
 ("cap10-factory-fit.txt","cap10-factory-fit.png","FIT de fabrica (bootea) - fdt@1 primero + filesystem@1"),
 ("cap11-our-fit.txt","cap11-our-fit.png","Nuestro FIT (falla) - kernel primero, sin filesystem"),
 ("cap12-solution.txt","cap12-solution.png","La solucion - TRANSITION: swap solo el kernel"),
 ("cap13-cmdline.txt","cap13-cmdline.png","Credenciales filtradas en la cmdline del kernel (enmascaradas)"),
 ("cap14-asm.txt","cap14-asm.png","Assembly ARM: como libcccrdm.so ejecuta openssl con la clave incrustada"),
]

def color(line):
    l = line.lower()
    import re as _re
    if ('LA CLAVE' in line): return '#ffbd2e'
    if _re.match(r'\s+[0-9a-f]{3,8}:', line): return '#d2a8ff'
    if any(k in l for k in ['fail','halt','error','badstructure','not found','can\'t get','abort','panic']):
        return '#ff6b6b'
    if any(k in line for k in ['FIXER_SLAVE_SEQ','DRAM size=512MB']) or line.strip()=='D':
        return '#7ee787'
    if any(k in l for k in ['crc32+','sha1+','booting from second','imagesequence','press x','ccc','econet','tapi','slic','found!','dram size']):
        return '#79c0ff'
    if ('username=' in line) or ('password=' in line):
        return '#ffbd2e'
    if line.startswith(' 8000') or line.lstrip().startswith(';'):
        return '#d2a8ff'
    if line.startswith('#') or line.startswith('$'):
        return '#8b949e'
    return '#c9d1d9'

def build(txt, title):
    lines = txt.rstrip('\n').split('\n') if txt.strip() else ['(vacio)']
    rows = '\n'.join(f'<div class="ln" style="color:{color(x)}">{html.escape(x) or "&nbsp;"}</div>' for x in lines)
    h = 92 + len(lines)*23 + 28
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#010409;font-family:'DejaVu Sans Mono',monospace}}
.win{{width:940px;background:#0d1117;border:1px solid #30363d;border-radius:10px;overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,.6)}}
.bar{{background:#161b22;padding:11px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid #30363d}}
.dot{{width:12px;height:12px;border-radius:50%}}
.r{{background:#ff5f56}}.y{{background:#ffbd2e}}.g{{background:#27c93f}}
.ttl{{color:#8b949e;font-size:13px;margin-left:12px;font-family:'DejaVu Sans Mono',monospace}}
.body{{padding:16px 18px;font-size:15px;line-height:23px}}
.ln{{white-space:pre-wrap;word-break:break-word}}
.cap{{color:#6e7681;font-size:12px;padding:4px 18px 14px;font-style:italic}}
</style></head><body>
<div class="win">
 <div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
   <span class="ttl">UART &nbsp;115200 8N1 &nbsp;—&nbsp; /dev/ttyUSB0</span></div>
 <div class="body">{rows}</div>
 <div class="cap">{html.escape(title)}</div>
</div></body></html>''', 970, h

os.makedirs('./.render', exist_ok=True)
chromium = shutil.which('chromium') or '/snap/bin/chromium'
ok=0
for src,out,title in CAPS:
    if not os.path.exists(src):
        print("skip (no existe):",src); continue
    txt = open(src,encoding='utf-8',errors='replace').read()
    page,W,H = build(txt,title)
    hf=f'./.render/_{out}.html'; open(hf,'w').write(page)
    r=subprocess.run([chromium,'--headless','--no-sandbox','--hide-scrollbars','--force-device-scale-factor=2',
        f'--screenshot={os.path.abspath(out)}',f'--window-size={W},{H}',f'file://{hf}'],
        capture_output=True,timeout=60)
    if os.path.exists(out): print("OK",out,os.path.getsize(out),"bytes"); ok+=1
    else: print("FALLO",out,r.stderr.decode()[-200:])
print(f"\n{ok}/{len(CAPS)} imagenes generadas")
