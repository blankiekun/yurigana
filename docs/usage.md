# Using yurigana

The [README](../README.md) has install and a first example. This page has the details.

## Reader.read

そら over 宇宙 is flavour ruby, so 宇宙 keeps its dictionary reading. 見上げる gets みあげる
(`source='only'`: the list, JMdict's pairs unless you give one, has one reading for it).

`read` gives one `Word` (a named tuple, easy to serialise) per token whose surface has
kanji, or per compound ([how it works](how-it-works.md#the-order-of-readings)): its character offsets in `text`, its dictionary form (行った: 行く), the reading of
that form in hiragana, where the reading came from and how certain it is. `reading` is
None when nothing gives one (a conjugated word whose listed readings don't single out one
that fits Sudachi's reading of it, or whose surface isn't its kanji stem plus kana). `readings.surface_reading(surface, form, reading, after)` turns it into the
reading of the surface, for furigana: 行っ, 行く, いく → いっ; 来 before た is き, before ない こ.

For one sentence (or any short text), `furigana` gives it back with each kanji run's reading
in brackets, the reading of the surface as written, okurigana outside:

```python
from yurigana import furigana

furigana('三本の取り扱いに注意して、十分に休んだ。')
# '三本[さんぼん]の取[と]り扱[あつか]いに注意[ちゅうい]して、十分[じゅうぶん]に休[やす]んだ。'
furigana('王の都へ向かった。', known='jiten_freq_global.zip')  # with a reading list
```

From the shell: `python -m yurigana 本を読んだ。` (or text on stdin, one line at a time;
`--known LIST`). `Reader.segments(text, hints)` gives the same as (piece, reading or None)
pairs, and `Reader.furigana(text, hints)` the bracketed string for a Reader you already have.
Words with no reading are left plain.

`book_text(path, 'EPUB' | 'HTMLZ' | 'TXT', None, hints)` gives a book's plain text, one
paragraph per line, without tables of contents or colophons, and its ruby as hints.

## Options

Options, all optional:

- `Reader(known=...)`: the (form, reading) pairs a reading must be one of: a set, a dict
  keyed by them, or the path of a rank-based Yomitan frequency list with readings (e.g.
  [Jiten's](https://jiten.moe/frequency-dictionaries), `jiten_freq_global.zip`, not
  included). With one, ruby, rules and the model never give a reading outside the list
  (Sudachi's own reading can be one: certainty 0, see [Certainty](how-it-works.md#certainty)), and forms the list gives a single
  reading get `source='only'` when JMdict (`jmdict-pairs.json.gz`, bundled) gives the form
  that reading too or has no entry for it: Jiten's list carries parser noise (声がけ こえかけ,
  振り幅 しんぷく). Without one, JMdict's pairs are the list (about 0.5 s and 140 MB more at
  start), and ruby JMdict doesn't list is still taken when it is spelled by its kanji's readings
  (`kanji-readings.json`: names, 柚木 ゆき).
- `Reader(tables=[path])`: reading-model tables built from your own library ([training](training.md)), tried
  before the public one. A missing file is skipped, so you can always pass the path.
- `Reader(tokenizer=...)`: anything with `tokens(text)` yielding `yurigana.tokens.Token`s;
  the default is `SudachiTokenizer()`: SudachiDict-core in split mode C, or the dictionary
  `SudachiTokenizer("full")` or the environment variable `YURIGANA_SUDACHI_DICT` names
  (`full` needs `pip install "yurigana[full]"`).

## JavaScript: "Known" furigana

`hideKnownRuby(base, reading, kanjiTotals, readings, minCount = 10)` is true when the ruby
is hiragana, every kanji of the base was met at least `minCount` times, and the reading is
spelled by the kanji's on and kun readings (常用 and 人名用 kanji, KANJIDIC2) and the base's
kana, with rendaku (ひと → びと) and a final っ (がく → がっ). Katakana ruby, ruby with kanji,
gikun (そら over 宇宙) and jukujikun (きょう over 今日) always stay.
