# pyserial + pymavlink are dependencies of mavlink_shell.
# unfortunately gcc is required to install pymavlink for amd64
# and build essentials for other architectures

FROM ghcr.io/tiiuae/fog-ros-baseimage-builder:v3.0.2

RUN apt update \
    && apt install -y --no-install-recommends \
        python3 \
        python3-pip \
        rosbag2 \
        rosbag2-py \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --upgrade pip \
    && pip install --upgrade \
        setuptools \
        wheel \
    && pip install \
        mavsdk \
        pymavlink \
        pyserial \
    && rm -rf $HOME/.cache/pip/*
    
WORKDIR /fog-tools

# make all commands in /fog-tools/* invocable without full path
ENV PATH=$PATH:/fog-tools
ENV PYTHONPATH=/usr/lib/python3.10/site-packages

COPY src/ /fog-tools/

WORKDIR /tools-data

CMD ["ls", "-1", "/fog-tools"]
