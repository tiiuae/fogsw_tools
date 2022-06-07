FROM ghcr.io/tiiuae/fog-ros-baseimage:stable

# pyserial + pymavlink are dependencies of mavlink_shell.
# unfortunately gcc is required to install pymavlink.
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    python3-pip python3-systemd gcc \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install pyserial pymavlink mavsdk

RUN apt-get update -y && apt-get install -y  \
    ros-${ROS_DISTRO}-bondcpp \
    ros-${ROS_DISTRO}-fognav-msgs \
    ros-${ROS_DISTRO}-nav-msgs \
    ros-${ROS_DISTRO}-geometry-msgs \
    ros-${ROS_DISTRO}-octomap-msgs \
    ros-${ROS_DISTRO}-shape-msgs \
    ros-${ROS_DISTRO}-std-msgs \
    ros-${ROS_DISTRO}-sensor-msgs \
    ros-${ROS_DISTRO}-visualization-msgs \
    ros-${ROS_DISTRO}-tf2 \
    ros-${ROS_DISTRO}-tf2-eigen \
    ros-${ROS_DISTRO}-tf2-geometry-msgs \
    ros-${ROS_DISTRO}-trajectory-msgs \
    ros-${ROS_DISTRO}-ros2bag \
    ros-${ROS_DISTRO}-rosbag2-storage-default-plugins\
    && rm -rf /var/lib/apt/lists/*
WORKDIR /fog-tools

# Install pip and python dependencies
# RUN python3 -m pip install systemd

# make all commands in /fog-tools/* invocable without full path
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/fog-tools

# these do some of the things $ source /opt/ros/ROS_DISTRO/setup.bash does. we try
# to do this as not to require a separate shell just to prepare for launching the actual tool from fog-tools.
ENV PYTHONPATH=/opt/ros/${ROS_DISTRO}/lib/python3.8/site-packages
ENV LD_LIBRARY_PATH=/opt/ros/${ROS_DISTRO}/opt/yaml_cpp_vendor/lib:/opt/ros/${ROS_DISTRO}/lib/x86_64-linux-gnu:/opt/ros/${ROS_DISTRO}/lib

COPY src/ /fog-tools/

WORKDIR /tools-data

CMD ["ls", "-1", "/fog-tools"]
