fog ssh mesh "iptables -P FORWARD ACCEPT"
fog ssh mesh "iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE"
fog ssh mesh "iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE"
