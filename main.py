"""On-device micro:bit speech engine (MicroPython firmware).

On a micro:bit V2, speech is generated locally by the built-in SAM speech
synthesizer and played through the built-in speaker. No PC, USB TTS bridge,
network connection, or speech extension is required.

Radio compatibility:
- Receives MakeCode radio.sendString packets on group 42.
- Expects the controller's text packet format: ~<id><part><total><text>.
- The controller should send chunks of up to 8 text characters. Each complete
  packet must remain below MakeCode's 19-character sendString limit.

IMPORTANT: This MicroPython firmware replaces the MakeCode runtime. The
Maqueen Plus V2 MakeCode motor extension cannot run at the same time as this
MicroPython program. Maqueen motor control must be ported to MicroPython
separately if you want movement and speech from the same robot board.
"""
from microbit import *
import radio
import speech
from onboard_dictionary import ONBOARD_DICTIONARY, WORD_COUNT

VOICE = {"pitch": 64, "speed": 72, "mouth": 128, "throat": 128}
CUSTOM = {}
DEMO_WORDS = ("hello", "microbit", "computer", "language", "speech")

# MakeCode radio group used by the controller.
RADIO_GROUP = 42
MAX_MESSAGE = 32
MAX_PARTS = 4

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
    target = str(word).strip().lower()
    if not target:
        return None
    start = 0
    data = ONBOARD_DICTIONARY
    while start < len(data):
        end = data.find("\n", start)
        if end < 0:
            end = len(data)
        key, sep, phones = data[start:end].partition("|")
        if sep and key == target:
            return phones
        start = end + 1
    return None

def arpabet_to_sam(arpabet):
    """Convert CMU ARPAbet into MicroPython SAM phoneme notation."""
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
    """Speak text through the micro:bit speaker."""
    text = str(text).strip()
    if not text:
        return
    words = text.split()
    chunk = ""
    for word in words:
        candidate = word if not chunk else chunk + " " + word
        if len(candidate) > 240:
            if chunk:
                speech.say(chunk, **VOICE)
            chunk = word
        else:
            chunk = candidate
    if chunk:
        speech.say(chunk, **VOICE)

def say_word(word):
    """Speak a dictionary word using its bundled pronunciation when available."""
    word = str(word).strip().lower()
    if not word:
        return False
    custom = CUSTOM.get(word)
    if custom:
        speech.pronounce(custom, **VOICE)
        return True
    phones = lookup(word)
    if phones is None:
        say_text(word)
        return False
    speech.pronounce(arpabet_to_sam(phones), **VOICE)
    return True

def add_custom(word, sam_phonemes):
    """Add a RAM-only custom SAM pronunciation for this session."""
    word = str(word).strip().lower()
    phonemes = str(sam_phonemes).strip()
    if not word or not phonemes or len(phonemes) > 120:
        raise ValueError("Word and 1-120 SAM phoneme characters are required")
    CUSTOM[word] = phonemes

def show_word(word):
    display.scroll(str(word)[:20])

# Message assembly state for the controller's ~<id><part><total><chunk> format.
current_message_id = None
current_total = 0
received_parts = []

def reset_message(message_id, total):
    global current_message_id, current_total, received_parts
    current_message_id = message_id
    current_total = total
    received_parts = [None] * total

def handle_controller_text(packet_text):
    """Reassemble a text packet after its MakeCode radio header is removed."""
    global current_message_id, current_total, received_parts

    if not packet_text or packet_text[0] != "~":
        return
    if len(packet_text) < 5:
        return

    message_id = packet_text[1]
    part_char = packet_text[2]
    total_char = packet_text[3]
    if not part_char.isdigit() or not total_char.isdigit():
        return

    part_index = int(part_char)
    total = int(total_char)
    if total < 1 or total > MAX_PARTS or part_index < 0 or part_index >= total:
        return

    if message_id != current_message_id or total != current_total:
        reset_message(message_id, total)

    received_parts[part_index] = packet_text[4:]
    for part in received_parts:
        if part is None:
            return

    message = "".join(received_parts)[:MAX_MESSAGE]
    current_message_id = None
    current_total = 0
    received_parts = []
    if message:
        display.show(Image.HAPPY)
        say_text(message)
        display.show(Image.YES)

def receive_makecode_radio():
    """Read one raw MakeCode radio packet and extract its string payload.

    MakeCode radio packets have a 12-byte header. Byte 3 is packet type 2
    (string), byte 12 is the text length, and text begins at byte 13.
    """
    try:
        raw = radio.receive_bytes()
        if raw is None or len(raw) < 13:
            return
        if raw[3] != 2:
            return
        text_length = raw[12]
        if text_length < 1 or text_length > 19 or len(raw) < 13 + text_length:
            return
        payload = raw[13:13 + text_length].decode("utf-8")
        handle_controller_text(payload)
    except (ValueError, UnicodeError, IndexError):
        # Ignore malformed or unrelated radio packets rather than stopping.
        return

def startup():
    display.show(Image.HAPPY)
    sleep(300)
    say_text("Hello. I am your micro bit speech engine.")
    display.show(Image.YES)

# Enable radio reception using the same group as the MakeCode controller.
radio.config(group=RADIO_GROUP, length=32, queue=10)
radio.on()
startup()

demo_index = 0
while True:
    receive_makecode_radio()

    if button_a.was_pressed():
        say_text("Hello. Send me a message and I will speak it.")
        display.show(Image.HAPPY)

    if button_b.was_pressed():
        word = DEMO_WORDS[demo_index]
        show_word(word)
        say_word(word)
        demo_index = (demo_index + 1) % len(DEMO_WORDS)

    sleep(20)
