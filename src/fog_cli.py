#!/usr/bin/env python3

from mimetypes import init
import string
import sys
import os
import argparse
from random import uniform
import time



from std_srvs.srv import SetBool, Trigger
from fog_msgs.srv import Vec4
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy
from rcl_interfaces.msg import ParameterValue, ParameterType
from rcl_interfaces.srv import SetParameters, GetParameters

from px4_msgs.msg import VehicleStatus
from std_msgs.msg import String

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

    def send_test(self):
        self.cli = self.create_client(SetBool, '/%s/control_interface/arming' % self.drone_device_id)
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = SetBool.Request()
        self.req.data = True
        self.future = self.cli.call_async(self.req)
        self.__wait_for_response('testing arm')

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


class FogClientSync(Node):
    def __init__(self, args):
        super().__init__('minimal_subscriber', namespace=os.getenv('DRONE_DEVICE_ID'))
        self.drone_device_id = os.getenv('DRONE_DEVICE_ID')
        self.args = args
        self.vehicle_status_subs = None
        self.navigation_status_subs = None
        # self.msg_type = importlib.import_module(args.msg_type)
        self._waiting = True
        # self.topic = args.topic
        self.qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )


    def vehicle_status_listener_cb(self, msg):
        self.get_logger().info('nav_state={}, arming_state={}'.format(msg.nav_state, msg.arming_state))
        if self.args.command == 'arming':
            if msg.arming_state == 2:
                self._waiting = False
        elif self.args.command == 'takeoff':
            if msg.nav_state == 3:
                self._waiting = False
        elif self.args.command == 'land':
            if msg.arming_state == 1:
                self._waiting = False

    def navigation_status_listener_cb(self, msg):
        self.get_logger().info('msg data={}'.format(msg.data))
        if msg.data == 'IDLE':
            self._waiting = False


    def create_subs(self):
        if self.args.command in ['arming', 'takeoff', 'land']:
            self.vehicle_status_subs = self.create_subscription(
                VehicleStatus,
                '/{}/fmu/vehicle_status/out'.format(self.drone_device_id),
                self.vehicle_status_listener_cb,
                self.qos_profile)
            self.vehicle_status_subs  # prevent unused variable warning
        elif self.args.command in ['goto', 'local']:
            self.navigation_status_subs = self.create_subscription(
                String,
                '/{}/navigation/status_out'.format(self.drone_device_id),
                self.navigation_status_listener_cb,
                self.qos_profile)
            self.navigation_status_subs  # prevent unused variable warning

    def waiting(self):
        return self._waiting



def run_command(parser, args):

    if (args.sync == True) and (args.timeout == None):
        print('These optional arguments are required for goto command is run as synchronously:\n'
              '\t--timeout\nSetting default value 30s')
        args.timeout = 30 # set default 30s timeout, better than nothing
    elif args.command == 'area' and args.number == None:
        print('These optional arguments are required for area command is run as synchronously:\n'
              '\t--number\n')

def init_arg_parser():
    parser = argparse.ArgumentParser(
        prog='fog_cli.py',
        epilog="See '<command> --help' to read about a specific sub-command."
    )
    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')

    arming_parser = subparsers.add_parser('arming', help='Arming')
    arming_parser.add_argument('--sync', action='store_true', help='Run command synchronously')
    arming_parser.add_argument('--timeout', type=int)
    arming_parser.set_defaults(func=run_command)

    takeoff_parser = subparsers.add_parser('takeoff', help='Takeoff')
    takeoff_parser.add_argument('--sync', action='store_true')
    takeoff_parser.add_argument('--timeout', type=int)
    takeoff_parser.set_defaults(func=run_command)

    goto_parser = subparsers.add_parser('goto', help='Goto')
    goto_parser.add_argument('latitude', nargs='?', type=float)
    goto_parser.add_argument('longitude', nargs='?', type=float)
    goto_parser.add_argument('altitude', nargs='?', type=float)
    goto_parser.add_argument('yaw', nargs='?', type=float)
    goto_parser.add_argument('--timeout', type=int)
    goto_parser.add_argument('--sync', action='store_true')

    goto_parser.set_defaults(func=run_command)

    local_parser = subparsers.add_parser('local', help='Local')
    local_parser.add_argument('latitude', nargs='?', type=float)
    local_parser.add_argument('longitude', nargs='?', type=float)
    local_parser.add_argument('altitude', nargs='?', type=float)
    local_parser.add_argument('yaw', nargs='?', type=float)
    local_parser.add_argument('--timeout', type=int)
    local_parser.add_argument('--sync', action='store_true')

    local_parser.set_defaults(func=run_command)

    area_parser = subparsers.add_parser('area', help='Area')
    area_parser.add_argument('--number', nargs='?', type=int)
    area_parser.add_argument('--sync', action='store_true')
    area_parser.add_argument('--timeout', type=int)
    area_parser.set_defaults(func=run_command)

    params_parser = subparsers.add_parser('get_params', help='get_params')
    params_parser.set_defaults(func=run_command)

    land_parser = subparsers.add_parser('land', help='Land')
    land_parser.add_argument('--sync', action='store_true')
    land_parser.add_argument('--timeout', type=int)
    land_parser.set_defaults(func=run_command)

    args = parser.parse_args()
    if args.command is not None:
        args.func(parser, args)
    else:
        parser.print_help()

    return args

def random_points_range(startx, endx, starty, endy):

    x = round(uniform(startx, endx), 2)
    y = round(uniform(starty, endy), 2)
    z = round(uniform(1, 2), 2)

    return x, y, z


def get_waypoint(area):
    if area == 0:
        return 0.0, 0.0, 1.0
    elif area == 1:
        return random_points_range(-0.5, 0, 0, 1.5)
    elif area == 2:
        return random_points_range(-0.5, 0, -2, -3.5)
    elif area == 3:
        return random_points_range(-2, -2.5, -2, -3.5)
    elif area == 4:
        return random_points_range(-2, -2.5, 0, 1.5)
    print("Area command failed. Choose an integer between 0 and 4.")
    raise ValueError


def main(args):

    status = 0

    rclpy.init()

    if args.sync == False:

        fog_client = FogClientAsync()

        if args.command == 'test':
            fog_client.send_test()

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
            print(x, y, z)
            fog_client.send_local(x, y, z, -1.57)

        if args.command == 'get_params':
            value = fog_client.read_params()

        fog_client.destroy_node()
    # sync
    else:
        fog_client = FogClientAsync()
        fog_client_sync = FogClientSync(args)

        if args.command == 'arming':
            # send message
            fog_client.send_arming()
            
        elif args.command == 'takeoff':
            fog_client.send_arming()
            fog_client.send_takeoff()
            
        elif args.command == 'goto':
            fog_client.send_goto(
                args.latitude,
                args.longitude,
                args.altitude,
                args.yaw)
            
        elif args.command == 'local':
            fog_client.send_local(
                args.latitude,
                args.longitude,
                args.altitude,
                args.yaw)
            
        elif args.command == 'land':
            fog_client.send_land()
            
        elif args.command == 'area':
            pass
        elif args.command == 'get_params':
            pass

        fog_client_sync.create_subs()
        timeout = time.time() + args.timeout
        while fog_client_sync.waiting() and (time.time() < timeout):
            rclpy.spin_once(fog_client_sync)

        if fog_client_sync.waiting():
            status = False

        fog_client.destroy_node()
        fog_client_sync.destroy_node()


    rclpy.shutdown()

    return status


if __name__ == '__main__':
    args = init_arg_parser()
    status = main(args)


sys.exit(status)
