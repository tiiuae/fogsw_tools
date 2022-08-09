# Description

This repo contains scripts that can help during debugging work.
Feel free to contribute with new tools or update the current version to make it better.

# fog_log_flight.sh
Run this script to start recording logs of key applications in the Mission Computer of the FOG drone.
The script will block until any key is pressed. Then it will stop recoding the rosbag.
It uses some of the scripts included in this package like fogsw_package_list.sh, mesh_installation_chech.sh and fog_record_bag_all_topics.sh.

# mesh_installation_check.sh
Prints information about the mesh configuration, packages installed and its versions.

# fog_record_bag_all_topics.sh
Starts recording all topics in the Mission Computer in a ros bag. Note that the ros bag might get quite big quickly.

# fog_cli.py
This tool is useful to send simple commands to the navigation stack: arm, takeoff, go to waypoint and land.

## Arming
```
fog_cli.py arming
```

## Takeoff
```
fog_cli.py takeoff
```

## Go to waypoint
```
# The way point in the example are coordinates in Tampere.
fog_cli.py goto 61.50338377 23.77508231 1.0 -1.57
```

## Land

```
fog_cli.py land
```

# flight_env_config.py
This script is used for changing px4 parameter setup according to the flight environment (e.g. indoor, hitl). The setup is a config.txt file stored into px4 sd-card.
The script allows:
 - to check the current env setup in px4
 - to download the current config.txt from px4
 - to upload new config.txt to px4
 - to remove the config.txt from the px4 in order to use the original PX4 Airframe params

# download_px4_logfile.py
Script to download ulog files from PX4 (sdcard) interactively. Script fetches a list of available logfiles in PX4 log directory and request selection to download. flag '--latest' can be used to skip interactive selection and just download the latest log file for automation purposes.
