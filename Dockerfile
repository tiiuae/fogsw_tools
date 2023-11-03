# pyserial + pymavlink are dependencies of mavlink_shell.
# unfortunately gcc is required to install pymavlink for amd64
# and build essentials for other architectures

FROM ghcr.io/tiiuae/fog-ros-baseimage:v3.0.2

RUN apt update \
    && apt install -y --no-install-recommends \
        mavsdk \
        pymavlink \
        python3 \
        python3-future \
        python3-lxml \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        python3-pyserial \
        rosbag2 \
        rosbag2-py \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /fog-tools

# make all commands in /fog-tools/* invocable without full path
ENV PATH=$PATH:/fog-tools
ENV PYTHONPATH=/usr/lib/python3.10/site-packages

COPY src/ /fog-tools/

WORKDIR /tools-data

CMD ["ls", "-1", "/fog-tools"]
