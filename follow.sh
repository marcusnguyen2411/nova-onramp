#!/usr/bin/env bash
# Spawn turtle2 and make it follow turtle1 (follow.py).
# Needs control.sh already running (it opens turtlesim).
source /ros_humble/install/setup.bash

exec python3 /ros2_ws/follow.py
