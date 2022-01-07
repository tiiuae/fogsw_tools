#!/bin/bash

source /opt/ros/galactic/setup_fog.sh

ros2 bag record -a --qos-profile-overrides-path /opt/ros/galactic/share/mission-data-recorder/fog_qos_overrides.yaml &
ROS_BAG_PID=$!

echo "Press any key to stop recording."
while [ true ] ; do
    read -t 3 -n 1
    if [ $? = 0 ] ; then
        break
    fi
done

kill ${ROS_BAG_PID}

exit 0
