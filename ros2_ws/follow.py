# Spawn a second turtle (turtle2) that follows turtle1 around.

# turtle2 drives toward turtle1 and stops when it gets close,
# so it trails behind without bumping into it.

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist  # ROS2 message type: forward speed + turn speed
from turtlesim.msg import Pose       # ROS2 message type: turtle position (x, y) and heading (theta)
from turtlesim.srv import Spawn      # ROS2 service type: ask turtlesim to add a new turtle

FOLLOW_DIST = 1.0  # stay about this far behind turtle1 (turtle-world units)


class Turtle_Follower(Node):
    def __init__(self):
        super().__init__('turtle_follower')

        # Ask turtlesim to spawn turtle2 in the bottom-left corner.
        spawn = self.create_client(Spawn, 'spawn')
        spawn.wait_for_service()
        spawn.call_async(Spawn.Request(x=2.0, y=2.0, theta=0.0, name='turtle2'))

        # Send drive commands to turtle2.
        self.publisher_ = self.create_publisher(Twist, 'turtle2/cmd_vel', 10)
        # Track both turtles: the leader (turtle1) and ourselves (turtle2).
        self.create_subscription(Pose, 'turtle1/pose', self.on_leader_pose, 10)
        self.create_subscription(Pose, 'turtle2/pose', self.on_pose, 10)
        # Recompute drive command 20 times a second (20 Hz)
        self.timer_ = self.create_timer(0.05, self.timer_callback)

        self.leader = None  # latest turtle1 position
        self.pose = None    # latest turtle2 position

        self.get_logger().info('turtle2 spawned and following turtle1. Ctrl+C quit.')

    def on_leader_pose(self, msg):
        self.leader = msg

    def on_pose(self, msg):
        self.pose = msg

    def timer_callback(self):
        twist = Twist()  # all zeros = stand still (no movement)

        if self.leader and self.pose:
            dx = self.leader.x - self.pose.x
            dy = self.leader.y - self.pose.y
            dist = math.hypot(dx, dy)
            if dist > FOLLOW_DIST:
                # Same steering as control.py, but the target is turtle1.
                err = math.atan2(dy, dx) - self.pose.theta
                err = math.atan2(math.sin(err), math.cos(err))
                twist.angular.z = 4.0 * err
                # Only the distance beyond FOLLOW_DIST counts, so it eases to a stop behind turtle1.
                gap = dist - FOLLOW_DIST
                twist.linear.x = min(2.0, 1.5 * gap) * max(0.0, math.cos(err))

        self.publisher_.publish(twist)


if __name__ == '__main__':
    rclpy.init()
    node = Turtle_Follower()
    try:
        rclpy.spin(node)  # keep running the timer and listeners until Ctrl+C
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():  # Ctrl+C may have already shut ROS down
            rclpy.shutdown()
