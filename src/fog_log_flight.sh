#!/bin/bash

source /opt/ros/galactic/setup_fog.sh

LOG_FOLDER_NAME=flight_logs-$(date +%Y_%m_%d-%H%M%S)
LOG_FOLDER_PATH=/home/sad/${LOG_FOLDER_NAME}
LOG_PIDS=()
NODES_PARAMS_TO_LOG=("bumper" "control_interface" "navigation")

mkdir ${LOG_FOLDER_PATH}

function start_service_logging () {
    RUNNING_SINCE=$(uptime -s)
    echo "journalctl -u $1 -f -S \"${RUNNING_SINCE}\" > ${LOG_FOLDER_PATH}/${1%".service"}.log"
    journalctl -u $1 -f -S "${RUNNING_SINCE}" > ${LOG_FOLDER_PATH}/${1%".service"}.log &
    LOG_PIDS+=($!)
}

# Cloud/mission
start_service_logging cloud_link.service
start_service_logging mission-data-recorder.service
start_service_logging mission_engine.service
start_service_logging ota_update.service
start_service_logging provisioning-agent.service
start_service_logging update_agent.service

# Mesh
start_service_logging mesh-init.service
start_service_logging mesh_pub.service
start_service_logging mesh.service

# F4F
# start_service_logging bumper.service
start_service_logging control_interface.service
start_service_logging navigation.service
# start_service_logging odometry2.service
start_service_logging octomap_server2.service
start_service_logging mocap_pose.service
start_service_logging rplidar.service

# Flight controller
start_service_logging agent_protocol_splitter.service
start_service_logging mavlink-router.service
start_service_logging micrortps_agent.service

start_service_logging depthai_ctrl.service
start_service_logging depthai_gstreamer_node.service
start_service_logging mocap_pose.service

# FOG package list
if [ -e /usr/bin/fogsw_package_list.sh ]; then
    /usr/bin/fogsw_package_list.sh > ${LOG_FOLDER_PATH}/fogsw_package_list.log
fi

if [ -e /usr/bin/mesh_installation_check.sh ]; then
    sudo /usr/bin/mesh_installation_check.sh > ${LOG_FOLDER_PATH}/mesh_installation_check.log
fi

# Get parameters of some nodes.
for NODE in "${NODES_PARAMS_TO_LOG[@]}"; do
    ros2 param dump --output-dir ${LOG_FOLDER_PATH} /${DRONE_DEVICE_ID}/${NODE}
done

# ROS2 bag.
# NOTE: fog_record_bag_all_topics.sh will block until the user stops the script.
pushd ${LOG_FOLDER_PATH}
/usr/bin/fog_record_bag_all_topics.sh
popd

for PID in "${LOG_PIDS[@]}"; do
    echo "kill $PID"
    kill $PID
done

echo "Packing flight logs."
tar -czvf ${LOG_FOLDER_PATH}.tgz ${LOG_FOLDER_PATH}

exit 0
