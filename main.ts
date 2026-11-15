/**
 * On-device tonal English speech for MakeCode Python on micro:bit V2.
 *
 * Uses the bundled 1,000-word CMU-ARPAbet dictionary and the micro:bit
 * music tone API. This is a tonal/phoneme-coded voice, NOT a formant or
 * natural-language synthesizer: consonants are short tone cues and vowels
 * are pitched syllable centres. It is intended as an experimental audible
 * approximation. This version uses changing vowel contours, stress timing and different consonant rhythms to make the tone-coded output less like isolated beeps.
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

    // Tone-only MakeCode cannot create real vocal noise or simultaneous formants.
    // These short pitch contours and consonant rhythms make phonemes less like
    // isolated equal-length beeps and give syllables a more speech-like shape.
    function vowelEndPitch(phone: string, startPitch: number): number {
        const p = phoneBase(phone);
        if (p == "AW") return 260;
        if (p == "AY") return 405;
        if (p == "EY") return 330;
        if (p == "OW") return 375;
        if (p == "OY") return 300;
        if (p == "IY") return 385;
        if (p == "UW") return 340;
        if (p == "ER") return 235;
        return startPitch + 12;
    }

    function consonantPitch(phone: string): number {
        const p = phoneBase(phone);
        if (p == "P" || p == "B") return 175;
        if (p == "T" || p == "D") return 205;
        if (p == "K" || p == "G") return 235;
        if (p == "M" || p == "N" || p == "NG") return 220;
        if (p == "F" || p == "V") return 285;
        if (p == "TH" || p == "DH") return 310;
        if (p == "S" || p == "Z") return 365;
        if (p == "SH" || p == "ZH") return 330;
        if (p == "CH" || p == "JH") return 345;
        if (p == "L" || p == "R") return 265;
        if (p == "W" || p == "Y") return 300;
        if (p == "HH") return 250;
        return 250;
    }

    function smoothPitch(target: number): number {
        const maximumStep = 55;
        if (target > lastPitch + maximumStep) target = lastPitch + maximumStep;
        if (target < lastPitch - maximumStep) target = lastPitch - maximumStep;
        lastPitch = target;
        return target;
    }

    function playVowel(phone: string): void {
        const stress = phone.charAt(phone.length - 1);
        let startPitch = vowelPitch(phone);
        let length = 115;
        if (stress == "1") {
            startPitch = Math.idiv(startPitch * 110, 100);
            length = 185;
        } else if (stress == "2") {
            startPitch = Math.idiv(startPitch * 105, 100);
            length = 145;
        }

        const first = smoothPitch(startPitch);
        const finish = smoothPitch(vowelEndPitch(phone, startPitch));
        // A two-part vowel contour gives diphthongs a changing sound instead
        // of holding one pitch like a notification beep.
        music.playTone(first, duration(Math.idiv(length * 65, 100)));
        music.playTone(finish, duration(Math.idiv(length * 35, 100)));
    }

    function playConsonant(phone: string): void {
        const p = phoneBase(phone);
        const pitch = smoothPitch(consonantPitch(phone));

        // Stops have a tiny closure followed by a sharper release.
        if (p == "P" || p == "T" || p == "K" || p == "B" || p == "D" || p == "G") {
            basic.pause(duration(12));
            music.playTone(pitch + 35, duration(18));
        // Fricatives use two short pulses to suggest continuous airflow.
        } else if (p == "F" || p == "V" || p == "TH" || p == "DH" ||
                   p == "S" || p == "Z" || p == "SH" || p == "ZH" ||
                   p == "CH" || p == "JH" || p == "HH") {
            music.playTone(pitch, duration(20));
            music.playTone(pitch + 22, duration(24));
        // Nasals and liquids are longer and connect into the following vowel.
        } else {
            music.playTone(pitch, duration(48));
        }
    }

    function playPhone(phone: string): void {
        if (stopped || phone.length == 0) return;
        if (isVowel(phone)) playVowel(phone);
        else playConsonant(phone);
        basic.pause(duration(4));
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
