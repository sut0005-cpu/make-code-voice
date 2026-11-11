#!/usr/bin/env python3
"""Validate the micro:bit English Speech Engine project data and structure."""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "pxt.json", "main.ts", "dictionary.ts", "README.md", "sound_units.csv",
    "pronunciation_dictionary.csv", "custom_pronunciations.csv", "bridge.py",
    "main.py", "onboard_dictionary.py", "microbit_speech_api.py", "docs/ON_DEVICE_SPEECH.md",
    "examples/basic_speech.ts", "examples/custom_pronunciation.ts",
    "examples/word_lookup.ts", "generate_project.py", "requirements.txt",
    "requirements-generator.txt", "docs/PROTOCOL.md", "firmware/microbit-controller.hex",
    "firmware/microbit-robo.hex", "tests/test_bridge.py"
]
CONSONANTS = {"B","CH","D","DH","F","G","HH","JH","K","L","M","N","NG","P","R","S","SH","T","TH","V","W","Y","Z","ZH"}
VOWELS = {"AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"}
VALID = CONSONANTS | VOWELS
TOKEN_RE = re.compile(r"^[A-Z]+[012]?$")
errors = []

def rows(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def check_pron(row, symbol_to_id, label):
    phones = row.get("arpabet", "").split()
    ids = row.get("unit_sequence", "").split()
    if not phones:
        errors.append(f"{label}: empty ARPAbet pronunciation")
    if len(phones) != len(ids):
        errors.append(f"{label}: phone/unit sequence lengths differ")
    for p in phones:
        base = p[:-1] if p[-1:] in "012" else p
        if not TOKEN_RE.match(p) or base not in VALID:
            errors.append(f"{label}: invalid ARPAbet token {p}")
        elif p not in symbol_to_id:
            errors.append(f"{label}: no sound unit defined for {p}")
    for unit_id in ids:
        if unit_id not in set(symbol_to_id.values()):
            errors.append(f"{label}: unknown sound-unit ID {unit_id}")

for filename in REQUIRED:
    if not (ROOT / filename).is_file():
        errors.append(f"Missing required file: {filename}")

if errors:
    print("\\n".join("ERROR: " + e for e in errors))
    sys.exit(1)

sound = rows("sound_units.csv")
dictionary = rows("pronunciation_dictionary.csv")
custom = rows("custom_pronunciations.csv")

if len(sound) != 100:
    errors.append(f"Expected exactly 100 sound units; found {len(sound)}")
ids = [r["unit_id"] for r in sound]
symbols = [r["phonetic_symbol"] for r in sound]
if len(ids) != len(set(ids)):
    errors.append("Duplicate sound-unit IDs")
if len(symbols) != len(set(symbols)):
    errors.append("Duplicate sound-unit symbols")
if any(not r["unit_id"] or not r["phonetic_symbol"] or not r["description"] for r in sound):
    errors.append("One or more sound-unit rows have missing required fields")

symbol_to_id = {r["phonetic_symbol"]: r["unit_id"] for r in sound}
if len(dictionary) != 1000:
    errors.append(f"Expected exactly 1000 dictionary entries; found {len(dictionary)}")
words = [r["word"].strip().lower() for r in dictionary]
if len(words) != len(set(words)):
    errors.append("Duplicate dictionary words (case-insensitive)")
for row in dictionary:
    if not row["word"].strip().isalpha():
        errors.append(f"Invalid dictionary word: {row['word']!r}")
    check_pron(row, symbol_to_id, row["word"])

custom_words = [r["word"].strip().lower() for r in custom]
if len(custom_words) != len(set(custom_words)):
    errors.append("Duplicate custom pronunciation words")
for row in custom:
    if not row["word"].strip():
        errors.append("Custom pronunciation has empty word")
    check_pron(row, symbol_to_id, "custom:" + row["word"])

# Verify that TypeScript exposes the expected blocks and only relies on
# documented MakeCode serial output API in this extension.
ts = (ROOT / "main.ts").read_text(encoding="utf-8")
for marker in ["serial.writeLine", "speakWord", "speakText", "lookupPronunciation",
               "addCustomPronunciation", "removeCustomPronunciation", "checkWord"]:
    if marker not in ts:
        errors.append("Missing TypeScript API/function marker: " + marker)
if "serial.writeLine" not in ts:
    errors.append("Unsupported/missing serial output implementation")

# Check the primary on-device MicroPython speech implementation.
for filename, marker_text in [("main.py", "import speech"), ("microbit_speech_api.py", "speech.pronounce"), ("onboard_dictionary.py", "WORD_COUNT = 1000")]:
    path = ROOT / filename
    if not path.exists() or marker_text not in path.read_text(encoding="utf-8"):
        errors.append("Missing on-device speech implementation marker: " + filename)

if errors:
    print("\\n".join("ERROR: " + e for e in errors))
    sys.exit(1)

print("PASS: required files present")
print("PASS: 100 unique sound units")
print("PASS: 1000 unique dictionary words with valid sound-unit mappings")
print(f"PASS: {len(custom)} valid custom pronunciation examples")
print("PASS: TypeScript source contains required extension functions")
print("NOTE: This is data/static validation, not a PXT compilation test.")
