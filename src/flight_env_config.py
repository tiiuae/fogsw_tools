#!/bin/python3

"""
Flight Environment Config Changer
=================================
This script is used for changing px4 parameter
setup according to the flight environment

Command description:
 - check     : To read current env setup tag from px4
 - download  : To download the current config.txt from px4
 - upload    : To upload new config.txt to px4
 - remove    : To remove the config.txt from the px4
 - reboot    : To restart px4
"""

import asyncio
from mavsdk import System
import sys, os, re
import argparse
import shutil


class FlightEnvChanger:

    mav = None

    default_env = "outdoor"
    environment = "[unknown]"
    # Exampler configuraition tag in config file:
    # [ env: indoor ]

    root_dir = "/fs/microsd"
    config_dir = "etc"
    config_file_name = "config.txt"

    config_dir_path = ""
    config_file_path = ""
    tmp_file = "/tmp/" + config_file_name

    async def initialize(self):
        self.config_dir_path = os.path.join(self.root_dir, self.config_dir)
        self.config_file_path = os.path.join(self.config_dir_path, self.config_file_name)

        self.mav = System()

        print("Connecting to px4...")
        # Connect
        await self.mav.connect(system_address=self.args.address)
        # This waits till a mavlink based drone is connected
        async for state in self.mav.core.connection_state():
            if state.is_connected:
                print(".. Connected to px4!")
                break
        print()

    async def check_dir(self, path):
        if path.startswith('/'):
            path = path[1:]
        if path.endswith('/'):
            path = path[:-1]
        req_dirs = path.split('/')

        new_path = "/"
        dirs = await self.mav.ftp.list_directory(new_path)

        for dir in req_dirs:
            if ("D"+dir) in dirs:
                new_path = os.path.join(new_path, dir)
                dirs = await self.mav.ftp.list_directory(new_path)
            else:
                return 0
        return 1

    def read_config_type(self, path):
        fh = open(path, "r")
        while True:
            line = fh.readline()
            if not line:
                break
            match = re.search(r'#\s*\[\s*(type|env):\s*(\S+)\s*\]', line)
            if match:
                return match.group(2)
        return "[unknown]"

    async def validate_config_path(self):
        # Check if config directory structure exists
        ret = await self.check_dir(self.root_dir)
        if ret == 0:
            print(f"ERROR: Directory {self.root_dir} not found!")
            return False

        ret = await self.check_dir(self.config_dir_path)
        if ret == 0:
            print(f"config directory {self.config_dir_path} missing, creating..")
            await self.mav.ftp.create_directory(self.config_dir_path)
        return True

    async def validate_config_file(self):
        # Check if config file exists
        if await self.validate_config_path():
            files = await self.mav.ftp.list_directory(self.config_dir_path)
            for file in files:
                file=file[1:]
                file=file.split('\t')[0]
                if self.config_file_name == file:
                    # File found
                    return True
        # File not found
        self.environment = self.default_env
        return False

    async def check_current_config(self):
        await self.download_config_file(logging=False, copyfile=False)
        print(f"Current flight environment: '{self.environment}'")

    async def upload_config_file(self):
        if os.path.exists(self.args.file):
            if await self.validate_config_path():
                shutil.copyfile(self.args.file, self.tmp_file)
                self.environment = self.read_config_type(self.tmp_file)
                print(f"upload new config file '{self.args.file}' -- env: {self.environment}")
                sys.stdout.write("Upload")
                progress = self.mav.ftp.upload(self.tmp_file, self.config_dir_path)
                async for p in progress:
                    sys.stdout.write(".")
                    sys.stdout.flush()
                print()
                print("Done")
                os.remove(self.tmp_file)
        else:
            print(f"Config file not found: '{self.args.file}'")

    async def download_config_file(self, copyfile=True, logging=True):
        if await self.validate_config_file():
            if logging:
                sys.stdout.write("Download")
            progress = self.mav.ftp.download(self.config_file_path, '/tmp')
            async for p in progress:
                if logging:
                    sys.stdout.write(".")
                    sys.stdout.flush()
                else:
                    pass
            if logging:
                print()
                print("Done")
            self.environment = self.read_config_type(self.tmp_file)
            if copyfile:
                shutil.copyfile(self.tmp_file, self.args.file)
            os.remove(self.tmp_file)
            if logging:
                print(f"Config file downloaded: '{self.args.file}' -- env: {self.environment}")
            return True
        else:
            return False

    async def clear_hitl_param(self):
        print(f"Clear SYS_HITL in case set by config")
        await self.mav.param.set_param_int("SYS_HITL", 0)

    async def remove_config_file(self):
        if await self.validate_config_file():
            self.environment = self.default_env
            # Remove the file from px4 sdcard
            print(f"Remove file from PX4 path: '{self.config_file_path}'")
            await self.mav.ftp.remove_file(self.config_file_path)
            # Clear SYS_HITL definition, in case set by config.txt
            await self.clear_hitl_param()
            return True
        else:
            await self.clear_hitl_param()
            return False

    async def reboot(self):
        print(f"Reboot PX4")
        await self.mav.action.reboot()


    async def run(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=__doc__)
        parser.add_argument('COMMAND', choices=['check', 'download', 'upload', 'remove', 'reboot'], help='Command to execute',)
        parser.add_argument('-f', '--file', action="store", help='Path to local config file to be read/write', default='./config.txt')
        parser.add_argument('-a', '--address', action="store", help='Address to connect. (e.g serial:///dev/ttyACM0, udp://192.168.200.101:14540, tcp://:5760)', default='tcp://192.168.100.2:5760')
        self.args = parser.parse_args()

        await self.initialize()

        if self.args.COMMAND == "check":
            await self.check_current_config()
        elif self.args.COMMAND == "download":
            await self.download_config_file()
        elif self.args.COMMAND == "upload":
            await self.upload_config_file()
        elif self.args.COMMAND == "remove":
            await self.remove_config_file()
        elif self.args.COMMAND == "reboot":
            await self.reboot()


def main():
    changer = FlightEnvChanger()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(changer.run())

if __name__ == "__main__":
    main()
