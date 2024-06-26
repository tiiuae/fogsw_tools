FROM ghcr.io/tiiuae/fog-ros-baseimage:sha-c66a922

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

# make all commands in /fog-tools/* invocable without full path
ENV PATH=$PATH:/fog-tools
ENV PYTHONPATH=/usr/lib/python3.10/site-packages

COPY src/ /fog-tools/

# this dir is mounted to us by at least when running from fog-hyper's `$ fog tool` wrapper.
# the point of it is to make it that if we write files (like recording a ROS bag or
# downloading logs from Flight Controller), they end up in dir that is visible to debug web UI.
WORKDIR /tools-data

# explicitly remove possible entrypoint inherited from base image.
#
# this container shall have no `ENTRYPOINT` because the container is designed to be ran like:
#   `$ docker run --rm -it fogsw-tools TOOL_NAME` and thus `/fog-tools/TOOL_NAME` will be invoked.
# if we set ENTRYPOINT to ["bash", "-c"], the above command would then run something like `bash -c TOOL_NAME`. that would:
# 1. work for single-argument commands (but we'd use shell unnecessarily)
# 2. running `$ docker run .... fogsw-tools mavlink_shell.py --help` would exec `["bash", "-c", "mavlink_shell.py", "--help"]`
#    i.e. the `--help` would go actually to Bash, so we'd lose multi-arg support and semantically it's borked.
ENTRYPOINT []

# intentionally no entrypoint but when container run without commands, list the tools available so
# user knows to run the container again with the proper tool argument.
CMD ["bash", "-c", "ls -1 /fog-tools"]
