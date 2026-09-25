# Drive the turtlesim turtle toward the mouse pointer.

# Move the pointer over the TurtleSim window and the turtle chases it.
# Move the pointer off the window and the turtle stops.

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist  # ROS2 message type: forward speed + turn speed
from turtlesim.msg import Pose       # ROS2 message type: turtle position (x, y) and heading (theta)

from Xlib import display as xdisplay  # X11 library: talks to the screen to find windows, read the mouse

WORLD_SIZE = 499 / 45  # turtlesim: 500 px window, 45 px per unit
ARRIVE_DIST = 5 / 45   # stop within about 5 px of the pointer


class Mouse_Controller(Node):
    def __init__(self):
        super().__init__('mouse_controller')
        # Send drive command message to the topic 'turtle1/cmd_vel' to move the turtle
        self.publisher_ = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)
        # Receive turtle position message from the topic 'turtle1/pose' to get the turtle's position
        self.create_subscription(Pose, 'turtle1/pose', self.on_pose, 10)
        # Recompute drive command message 20 times a second (20 Hz)
        self.timer_ = self.create_timer(0.05, self.timer_callback)

        self.display = xdisplay.Display()
        self.pose = None    # latest turtle position, filled in by on_pose()
        self.window = None  # TurtleSim window, found on first use

        self.get_logger().info(
            'Mouse follower ready: move the pointer over the TurtleSim window. Ctrl+C quit.'
        )

    def on_pose(self, msg):
        self.pose = msg

    def find_window(self, win):
        # Search win and every window nested inside it for TurtleSim.
        # Exact title: Qt also makes tiny hidden windows named "...turtlesim...".
        if win.get_wm_name() == 'TurtleSim':
            return win
        for child in win.query_tree().children:
            found = self.find_window(child)
            if found:
                return found
        return None

    def mouse_to_world(self):
        # Return the pointer as turtle-world (x, y), or None if it's off the window.
        if self.window is None:
            self.window = self.find_window(self.display.screen().root)
            if self.window is None:
                return None  # turtlesim window hasn't opened yet

        geom = self.window.get_geometry()
        pointer = self.window.query_pointer()  # get the mouse position from the window's top-left
        u = pointer.win_x / geom.width  # fraction of the window width
        v = pointer.win_y / geom.height  # fraction of the window height
        if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
            return None
        # Screen y counts down from the top; turtlesim y counts up, so flip it (invert y-axis)
        return u * WORLD_SIZE, (1.0 - v) * WORLD_SIZE

    def timer_callback(self):
        twist = Twist()  # all zeros = stand still (no movement)
        goal = self.mouse_to_world() if self.pose else None

        if goal:
            dx = goal[0] - self.pose.x
            dy = goal[1] - self.pose.y
            dist = math.hypot(dx, dy)
            if dist > ARRIVE_DIST:
                # How far to turn: direction to the pointer minus where we are facing now.
                err = math.atan2(dy, dx) - self.pose.theta
                # Wrap to -180°..180° so it turns the short way round.
                err = math.atan2(math.sin(err), math.cos(err))
                twist.angular.z = 4.0 * err
                # Faster when far (capped at 2.0); slows to 0 while facing away.
                twist.linear.x = min(2.0, 1.5 * dist) * max(0.0, math.cos(err))

        self.publisher_.publish(twist)


if __name__ == '__main__':
    rclpy.init()
    node = Mouse_Controller()
    try:
        rclpy.spin(node)  # keep running the timer and listener until Ctrl+C
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():  # Ctrl+C may have already shut ROS down
            rclpy.shutdown()
