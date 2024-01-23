FROM ghcr.io/tiiuae/fog-ros-baseimage:v3.1.0

RUN apt update \
    && apt install -y --no-install-recommends \
        mavsdk \
        pymavlink \
        python3 \
        python3-future \
        python3-lxml \
        python3-pip \
        python3-pyserial \
        python3-setuptools \
        python3-wheel \
        rosbag2 \
        rosbag2-py \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

ARG BUILDARCH
ARG TARGETARCH

# For qemu emulated arm64 builds, the pip3 install takes a lot of time.
# This makes it so that at least for the native builds, we have the library.
RUN if [ "$BUILDARCH" = "$TARGETARCH" ]; then \
        pip3 install mavsdk; \
    fi

WORKDIR /fog-tools

# make all commands in /fog-tools/* invocable without full path
ENV PATH=$PATH:/fog-tools
ENV PYTHONPATH=/usr/lib/python3.10/site-packages

COPY src/ /fog-tools/

WORKDIR /tools-data

CMD ["ls", "-1", "/fog-tools"]
ENTRYPOINT [ "/bin/bash", "-c" ]
