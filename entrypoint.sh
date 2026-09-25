#!/bin/bash
# Load the ROS 2 environment compiled into /ros_humble/install
# (this puts the `ros2` command on $PATH)
source /ros_humble/install/setup.bash
exec "$@"
