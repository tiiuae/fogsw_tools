#!/usr/bin/env python3

import asyncio
import importlib.util
import sys, os

# For arm64, the docker image does not have mavsdk installed since qemu emulation is slow
# Installing during runtime should be faster
if importlib.util.find_spec('mavsdk') is None:
    os.system('pip3 install mavsdk')

from mavsdk import System
import argparse
import tempfile
import datetime

class LogFile:
    enc = False
    date = None
    time = None
    datafile = None
    size = 0.0
    keyfile = None


class LogFileDownloader:

    mav = None
    root_dir = "/fs/microsd"
    log_root_dir = "log"

    log_dir_path = ""

    # Dictionary of dictionaries
    log_list = []

    def GetEntry(self, k_date, k_time, search):
        if search:
            for entry in self.log_list:
                if entry.date == k_date and entry.time == k_time:
                    return entry

        return LogFile()

    def UpdateEntry(self, entry, search):
        index = None
        if search:
            for idx, e in enumerate(self.log_list):
                if e.date == entry.date and e.time == entry.time:
                    index = idx

        if index is not None:
            self.log_list[index] = entry
        else:
            self.log_list.append(entry)


    async def initialize(self):
        self.log_dir_path = os.path.join(self.root_dir, self.log_root_dir)

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

    async def validate_log_path(self):
        # Check if log directory structure exists
        ret = await self.check_dir(self.root_dir)
        if ret == 0:
            print(f"ERROR: Directory {self.root_dir} not found")
            print(f"Verify that SD-card exists in the drone!")
            return False

        ret = await self.check_dir(self.log_dir_path)
        if ret == 0:
            print(f"ERROR: Directory {self.log_dir_path} not found")
            return False
        return True

    def is_valid_date(self, now, date):
        try:
            log_d = datetime.datetime.strptime(date, "%Y-%m-%d")
            delta = (now - log_d).total_seconds()
            if delta < 0:
                print("WARNING: Invalid future date: " + date)
                return False
        except ValueError:
            # Not valid date format
            print("WARNING: Invalid date format: " + date)
            return False
        return True

    def is_valid_time(self, now, date, time):
        try:
            datetime.datetime.strptime(time, "%H_%M_%S")
        except ValueError:
            # Not valid time format
            print("WARNING: Invalid time format: " + time)
            return False
        return True

    async def list_logfiles(self):
        now = datetime.datetime.now()
        if await self.validate_log_path():
            date_dirs = await self.mav.ftp.list_directory(self.log_dir_path)
            for dir in date_dirs:
                if dir.startswith('D'):
                    log_date = dir[1:]
                    if self.args.latest and not self.is_valid_date(now, log_date):
                        continue

                    log_date_path = os.path.join(self.log_dir_path, log_date)
                    log_files = await self.mav.ftp.list_directory(log_date_path)
                    for file in log_files:
                        if file.startswith('F'):
                            fields = file[1:].split()
                            filename = fields[0]
                            log_time,file_ext = filename.split('.')
                            if self.args.latest and not self.is_valid_time(now, log_date, log_time):
                                continue

                            path = os.path.join(log_date_path,filename)
                            enc = False
                            if file_ext == "ulgk" or file_ext == "ulgc":
                                enc = True
                            entry = self.GetEntry(log_date, log_time, enc)
                            entry.time = log_time
                            entry.date = log_date
                            entry.enc = enc

                            if file_ext == "ulgk":
                                entry.keyfile = path
                            else:
                                #entry.size = round(float(fields[1])/1000, 2)
                                size = float(fields[1])
                                if size > 999999.0:
                                    entry.size = ("{:.2f}".format(size/1024/1024)).rjust(8) + " MB"
                                else:
                                    entry.size = ("{:.2f}".format(size/1024)).rjust(8) + " kB"
                                entry.datafile = path
                            self.UpdateEntry(entry, enc)
        index = 0
        if self.args.latest:
            print("latest:")
            for idx, entry in enumerate(self.log_list):
                if entry.date > self.log_list[index].date:
                    index = idx
                elif entry.date == self.log_list[index].date:
                    if entry.time > self.log_list[index].time:
                        index = idx
            print(self.log_list[index].date + "/" + self.log_list[index].time)
        else:
            # Interactive selection
            print("logs:")
            for idx, entry in enumerate(self.log_list):
                output = str(idx).rjust(5) + ": " + (entry.date+"/"+entry.time).ljust(25) + " " + str(entry.size)
                if entry.enc:
                    output = output + " (encrypted)"
                    if entry.keyfile is None:
                        output = output + " KEYFILE MISSING"
                print(output)
            index = input("\nSelect log file to download: ")
        return index

    async def download_file(self, file, date, dir):
        previous_progress = 0
        async for progress in self.mav.ftp.download(file, dir, False):
            new_progress = round((progress.bytes_transferred/progress.total_bytes)*100)
            if new_progress != previous_progress:
                sys.stdout.write(f"\r{new_progress} %")
                sys.stdout.flush()
            previous_progress = new_progress
        print()
        filename = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
        infilebase, infileext = filename[0].split('.')
        outfile = "log-" + date + "T" + infilebase.replace('_', '-') + "Z." + infileext
        print("file: " + outfile)
        os.rename(os.path.join(dir, filename[0]), os.path.join(self.args.dir, outfile))


    async def download_logfile(self, index):
        with tempfile.TemporaryDirectory(prefix=".part_", dir=".") as tmpdir:
            entry = self.log_list[index]
            await self.download_file(entry.datafile, entry.date, tmpdir)
            if entry.keyfile is not None:
                await self.download_file(entry.keyfile, entry.date, tmpdir)

    async def run(self):
        workdir = os.getcwd()
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=__doc__)
        parser.add_argument('-a', '--address', action="store", help='Address to connect. (e.g serial:///dev/ttyACM0, udp:192.168.200.101:14540, tcp://:5760)', default='udp://:15761')
        parser.add_argument('-d', '--dir', action="store", help='Output directory (default .)', default=workdir)
        parser.add_argument('-l', '--latest', action="store_true", help='Fetch latest logfile and skip interactive selection')
        self.args = parser.parse_args()
        self.args.dir = os.path.realpath(self.args.dir)

        await self.initialize()
        index = await self.list_logfiles()
        if str(index).isnumeric():
            await self.download_logfile(int(index))


def main():
    downloader = LogFileDownloader()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(downloader.run())

if __name__ == "__main__":
    main()
