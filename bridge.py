"""USB serial companion bridge for the micro:bit English Speech Engine.

Install dependencies:
    python -m pip install pyserial pyttsx3

Run:
    python bridge.py --port COM3
On macOS/Linux, use the appropriate /dev/tty* device.

The bridge performs dictionary lookup on the computer and speaks using
the computer's installed TTS engine. It does not run speech synthesis on
the micro:bit itself.
"""
import argparse
import csv
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHONE_RE = re.compile(r"^[A-Z]+[012]?$")
VALID_PHONES = {
    "B","CH","D","DH","F","G","HH","JH","K","L","M","N","NG","P","R","S","SH",
    "T","TH","V","W","Y","Z","ZH",
    "AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"
}

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_data():
    sound_rows = read_csv(ROOT / "sound_units.csv")
    dictionary_rows = read_csv(ROOT / "pronunciation_dictionary.csv")
    custom_rows = read_csv(ROOT / "custom_pronunciations.csv")
    unit_symbols = {r["unit_id"]: r["phonetic_symbol"] for r in sound_rows}
    standard = {r["word"].lower(): r for r in dictionary_rows}
    custom = {r["word"].lower(): r for r in custom_rows}
    return unit_symbols, standard, custom

def validate_phones(phones, unit_symbols):
    tokens = phones.upper().split()
    if not tokens:
        raise ValueError("pronunciation cannot be empty")
    for token in tokens:
        base = token[:-1] if token[-1:] in ("0", "1", "2") else token
        if base not in VALID_PHONES or not PHONE_RE.match(token):
            raise ValueError("unsupported ARPAbet token: " + token)
    symbol_to_id = {v: k for k, v in unit_symbols.items()}
    ids = []
    for token in tokens:
        if token not in symbol_to_id:
            raise ValueError("sound unit not defined: " + token)
        ids.append(symbol_to_id[token])
    return tokens, ids

def speak(engine, text):
    engine.say(text)
    engine.runAndWait()

def main():
    parser = argparse.ArgumentParser(description="micro:bit English speech companion bridge")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM3")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    try:
        import serial
    except ImportError:
        print("Missing dependency: install pyserial")
        return 2
    try:
        import pyttsx3
        tts = pyttsx3.init()
    except Exception as exc:
        print("Could not initialise computer TTS:", exc)
        return 2

    unit_symbols, standard, custom = load_data()
    print("Loaded", len(standard), "standard words and", len(unit_symbols), "sound units.")
    print("Custom pronunciations override standard entries.")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except Exception as exc:
        print("Could not open serial port:", exc)
        return 2

    print("Connected. Press Ctrl+C to stop.")
    try:
        while True:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            parts = line.split("\t")
            if len(parts) < 3 or parts[0] != "MBSPEECH":
                continue
            command = parts[2]
            args_part = parts[3:]
            if command == "HELLO":
                print("micro:bit speech engine connected (protocol", parts[1] + ")")
            elif command in ("SPEAK", "LOOKUP", "EXISTS") and args_part:
                word = args_part[0].strip().lower()
                row = custom.get(word) or standard.get(word)
                if command == "EXISTS":
                    print(word, "FOUND" if row else "NOT FOUND")
                elif not row:
                    print("Word not found:", word)
                elif command == "LOOKUP":
                    print(word + ":", row["arpabet"], "| units:", row["unit_sequence"])
                else:
                    # Computer TTS speaks the word. The pronunciation mapping
                    # remains available for inspection and custom dictionary work.
                    speak(tts, word)
            elif command == "TEXT" and args_part:
                speak(tts, " ".join(args_part)[:1000])
            elif command == "CUSTOM" and len(args_part) >= 2:
                word = args_part[0].strip().lower()
                if not word or not word.isalpha():
                    print("Rejected custom word: use letters only")
                    continue
                phones, ids = validate_phones(args_part[1], unit_symbols)
                custom[word] = {"word": word, "arpabet": " ".join(phones), "unit_sequence": " ".join(ids)}
                path = ROOT / "custom_pronunciations.csv"
                with path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["word","arpabet","unit_sequence"])
                    writer.writeheader()
                    writer.writerows(custom.values())
                print("Saved custom pronunciation:", word)
            elif command == "REMOVE" and args_part:
                word = args_part[0].strip().lower()
                custom.pop(word, None)
                path = ROOT / "custom_pronunciations.csv"
                with path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["word","arpabet","unit_sequence"])
                    writer.writeheader()
                    writer.writerows(custom.values())
                print("Removed custom pronunciation:", word)
    except KeyboardInterrupt:
        print("\\nStopping bridge.")
    finally:
        ser.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
