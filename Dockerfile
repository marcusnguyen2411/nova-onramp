
# ROS 2 Humble from source (for turtlesim)

# What this image does:
#   1. Set up Ubuntu 22.04 (inherits from the official Ubuntu image)
#   2. Install build tools (ros-dev-tools, Qt libs, etc.)
#   3. Download ROS 2 Humble source code
#   4. Install system libraries those sources need
#   5. Compile turtlesim + the ros2 CLI from that source
#   6. Auto-load the install so `ros2` works when you open a shell

FROM ubuntu:jammy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ROS_DISTRO=humble


# 1) Basic Ubuntu setup
RUN apt-get update && apt-get install -y \
    locales \
    software-properties-common \
    curl \
    git \
    && locale-gen en_US.UTF-8 \
    && add-apt-repository -y universe


# 2) ROS apt repo to install ros-dev-tools
RUN ROS_APT_SOURCE_VERSION=$(curl -s \
    https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
    | grep -F "tag_name" | awk -F'"' '{print $4}') \
    && curl -L -o /tmp/ros2-apt-source.deb \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.jammy_all.deb" \
    && dpkg -i /tmp/ros2-apt-source.deb


# ros-dev-tools so we can use rosdep, vcs, and colcon + Qt libs (turtlesim needs Qt to draw its window)
RUN apt-get update && apt-get install -y \
    ros-dev-tools \
    libgl1-mesa-glx \
    libx11-xcb1 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*


# 3) Download ROS 2 Humble source from GitHub
WORKDIR /ros_humble
RUN mkdir -p src

# Official Humble source list. --shallow = smaller/faster download.
RUN vcs import \
    --shallow \
    --input https://raw.githubusercontent.com/ros2/ros2/humble/ros2.repos \
    src


# 4) Check for and install system dependencies for the packages we will build
RUN rosdep init && rosdep update

RUN apt-get update \
    && rosdep install -y \
    --from-paths $(colcon list --packages-up-to turtlesim ros2cli_common_extensions --paths-only) \
    --ignore-src \
    --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers" \
    && rm -rf /var/lib/apt/lists/*


# 5) Compile from source
# --packages-up-to = build these packages AND their dependencies, but skip unrelated packages (keeps build shorter)
RUN colcon build \
    --packages-up-to turtlesim ros2cli_common_extensions \
    --merge-install \
    --parallel-workers 2 \
    --cmake-args -DBUILD_TESTING=OFF

# After this step we should have:
#   /ros_humble/install/setup.bash   <- source this to use ROS
#   /ros_humble/install/bin/ros2     <- the ros2 command


# Keyboard teleop needs real press/release events (terminal stdin can't chord keys)
RUN apt-get update && apt-get install -y \
    python3-pynput \
    && rm -rf /var/lib/apt/lists/*

# 6) Make `ros2` available in every new shell
# entrypoint.sh runs "source setup.bash" before starting bash.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && echo "source /ros_humble/install/setup.bash" >> /root/.bashrc


# 7) Turtle programs + a launcher script for each.
# The launchers go on PATH, so any container can run them by name:
#   control.sh  -> turtlesim window + mouse control (control.py)
#   follow.sh   -> turtle2 that follows turtle1 (follow.py)
COPY ros2_ws/control.py ros2_ws/follow.py /ros2_ws/
COPY control.sh follow.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/control.sh /usr/local/bin/follow.sh

ENTRYPOINT ["/entrypoint.sh"]
