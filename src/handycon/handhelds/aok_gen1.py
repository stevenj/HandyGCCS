#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

import os
import sys
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff

from .. import constants as cons

handycon = None

# AOKZOE A1 KEY MAP

AOKZOE_A1_HOME = [125, 32]                # Left Meta + D
AOKZOE_A1_HOME_LONG = [125, 34]           # Left Meta + G
AOKZOE_A1_KBD = [97, 125, 24]             # Left Ctrl + Left Meta + O
AOKZOE_A1_TURBO = [29, 125, 56]           # Left Ctrl + Left Meta + Left Alt
AOKZOE_A1_HOME_PLUS_KBD = [100, 97, 111]  # Ctrl Alt Del
AOKZOE_A1_HOME_PLUS_TURBO = [99, 125]     # Left Meta + Sysreq
AOKZOE_A1_TURBO_LONG_DELAY = 1.5


AOKZOE_A1_START = []
AOKZOE_A1_BACK = []

AOKZOE_A1_VOLUME_DOWN = e.KEY_VOLUMEDOWN
AOKZOE_A1_VOLUME_UP = e.KEY_VOLUMEUP

def init_handheld(handheld_controller):
    global handycon
    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.09
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:e4:00.3-4/input0'
    handycon.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    handycon.KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
    handycon.KEYBOARD_NAME = 'AT Translated Set 2 keyboard'

    # See if we need to capture the Turbo button
    tt_toggle = '/sys/devices/platform/oxp-platform/tt_toggle'
    if handycon.turbo.capture() and os.path.exists(tt_toggle):
        command = f'echo 1 > {tt_toggle}'
        run = os.popen(command, 'r', 1).read().strip()
        handycon.logger.info(f'Turbo button takeover enabled')
        # Setup the turbo handler default settings.
    handycon.turbo.set_turbo()


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button1 = handycon.button_map["button1"]  # Default Screenshot
    button2 = handycon.button_map["button2"]  # Default QAM
    button3 = handycon.button_map["button3"]  # Default ESC
    button4 = handycon.button_map["button4"]  # Default OSK
    button5 = handycon.button_map["button5"]  # Default MODE
    button6 = handycon.button_map["button6"]  # Default OPEN_CHIMERA
    button7 = handycon.button_map["button7"]  # Default TOGGLE_PERFORMANCE

    ## Loop variables
    events = []
    this_button = None
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        await handycon.emit_events([seed_event])

    # Handle missed keys.
    if active_keys == [] and handycon.event_queue != []:
        this_button = handycon.event_queue[0]

    # BUTTON 1 (Possible dangerous fan activity!) Short press orange + |||||
    if active_keys == AOKZOE_A1_HOME_PLUS_TURBO and button_on == 1 and button1 not in handycon.event_queue:
        handycon.event_queue.append(button1)
    elif active_keys == [] and seed_event.code in AOKZOE_A1_HOME_PLUS_TURBO and button_on == 0 and button1 in handycon.event_queue:
        this_button = button1

    # BUTTON 2 (Default: QAM) Turbo Button
    # This event won't fire if turbo was not captured
    if active_keys == AOKZOE_A1_TURBO and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
    elif active_keys == [] and seed_event.code in AOKZOE_A1_TURBO and button_on == 0 and button2 in handycon.event_queue:
        this_button = button2
        await handycon.do_rumble(0, 150, 1000, 0)

    # BUTTON 3 (Default: ESC) Short press orange + KB
    if active_keys == AOKZOE_A1_HOME_PLUS_KBD and button_on == 1 and button3 not in handycon.event_queue:
        handycon.event_queue.append(button3)
    elif active_keys == [] and seed_event.code in AOKZOE_A1_HOME_PLUS_KBD and button_on == 0 and button3 in handycon.event_queue:
        this_button = button3

    # BUTTON 4 (Default: OSK) Short press KB
    if active_keys == AOKZOE_A1_KBD and button_on == 1 and button4 not in handycon.event_queue:
        handycon.event_queue.append(button4)
    elif active_keys == [] and seed_event.code in AOKZOE_A1_KBD and button_on == 0 and button4 in handycon.event_queue:
        this_button = button4

    # BUTTON 5 (Default: MODE) Short press orange
    if active_keys == AOKZOE_A1_HOME and button_on == 1 and button5 not in handycon.event_queue:
        handycon.event_queue.append(button5)
    elif active_keys == [] and seed_event.code in AOKZOE_A1_HOME and button_on == 0 and button5 in handycon.event_queue:
        this_button = button5

    # BUTTON 6 (Default: Launch Chimera) Long press orange
    if active_keys == AOKZOE_A1_HOME_LONG and button_on == 1 and button6 not in handycon.event_queue:
        handycon.event_queue.append(button6)
    elif active_keys == [] and seed_event.code in AOKZOE_A1_HOME_LONG and button_on == 0 and button6 in handycon.event_queue:
        this_button = button6

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and  handycon.event_queue == [] and handycon.shutdown == True:
        handycon.shutdown = False

    # Create list of events to fire.
    # Handle new button presses.
    if this_button and not handycon.last_button:
        handycon.event_queue.remove(this_button)
        handycon.last_button = this_button
        await handycon.emit_now(seed_event, this_button, 1)

    # Clean up old button presses.
    elif handycon.last_button and not this_button:
        await handycon.emit_now(seed_event, handycon.last_button, 0)
        handycon.last_button = None


def get_powersave_config() -> list[str]:
    # get the default powersave config for this device
    # Emulates the Turbo button defaults plus enables powersaving governor
    return [
        "ryzenadj -a 15 -b 25 -c 20 -f 95 -g 52 -j 13 -k 105 -l 17 --power-saving",
        "cpupower frequency-set -g powersave",
    ]

def get_performance_config() -> list[str]:
    # get the default performance config for this device
    # Emulates the Turbo button defaults plus enables powersaving governor
    return [
        "ryzenadj -a 28 -b 35 -c 32 -f 95 -g 52 -j 13 -k 105 -l 17 --max-performance",
        "cpupower frequency-set -g performance",
    ]
