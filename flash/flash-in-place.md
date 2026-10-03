# Flasheo en caliente (desde OpenWrt, sin BootROM)

Una vez que OpenWrt bootea y el switch pasa trafico (tenes red), ya no hace
falta el baile de RESET + BootROM. Flasheas desde el propio OpenWrt:

```sh
# 1) en tu PC, serví la imagen:
python3 -m http.server 8188

# 2) en el router (SSH o serie), bajala a RAM y escribila al slot:
cd /tmp
wget -O o.bin http://<IP-de-tu-PC>:8188/owrt-final.bin
mtd -r write o.bin firmware      # 'firmware' = el slot slave; -r rebootea al terminar
```

`mtd -r write` reescribe la particion desde el proceso ya cargado en RAM y
rebootea solo, igual que un sysupgrade. El slot se llama `firmware` en el DTB
de OpenWrt (es la particion del slave, @0x5ac0000).

> El equipo ya se actualiza a si mismo. El BootROM queda solo como red de
> seguridad por si una imagen no bootea.
