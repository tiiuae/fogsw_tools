fog ssh connection "iptables -P FORWARD ACCEPT"
fog ssh connection "iptables -t nat -A POSTROUTING -s 192.168.0.0/16 -j MASQUERADE"
fog ssh connection "route del default gw 172.18.32.1 wlp0s5u1 && route add default gw 192.168.32.1 bat0"

fog ssh connection "mesh-11s.sh mesh 192.168.32.10 255.255.255.0 00:11:22:33:44:55 1234567890 nickel 5745 30 cn"
