#!/usr/bin/env python3

import sys
import os
import argparse
from random import uniform

from std_srvs.srv import SetBool, Trigger
from fog_msgs.srv import Vec4
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import ParameterValue, ParameterType
from rcl_interfaces.srv import SetParameters, GetParameters


class FogClientAsync(Node):

    def __init__(self):
        super().__init__('fog_client_async')
        self.drone_device_id = os.getenv('DRONE_DEVICE_ID')

    def __wait_for_response(self, cmd):
        while rclpy.ok():
            rclpy.spin_once(self)
            if self.future.done():
                try:
                    response = self.future.result()
                except Exception as e:
                    self.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    self.get_logger().error(
                        'Result of %s: %s' % (cmd, response.message))
                if response.success:
                    self.get_logger().info('Command executed successfully.')
                break

    # One safe waypoint: [61.50338377, 23.77508231, 1.0, -1.57]
    # Home goal: [61.50343681, 23.77506587, 1.0, -1.57]
    def send_goto(self, lat, lon, alt, yaw):
        self.cli = self.create_client(Vec4, '/%s/gps_waypoint' % self.drone_device_id)
        attempts = 3
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
            attempts -= 1
            if attempts == 0:
                self.get_logger().error('Failed to send goto command!')
                return
        self.req = Vec4.Request()
        self.req.goal = [lat, lon, alt, yaw]
        self.future = self.cli.call_async(self.req)
        self.__wait_for_response('goto')

    def send_land(self):
        self.cli = self.create_client(Trigger, '/%s/land' % self.drone_device_id)
        attempts = 3
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
            attempts -= 1
            if attempts == 0:
                self.get_logger().error('Failed to send land command!')
                return
        self.req = Trigger.Request()
        self.future = self.cli.call_async(self.req)
        self.__wait_for_response('land')


def main(args):
    rclpy.init()

    fog_client = FogClientAsync()

    if args.command == 'land':
        fog_client.send_land()

    if args.command == 'goto':
        fog_client.send_goto(
            args.latitude, 
            args.longitude,
            args.altitude,
            args.yaw)

    fog_client.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Tool to send flight commands to drone.")
    parser.add_argument('command', choices=['goto', 'land'])
    parser.add_argument('latitude', nargs='?', type=float)
    parser.add_argument('longitude', nargs='?', type=float)
    parser.add_argument('altitude', nargs='?', type=float)
    parser.add_argument('yaw', nargs='?', type=float)
    args = parser.parse_args()

    main(args)


sys.exit(0)
