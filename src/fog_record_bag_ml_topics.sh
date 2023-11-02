#!/bin/bash

source /etc/profile.d/ros/setup.bash
source ~/respeaker_array/install/setup.bash

ros2 bag record --qos-profile-overrides-path /opt/ros/foxy/share/mission-data-recorder/fog_qos_overrides.yaml \
     /$DRONE_DEVICE_ID/PhidgetSpatialIMU_PubSubTopic /$DRONE_DEVICE_ID/PhidgetSpatialMag_PubSubTopic \
     /$DRONE_DEVICE_ID/RawAudio_PubSubTopic /$DRONE_DEVICE_ID/SensorMag_PubSubTopic \
     /$DRONE_DEVICE_ID/SensorCombined_PubSubTopic /$DRONE_DEVICE_ID/VehicleStatus_PubSubTopic &
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
