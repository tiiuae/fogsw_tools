fog ssh mesh "iptables -P FORWARD ACCEPT"
fog ssh mesh "iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE"
fog ssh mesh "iptables -t nat -A POSTROUTING -s 192.168.32.0/24 -o eth0 -j MASQUERADE"
fog ssh mesh "mesh-11s.sh mesh 192.168.32.1 255.255.255.0 00:11:22:33:44:55 1234567890 nickel 5745 30 cn"
