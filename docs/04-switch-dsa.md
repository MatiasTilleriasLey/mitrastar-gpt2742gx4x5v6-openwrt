# 04 — Switch DSA (los 4 puertos LAN)

Al bootear OpenWrt, solo aparecia `eth0` (el enlace interno CPU↔switch). Los
jacks fisicos no pasaban trafico.

## Causa: un typo de config
El EN7523 **si** tiene driver de switch en el kernel 6.18: es **DSA**, con
`mt7530-mmio` matcheando el `compatible = "airoha,en7523-switch"`. Pero el
config del target se contradecia:

```
CONFIG_NET_DSA_MT7530=y
CONFIG_NET_DSA_MT7530_MMIO=y
# CONFIG_NET_DSA is not set      <- todo el menu DSA depende de esto
```

Con `NET_DSA` apagado, Kconfig descarta `MT7530` aunque este en `=y`. Fix:
`CONFIG_NET_DSA=y` (ver `openwrt/config-fragment.txt`). Tras el rebuild, los 4
puertos aparecen como `eth1`..`eth4` (conduit `eth0`).

## Nombres de los puertos
Los nodos `port@1..4` del DTS **no llevan `label`**. Sin label, DSA los nombra
`eth%d` (`net/dsa/user.c`): quedan `eth1`..`eth4`, que es justo lo que espera
el `board.d` comunitario.

## Polling en vez de IRQ (workaround)
El nodo `switch@1fb58000` del DTS lleva `interrupt-controller` + `interrupts`.
Lo sacamos para que `mt7530` haga **polling** de los PHYs por MDIO
(`irq=POLL`) en vez de usar el IRQ del switch. (Durante el debug el IRQ parecia
el culpable del cuelgue; resulto que no lo era — ver `05-wifi-cfg80211.md` —
pero el polling quedo porque funciona y es inofensivo.)

## Config de red para AP
El default venia mal para AP (`eth0` en el bridge, `eth1` como WAN). Para AP,
bridgea los 4 puertos y saca el WAN:

```
config device
    option name 'br-lan'
    option type 'bridge'
    list ports 'eth1'
    list ports 'eth2'
    list ports 'eth3'
    list ports 'eth4'
```
