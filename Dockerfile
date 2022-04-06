# fog-sw BUILDER
#FROM ros:galactic-ros-base as fog-sw-builder
# FROM ubuntu:20.04
# Docker ghcr.io read packages — read:packages : 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

LABEL org.opencontainers.image.source = "https://github.com/tiiuae/fogsw_tools"

FROM ghcr.io/tiiuae/tii-ubuntu-ros 

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ros-galactic-fog-msgs ros-galactic-px4-msgs python3-pip python3-systemd \
    && rm -rf /var/lib/apt/lists/*

# Install pip and python dependencies
# RUN python3 -m pip install systemd

# make all commands in /fog-tools/* invocable without full path
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/fog-tools
ENV PYTHONPATH=/opt/ros/galactic/lib/python3.8/site-packages
ENV LD_LIBRARY_PATH=/opt/ros/galactic/opt/yaml_cpp_vendor/lib:/opt/ros/galactic/lib/x86_64-linux-gnu:/opt/ros/galactic/lib

COPY src/ /fog-tools/