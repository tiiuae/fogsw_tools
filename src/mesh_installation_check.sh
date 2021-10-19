#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "this script must be run as root:"
    echo "  sudo $0 |& tee logfile.log"
    exit 1
fi

echo "-------------------------------------------------------"
echo "check deb packages.."
PACKAGE_LIST="wifi-firmware wpasupplicant ros-foxy-mesh-com"

for e in $PACKAGE_LIST; do
    apt-cache policy "$e"
done

echo "-------------------------------------------------------"
echo "check systemd files.."
SYSTEMD_LIST="/etc/systemd/system/mesh-init.service \
/etc/systemd/system/mesh.service \
/etc/systemd/system/mesh_pub.service"

for f in $SYSTEMD_LIST; do
    if [ -f "$f" ]; then
        echo Found: "$f"

        service="$(basename -- "$f")"
        echo Saving "$service".log
        journalctl -u "$service" -S today > "$service".log
    else
        echo NOT FOUND: "$f"
    fi
done
echo "-------------------------------------------------------"
echo "commandline tools dependency.."
EXECUTABLE="alfred batadv-vis batctl ifconfig iw kill killall pkill ip route wpa_cli"

for e in $EXECUTABLE; do
    if [ $(which "$e") ]; then
        echo Found: "$e"
    else
        echo FAIL: missing "$e"
    fi
done
echo "-------------------------------------------------------"
echo "ifconfig:"
ifconfig
echo "-------------------------------------------------------"
echo "wifi device status:"
iw dev
echo "-------------------------------------------------------"
echo "wpa status:"
wpa_cli status
echo "-------------------------------------------------------"
echo "batman network status:"
batctl n
echo "-------------------------------------------------------"
echo "netif device status:"
ip -brief link
echo "-------------------------------------------------------"
echo "active routes:"
route
echo "-------------------------------------------------------"
echo "iw dev <wifi> get mesh_param mesh_fwding:"
batctl if | cut -d ":" -f 1 | xargs -I{} iw dev {} get mesh_param mesh_fwding
echo "-------------------------------------------------------"

