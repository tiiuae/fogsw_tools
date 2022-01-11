#!/bin/bash

/usr/bin/dpkg -l \
  agent-protocol-splitter \
  cloud-link \
  mission-engine \
  fogsw-configs \
  fog-sw-systemd-services \
  libsurvive \
  mavlink-router \
  ros-galactic-depthai-ctrl \
  ros-galactic-indoor-pos \
  ros-galactic-mesh-com \
  ros-galactic-px4-msgs \
  ros-galactic-px4-ros-com \
  mission-data-recorder \
  ros-galactic-control-interface \
  ros-galactic-fog-msgs \
  ros-galactic-mocap-pose \
  ros-galactic-navigation \
#  ros-galactic-fog-bumper \
#  ros-galactic-odometry2 \
  ros-galactic-octomap-server2 \
  ros-galactic-rplidar-ros2 \
  rtl8812au-kmod \
  px4-firmware-updater \
  wpasupplicant \
  linux-image-5.11.22-git20210928.2710467-fog \
  wifi-firmware
/usr/bin/dpkg -l provisioning-agent
/usr/bin/dpkg -l ros-galactic-update-agent

exit 0
