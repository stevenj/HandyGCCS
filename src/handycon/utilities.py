#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

# Python Modules
import asyncio
import configparser
import os
import re
import subprocess
import sys
from . import devices

## Local modules
import handycon.handhelds.ally_gen1 as ally_gen1
import handycon.handhelds.anb_gen1 as anb_gen1
import handycon.handhelds.aok_gen1 as aok_gen1
import handycon.handhelds.aok_gen2 as aok_gen2
import handycon.handhelds.aya_gen1 as aya_gen1
import handycon.handhelds.aya_gen2 as aya_gen2
import handycon.handhelds.aya_gen3 as aya_gen3
import handycon.handhelds.aya_gen4 as aya_gen4
import handycon.handhelds.aya_gen5 as aya_gen5
import handycon.handhelds.aya_gen6 as aya_gen6
import handycon.handhelds.aya_gen7 as aya_gen7
import handycon.handhelds.ayn_gen1 as ayn_gen1
import handycon.handhelds.gpd_gen1 as gpd_gen1
import handycon.handhelds.gpd_gen2 as gpd_gen2
import handycon.handhelds.gpd_gen3 as gpd_gen3
import handycon.handhelds.oxp_gen1 as oxp_gen1
import handycon.handhelds.oxp_gen2 as oxp_gen2
import handycon.handhelds.oxp_gen3 as oxp_gen3
import handycon.handhelds.oxp_gen4 as oxp_gen4
from .constants import *

## Partial imports
from time import sleep

handycon = None
def set_handycon(handheld_controller):
    global handycon
    handycon = handheld_controller


# Capture the username and home path of the user who has been logged in the longest.
def get_user():
    global handycon

    handycon.logger.debug("Identifying user.")
    cmd = "who | awk '{print $1}' | sort | head -1"
    while handycon.USER is None:
        USER_LIST = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        for get_first in USER_LIST.stdout:
            name = get_first.decode().strip()
            if name is not None:
                handycon.USER = name
            break
        sleep(1)

    handycon.logger.debug(f"USER: {handycon.USER}")
    handycon.HOME_PATH = "/home/" + handycon.USER
    handycon.logger.debug(f"HOME_PATH: {handycon.HOME_PATH}")


# Identify the current device type. Kill script if not atible.
def id_system():
    global handycon

    system_id = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()
    cpu_vendor = get_cpu_vendor()
    handycon.logger.debug(f"Found CPU Vendor: {cpu_vendor}")

    ## ANBERNIC Devices
    if system_id in (
            "Win600",
            ):
        handycon.system_type = "ANB_GEN1"
        handycon.system_handler = anb_gen1

    ## AOKZOE Devices
    elif system_id in (
        "AOKZOE A1 AR07",
        ):
        handycon.system_type = "AOK_GEN1"
        handycon.system_handler = aok_gen1

    elif system_id in (
        "AOKZOE A1 Pro",
        ):
        handycon.system_type = "AOK_GEN2"
        handycon.system_handler = aok_gen2


    ## ASUS Devices
    elif system_id in (
        "ROG Ally RC71L_RC71L",
        ):
        handycon.system_type = "ALY_GEN1"
        handycon.system_handler = ally_gen1

    ## Aya Neo Devices
    elif system_id in (
        "AYA NEO FOUNDER",
        "AYA NEO 2021",
        "AYANEO 2021",
        "AYANEO 2021 Pro",
        "AYANEO 2021 Pro Retro Power",
        ):
        handycon.system_type = "AYA_GEN1"
        handycon.system_handler = aya_gen1

    elif system_id in (
        "NEXT",
        "NEXT Pro",
        "NEXT Advance",
        "AYANEO NEXT",
        "AYANEO NEXT Pro",
        "AYANEO NEXT Advance",
        ):
        handycon.system_type = "AYA_GEN2"
        handycon.system_handler = aya_gen2

    elif system_id in (
        "AIR",
        "AIR Pro",
        ):
        handycon.system_type = "AYA_GEN3"
        handycon.system_handler = aya_gen3

    elif system_id in (
        "AYANEO 2",
        "GEEK",
        ):
        handycon.system_type = "AYA_GEN4"
        handycon.system_handler = aya_gen4

    elif system_id in (
        "AIR Plus",
        ):
        if cpu_vendor == "GenuineIntel":
            handycon.system_type = "AYA_GEN7"
            handycon.system_handler = aya_gen7
        else:
            handycon.system_type = "AYA_GEN5"
            handycon.system_handler = aya_gen5

    elif system_id in (
        "AYANEO 2S",
        "GEEK 1S",
        "AIR 1S",
        ):
        handycon.system_type = "AYA_GEN6"
        handycon.system_handler = aya_gen6

    ## Ayn Devices
    elif system_id in (
            "Loki Max",
        ):
        handycon.system_type = "AYN_GEN1"
        handycon.system_handler = ayn_gen1

    ## GPD Devices.
    # Have 2 buttons with 3 modes (left, right, both)
    elif system_id in (
        "G1618-03", #Win3
        ):
        handycon.system_type = "GPD_GEN1"
        handycon.system_handler = gpd_gen1

    elif system_id in (
        "G1619-04", #WinMax2
        ):
        handycon.system_type = "GPD_GEN2"
        handycon.system_handler = gpd_gen2

    elif system_id in (
        "G1618-04", #Win4
        ):
        handycon.system_type = "GPD_GEN3"
        handycon.system_handler = gpd_gen3

## ONEXPLAYER and AOKZOE devices.
    # BIOS have inlete DMI data and most models report as "ONE XPLAYER" or "ONEXPLAYER".
    elif system_id in (
        "ONE XPLAYER",
        "ONEXPLAYER",
        ):
        if cpu_vendor == "GenuineIntel":
            handycon.system_type = "OXP_GEN1"
            handycon.system_handler = oxp_gen1
        else:
            handycon.system_type = "OXP_GEN2"
            handycon.system_handler = oxp_gen2

    elif system_id in (
        "ONEXPLAYER mini A07",
        ):
        handycon.system_type = "OXP_GEN3"
        handycon.system_handler = oxp_gen3

    elif system_id in (
        "ONEXPLAYER Mini Pro",
        ):
        handycon.system_type = "OXP_GEN4"
        handycon.system_handler = oxp_gen4

    # Block devices that aren't supported as this could cause issues.
    else:
        handycon.logger.error(f"{system_id} is not currently supported by this tool. Open an issue on \
ub at https://github.ShadowBlip/HandyGCCS if this is a bug. If possible, \
se run the capture-system.py utility found on the GitHub repository and upload \
 file with your issue.")
        sys.exit(0)

    # So that we can use the config during init, we need to get it BEFORE we init the handheld.
    get_config()

    handycon.system_handler.init_handheld(handycon)
    handycon.logger.info(f"Identified host system as {system_id} and configured defaults for {handycon.system_type}.")


def get_cpu_vendor():
    global handycon

    cmd = "cat /proc/cpuinfo"
    all_info = subprocess.check_output(cmd, shell=True).decode().strip()
    for line in all_info.split("\n"):
        if "vendor_id" in line:
                return re.sub( ".*vendor_id.*:", "", line,1).strip()


def get_config():
    global handycon
    # Check for an existing config file and load it.
    handycon.config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        handycon.logger.info(f"Loading existing config: {CONFIG_PATH}")
        handycon.config.read(CONFIG_PATH)
        if not "power_button" in handycon.config["Button Map"]:
            handycon.logger.info("Config file out of date. Generating new config.")
            set_default_config()
            write_config()
    else:
        set_default_config()
        write_config()
    map_config()


# Match runtime variables to the config
def map_config():
    # Assign config file values
    handycon.button_map = {
    "button1": EVENT_MAP[handycon.config["Button Map"]["button1"]],
    "button2": EVENT_MAP[handycon.config["Button Map"]["button2"]],
    "button3": EVENT_MAP[handycon.config["Button Map"]["button3"]],
    "button4": EVENT_MAP[handycon.config["Button Map"]["button4"]],
    "button5": EVENT_MAP[handycon.config["Button Map"]["button5"]],
    "button6": EVENT_MAP[handycon.config["Button Map"]["button6"]],
    "button7": EVENT_MAP[handycon.config["Button Map"]["button7"]],
    "button8": EVENT_MAP[handycon.config["Button Map"]["button8"]],
    "button9": EVENT_MAP[handycon.config["Button Map"]["button9"]],
    "button10": EVENT_MAP[handycon.config["Button Map"]["button10"]],
    "button11": EVENT_MAP[handycon.config["Button Map"]["button11"]],
    "button12": EVENT_MAP[handycon.config["Button Map"]["button12"]],
    }
    handycon.power_action = POWER_ACTION_MAP[handycon.config["Button Map"]["power_button"]][0]

    handycon.turbo = turbo_handler(handycon.config.get("turbo",{}))



# Sets the default configuration.
def set_default_config():
    global handycon
    handycon.config["Button Map"] = {
            "button1": "SCR",
            "button2": "QAM",
            "button3": "ESC",
            "button4": "OSK",
            "button5": "MODE",
            "button6": "OPEN_CHIMERA",
            "button7": "TOGGLE_PERFORMANCE",
            "button8": "MODE",
            "button9": "TOGGLE_MOUSE",
            "button10": "ALT_TAB",
            "button11": "KILL",
            "button12": "TOGGLE_GYRO",
            "power_button": "SUSPEND",
            }

    handycon.config["Turbo"] = turbo_handler.get_default_config()


# Writes current config to disk.
def write_config():
    global handycon
    # Make the HandyGCCS directory if it doesn't exist.
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)

    with open(CONFIG_PATH, 'w') as config_file:
        handycon.config.write(config_file)
        handycon.logger.info(f"Created new config: {CONFIG_PATH}")


def steam_ifrunning_deckui(cmd):
    global handycon

    # Get the currently running Steam PID.
    steampid_path = handycon.HOME_PATH + '/.steam/steam.pid'
    try:
        with open(steampid_path) as f:
            pid = f.read().strip()
    except Exception as err:
        handycon.logger.error(f"{err} | Error getting steam PID.")
        return False

    # Get the andline for the Steam process by checking /proc.
    steam_cmd_path = f"/proc/{pid}/cmdline"
    if not os.path.exists(steam_cmd_path):
        # Steam not running.
        return False

    try:
        with open(steam_cmd_path, "rb") as f:
            steam_cmd = f.read()
    except Exception as err:
        handycon.logger.error(f"{err} | Error getting steam cmdline.")
        return False

    # Use this andline to determine if Steam is running in DeckUI mode.
    # e.g. "steam://shortpowerpress" only works in DeckUI.
    is_deckui = b"-gamepadui" in steam_cmd
    if not is_deckui:
        return False

    steam_path = handycon.HOME_PATH + '/.steam/root/ubuntu12_32/steam'
    try:
        result = subprocess.run(["su", handycon.USER, "-c", f"{steam_path} -ifrunning {cmd}"])
        return result.returncode == 0
    except Exception as err:
        handycon.logger.error(f"{err} | Error sending and to Steam.")
        return False


def launch_chimera():
    global handycon

    if not handycon.HAS_CHIMERA_LAUNCHER:
        return
    subprocess.run([ "su", handycon.USER, "-c", CHIMERA_LAUNCHER_PATH ])


def is_process_running(name) -> bool:
    read_proc = os.popen("ps -Af").read()
    proc_count = read_proc.count(name)
    if proc_count > 0:
        handycon.logger.debug(f'Process {name} is running.')
        return True
    handycon.logger.debug(f'Process {name} is NOT running.')
    return False

class turbo_handler:
    DEFAULT_CONFIG = {
            "capture": True,
            # Default emulates existing TOGGLE_PERFORMANCE Behaviour
            "speeds" : { # Only used for toggle mode.  Will start at default, and step through the numbered keys, in order.
                0: {
                    "command": [
                        "ryzenadj --power-saving",
                        "cpupower frequency-set -g powersave",
                    ],
                    "feedback": [
                        "export XDG_RUNTIME_DIR=/run/user/1000",
                        "pw-play /usr/share/notifications/power-saving.ogg",
                    ],
                    "rumble": 1,
                    "default" : True,
                },
                1: {
                    "command": [
                        "ryzenadj --max-performance",
                        "cpupower frequency-set -g performance",
                    ],
                    "feedback": [
                        "export XDG_RUNTIME_DIR=/run/user/1000",
                        "pw-play /usr/share/notifications/max-performance.ogg",
                    ],
                    "rumble": 2,
                    "default" : True,
                },
            }}

    IGNORE_MODE = "ignore"
    KEY_MODE = "key"
    TOGGLE_MODE = "toggle"


    def __init__(self, config:dict|None):
        self.enabled = False
        self.config = config if not None else self.DEFAULT_CONFIG

        # Get all the speeds and remove the default indicator.
        self.default = 0
        self.speeds = sorted(self.config.get("speeds",{}).keys())
        # Find the default speed, or just set to the first.
        for speed in speeds:
            if speed.get("default",False):
                self.default = speed
                break

    @classmethod
    def get_default_config(cls) -> dict:
        cfg = cls.DEFAULT_CONFIG

        # Override defaults for Powersave and Performance if we know a better set for a particular device.
        try:
            cfg["speeds"][0][command] = handycon.system_handler.get_powersave_config()
            cfg["speeds"][1][command] = handycon.system_handler.get_performance_config()

        except Exception:
            # Ignore if this fails. It just means the module doesn't change the defaults.
            pass

        return cfg

    def capture(self) -> bool:
        # Do we want to capture the Turbo Key?
        mode = self.config.get("capture",False)
        return mode is True

    def set_turbo(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.toggle(0))

    async def toggle(self, step = 1):
        # Normally don't set step.  Its only purpose is to reuse logic at startup.
        self.current += step

        # Make sure the current speed is valid
        current = self.current
        if current > len(self.speeds):
            current = 0
        self.current = current

        if current > len(self.speeds):
            # Nothing to do, no speeds.
            return

        new_speed = self.config.get("speeds",{}).get(current,{})
        command = new_speed.get("command",None)
        if command is not None:
            # Execute the speed setting command.
            await run_async(command, 'Turbo Toggled with:')

        feedback = new_speed.get("feedback",None)
        if feedback is not None:
            # execute the feedback command.
            await run_async(feedback, 'Turbo Feedback with:')

        rumble = new_speed.get("rumble",None)
        if rumble is not None:
            # execute the rumble command.
            while rumble > 0:
                await devices.do_rumble(0, 100, 100, 0)
                await asyncio.sleep(FF_DELAY)


async def run_async(cmd: list[str] | str, prompt="Ran external command:"):
    if isinstance(cmd, list):
        # Turn an array of commands into a single command with `;` between them,
        # so they can be executed in a single call.
        cmd = " ; ".join(cmd)

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr= asyncio.subprocess.STDOUT)
    stdout, _ = await proc.communicate()
    rc = proc.returncode
    handycon.logger.info(f'{prompt} {cmd} : {rc} : {stdout}')

