# MakeCode tonal speech engine (micro:bit V2)

This extension adds an experimental **on-device tonal speech mode** for Microsoft MakeCode Python. It reuses the bundled 1,000-entry CMU-ARPAbet pronunciation dictionary and plays a repeatable sequence of pitches through the micro:bit V2 speaker.

## Important sound limitation

This is not a human voice, SAM, formant synthesis, or a cloud TTS service. MakeCode's tone playback produces musical tones, not arbitrary speech waveforms. This extension maps vowel phonemes to pitched syllable centres and consonants to short tone cues. It is an audible pronunciation-coded approximation, but listeners should not expect ordinary English words to be clearly understood without learning its sound pattern. Unknown words are spelled with distinct letter pitches.

## Add it to MakeCode

1. Open the MakeCode project.
2. Choose **Extensions**.
3. Paste this repository URL: https://github.com/sut0005-cpu/make-code-voice
4. Add the **English Speech** extension.
5. Use the API below in MakeCode Python.

The robot micro:bit must be a **micro:bit V2** to use its built-in speaker. Enable the speaker in MakeCode if your project has disabled it.

## MakeCode Python API

```python
english_speech.speak_text("Hello there. I am your robot.")
english_speech.speak_word("robot")
english_speech.lookup_pronunciation("microbit")
english_speech.set_rate(100)  # 60 slow, 180 fast
english_speech.stop()
```

The dictionary count function returns 1000:

```python
basic.show_number(english_speech.dictionary_word_count())
```

## Using it with the Maqueen Plus V2

Keep this extension and the official DFRobot Maqueen Plus V2 extension in the same MakeCode project. They both run in MakeCode; the speech extension uses the micro:bit speaker while the DFRobot extension controls the Maqueen over I2C.

For a received radio message, call:

```python
def on_received_string(received):
    english_speech.speak_text(received)

radio.set_group(42)
radio.on_received_string(on_received_string)
```

This file documents the experimental tonal implementation. Test volume, timing, and performance on the actual robot before relying on it.
