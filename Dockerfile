FROM ghcr.io/tiiuae/fog-ros-baseimage-builder:sha-71b9710

# pyserial + pymavlink are dependencies of mavlink_shell.
# unfortunately gcc is required to install pymavlink.
#
# ros-galactic-rosbag2 so we can record ROS bags
RUN apt update \
    && apt install -y --no-install-recommends \
        python3-pip \
        python3 \
        rosbag2 \
        rosbag2-py \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --upgrade pip \
    && pip install --upgrade \
        setuptools \
        wheel \
    && pip install \
        mavsdk \
        pymavlink \
        pyserial \
        systemd

WORKDIR /fog-tools

# Install pip and python dependencies
# RUN python3 -m pip install systemd

# make all commands in /fog-tools/* invocable without full path
ENV PATH=$PATH:/fog-tools

# these do some of the things $ source /opt/ros/ROS_DISTRO/setup.bash does. we try
# to do this as not to require a separate shell just to prepare for launching the actual tool from fog-tools.
ENV PYTHONPATH=/usr/lib/python3.10/site-packages
# ENV LD_LIBRARY_PATH=/opt/ros/galactic/opt/yaml_cpp_vendor/lib:/opt/ros/galactic/lib/x86_64-linux-gnu:/opt/ros/galactic/lib

COPY src/ /fog-tools/

WORKDIR /tools-data

CMD ["ls", "-1", "/fog-tools"]
