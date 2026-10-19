/**
 * The "Known" furigana style: hide ruby over kanji the reader has met often, but only ruby
 * that is a plain hiragana reading of its base. The readings table is
 * `yurigana/kanji-readings.json` (on and kun readings of 常用 and 人名用 kanji, KANJIDIC2).
 */

/** Times every kanji of a base must have been met for its ruby to hide. */
export const knownKanjiMinCount = 10;

const kanjiPattern = /\p{Unified_Ideograph}/u;
const hiraganaOnly = /^[ぁ-ゖ]+$/;
const voiced = {
  か: 'が',
  き: 'ぎ',
  く: 'ぐ',
  け: 'げ',
  こ: 'ご',
  さ: 'ざ',
  し: 'じ',
  す: 'ず',
  せ: 'ぜ',
  そ: 'ぞ',
  た: 'だ',
  ち: 'ぢ',
  つ: 'づ',
  て: 'で',
  と: 'ど',
  は: 'ばぱ',
  ひ: 'びぴ',
  ふ: 'ぶぷ',
  へ: 'べぺ',
  ほ: 'ぼぽ'
};

function toHiragana(text) {
  return text.replace(/[ァ-ヶ]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0x60));
}

/** A kanji's reading as it can sound in a word: rendaku (ひと → びと) and っ (がく → がっ). */
function variants(reading) {
  const starts = [reading[0], ...(voiced[reading[0]] ?? '')];
  const result = [];

  for (const start of starts) {
    const word = start + reading.slice(1);
    result.push(word);
    if (word.length > 1 && 'つちくき'.includes(word[word.length - 1])) {
      result.push(`${word.slice(0, -1)}っ`);
    }
  }

  return result;
}

/**
 * Whether `reading` is spelled by the readings of the base's kanji and its kana. Gikun like
 * そら over 宇宙 and jukujikun like きょう over 今日 aren't, and neither are kanji outside the table.
 */
export function isPlainReading(base, reading, readings) {
  const match = (i, j) => {
    if (i === base.length) {
      return j === reading.length;
    }

    const char = base[i];
    if (!kanjiPattern.test(char) && char !== '々') {
      return reading[j] === toHiragana(char) && match(i + 1, j + 1);
    }

    const own = readings[char === '々' && i > 0 ? base[i - 1] : char];
    return (own?.split(' ') ?? [])
      .flatMap(variants)
      .some((form) => reading.startsWith(form, j) && match(i + 1, j + form.length));
  };

  return match(0, 0);
}

/**
 * Hide ruby only when its reading is plain hiragana that spells the base's usual reading and
 * every kanji of the base was met at least `minCount` times. Ruby that is katakana, contains
 * kanji or is any other reading is the author's choice and stays.
 */
export function hideKnownRuby(base, reading, kanjiTotals, readings, minCount = knownKanjiMinCount) {
  const kanji = [...base].filter((char) => kanjiPattern.test(char));

  return (
    kanji.length > 0 &&
    hiraganaOnly.test(reading) &&
    kanji.every((char) => (kanjiTotals[char] ?? 0) >= minCount) &&
    isPlainReading(base, reading, readings)
  );
}
