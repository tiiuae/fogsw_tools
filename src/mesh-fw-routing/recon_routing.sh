fog ssh mesh "route del default gw 192.168.200.1 eth0 && route add default gw 192.168.1.10 bat0"
fog ssh app	"route del default gw 192.168.200.1 eth0 && route add default gw 192.168.200.3 eth0"
route del default gw 192.168.200.1 foglan && route add default gw 192.168.200.3 foglan
fog ssh connection "route del default gw 172.18.32.1 wlp0s4u1 && route add default gw 192.168.200.3 eth0"

fog ssh mesh "route del default gw 192.168.200.1 eth0 && route add default gw 192.168.1.10 bat0" && fog ssh app "route del default gw 192.168.200.1 eth0 && route add default gw 192.168.200.3 eth0" && route del default gw 192.168.200.1 foglan && route add default gw 192.168.200.3 foglan && fog ssh connection "route del default gw 172.18.32.1 wlp0s4u1 && route add default gw 192.168.200.3 eth0"