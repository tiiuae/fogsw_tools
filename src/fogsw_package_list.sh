#!/bin/bash

/usr/bin/dpkg -l \
  agent-protocol-splitter \
  communication-link \
  mission-engine \
  fogsw-configs \
  fog-sw-systemd-services \
  libsurvive \
  mavlink-router \
  ros-foxy-depthai-ctrl \
  ros-foxy-indoor-pos \
  ros-foxy-mesh-com \
  ros-foxy-px4-msgs \
  ros-foxy-px4-ros-com \
  mission-data-recorder \
  ros-foxy-control-interface \
  ros-foxy-fog-msgs \
  ros-foxy-mocap-pose \
  ros-foxy-navigation \
  ros-foxy-octomap-server2 \
  ros-foxy-rplidar-ros2 \
  rtl8812au-kmod \
  px4-firmware-updater \
  wpasupplicant \
  linux-image-5.11.22-git20210928.2710467-fog \
  wifi-firmware
/usr/bin/dpkg -l provisioning-agent
/usr/bin/dpkg -l ros-foxy-update-agent

exit 0
