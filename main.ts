/**
 * English Speech Engine for micro:bit (host-backed edition).
 *
 * The micro:bit sends commands over its USB serial connection.
 * A companion computer runs bridge.py, which looks up the pronunciation
 * and speaks through the computer's audio output using its installed TTS.
 * This design avoids placing a 1000-word dictionary in constrained
 * micro:bit RAM and does not pretend the micro:bit has a built-in speaker.
 */
namespace englishSpeech {
    let connected = false;

    function cleanField(value: string): string {
        // The serial protocol is tab-delimited; reject line breaks/tabs.
        return value.replace(/\t/g, " ").replace(/\r/g, " ").replace(/\n/g, " ");
    }

    function sendCommand(command: string): void {
        serial.writeLine("MBSPEECH\t" + EnglishSpeechDictionary.PROTOCOL_VERSION + "\t" + command);
    }

    /**
     * Initialise the serial speech connection.
     */
    //% block="initialise English speech engine"
    //% weight=100
    export function initialise(): void {
        connected = true;
        sendCommand("HELLO");
    }

    /**
     * Ask the companion computer to speak a dictionary word.
     */
    //% block="speak word %word"
    //% weight=90
    export function speakWord(word: string): void {
        if (!connected) initialise();
        sendCommand("SPEAK\t" + cleanField(word));
    }

    /**
     * Speak a sentence using the companion computer's TTS engine.
     * This is host TTS, not on-device phoneme synthesis.
     */
    //% block="speak text %text"
    //% weight=80
    export function speakText(text: string): void {
        if (!connected) initialise();
        sendCommand("TEXT\t" + cleanField(text));
    }

    /**
     * Request the ARPAbet and sound-unit sequence for a word.
     * The companion bridge prints the result to its console.
     */
    //% block="look up pronunciation of %word"
    //% weight=70
    export function lookupPronunciation(word: string): void {
        if (!connected) initialise();
        sendCommand("LOOKUP\t" + cleanField(word));
    }

    /**
     * Add or replace a custom pronunciation.
     * Example phones: "M AY1 K R OW2 B IH2 T".
     */
    //% block="add custom pronunciation word %word phones %phones"
    //% weight=60
    export function addCustomPronunciation(word: string, phones: string): void {
        if (!connected) initialise();
        sendCommand("CUSTOM\t" + cleanField(word) + "\t" + cleanField(phones));
    }

    /**
     * Remove a custom pronunciation for a word.
     */
    //% block="remove custom pronunciation for %word"
    //% weight=50
    export function removeCustomPronunciation(word: string): void {
        if (!connected) initialise();
        sendCommand("REMOVE\t" + cleanField(word));
    }

    /**
     * Ask the bridge whether a word exists in either dictionary.
     */
    //% block="check dictionary for %word"
    //% weight=40
    export function checkWord(word: string): void {
        if (!connected) initialise();
        sendCommand("EXISTS\t" + cleanField(word));
    }

    /**
     * Report the number of standard words in the bundled dictionary.
     */
    //% block="dictionary word count"
    //% weight=30
    export function dictionaryWordCount(): number {
        return EnglishSpeechDictionary.WORD_COUNT;
    }

    /**
     * Report the number of defined sound units.
     */
    //% block="sound unit count"
    //% weight=20
    export function soundUnitCount(): number {
        return EnglishSpeechDictionary.SOUND_UNIT_COUNT;
    }
}
