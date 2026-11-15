/**
 * On-device tonal English speech for MakeCode Python on micro:bit V2.
 *
 * Uses the bundled 1,000-word CMU-ARPAbet dictionary and the micro:bit
 * music tone API. This is a tonal/phoneme-coded voice, NOT a formant or
 * natural-language synthesizer: consonants are short tone cues and vowels
 * are pitched syllable centres. It is intended as an experimental audible
 * approximation. This version gives vowels a wider, distinct pitch identity while smoothing only the transitions.
 *
 * Python API (MakeCode Python):
 *   english_speech.speak_text("Hello there")
 *   english_speech.speak_word("robot")
 *   english_speech.lookup_pronunciation("robot")
 *   english_speech.dictionary_word_count()
 *   english_speech.set_rate(100)
 */
//% color=#2673A8 icon="\uf0a1" block="English Speech"
namespace englishSpeech {
    let rate = 100;
    let stopped = false;
    let lastPitch = 260;

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

    // ARPAbet vowels end in a stress digit (0, 1 or 2); consonants do not.
    // Only remove the final character when it is actually a stress marker.
    function phoneBase(phone: string): string {
        if (phone.length > 0) {
            const last = phone.charAt(phone.length - 1);
            if (last == "0" || last == "1" || last == "2") {
                return phone.substr(0, phone.length - 1);
            }
        }
        return phone;
    }

    function isVowel(phone: string): boolean {
        const p = phoneBase(phone);
        return p == "AA" || p == "AE" || p == "AH" || p == "AO" ||
            p == "AW" || p == "AY" || p == "EH" || p == "ER" ||
            p == "EY" || p == "IH" || p == "IY" || p == "OW" ||
            p == "OY" || p == "UH" || p == "UW";
    }

    // Vowels use a wider register so each vowel has a recognisably different tone.
    function vowelPitch(phone: string): number {
        const p = phoneBase(phone);
        if (p == "AA") return 245;
        if (p == "AE") return 300;
        if (p == "AH") return 220;
        if (p == "AO") return 205;
        if (p == "AW") return 335;
        if (p == "AY") return 365;
        if (p == "EH") return 280;
        if (p == "ER") return 255;
        if (p == "EY") return 385;
        if (p == "IH") return 315;
        if (p == "IY") return 405;
        if (p == "OW") return 270;
        if (p == "OY") return 350;
        if (p == "UH") return 230;
        if (p == "UW") return 375;
        return 252;
    }

    // Consonants use separate lower/mid tone families to distinguish articulation.
    function consonantPitch(phone: string): number {
        const p = phoneBase(phone);
        if (p == "P" || p == "B" || p == "M" || p == "N" || p == "NG") return 155;
        if (p == "T" || p == "D" || p == "K" || p == "G") return 185;
        if (p == "F" || p == "V" || p == "TH" || p == "DH") return 225;
        if (p == "S" || p == "Z" || p == "SH" || p == "ZH") return 295;
        if (p == "CH" || p == "JH") return 265;
        if (p == "L" || p == "R" || p == "W" || p == "Y") return 325;
        if (p == "HH") return 205;
        return 250;
    }

    // Smooth transitions without flattening the differences between phonemes.
    function smoothPitch(target: number): number {
        const maximumStep = 28;
        if (target > lastPitch + maximumStep) target = lastPitch + maximumStep;
        if (target < lastPitch - maximumStep) target = lastPitch - maximumStep;
        lastPitch = target;
        return target;
    }

    function playPhone(phone: string): void {
        if (stopped || phone.length == 0) return;

        if (isVowel(phone)) {
            const stress = phone.charAt(phone.length - 1);
            let pitch = vowelPitch(phone);
            let length = 100;

            // Stress is mainly expressed through duration, with only a
            // gentle pitch lift rather than a large jump.
            if (stress == "1") {
                pitch = Math.idiv(pitch * 108, 100);
                length = 165;
            } else if (stress == "2") {
                pitch = Math.idiv(pitch * 104, 100);
                length = 135;
            }

            pitch = smoothPitch(pitch);
            music.playTone(pitch, duration(length));

            // Tiny glide: enough to soften the note edge without sounding
            // like a separate musical note.
            music.playTone(pitch + 6, duration(35));
        } else {
            const pitch = smoothPitch(consonantPitch(phone));
            music.playTone(pitch, duration(24));
        }

        basic.pause(duration(6));
    }

    function spellUnknown(word: string): void {
        // Unknown words use a steady, neutral pulse instead of a rising
        // alphabet-by-alphabet chromatic scale.
        for (let i = 0; i < word.length; i++) {
            const c = word.charCodeAt(i);
            if (c >= 97 && c <= 122) {
                music.playTone(250, duration(55));
                basic.pause(duration(22));
            }
        }
    }

    function speakOneWord(word: string): void {
        const key = cleanWord(word);
        if (key.length == 0) return;
        lastPitch = 260;
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
