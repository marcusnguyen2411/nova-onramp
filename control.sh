#!/usr/bin/env bash
# Open the turtlesim window, then drive turtle1 with the mouse (control.py).
source /ros_humble/install/setup.bash

ros2 run turtlesim turtlesim_node &
sim_pid=$!
# Close the turtlesim window when control.py stops (e.g. Ctrl+C).
trap "kill $sim_pid 2>/dev/null; wait $sim_pid 2>/dev/null" EXIT

sleep 1  # give the window a moment to open
python3 /ros2_ws/control.py
