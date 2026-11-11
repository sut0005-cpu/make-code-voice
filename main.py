"""On-device micro:bit speech engine (MicroPython firmware).

This program uses MicroPython's built-in SAM-derived speech synthesizer.
Audio is generated on the micro:bit; no computer TTS bridge or network is used.

micro:bit V2: built-in speaker.
micro:bit V1: connect a small speaker/headphones between P0 and GND.
"""
from microbit import *
import speech
from onboard_dictionary import ONBOARD_DICTIONARY, WORD_COUNT

# Voice defaults can be changed here. SAM voice parameters range 0..255.
VOICE = {"pitch": 64, "speed": 72, "mouth": 128, "throat": 128}
CUSTOM = {}  # RAM-only custom SAM phoneme overrides for this session.
DEMO_WORDS = ("hello", "microbit", "computer", "language", "speech")

# CMU ARPAbet -> the phoneme symbols accepted by MicroPython speech.pronounce.
# The stress digits are translated to SAM stress levels (0=neutral, 1=normal, 2=secondary).
ARPABET_TO_SAM = {
    "B":"B", "CH":"CH", "D":"D", "DH":"DH", "F":"F", "G":"G",
    "HH":"/H", "JH":"J", "K":"K", "L":"L", "M":"M", "N":"N",
    "NG":"NX", "P":"P", "R":"R", "S":"S", "SH":"SH", "T":"T",
    "TH":"TH", "V":"V", "W":"W", "Y":"Y", "Z":"Z", "ZH":"ZH",
    "AA":"AA", "AE":"AE", "AH":"AH", "AO":"AO", "AW":"AW",
    "AY":"AY", "EH":"EH", "ER":"ER", "EY":"EY", "IH":"IH",
    "IY":"IY", "OW":"OW", "OY":"OY", "UH":"UH", "UW":"UX"
}
STRESS_TO_SAM = {"0":"6", "1":"4", "2":"5"}

def lookup(word):
    """Return the CMU ARPAbet entry for a word, or None."""
    target = word.strip().lower()
    if not target:
        return None
    # Scan without splitlines() so no 1000-item temporary list is allocated.
    start = 0
    data = ONBOARD_DICTIONARY
    while start < len(data):
        end = data.find("\n", start)
        if end < 0:
            end = len(data)
        line = data[start:end]
        key, sep, phones = line.partition("|")
        if sep and key == target:
            return phones
        start = end + 1
    return None

def arpabet_to_sam(arpabet):
    """Convert a CMU ARPAbet sequence into MicroPython SAM phoneme notation."""
    output = []
    for token in arpabet.split():
        stress = token[-1] if token[-1:] in ("0", "1", "2") else None
        base = token[:-1] if stress else token
        phoneme = ARPABET_TO_SAM.get(base)
        if phoneme is None:
            raise ValueError("Unsupported ARPAbet phoneme: " + token)
        output.append(phoneme + (STRESS_TO_SAM[stress] if stress else ""))
    return "".join(output)

def say_text(text):
    """Speak text directly through the micro:bit speech synthesizer."""
    text = str(text).strip()
    if not text:
        return
    # The SAM synthesizer accepts up to 255 characters per utterance.
    # Chunk on spaces to stay under that limit.
    words = text.split()
    chunk = ""
    for word in words:
        candidate = word if not chunk else chunk + " " + word
        if len(candidate) > 240:
            speech.say(chunk, **VOICE)
            chunk = word
        else:
            chunk = candidate
    if chunk:
        speech.say(chunk, **VOICE)

def say_word(word):
    """Speak one word on-device; custom entries use SAM phoneme notation."""
    word = str(word).strip().lower()
    if not word:
        return False
    custom = CUSTOM.get(word)
    if custom:
        speech.pronounce(custom, **VOICE)
        return True
    phones = lookup(word)
    if phones is None:
        # The built-in translator can still attempt words outside the 1000 list.
        say_text(word)
        return False
    # Use the 1000-word dictionary's phonemes for the actual on-device voice.
    speech.pronounce(arpabet_to_sam(phones), **VOICE)
    return True

def add_custom(word, sam_phonemes):
    """Add a custom SAM phoneme pronunciation for this running session."""
    word = str(word).strip().lower()
    phonemes = str(sam_phonemes).strip()
    if not word or not phonemes or len(phonemes) > 120:
        raise ValueError("Word and 1-120 SAM phoneme characters are required")
    CUSTOM[word] = phonemes

def show_word(word):
    display.scroll(word[:20])

def startup():
    display.show(Image.HAPPY)
    sleep(400)
    say_text("Hello. I am your micro bit speech engine.")
    display.show(Image.YES)

startup()
demo_index = 0
while True:
    if button_a.was_pressed():
        # Button A: speak a short greeting.
        say_text("Hello. Press B to hear a word.")
        display.show(Image.HAPPY)
    if button_b.was_pressed():
        # Button B: cycle through built-in dictionary examples.
        word = DEMO_WORDS[demo_index]
        show_word(word)
        say_word(word)
        demo_index = (demo_index + 1) % len(DEMO_WORDS)
    sleep(50)
