/** Kanji -> its readings in hiragana, space-separated (`yurigana/kanji-readings.json`). */
export type KanjiReadings = Record<string, string>;

/** Times every kanji of a base must have been met for its ruby to hide. */
export declare const knownKanjiMinCount: number;

/** Whether `reading` is spelled by the readings of the base's kanji and its kana. */
export declare function isPlainReading(base: string, reading: string, readings: KanjiReadings): boolean;

/** Whether ruby `reading` over `base` can hide: plain hiragana, every kanji met `minCount` times. */
export declare function hideKnownRuby(
  base: string,
  reading: string,
  kanjiTotals: Record<string, number>,
  readings: KanjiReadings,
  minCount?: number
): boolean;
