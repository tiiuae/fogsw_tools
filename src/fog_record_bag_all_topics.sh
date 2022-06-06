#!/bin/bash

source /opt/ros/galactic/setup.bash

template_yamlpath=/fog-tools/qos_overrides/fog_qos_overrides_template.yaml
yamlpath=/fog-tools/qos_overrides/fog_qos_overrides.yaml
sed "s/_DRONE_DEVICE_ID_/${DRONE_DEVICE_ID}/g" ${template_yamlpath} > ${yamlpath}
cat ${yamlpath}
ros2 bag record -a --qos-profile-overrides-path ${yamlpath} &
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
