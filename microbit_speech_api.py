"""Reusable on-device speech API for micro:bit MicroPython projects."""
import speech
from onboard_dictionary import ONBOARD_DICTIONARY, WORD_COUNT

DEFAULT_VOICE = {"pitch": 64, "speed": 72, "mouth": 128, "throat": 128}
_custom = {}
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
    word = str(word).strip().lower()
    start = 0
    data = ONBOARD_DICTIONARY
    while start < len(data):
        end = data.find("\n", start)
        if end < 0:
            end = len(data)
        key, sep, phones = data[start:end].partition("|")
        if sep and key == word:
            return phones
        start = end + 1
    return None

def arpabet_to_sam(arpabet):
    output = []
    for token in arpabet.split():
        stress = token[-1] if token[-1:] in ("0", "1", "2") else None
        base = token[:-1] if stress else token
        phoneme = ARPABET_TO_SAM.get(base)
        if phoneme is None:
            raise ValueError("Unsupported ARPAbet phoneme: " + token)
        output.append(phoneme + (STRESS_TO_SAM[stress] if stress else ""))
    return "".join(output)

def say(text, **voice):
    settings = DEFAULT_VOICE.copy()
    settings.update(voice)
    speech.say(str(text)[:255], **settings)

def speak_word(word, **voice):
    word = str(word).strip().lower()
    settings = DEFAULT_VOICE.copy()
    settings.update(voice)
    custom = _custom.get(word)
    if custom:
        speech.pronounce(custom, **settings)
    else:
        speech.say(word, **settings)
    return lookup(word) is not None

def speak_phonemes(sam_phonemes, **voice):
    settings = DEFAULT_VOICE.copy()
    settings.update(voice)
    speech.pronounce(str(sam_phonemes), **settings)

def set_custom_pronunciation(word, sam_phonemes):
    word = str(word).strip().lower()
    sam_phonemes = str(sam_phonemes).strip()
    if not word or not sam_phonemes:
        raise ValueError("word and SAM phonemes cannot be empty")
    _custom[word] = sam_phonemes

def dictionary_count():
    return WORD_COUNT
