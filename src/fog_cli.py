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

    # Returns list of rcl_interfaces.msg.ParameterValue or None
    def __wait_for_param_response(self):
        while rclpy.ok():
            rclpy.spin_once(self)
            if self.future.done():
                try:
                    response = self.future.result()
                except Exception as e:
                    self.get_logger().error(
                        'Service call failed %r' % (e,))
                else:
                    return response.values
                break
        return None

    def send_arming(self):
        self.cli = self.create_client(SetBool, '/%s/control_interface/arming' % self.drone_device_id)
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = SetBool.Request()
        self.req.data = True
        self.future = self.cli.call_async(self.req)
        self.__wait_for_response('arming')

    def send_takeoff(self):
        self.cli = self.create_client(Trigger, '/%s/control_interface/takeoff' % self.drone_device_id)
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = Trigger.Request()
        self.future = self.cli.call_async(self.req)
        self.__wait_for_response('takeoff')

    # One safe waypoint: [61.50338377, 23.77508231, 1.0, -1.57]
    # Home goal: [61.50343681, 23.77506587, 1.0, -1.57]
    def send_goto(self, lat, lon, alt, yaw):
        self.cli = self.create_client(Vec4, '/%s/navigation/gps_waypoint' % self.drone_device_id)
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = Vec4.Request()
        self.req.goal = [lat, lon, alt, yaw]
        self.future = self.cli.call_async(self.req)
        self.__wait_for_response('goto')

    # Home goal: [0.0, 0.0, 1.0, -1.57]
    def send_local(self, lat, lon, alt, yaw):
        self.cli = self.create_client(Vec4, '/%s/navigation/local_waypoint' % self.drone_device_id)
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = Vec4.Request()
        self.req.goal = [lat, lon, alt, yaw]
        self.future = self.cli.call_async(self.req)
        self.__wait_for_response('local')

    def send_land(self):
        self.cli = self.create_client(Trigger, '/%s/control_interface/land' % self.drone_device_id)
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = Trigger.Request()
        self.future = self.cli.call_async(self.req)
        self.__wait_for_response('land')

    def read_params(self):
        #self.cli = self.create_client(SetParameters, '/%s/navigation/set_parameters' % self.drone_device_id)
        #while not self.cli.wait_for_service(timeout_sec=2.0):
        #    self.get_logger().info('service not available, waiting again...')
        #self.req = SetParameters.Request()
        #new_param_value = ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=1.2)
        #self.req.parameters = [Parameter(name='planning.safe_obstacle_distance', value=new_param_value)]
        #self.future = self.cli.call_async(self.req)
        #self.__wait_for_response('SET')

        self.cli = self.create_client(GetParameters, '/%s/bumper/get_parameters' % self.drone_device_id)
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = GetParameters.Request()
        self.req.names = ['lidar2d.filter_size']
        self.future = self.cli.call_async(self.req)
        values = self.__wait_for_param_response()
        print('/%s/bumper' % self.drone_device_id)
        for i in range(len(values)):
            if values[i].type == ParameterType.PARAMETER_INTEGER:
                print('\t', self.req.names[i], values[i].integer_value)
            elif values[i].type == ParameterType.PARAMETER_BOOL:
                print('\t', self.req.names[i], values[i].bool_value)
            elif values[i].type == ParameterType.PARAMETER_DOUBLE:
                print('\t', self.req.names[i], values[i].double_value)

        self.cli = self.create_client(GetParameters, '/%s/navigation/get_parameters' % self.drone_device_id)
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = GetParameters.Request()
        self.req.names = ['planning.bumper_distance_factor', 'planning.safe_obstacle_distance', 'bumper.enabled']
        self.future = self.cli.call_async(self.req)
        values = self.__wait_for_param_response()
        print('/%s/navigation/get_parameters' % self.drone_device_id)
        for i in range(len(values)):
            if values[i].type == ParameterType.PARAMETER_INTEGER:
                print('\t', self.req.names[i], values[i].integer_value)
            elif values[i].type == ParameterType.PARAMETER_BOOL:
                print('\t', self.req.names[i], values[i].bool_value)
            elif values[i].type == ParameterType.PARAMETER_DOUBLE:
                print('\t', self.req.names[i], values[i].double_value)


def random_points_range(startx, endx, starty, endy):

    x = round(uniform(startx, endx), 2)
    y = round(uniform(starty, endy), 2)
    z = round(uniform(1, 2), 2)

    return x, y, z


def get_waypoint(area):
    if area == 1:
        return random_points_range(-0.5, 1, 0, 3)
    elif area == 2:
        return random_points_range(-0.5, 1, -3, -6)
    elif area == 3:
        return random_points_range(-2.5, -4, -3, -6)
    elif area == 4:
        return random_points_range(-2.5, -4, -3, -6)
    raise ValueError


def main(args):
    rclpy.init()

    fog_client = FogClientAsync()

    if args.command == 'arming':
        fog_client.send_arming()

    # Includes arming
    if args.command == 'takeoff':
        fog_client.send_arming()
        fog_client.send_takeoff()

    if args.command == 'land':
        fog_client.send_land()

    if args.command == 'goto':
        fog_client.send_goto(
            args.latitude, 
            args.longitude,
            args.altitude,
            args.yaw)

    if args.command == 'local':
        fog_client.send_local(
            args.latitude,
            args.longitude,
            args.altitude,
            args.yaw)

    if args.command == 'area':
        x, y, z = get_waypoint(args.latitude)
        fog_client.send_local(x, y, z, -1.57)

    if args.command == 'get_params':
        value = fog_client.read_params()

    fog_client.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Tool to send flight commands to drone.")
    parser.add_argument('command', choices=['arming', 'takeoff', 'goto', 'land', 'local', 'area','get_params'])
    parser.add_argument('latitude', nargs='?', type=float)
    parser.add_argument('longitude', nargs='?', type=float)
    parser.add_argument('altitude', nargs='?', type=float)
    parser.add_argument('yaw', nargs='?', type=float)
    args = parser.parse_args()

    if (args.command == 'area' and args.longitude is None) or (args.command in ['goto', 'local'] and
                                                               (args.latitude is None or args.longitude is None or
                                                                args.altitude is None or args.yaw is None)):
        print('ERROR: wrong number of arguments.')
        parser.print_usage()
        sys.exit(1)

    main(args)


sys.exit(0)
