import os
import yaml
import re
import keyboard
import pygame.midi as midi
import mido
import time
from functools import reduce

def exit(code):
    try:
        os.system('pause')
    except:
        os.system('read -p "Press any key to continue"')
    os._exit(code)

def open_yaml(pth):
    if not os.path.isfile(pth):
        print(f"[ERROR] {pth} does not exist.")
        return None
    with open(pth, encoding="utf-8") as f:
        str = f.read()
    try:
        return yaml.safe_load(str)
    except:
        print(f"[ERROR] {pth} is not a valid YAML file")
        return None

def add_entries(src, match, ret=None, fn=None, fn2=None):
    if ret is None:
        ret = dict()
    for k in [x for x in src.keys() if re.match(match, x)]:
        keys = k[(k.index("_") + 1):]
        if fn is not None:
            keys = fn(keys)
        if type(keys) is not list:
            keys = [keys]
        value = src[k]
        if fn2 is not None:
            value = fn2(value)
        for kk in keys:
            if kk in ret:
                ret[kk].append(value)
            else:
                ret[kk] = [value]
    return ret


NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
def note_to_midi(note):
    global NOTES
    note = note.strip().upper()
    idx = re.search(r"\d", note).start()
    ret = NOTES.index(note[:idx])
    if ret is None:
        print("[ERROR] note is not valid")
        return None
    return f'{int(note[idx:]) * 12 + ret:02x}'.upper()

def midi_to_note(midi):
    global NOTES
    note = int(midi, 16)
    return NOTES[note % 12] + str(int(note / 12))

midi.init()
inputs = dict()
for i in range(midi.get_count()):
    info = midi.get_device_info(i)
    if info[2] != 1:
        continue
    inputs[info[1].decode('UTF-8')] = i
print()
print(r"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")
print(r"\\                                \\")
print(r"\\ Kalimba Radio       r2 by prod \\")
print(r"\\    Midi to Keyboard Translator \\")
print(r"\\                                \\")
print(r"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")
print()

file_config = open_yaml("@config.yaml")
if file_config is None:
    exit(1)
if file_config["pattern"] is None:
    print("edit the @config.yaml before running this program!")
    exit(0)
else:
    file_pattern = open_yaml(file_config["pattern"] + ".yaml")
    if file_pattern is None:
        exit(1)
DEBUG = file_config["debug"]
FPS = file_config["fps"]
if file_config["input"] in inputs:
    print("Connected MIDI device: " + file_config["input"])
    midi_input = midi.Input(inputs[file_config["input"]])
else:
    print("MIDI devices not found, connected device names:\n" + "\n  ".join(inputs.keys()))

# thank you insertion ordered dicts
keybind = add_entries(file_config, r"^key_")
for k in keybind:
    keybind[k] = keybind[k][0]
tuning = add_entries(file_pattern, r"^_")
for k in tuning:
    tuning[k] = tuning[k][0]
pattern = dict()
# META_OCTAVE
pattern = add_entries(file_pattern, r"^press_\d+$", pattern, lambda x: ["^90" + note_to_midi(note + str(x)) for note in NOTES])
pattern = add_entries(file_pattern, r"^release_\d+$", pattern, lambda x: ["^80" + note_to_midi(note + str(x)) for note in NOTES])
pattern = add_entries(file_pattern, r"^toggle_\d+$", pattern, lambda x: ["^90" + note_to_midi(note + str(x)) for note in NOTES])
pattern = add_entries(file_pattern, r"^toggle_\d+$", pattern, lambda x: ["^80" + note_to_midi(note + str(x)) for note in NOTES], lambda x: ", ".join(["^" + y.strip() for y in x.split(",")]))
# META_NOTE
pattern = add_entries(file_pattern, r"^press_[A-G]#?$", pattern, lambda x: ["^90" + note_to_midi(x + str(o)) for o in range(11)])
pattern = add_entries(file_pattern, r"^release_[A-G]#?$", pattern, lambda x: ["^80" + note_to_midi(x + str(o)) for o in range(11)])
pattern = add_entries(file_pattern, r"^toggle_[A-G]#?$", pattern, lambda x: ["^90" + note_to_midi(x + str(o)) for o in range(11)])
pattern = add_entries(file_pattern, r"^toggle_[A-G]#?$", pattern, lambda x: ["^80" + note_to_midi(x + str(o)) for o in range(11)], lambda x: ", ".join(["^" + y.strip() for y in x.split(",")]))
# SPECIFIC_NOTE
pattern = add_entries(file_pattern, r"^press_[A-G]#?\d+$", pattern, lambda x: "^90" + note_to_midi(x))
pattern = add_entries(file_pattern, r"^release_[A-G]#?\d+$", pattern, lambda x: "^80" + note_to_midi(x))
pattern = add_entries(file_pattern, r"^toggle_[A-G]#?\d+$", pattern, lambda x: "^90" + note_to_midi(x))
pattern = add_entries(file_pattern, r"^toggle_[A-G]#?\d+$", pattern, lambda x: "^80" + note_to_midi(x), lambda x: ", ".join(["^" + y.strip() for y in x.split(",")]))
# MIDI
pattern = add_entries(file_pattern, r"^midi_", pattern)
if tuning["idle_delay"] <= 0:
    print("[ERROR] idle_delay is 0 or negative!")
    exit(1)

state = "idle" # idle, input, midi, paused
safe_mode = False
midi_second = 0
midi_track = []
def onkey(key):
    global state, keybind, fname, safe_mode, midi_second, midi_track
    key = key.name
    if DEBUG:
        print("Key Pressed: " + key)
    if state == "idle":
        if key == keybind["playmidi"]:
            print("Type the name of the midi file and press enter. (\"song\" for song.midi, in same folder)")
            fname = ""
            state = "input"
        if key == keybind["modechange"]:
            safe_mode = not safe_mode
            if safe_mode:
                print("Safe Mode Activated (prioritize note integrity)")
            else:
                print("Precise Mode Activated (prioritize timing)")
        if key == keybind["quit"]:
            print("Exiting Kalimba Radio")
            state = "quit"
    elif state == "input":
        if key == "backspace":
            if len(fname) > 0:
                fname = fname[:-1]
            print("  > open: " + fname)
        if len(key) == 1:
            fname += key
            print("  > open: " + fname)
        if key == "space":
            fname += " "
            print("  > open: " + fname)
        if key == "enter":
            if not os.path.isfile(fname):
                print("File does not exist. Process aborted")
                state = "idle"
            else:
                print("Playing " + fname)
                file = mido.MidiFile(fname)
                tick = 0
                midi_track = list()
                tempo = 1000
                for k in file.merged_track:
                    data = k.dict()
                    if "tempo" in data:
                        tempo = data["tempo"]
                    tick += data["time"]
                    midi_track.append((k.hex(""), mido.tick2second(tick, file.ticks_per_beat, tempo)))
                midi_second = 0
                state = "midi"
        if key == keybind["stopmidi"]:
            print("Midi Play Aborted")
            state = "idle"
    elif state == "midi":
        if key == keybind["pausemidi"]:
            print("Pausing MIDI file")
            state = "paused"
        if key == keybind["stopmidi"]:
            print("Stopping MIDI file")
            state = "idle"
        if key == keybind["modechange"]:
            safe_mode = not safe_mode
            if safe_mode:
                print("Safe Mode Activated (prioritize note integrity)")
            else:
                print("Precise Mode Activated (prioritize timing)")
    elif state == "paused":
        if key == keybind["pausemidi"]:
            print("Resuming MIDI file")
            state = "midi"
        if key == keybind["stopmidi"]:
            print("Stopping MIDI file")
            state = "idle"
        if key == keybind["modechange"]:
            safe_mode = not safe_mode
            if safe_mode:
                print("Safe Mode Activated (prioritize note integrity)")
            else:
                print("Precise Mode Activated (prioritize timing)")
keyboard.on_press(onkey)
queue = list()
delay = 0
playing = dict()
octave = list()
def onmidi(data):
    global queue, tuning, pattern, octave
    if len(data) == 0:
        return
    data.sort()
    data.reverse()
    if DEBUG:
        print("MIDI Data Recieved: " + str(data))
    keys = list()
    for note in data:
        _keys = list()
        for k in pattern:
            if re.match(k, note):
                _keys.extend(pattern[k])
        if len(_keys) > 0:
            if tuning["smart_octave"]:
                octave_new = _keys[:-1]
                keys.extend(["^" + x, 0] for x in octave if x not in octave_new)
                keys.extend([x, float('inf')] for x in octave_new if x not in octave)
                keys.append([_keys[-1], 1])
                octave = octave_new
            else:
                keys.extend([[x, len(_keys) - i] for i, x in enumerate(_keys)])
    if len(keys) > 0:
        if tuning["busy_delay"] == 0:
            keys = [x for x in keys if not x[0].startswith("^") or x[0][1:] not in keys]
        queue.extend(keys)

while state != "quit":
    data = list()
    while midi_input != None and midi_input.poll():
        data.append(''.join([f'{x:02x}'.upper() for x in (midi_input.read(1))[0][0]]))
    if state == "midi":
        if len(midi_track) == 0:
            print("Finished Playing MIDI file")
            state = "idle"
        else:
            while len(midi_track) > 0 and midi_track[0][1] <= midi_second:
                data.append(midi_track.pop(0)[0])
        midi_second += tuning["idle_delay"] / FPS
    onmidi(data)
    for note in playing:
        playing[note] -= tuning["idle_delay"]
        if playing[note] <= 0:
            queue.insert(0, ["^" + note, 0])
    while delay <= 0 and len(queue) > 0:
        note = queue.pop(0)
        if not note[0].startswith("^"):
            duration = (tuning["release_duration"] + (1 if safe_mode and tuning["release_duration"] > 0 else 0)) * note[1]
            if note[0] in playing:
                playing[note[0]] = duration
                if DEBUG:
                    print("Key Held: " + note[0])
            else:
                keyboard.press(note[0])
                playing[note[0]] = duration
                if DEBUG:
                    print("Key Pressed: " + note[0])
            if tuning["panic_threshold_notes"] > 0 and len(queue) > tuning["panic_threshold_notes"]:
                print("Note Panic! Skipping some notes...")
            else:
                delay += tuning["busy_delay"] + (1 if safe_mode and tuning["busy_delay"] > 0 else 0)
        else:
            note = [note[0][1:], note[1]]
            if note[0] in playing:
                keyboard.release(note[0])
                playing.pop(note[0])
                if DEBUG:
                    print("Key Released: " + note[0])
    if delay > 0:   
        delay -= tuning["idle_delay"]
    time.sleep(tuning["idle_delay"] / FPS)
midi.quit()
exit(0)