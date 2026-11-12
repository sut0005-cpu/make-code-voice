# On-device speech through the micro:bit speaker

The primary speech engine runs as **MicroPython firmware on the micro:bit**. It imports the official `speech` module and generates the speech audio locally on the board. It does not use `pyttsx3`, `bridge.py`, a cloud API, or a connected computer.

## Hardware

- **micro:bit V2:** speech plays through the built-in speaker.
- **micro:bit V1:** connect a small speaker or headphones between P0 and GND.

## Flash and run

1. Open the [micro:bit Python Editor](https://python.microbit.org/).
2. Create a MicroPython project for your board.
3. Add `main.py` and `onboard_dictionary.py` from this repository.
4. Flash the program to the micro:bit.
5. It speaks a greeting after startup. Press A for another greeting or B to hear demo words.

## Receive text from the MakeCode controller

The firmware also listens on micro:bit radio group **42**. It reads MakeCode's raw radio string packets, extracts the string payload, and reassembles the controller's chunk format:

```text
~<one-digit-message-id><one-digit-part-index><one-digit-part-count><text>
```

For example, `~400Hello wo` is part 0 of a three-part message with ID 4. Send no more than 8 message characters in each chunk, and no more than 4 chunks (32 characters total). This keeps each `radio.sendString` packet within MakeCode's 19-character limit.

The receiver parses the MakeCode packet header before processing the string. It does not treat the raw radio bytes as plain text.

## Critical: MakeCode and MicroPython cannot run together

This speech firmware is MicroPython. Flashing it replaces the MakeCode program on that micro:bit. The Maqueen Plus V2 MakeCode extension and its motor-control blocks will not run in this MicroPython program. If the same robot micro:bit must drive the Maqueen and speak, the Maqueen motor-control functions need a separate MicroPython port.

## Speech and dictionary

- `speech.say(text)` speaks ordinary English using the micro:bit's built-in SAM-derived synthesizer.
- `speech.pronounce(phonemes)` speaks SAM phoneme strings.
- Words found in the bundled packed dictionary use the stored CMU ARPAbet pronunciation converted to SAM phonemes.
- Words not in the dictionary fall back to `speech.say`.
- Custom SAM pronunciations added with `add_custom` are held in RAM for the current run.

The voice is compact and robotic; it is not neural or recorded human speech.

## Optional PC bridge

`main.ts` and `bridge.py` remain available as a separate USB-connected host-TTS mode. That mode speaks through the computer, not through the micro:bit speaker. It is not required for this on-device firmware.
