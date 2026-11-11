# On-device speech (primary mode)

The primary speech engine runs as **MicroPython firmware on the micro:bit**. It uses the official MicroPython `speech` module, a compact SAM-derived formant synthesizer. Text is converted to phonemes and audio is generated locally by the board. It does not call `pyttsx3`, a cloud API, or a PC speech service.

## Hardware

- **micro:bit V2:** use the built-in speaker.
- **micro:bit V1:** connect a small speaker or headphones between P0 and GND. The V1 board has no built-in speaker.

## Flash and run

1. Open the official micro:bit MicroPython editor or another supported MicroPython editor.
2. Select the correct micro:bit MicroPython firmware/device target.
3. Copy `main.py` and `onboard_dictionary.py` to the device (or combine them into one `main.py` if your editor only supports one file).
4. Reset the board. It speaks a greeting at startup.
5. Press A for a greeting, B to cycle through example words, or touch the V2 logo to hear the dictionary count.

The on-board dictionary contains 750 CMU ARPAbet lookup entries. To keep RAM overhead lower, it is stored as one packed text string and searched linearly. For words in the 750-entry dictionary, the runtime converts CMU ARPAbet tokens to the corresponding MicroPython SAM phoneme symbols and calls `speech.pronounce`; this makes the bundled dictionary drive the actual audible pronunciation. Words outside the list fall back to `speech.say`. Stress digits are mapped to SAM stress markers.

## Custom pronunciation

Use `microbit_speech_api.set_custom_pronunciation("robot", "ROW4BAHT")` with SAM phoneme notation. Custom overrides are held in RAM for the current run; persistent editing/storage is a future enhancement. See the official MicroPython speech API for the complete SAM phoneme table and voice parameters.

## Limits

- This is a compact, robotic/formant voice, not recorded human speech or modern neural TTS.
- Words in the 750-entry dictionary use the bundled CMU pronunciation converted to SAM phonemes. Words outside the list use the built-in English-to-phoneme conversion, which is approximate. Use SAM phonemes for custom pronunciation.
- The 750-word list supports on-device lookup. Words outside it can still be attempted by the built-in speech translator.
- The original MakeCode extension and `bridge.py` are retained as an optional host-bridge mode. They are not required for the on-device MicroPython speech program.
- micro:bit V1 has much less RAM than V2. The complete 750-entry dictionary is primarily targeted at V2; on V1, use the speech demo without importing the full dictionary if memory is insufficient.
