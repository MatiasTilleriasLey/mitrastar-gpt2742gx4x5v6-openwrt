# 01 — Puente UART y reconocimiento

## El puente
No hace falta un adaptador USB-serie dedicado: cualquier placa **ESP32** trae
un **CP2102** (conversor USB↔serie). Se deja el ESP32 en reset permanente
(`EN` a GND) y se usa solo su CP2102:

```
ESP32 EN  -> GND         (micro en reset, no molesta)
ESP32 TX0 -> router TX
ESP32 RX0 -> router RX
GND comun. Sin alimentar desde el ESP32.
```

`dmesg`: `cp210x converter now attached to ttyUSB0`. Consola a **115200 8N1**.

## Root por el cable
La CLI de fabrica por SSH es una jaula restringida. Pero **la CLI del cable
serie no es la misma que la de SSH**: expone mas subcomandos, entre ellos `sh`.

```
Login: <usuario-supervisor>
Password: ********
> sh
BusyBox built-in shell
# id
uid=0(...) gid=0(root)
```

El usuario supervisor y su clave dependen de cada equipo (la clave se deriva
del numero de serie). No se publican aca.

## Dump (red de seguridad)
Este BusyBox no trae `dd`. Se exfiltra cada particion con `cat` + `nc`:

```sh
# en la PC:      nc -lnp 9000 > mtdN.bin
# en el router:  cat /dev/mtdblockN | nc <ip-pc> 9000
```

Guarda al menos el slot `tclinux` completo (tiene el header MitraStar que
`build-image.py` necesita) y el `bootloader` (mtd0, para el fixer BL2).
