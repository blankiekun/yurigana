# yurigana

Readings of Japanese kanji words in context. Given a text, and the ruby (furigana) the
book prints if it has any, yurigana says how each kanji word is read there: 人気 as にんき
in この店は人気だ and as ひとけ in 人気のない道. It also decides which of a book's ruby a reader
no longer needs (the JS package).

It was written for [chimimouryou](https://github.com/blankiekun/chimimouryou), a
self-hosted reader for Japanese books, where it gives the difficulty service's word lists
their readings and the reader its "Known" furigana style.

## Python

```sh
pip install "yurigana @ https://github.com/blankiekun/yurigana/archive/refs/tags/v0.1.1.tar.gz"
```

That installs SudachiPy and SudachiDict-full too (the dictionary at the version the numbers below were measured with). Then:

```python
from yurigana import Reader, aozora_text

reader = Reader()
hints = []  # the book's ruby: (start, end, reading) offsets in the plain text
text = aozora_text('夜の公園は人気がなく、静かだった。\n｜宇宙《そら》を見上げ、学校へ行《い》った。', None, hints)
for word in reader.read(text, hints):
    print(word)
# Word(start=0, end=1, form='夜', reading='よる', source='dictionary', certainty=None)
# Word(start=2, end=4, form='公園', reading='こうえん', source='dictionary', certainty=None)
# Word(start=5, end=7, form='人気', reading='ひとけ', source='rule', certainty=1.0)
# Word(start=11, end=13, form='静か', reading='しずか', source='dictionary', certainty=None)
# Word(start=18, end=20, form='宇宙', reading='うちゅう', source='dictionary', certainty=None)
# Word(start=21, end=24, form='見上げる', reading=None, source='dictionary', certainty=None)
# Word(start=25, end=27, form='学校', reading='がっこう', source='dictionary', certainty=None)
# Word(start=28, end=30, form='行く', reading='いく', source='ruby', certainty=1.0)
```

そら over 宇宙 is flavour ruby, so 宇宙 keeps its dictionary reading. With a reading list,
`Reader(known='jiten_freq_global.zip')`, 見上げる gets みあげる (`source='only'`: the list
gives it one reading).

`read` gives one `Word` (a named tuple, easy to serialise) per token whose surface has
kanji, or per compound (below): its character offsets in `text`, its dictionary form (行った: 行く), the reading of
that form in hiragana, where the reading came from and how certain it is. `reading` is
None when nothing gives one (without a reading list: a conjugated word without ruby, rule or
model; with one: a conjugated word none or several of whose listed readings fit Sudachi's
reading of it). `readings.surface_reading(surface, form, reading, after)` turns it into the
reading of the surface, for furigana: 行っ, 行く, いく → いっ; 来 before た is き, before ない こ.

`book_text(path, 'EPUB' | 'HTMLZ' | 'TXT', None, hints)` gives a book's plain text, one
paragraph per line, without tables of contents or colophons, and its ruby as hints.

Options, all optional:

- `Reader(known=...)`: the (form, reading) pairs a reading must be one of: a set, a dict
  keyed by them, or the path of a rank-based Yomitan frequency list with readings (e.g.
  [Jiten's](https://jiten.moe/frequency-dictionaries), `jiten_freq_global.zip`, not
  included). With one, readings outside the list are never given, and forms the list gives
  a single reading get `source='only'`. Without one, ruby must be spelled by its kanji's
  readings (`kanji-readings.json`) and the rules and the model are trusted.
- `Reader(tables=[path])`: reading-model tables built from your own library (below), tried
  before the public one. A missing file is skipped, so you can always pass the path.
- `Reader(tokenizer=...)`: anything with `tokens(text)` yielding `yurigana.tokens.Token`s;
  the default is SudachiDict-full in split mode C.

### The order of readings

With a reading list, 2-4 adjacent tokens whose joined form the list gives one reading
become one `Word` with that reading (`source='only'`): 三|日|月 みかづき, 身の上|話
みのうえばなし, 一|石|二鳥 いっせきにちょう, 昼|時 ひるどき. Spans with particles or ending in
kana are left out (Jiten's list has phrases such as 彼の かの), as are a number with its
counter (一|枚), spans right after a number (１|日|中) and spans with ruby. Otherwise each
token is read on its own; the first step that gives a reading wins:

1. **The book's ruby** (`ruby_reading`): ruby over the token, as one span or kanji by kanji
   (人《ひと》気《け》 gives ひとけ); ruby over the kanji stem of an inflected word, with the
   lemma's okurigana added (行《い》った is 行く read いく); ruby set in large kana, as older
   books do (いつしよ gives いっしょ).
2. **A context rule** (`context_reading`): about 40 forms whose reading depends on the
   words around them (人気, 今日, 明日, 上手, 市場, 金, 方, 間, 気に入る いる, カナダ人 じん …), in
   `readings._CONTEXT_RULES`.
   人気がない is にんき as often as ひとけ, so it is ひとけ only with a cue (人気がない場所,
   周囲に人気がない); この店は人気がない stays にんき.
3. **The reading model** (`ReadingModel`): a small naive Bayes classifier per form, over
   the two tokens on each side, their pairs and the content words within six tokens of the
   line. It answers only when its best reading's posterior is at least 0.7, and never for a
   form that has rules.
4. **Sudachi's reading** of the token, for an unconjugated word. For a conjugated one
   (行っ, 言わ, 早く), with a reading list: the one listed reading of its form that conjugates
   to Sudachi's reading of the surface (行っ read いっ is 行く いく, not ゆく; 来 read き or こ
   is くる), when exactly one does (`readings.conjugated_reading`, `source='dictionary'`).
   A few of Sudachi's readings that are almost always wrong in modern text are replaced
   (`readings.DEFAULT_READINGS`, `source='default'`): 私 わたくし → わたし, 言う ゆう → いう,
   富士山 ふじやま → ふじさん, 鶏肉, 今日 こんにち, 明後日. They were chosen on Tatoeba's half a:
   each fixes 10+ occurrences there and is right 90%+ of the times it changes a reading.
   日本 にっぽん → にほん is the exception: Tatoeba's machine gold keeps にっぽん often enough
   to miss that bar, but the human ruby of the NDL test set almost never uses it.
   鼻血, 間近, 手近 and 近々 get ぢ, the spelling of their rendaku (Sudachi writes じ).

### Numbers and counters

Sudachi gives a number and its counter as separate tokens with fixed readings (三/さん +
本/ぽん), so `read` also gives one `Word` per number + counter span with the reading of the
whole, `source='counter'` and certainty None: `Word(start, end, '三本', 'さんぼん', 'counter', None)`.
It comes just before the tokens' own Words, which stay: the counter's Word gets the
counter's plain reading (本 ほん) for word lists, with `source='counter'` too (never `only`:
the plain reading is not how it reads there). Ruby over any part of the span wins: no
span Word then. Words Sudachi keeps whole (一人, 二十歳, 十分 じゅうぶん, 何本, 一日 ついたち
after a month) are its own. A number alone gets the same readings (六百 ろっぴゃく, 三千
さんぜん; Sudachi reads them digit by digit), as `source='counter'`.

The readings follow standard counter grammar (`yurigana/counters.py`, as in Wiktionary's
[Japanese counters appendix](https://en.wiktionary.org/wiki/Appendix:Japanese_counters)):
numbers in kanji (三十五, 一九九九), digits (35, ３５) and 何, 幾, 何十/百/千/万, with

| | readings |
|---|---|
| gemination of 1, 6, 8, 10, 100 before k and h, of 1, 8, 10 before s and t (h becomes p) | 一本 いっぽん, 六回 ろっかい, 八杯 はっぱい, 十冊 じゅっさつ, 百個 ひゃっこ, 一対 いっつい |
| voicing after 3, 何, 千, 万 | 三本 さんぼん, 何匹 なんびき, 三階 さんがい, 三軒 さんげん, 三足 さんぞく, 何分 なんぷん |
| h counters | 本 匹 杯 発 泊 版 編 分 歩 (minutes; 四分 よんぷん; 分 read ぶん, as in 三分の一, stays ぶん) |
| 分 as a tenth | ぶ in pairs (五分五分, 七分三分, 五分と五分), after 割/寸/両 (三割五分) and before 咲き/目/通り (三分咲き) |
| k counters | 個 回 階 軒 件 曲 巻 箇所 か月 (ヶ月, カ月, 箇月) |
| s, t counters | 冊 歳/才 足 週 週間; 対 点 頭 通 着 |
| 羽 | わ, ば after 3/何/千, っぱ after 6, 8, 10, 100 |
| no sound change | 枚 台 度 番 倍 秒 名 円 年 年間 時 時間 人 |
| 4, 7, 9 | よん, なな, きゅう; 時, 時間 よ, しち, く; 人 よ, しち; 円, 年 よ; 月 し, しち, く |
| days (日, 日間) | ついたち after 月, else いちにち; ふつか … とおか, じゅうよっか, はつか, にじゅうよっか, 十七日 じゅうしちにち |
| others | 一人 ひとり, 二人 ふたり, 二十歳 はたち, 月 がつ only as a month name (1-12, 何) |

Where usage varies one reading is given: 8 geminates (はっぽん, not はちほん), 10 is じゅっ
(not じっ), 七人 しちにん. 一対一 (one on one) is left alone, and numbers with a point or
a comma are skipped.

`tests/test_counters.py` holds the acceptance grid: 1-10, 100, 1000 and 何, in kanji and
in digits, with 25 counters, written by hand from the grammar.

Tatoeba is not a fair test here: its readings come from MeCab + IPAdic and were mostly left
as they were, so they read the parts on their own (一匹 いち + ひき, ２杯 はい). On half b
(Jiten's list, the benchmark's span aligner, じっ = じゅっ), the 2,530 occurrences a counter
span covers go from 89.1% to 90.2% micro and 71.0% to 81.4% macro (all 72,838: 87.3% →
87.4% micro, 81.5% → 82.0% macro): 62 fixed, 32 worse, and all 32 are transcriptions
that keep the parts' own readings (三階 かい, 一本 いち) or split 二十歳 (はたち doesn't).

### The flavour rule

Books use ruby for flavour as well as for readings: マジ over 本気, スキル over 異能, そら
over 宇宙. Such ruby is never a reading:

- katakana ruby;
- ruby containing kanji;
- gikun or any reading the list doesn't give for the form (with no list: a reading not
  spelled by the kanji's own readings);
- ruby over part of a compound (魚《うお》市場).

### Certainty

`source` and `certainty`:

| source | certainty |
|---|---|
| `ruby`, `rule`, `only` | 1.0 |
| `model` | the model's posterior for its reading (0.7 or more) |
| `default`, `counter` | None |
| `dictionary` | for a form the model has a table entry for: the share of that reading in the entry's prior; else None |

Certainty is not calibrated. A ruby reading is the book's own, a rule reading what the rule
says; the model's posterior is a naive Bayes posterior, which is overconfident, and the only
calibration behind it is the 0.7 threshold, chosen because 0.5 changed hand-checked plain
sentences Sudachi had right. The dictionary value is a base rate, not a judgement of the
sentence. Use it to sort or flag, not as a probability.

### Building a table from your own library

The committed table (`reading-model-public.json.gz`, 42 forms) is trained on public-domain
works from Aozora Bunko and half of Tatoeba's reviewed sentences. A table trained on your
own library reads far more forms (403 on one library of 19,000 books):

```sh
python -m yurigana.reading_context build LIBRARY STATE --dictionary jiten_freq_global.zip
```

`LIBRARY` is a folder of EPUBs and Aozora-style TXTs (a Calibre library works; the first
folder level is taken as the author, for the held-out split), `STATE` where
`reading-model.json.gz` goes; pass that file to `Reader(tables=[...])`. It needs a few GB of
memory and about half an hour per 20,000 books on 3 processes (`--processes`). Don't publish
a table built from copyrighted books.

The steps one by one (`mine`, `report`, `train`, `evaluate`) and how the public table was
built are in `yurigana/reading_context.py`'s docstring:

1. `python -m yurigana.fetch_aozora AOZORA` and `python -m yurigana.fetch_tatoeba TATOEBA`;
2. `reading_context mine` each of `AOZORA`, `TATOEBA/a` and `TATOEBA/b`;
3. `train` on the Aozora and half a rows together, `--priors` half a's rows;
4. `evaluate` on half b's rows with `--all --prune`, which keeps the forms half b can score
   that read no worse than rules + Sudachi.

The hand-written sentences in `readings-test.tsv` are a unit test of the context rules
(`tests/test_rule_rows.py`); add rows with every new rule.

## Accuracy

`python -m yurigana.evaluate` scores the shipped `Reader.read` (no ruby in the input) next to
other tokenisers' readings, on gold sets with 95% intervals (bootstrap over sentences):

```sh
pip install "yurigana[eval]"  # the baselines: fugashi, ipadic, unidic-lite, pykakasi
python -m yurigana.evaluate tatoeba sets  # sets/tatoeba-b1.jsonl (tune), sets/tatoeba-b2.jsonl (report)
python -m yurigana.evaluate ndl aozora_dataset.zip sets  # NDL huriganacorpus-aozora, held-out authors
python -m yurigana.evaluate sets/tatoeba-b2.jsonl sets/ndl-test.jsonl --known jiten_freq_global.zip \
    --systems all --out report.json  # --compare old.json: items fixed and broken, McNemar p
tools/compare.sh sets  # this tree against origin/main on every set (base cached), misses in sets/.misses.tsv
```

Other annotators' output, such as an LLM's furigana, is scored like a system with
`--predictions NAME=FILE` (`ID | text with 漢字[かな]` lines). Agreement then becomes a review
queue: `--triage review.tsv` lists items where most systems agree on a reading the gold rejects
(candidate gold errors) and items where ours is wrong but most others are right (candidate
fixes). Gold is never changed automatically: a reading found acceptable on review goes in a
waiver file, `--alts waivers.tsv` (`set, id, surface, reading` per line), which adds it to that
span's accepted readings without editing the set.

The metrics and the gold format are in `yurigana/evaluate.py`'s docstring. Scoring is by
union span (the smallest stretch where gold and tokens line up), so segmentation doesn't
count, only readings: Sudachi's three split modes score alike. Word list folds voicing
(rendaku), display doesn't. Neither set is in git: Tatoeba's B2 is fixed by the ID list
`tatoeba-b2-ids.txt.gz`, NDL's test authors by a hash of their name.

Read the Tatoeba numbers with care: its gold is machine furigana made with MeCab + IPAdic,
mostly never corrected, so MeCab + IPAdic's lead there is partly an artefact. The public
table was pruned on all of half b, B2 included, so ours is slightly optimistic there; and the
NDL works are Aozora Bunko texts, some of which the public table was trained on (with their
ruby, not NDL's readings).

With Jiten's list as the reading list, 2026-10-19 (the full table with intervals is in the
pull request that added `evaluate`):

| | Tatoeba B2 word list | het. macro | NDL word list | het. macro |
|---|---|---|---|---|
| ours | 94.3 | 88.7 | 87.5 | 71.7 |
| Sudachi (A ≈ B = C) | 94.3 | 92.0 | 90.9 | 76.6 |
| MeCab + IPAdic | 97.0 | 89.6 | 87.2 | 68.1 |
| MeCab + unidic-lite | 93.3 | 90.3 | 90.5 | 76.1 |
| pykakasi | 93.7 | 82.4 | 85.7 | 61.6 |

Ours gives no reading to 4.2% (Tatoeba) and 4.8% (NDL) of items; the readings it would show
as furigana (only, rule, model) cover 63.5% / 57.6% of items and are right 99.3% / 96.7% of
the time.

The tables below are older measurements with earlier harnesses, not comparable to these.
They are for 0.1. Since then, the default readings above and a wider 何 rule
(なに before か, する, verbs and ？) give, on all of Tatoeba's half b with no ruby (72,838
occurrences, scored on spans as the sentences mark them), micro 79.4% → 86.3%, macro
79.7% → 80.2%, micro over forms with 2+ gold readings 81.4% → 82.6% (私 alone is 4,422 of
the 5,086 occurrences fixed; 32 got worse, all 何). Conjugated words read from Sudachi's
reading of the surface and the 気に入る and 〜人 rules then make it micro 80.1% → 87.5%,
macro 75.6% → 81.3% (scored with a missing reading as wrong; 5,353 occurrences that had none
got the right one, 64 a wrong one, none that were right changed). The hand-written
sentences, now 213 of 50 forms, macro: 96.0% with ruby, 92.2% without.

Hand-written sentences (`readings-test.tsv`, 193 sentences, 40 forms, then scored by a script since removed), macro:

| | with ruby | without ruby |
|---|---|---|
| no model | 95.0% | 80.3% |
| public table | 95.0% | 80.3% |
| table from one library | 95.0% | 79.8% |

Tatoeba's half b (54,086 reviewed sentences, never trained on): every occurrence of a form
the list gives 2+ readings that the transcription marks with a listed reading, 56,443
occurrences of 1,599 forms, 23,141 of them in the 210 forms with 2+ gold readings:

| | micro, all | micro, 210 forms | macro (per reading, 5+) |
|---|---|---|---|
| Sudachi alone | 83.6% | 85.1% | 91.8% |
| rules + Sudachi | 85.6% | 90.0% | 92.2% |
| + public table | 86.4% | 91.7% | 93.1% |
| + table from one library | 86.8% | 92.3% | 94.0% |

On one library's own ruby, hidden, held-out authors (macro / micro over 4,184 forms; macro
over the 1,210 with 2+ readings):

| | all forms | 2+ readings |
|---|---|---|
| rules, then Sudachi | 74.2% / 77.1% | 51.3% |
| + public table | 74.3% / 77.9% | 51.7% |
| + table from the library | 76.7% / 83.1% | 59.0% |

For scale: on the same Tatoeba half b occurrences of yomikata's forms (2,545 of 65 forms),
without 明日 (where Tatoeba's あした and yomikata's あす are both right), yomikata 92.9%,
Sudachi 88.4%, rules + Sudachi 89.3%, + public table 94.0%, + library table 96.0%.

## JavaScript: "Known" furigana

```sh
pnpm add github:blankiekun/yurigana#v0.1.1
```

```js
import { hideKnownRuby, isPlainReading } from 'yurigana';
const readings = (await import('yurigana/kanji-readings.json')).default;

isPlainReading('学校', 'がっこう', readings); // true
isPlainReading('宇宙', 'そら', readings); // false: gikun
// kanjiTotals: how often the reader has met each kanji
hideKnownRuby('人間', 'にんげん', { 人: 12, 間: 30 }, readings); // true
```

`hideKnownRuby(base, reading, kanjiTotals, readings, minCount = 10)` is true when the ruby
is hiragana, every kanji of the base was met at least `minCount` times, and the reading is
spelled by the kanji's on and kun readings (常用 and 人名用 kanji, KANJIDIC2) and the base's
kana, with rendaku (ひと → びと) and a final っ (がく → がっ). Katakana ruby, ruby with kanji,
gikun (そら over 宇宙) and jukujikun (きょう over 今日) always stay.

## Tests

`python -m unittest` (the Sudachi tests skip without SudachiPy) and `node --test js/*.test.js`.

## Licence

BSD 3-Clause (LICENSE), except `kanji-readings.json`, which is CC BY-SA 4.0 (KANJIDIC2).
The public table is trained on Aozora Bunko and Tatoeba (CC BY 2.0 FR). See NOTICE.
