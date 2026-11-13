/**
 * On-device tonal English speech for MakeCode Python on micro:bit V2.
 *
 * Uses the bundled 1,000-word CMU-ARPAbet dictionary and the micro:bit
 * music tone API. This is a tonal/phoneme-coded voice, NOT a formant or
 * natural-language synthesizer: consonants are short tone cues and vowels
 * are pitched syllable centres. It is intended as an experimental audible
 * approximation. A listener will not hear ordinary human speech.
 *
 * Python API (MakeCode Python):
 *   english_speech.speak_text("Hello there")
 *   english_speech.speak_word("robot")
 *   english_speech.lookup_pronunciation("robot")
 *   english_speech.dictionary_word_count()
 *   english_speech.set_rate(100)
 */
namespace englishSpeech {
    let rate = 100;
    let stopped = false;

    function cleanWord(word: string): string {
        let result = "";
        for (let i = 0; i < word.length; i++) {
            const c = word.charAt(i).toLowerCase();
            if ((c >= "a" && c <= "z") || (c >= "0" && c <= "9") || c == "'") {
                result += c;
            }
        }
        return result;
    }

    function pronunciation(word: string): string {
        const key = cleanWord(word);
        if (key.length == 0) return "";
        const data = EnglishSpeechDictionary.DATA;
        let contentStart = -1;
        if (data.substr(0, key.length + 1) == key + "|") {
            contentStart = key.length + 1;
        } else {
            const marker = "\n" + key + "|";
            const found = data.indexOf(marker);
            if (found >= 0) contentStart = found + marker.length;
        }
        if (contentStart < 0) return "";
        let end = data.indexOf("\n", contentStart);
        if (end < 0) end = data.length;
        return data.substr(contentStart, end - contentStart);
    }

    function duration(base: number): number {
        return Math.max(20, Math.idiv(base * 100, rate));
    }

    function isVowel(phone: string): boolean {
        const p = phone.substr(0, phone.length - 1);
        return p == "AA" || p == "AE" || p == "AH" || p == "AO" ||
            p == "AW" || p == "AY" || p == "EH" || p == "ER" ||
            p == "EY" || p == "IH" || p == "IY" || p == "OW" ||
            p == "OY" || p == "UH" || p == "UW";
    }

    function vowelPitch(phone: string): number {
        const p = phone.substr(0, phone.length - 1);
        if (p == "AA") return 440;
        if (p == "AE") return 520;
        if (p == "AH") return 390;
        if (p == "AO") return 350;
        if (p == "AW") return 560;
        if (p == "AY") return 610;
        if (p == "EH") return 490;
        if (p == "ER") return 300;
        if (p == "EY") return 650;
        if (p == "IH") return 540;
        if (p == "IY") return 740;
        if (p == "OW") return 420;
        if (p == "OY") return 580;
        if (p == "UH") return 330;
        if (p == "UW") return 690;
        return 440;
    }

    function consonantPitch(phone: string): number {
        const p = phone.substr(0, phone.length - 1);
        if (p == "P" || p == "B") return 205;
        if (p == "T" || p == "D") return 245;
        if (p == "K" || p == "G") return 285;
        if (p == "F" || p == "V") return 1250;
        if (p == "TH" || p == "DH") return 1050;
        if (p == "S" || p == "Z") return 1550;
        if (p == "SH" || p == "ZH") return 1750;
        if (p == "CH" || p == "JH") return 1450;
        if (p == "M" || p == "N" || p == "NG") return 225;
        if (p == "L" || p == "R" || p == "W" || p == "Y") return 320;
        if (p == "HH") return 900;
        return 400;
    }

    function playPhone(phone: string): void {
        if (stopped) return;
        if (phone.length == 0) return;
        if (isVowel(phone)) {
            const stress = phone.charAt(phone.length - 1);
            let pitch = vowelPitch(phone);
            let length = 105;
            if (stress == "1") {
                pitch = Math.idiv(pitch * 11, 10);
                length = 175;
            } else if (stress == "2") {
                pitch = Math.idiv(pitch * 106, 100);
                length = 145;
            }
            music.playTone(pitch, duration(length));
            // A small glide makes the vowel centre less like a plain beep.
            music.playTone(Math.idiv(pitch * 103, 100), duration(45));
        } else {
            // Brief consonant markers give the syllables a repeatable rhythm.
            music.playTone(consonantPitch(phone), duration(32));
        }
        basic.pause(duration(12));
    }

    function spellUnknown(word: string): void {
        // Predictable fallback: one short pitch per letter, not a fake claim
        // that an unknown word has been correctly pronounced.
        for (let i = 0; i < word.length; i++) {
            const c = word.charCodeAt(i);
            if (c >= 97 && c <= 122) {
                music.playTone(300 + (c - 97) * 24, duration(65));
                basic.pause(duration(25));
            }
        }
    }

    function speakOneWord(word: string): void {
        const key = cleanWord(word);
        if (key.length == 0) return;
        const phones = pronunciation(key);
        if (phones.length == 0) {
            spellUnknown(key);
            return;
        }
        const parts = phones.split(" ");
        for (let i = 0; i < parts.length; i++) {
            playPhone(parts[i]);
        }
    }

    /**
     * Speak one dictionary word through the micro:bit V2 speaker.
     */
    //% block="speak word %word"
    //% weight=100
    export function speakWord(word: string): void {
        stopped = false;
        speakOneWord(word);
    }

    /**
     * Speak a sentence. Spaces and punctuation create natural pauses.
     */
    //% block="speak text %text"
    //% weight=95
    export function speakText(text: string): void {
        stopped = false;
        let word = "";
        for (let i = 0; i < text.length; i++) {
            const c = text.charAt(i);
            const lower = c.toLowerCase();
            if ((lower >= "a" && lower <= "z") || (c >= "0" && c <= "9") || c == "'") {
                word += lower;
            } else {
                if (word.length > 0) {
                    speakOneWord(word);
                    word = "";
                    basic.pause(duration(55));
                }
                if (c == "." || c == "!" || c == "?") basic.pause(duration(260));
                else if (c == "," || c == ";" || c == ":") basic.pause(duration(150));
            }
        }
        if (word.length > 0) speakOneWord(word);
    }

    /**
     * Look up and play the pronunciation of a word.
     */
    //% block="play pronunciation of %word"
    //% weight=80
    export function lookupPronunciation(word: string): void {
        speakWord(word);
    }

    /**
     * Set playback rate: 60 (slow) to 180 (fast). Default is 100.
     */
    //% block="set speech rate to %value"
    //% value.min=60 value.max=180
    //% weight=70
    export function setRate(value: number): void {
        rate = Math.constrain(value, 60, 180);
    }

    /**
     * Stop the current tone sequence.
     */
    //% block="stop tonal speech"
    //% weight=60
    export function stop(): void {
        stopped = true;
        music.stopAllSounds();
    }

    /**
     * Number of entries in the bundled pronunciation dictionary.
     */
    //% block="speech dictionary word count"
    //% weight=50
    export function dictionaryWordCount(): number {
        return EnglishSpeechDictionary.WORD_COUNT;
    }
}
