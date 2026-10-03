# openwrt — config del kernel

`config-fragment.txt` lista los simbolos que agregamos/corregimos sobre el
target airoha/en7523 (kernel 6.18): switch DSA, cmdline forzado, y el chequeo
de `CFG80211_HEADERS`. Ver `../docs/04` y `../docs/05`.

Si tenes parches propios del target (DTS, drivers), ponelos en `patches/`.
