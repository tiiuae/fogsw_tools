#!/bin/bash

source /opt/ros/foxy/setup_fog.sh

ros2 bag record /$DRONE_DEVICE_ID/PhidgetSpatialIMU_PubSubTopic /$DRONE_DEVICE_ID/PhidgetSpatialMAG_PubSubTopic \
 /$DRONE_DEVICE_ID/RawAudio_PubSubTopic /$DRONE_DEVICE_ID/SensorMag_PubSubTopic /$DRONE_DEVICE_ID/SensorCombined_PubSubTopic \
 /$DRONE_DEVICE_ID/VehicleStatus_PubSubTopic \
 --qos-profile-overrides-path /opt/ros/foxy/share/mission-data-recorder/fog_qos_overrides.yaml &
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
