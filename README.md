# Kalimba Radio
Midi to Keyboard program except Good

This program is made to function for multiple videogames that allow playing instruments via keyboard presses. you can play .mid files, hook up your MIDI keyboard to play notes, etc.

Current official support is for:
- [Core Keeper](https://store.steampowered.com/app/1621690/Core_Keeper/)
- [Yume 2kki](https://wikiwiki.jp/yumenikki-g3/)
- [Collective Unconscious](https://ynoproject.net/unconscious/)

## How to Use / Specs
Open `@config.yaml`, this file functions as a global config.
- `pattern`: the pattern file to use, each game has a separate pattern file.
- `input`: the MIDI device to connect. if run left blank, currently connected MIDI input devices will be listed in the console.
- Keybinds
  - `modechange`: Changes between "Precise Mode" and "Safe Mode", that determines the priority for the MIDI parser. does nothing for chord-supporting games.
  - `playmidi`: play midi file, you will be prompted to type the name of the file upon pressing the key.
  - `pausemidi`: pause and resume midi file mid play.
  - `stopmidi`: stop midi file from play and return to normal mode.
  - `quit`: exit the program.
- `fps`: global clock speed of the program.
- `debug`: displays debug data.

You can also create a custom pattern file to support games not currently in. feel free to send a PR / notify me in issues with pattern files.
- `idle_delay`: number of ticks (1 = 1/`fps` second) to rest before polling MIDI and process notes again.
- `busy_delay`: number of ticks between each notes, used to arpeggiate chords. set to 0 to disable.
- `release_duration`: number of ticks to wait before releasing all notes. set to 0 to disable.
- `smart_octave`: treats everything but the last key in each entry as an "octave", and skips over unneeded octave presses and releases. if you have a "octave change" key and "note key", this optimizes number of keypresses and helps in case of arpeggiation.
- `panic_threshold_notes`: maximum number of notes that can exist in the queue, when the queue overloads, the program does not enforce `busy_delay` until the element is under the threshold. set to 0 to disable.
- Notes
  - Note names can be gotten by enabling the debug flag and typing.
  - notate releasing keys by prepending `^` in front, `^A`, `^C`, etc...
  - `midi_^903C`: operate directly on MIDI message, regex matched. this will match every MIDI message that starts with 903C (C5).
  - `press_C5`: same with above - but human readable.
  - `release_C5`: triggered when C5 is released.
  - `toggle_C5`: a shorthand for pressing keys at `press_C5` and releasing keys at `release_C5`. cannot be used to release keys at `press`.
  - `press_C`: triggered when any C note is pressed, regardless of octave.
  - `press_5`: triggered when any note of octave 5 is pressed.
  - order of key presses: `[META_OCTAVE] [META_NOTE] [SPECIFIC_NOTE] [MIDI]`, important for `smart_octave` related config.

## Video
:3
