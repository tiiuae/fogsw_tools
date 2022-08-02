fog ssh mesh "iptables -P FORWARD ACCEPT"
fog ssh mesh "iptables -t nat -A POSTROUTING -s 192.168.200.0/24 -o bat0 -j MASQUERADE"
