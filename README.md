# micro:bit English Speech Engine

An on-device English speech engine for the BBC micro:bit. The primary firmware is MicroPython and uses the micro:bit's built-in `speech` synthesizer. On a micro:bit V2, speech plays through the board's built-in speaker. No PC speech bridge, cloud API, or external TTS service is required.

The repository also retains an optional MakeCode-to-PC speech bridge. That is a separate mode; it is not used by the on-device speaker firmware.

## Use the built-in micro:bit speaker

### Hardware

- **micro:bit V2:** built-in speaker; no extra speaker wiring is needed.
- **micro:bit V1:** connect a small speaker or headphones between P0 and GND.

### Install the on-device firmware

1. Open the official [micro:bit Python Editor](https://python.microbit.org/).
2. Create a MicroPython project for a micro:bit V2.
3. Add both `main.py` and `onboard_dictionary.py` from this repository to the project.
4. Flash the project to the robot's micro:bit V2.
5. On reset, the board speaks a greeting. Press A for a greeting and B to cycle through demo words.
6. Set the controller to radio group **42**. The robot firmware listens for MakeCode radio string packets and speaks completed text messages.

### Radio message format

The robot firmware receives MakeCode `radio.sendString` packets on group 42. It expects the controller's existing chunk format:

```text
~<message-id><part-index><part-count><text-chunk>
```

For example, the first packet of a three-part message with ID 4 is:

```text
~400Hello wo
```

Use chunks of at most 8 message characters. Each packet must be no longer than MakeCode's 19-character `radio.sendString` limit. The firmware reassembles up to 32 characters before speaking.

### Important runtime limitation

The on-device speech firmware is **MicroPython**. Flashing it replaces the MakeCode runtime on that micro:bit. The Maqueen Plus V2 MakeCode motor extension therefore cannot run alongside this speech program. To have the same board both drive the Maqueen and speak, the Maqueen motor-control code must also be ported to MicroPython. Do not expect MakeCode extensions such as `maqueenPlusV2` to work in MicroPython.

## Repository contents

- `main.py` — on-device MicroPython speech firmware with MakeCode radio text reception.
- `onboard_dictionary.py` — packed on-device pronunciation dictionary.
- `microbit_speech_api.py` — reusable MicroPython speech API.
- `main.ts`, `dictionary.ts`, `pxt.json` — optional MakeCode extension for the USB-connected computer TTS bridge.
- `bridge.py` — optional USB serial bridge that speaks through the computer's installed TTS.
- `sound_units.csv`, `pronunciation_dictionary.csv`, `custom_pronunciations.csv` — pronunciation data.
- `generate_project.py` — data generator and ZIP packager.
- `firmware/` — supplied HEX files, preserved unchanged.

## Optional computer speech bridge

The computer bridge is a separate alternative. It uses the computer's audio output, not the micro:bit speaker:

```bash
python -m pip install -r requirements.txt
python bridge.py --port COM3
```

Replace `COM3` with the micro:bit serial port. Keep the bridge running and the micro:bit connected by USB.

## Generate and validate dictionary data

```bash
python -m pip install -r requirements-generator.txt
python generate_project.py
python generate_project.py --validate
python generate_project.py --zip
```

## Voice and pronunciation

The MicroPython speech engine uses the SAM-derived `speech.say` and `speech.pronounce` functions. The voice is intentionally compact and robotic rather than neural or human-recorded speech. Voice settings are configured near the top of `main.py`.

## License

MIT. The supplied firmware files are redistributed as user-provided originals; verify their own licensing/redistribution terms before public release.
