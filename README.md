# micro:bit English Speech Engine (1000 words)

A micro:bit English speech project with two paths: the MicroPython firmware (`main.py`) synthesizes speech directly on the micro:bit using its built-in `speech` module; the optional MakeCode extension and `bridge.py` provide a separate USB-connected host-TTS path.

## Repository contents

- `generate_project.py` — reproducible dictionary/data generator and ZIP packager.
- `sound_units.csv` — exactly 100 sound units (24 consonants, 45 vowel/stress units, 31 optional diphone transitions).
- `pronunciation_dictionary.csv` — exactly 1000 unique CMUdict-backed English entries.
- `custom_pronunciations.csv` — custom entries.
- `main.ts`, `dictionary.ts`, `pxt.json` — MakeCode extension; `dictionary.ts` now embeds all 1,000 word/pronunciation records and provides a lookup function.
- `main.py` — on-device MicroPython speech firmware.
- `onboard_dictionary.py` — compact 1000-word on-device lookup table.
- `microbit_speech_api.py` — reusable on-device speech API.
- `bridge.py` — USB serial + host computer TTS bridge.
- `firmware/` — supplied HEX images, preserved unchanged.
- `integration/`, `docs/`, `examples/`, `.github/` — integration boundary, documentation, examples, CI validation.

## Generate and validate

```bash
python -m pip install -r requirements-generator.txt
python generate_project.py
python generate_project.py --output generated
python generate_project.py --validate
python generate_project.py --zip
```

The generator uses CMUdict pronunciations and TextBlob's English spelling frequency list to select 1000 common words. Re-running it may update the word selection if upstream dependency datasets change; pin dependency versions for a frozen release.

## Run the speech bridge

```bash
python -m pip install -r requirements.txt
python bridge.py --port COM3
```

Replace `COM3` with the micro:bit serial port shown by your operating system. Keep the bridge running and the USB connection attached. On Linux, a system TTS backend such as eSpeak may also be required.

## MakeCode

Import this repository as a MakeCode extension from its Git URL. For local development install Node.js and PXT CLI, then run `pxt target microbit`, `pxt install`, and `pxt serve`. Static validation does not claim that PXT compilation has been performed; compile in the official MakeCode toolchain before publishing a release.

## Pronunciation and limitations

Pronunciations use CMU-style ARPAbet with vowel stress digits `0`, `1`, and `2`. The 100-unit inventory includes 31 optional diphone/coarticulation records; canonical dictionary sequences use individual phonemes and stressed vowels. The bridge validates and displays dictionary pronunciations, but `pyttsx3` speaks through the host OS TTS voice, which may not use the CSV phonemes directly.

## Supplied firmware

The two uploaded `.hex` images are retained byte-for-byte in `firmware/`. They are firmware binaries, not source code. Their precise target hardware and control protocol are not established by filename alone. Do not flash until device compatibility is confirmed. See `docs/FIRMWARE.md`.

## GitHub publishing

Create an empty GitHub repository, then from this folder run:

```bash
git init
git add .
git commit -m "Initial micro:bit English Speech Engine"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## License

MIT. The supplied firmware files are redistributed as user-provided originals; verify their own licensing/redistribution terms before public release.
