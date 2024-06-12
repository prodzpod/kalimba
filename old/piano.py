import sys
import os
import json
import re
import keyboard
import pygame.midi as midi
import time
from functools import reduce

INPUT = "loopMIDI Port"
DURATION = 2
OCTAVES = True
DELAY = 0.04
IDLE_DELAY = 0.01
NOTE_PANIC = 10
DEBUG = True

MATCH = dict()
keys = list()
octave = list()
is_idle = 1
notes = 0

if len(sys.argv) >= 2 and os.path.isfile(sys.argv[1]):
    with open(sys.argv[1], encoding="utf8") as f:
        print("Loaded Pattern: " + sys.argv[1])
        MATCH = json.loads(f.read())

midi.init()
inputs = dict()
for i in range(midi.get_count()):
    info = midi.get_device_info(i)
    if info[2] != 1:
        continue
    inputs[info[1].decode('UTF-8')] = i
midi_input = None
if INPUT in inputs:
    print("Connected MIDI device: " + INPUT)
    midi_input = midi.Input(inputs[INPUT])
else:
    print("MIDI devices not found, devices:\n" + "\n  ".join(inputs.keys()))
if DEBUG:
    keyboard.on_press(lambda x: print("Key Pressed: " + str(x)))
while True:
    if keyboard.is_pressed('esc'):
        break
    for k in keys:
        #print("Checking for Keys: " + str(k))
        k[1] += is_idle
        if k[1] >= DURATION:
            keyboard.release(k[0])
            keys.remove(k)
    is_idle = 1
    while midi_input != None and midi_input.poll():
        data = ''.join([f'{x:02x}'.upper() for x in (midi_input.read(1))[0][0]])
        print("Midi Recieved: " + data)
        for k in list(MATCH.keys()):
            if re.search(k, data):
                if notes >= 10:
                    if DEBUG:
                        print("panic! (too much notes, lower your bpm)")
                    is_idle = 1
                key = MATCH[k]
                if OCTAVES:
                    _key = [x.strip() for x in key.split(",")]
                    if len(_key) == len(octave) + 1 and reduce(lambda c, x: c and x in _key, octave, True):
                        key = _key[-1]
                    else:
                        release = [x for x in octave if x not in _key]
                        _key = [x for x in _key if x not in octave]
                        key = ", ".join(_key)
                        octave = _key[:-1]
                        if len(release):
                            keyboard.release(", ".join(release))
                    print("Keys Sent: " + key + " (octave: " + str(octave) + ")")
                else:
                    print("Keys Sent: " + key)
                #keyboard.release(key)
                keyboard.press(key)
                #_key = [x.strip() for x in key.split(",")]
                #for k in _key:
                #    keyboard.press(k)
                keys.append([key, 0])
                if DELAY > 0:
                    notes += 1
                    time.sleep(DELAY)
                    is_idle = 0
                    for k in keys:
                        #print("Checking for Keys: " + str(k))
                        k[1] += DELAY / IDLE_DELAY
                        if k[1] >= DURATION:
                            keyboard.release(k[0])
                            keys.remove(k)
    if is_idle == 1:
        notes = 0
        time.sleep(IDLE_DELAY)
midi.quit()