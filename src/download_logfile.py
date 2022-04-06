#!/bin/python3

import asyncio
from mavsdk import System
from mavsdk import log_files
import sys, os

import datetime
import dateutil.parser
import pytz

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

async def run():
    mav = System()

    print("Connecting to px4...")
    await mav.connect(system_address="tcp://:5760")

    # This waits till a mavlink based drone is connected
    async for state in mav.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to px4!")
            break

    entries = await mav.log_files.get_entries()
    latest = None
    latest_id = None
    for entry in entries:
        print(f"Log {entry.id} from {entry.date}")
        if latest is None:
            latest = dateutil.parser.parse(entry.date)
            latest_id = entry.id
            continue
        date = dateutil.parser.parse(entry.date)
        if date > latest:
            latest = date
            latest_id = entry.id
    print()
    print(f"Latest: {latest_id} - {latest}")

    print()
    print(f"Give log id [ 0 .. {len(entries)-1} ] or ENTER to exit")
    loop = True

    while loop:
        print()
        s = input("Selection: ")
        if s == "":
            loop = False
        else:
            id = int(s)
            if id < 0 or id > len(entries):
                print("ERROR: index out of bounds")
            else:
                loop = False
                entry = entries[id]
                date_without_colon = entry.date.replace(":", "-")
                filename = f"./log-{date_without_colon}.ulgc"
                if os.path.exists(filename):
                    ovr = input("File already exists, override? (Y/n) ")
                    if ovr == 'n' or ovr == 'N':
                        print("Cancelled.")
                        loop = False
                        continue
                    else:
                        os.remove(filename)

                previous_progress = -1
                async for progress in mav.log_files.download_log_file(entry, filename):
                    new_progress = round(progress.progress*100)
                    if new_progress != previous_progress:
                        sys.stdout.write(f"\r{new_progress} %")
                        sys.stdout.flush()
                        previous_progress = new_progress
                print()
                print("done.")

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
