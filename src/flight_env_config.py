#!/bin/python3

import asyncio
from mavsdk import System
import sys, os, re
import argparse
import shutil


class FlightEnvChanger:

    address = "tcp://:5760"
    mav = None

    configuration = "[unknown]"
    # Exampler configuraition tag in config file:
    # [ env: indoor ]

    root_dir = "/fs/microsd"
    config_dir = "etc"
    config_file_name = "config.txt"

    config_dir_path = ""
    config_file_path = ""
    local_config_file_path = ""
    tmp_file = "/tmp/" + config_file_name

    async def initialize(self):
        self.config_dir_path = os.path.join(self.root_dir, self.config_dir)
        self.config_file_path = os.path.join(self.config_dir_path, self.config_file_name)

        self.mav = System()

        print("Connecting to px4...")
        # Connect to mavlink-router TCP port 5760
        await self.mav.connect(system_address=self.address)
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
            match = re.search(r'#\s*\[\s*env:\s*(\S+)\s*\]', line)
            if match:
                return match.group(1)
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
            await self.mav.create_directory(self.config_dir_path)
        return True

    async def validate_config_file(self):
        # Check if config file exists
        if await self.validate_config_path():
            files = await self.mav.ftp.list_directory(self.config_dir_path)
            for file in files:
                file=file[1:]
                file=file.split('\t')[0]
                if self.config_file_name == file:
                    return True
        return False

    async def check_current_config(self):
        if await self.download_config_file(logging=False, copyfile=False):
            print(F"Current configuration: '{self.configuration}'")
        else:
            print("Config file not found")

    async def upload_config_file(self):
        if os.path.exists(self.local_config_file_path):
            shutil.copyfile(self.local_config_file_path, self.tmp_file)
            self.configuration = self.read_config_type(self.tmp_file)
            print(f"upload new config file '{self.local_config_file_path}' -- type: {self.configuration}")
            sys.stdout.write("Upload")
            progress = self.mav.ftp.upload(self.tmp_file, self.config_dir_path)
            async for p in progress:
                sys.stdout.write(".")
                sys.stdout.flush()
            print()
            print("Done")
            os.remove(self.tmp_file)
        else:
            print(f"Config file not found: '{self.local_config_file_path}'")

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
            self.configuration = self.read_config_type(self.tmp_file)
            if copyfile:
                shutil.copyfile(self.tmp_file, self.local_config_file_path)
            os.remove(self.tmp_file)
            if logging:
                print(f"Config file downloaded: '{self.local_config_file_path}' -- type: {self.configuration}")
            return True
        else:
            return False

    async def run(self):
        parser = argparse.ArgumentParser(description='Flight Environment Config Changer')
        parser.add_argument('COMMAND', choices=['check', 'download', 'upload'], help='Command to execute',)
        parser.add_argument('-f', '--file', action="store", help='Path to local config file to be read/write', default='./config.txt')
        args = parser.parse_args()

        await self.initialize()

        self.local_config_file_path = args.file

        if args.COMMAND == "check":
            await self.check_current_config()
        elif args.COMMAND == "download":
            await self.download_config_file()
        elif args.COMMAND == "upload":
            await self.upload_config_file()


def main():
    changer = FlightEnvChanger()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(changer.run())

if __name__ == "__main__":
    main()
