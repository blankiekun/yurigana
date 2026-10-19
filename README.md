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

That installs SudachiPy and SudachiDict-full too (pinned: readings depend on its version). Then:

```python
from yurigana import Reader, aozora_text

reader = Reader()
hints = []  # the book's ruby: (start, end, reading) offsets in the plain text
text = aozora_text('夜の公園は人気がなく、静かだった。\n｜宇宙《そら》を見上げ、学校へ行《い》った。', None, hints)
for word in reader.read(text, hints):
    print(word)
# Word(start=0, end=1, form='夜', reading='よる', source='dictionary', certainty=None)
# Word(start=2, end=4, form='公園', reading='こうえん', source='only', certainty=1.0)
# Word(start=5, end=7, form='人気', reading='ひとけ', source='rule', certainty=1.0)
# Word(start=11, end=13, form='静か', reading='しずか', source='only', certainty=1.0)
# Word(start=18, end=20, form='宇宙', reading='うちゅう', source='only', certainty=1.0)
# Word(start=21, end=24, form='見上げる', reading='みあげる', source='only', certainty=1.0)
# Word(start=25, end=27, form='学校', reading='がっこう', source='only', certainty=1.0)
# Word(start=28, end=30, form='行く', reading='いく', source='ruby', certainty=1.0)
```

そら over 宇宙 is the book's flavour ruby, so 宇宙 keeps its dictionary reading. With no reading
list, JMdict's (form, reading) pairs (bundled) are the list: words JMdict reads one way are
`only`. A frequency list with readings (`Reader(known='jiten_freq_global.zip')`,
[Jiten's](https://jiten.moe/frequency-dictionaries), not included) replaces them.

For one sentence, `furigana` gives it back with readings in brackets:

```python
from yurigana import furigana

furigana('三本の取り扱いに注意して、十分に休んだ。')
# '三本[さんぼん]の取[と]り扱[あつか]いに注意[ちゅうい]して、十分[じゅうぶん]に休[やす]んだ。'
```

From the shell: `python -m yurigana 本を読んだ。`

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

## How it compares

Word list accuracy (%): the share of kanji words whose reading is right, with Jiten's list,
yurigana main, 2026-10-19. Sudachi is SudachiDict-full, mode C; MeCab runs with IPAdic and
unidic-lite. Opus is Claude Opus annotating the same sentences blind, as a ceiling.

| | modern books | older books (NDL) | Tatoeba B2 |
|---|---|---|---|
| **yurigana** | **93.2** | **91.6** | **99.0** |
| Sudachi | 92.1 | 90.5 | 94.3 |
| GiNZA | 92.1 | 90.4 | 94.3 |
| yomikata | 90.8 | 90.6 | 93.1 |
| MeCab + unidic-lite | 90.8 | 90.2 | 93.3 |
| MeCab + IPAdic | 85.2 | 86.7 | 97.0 |
| pykakasi | 83.7 | 83.3 | 93.7 |
| Claude Opus | 96.6 | 95.3 | – |

- **Modern books**: the books' own ruby (furigana) over 1,875 words in post-war novels and light
  novels by authors the tables never saw. The books are a private library, so this set isn't
  published.
- **Older books**: 300 sentences of NDL's huriganacorpus-aozora (human ruby, mostly pre-war
  Aozora Bunko texts), authors held out.
- **Tatoeba B2**: 27,000 sentences. Its gold is MeCab + IPAdic machine furigana, so
  MeCab + IPAdic's score there is inflated.

The furigana yurigana marks as sure (sources `ruby`, `rule`, `model`, `only`) are right 99.1% of
the time on the modern books and cover 70% of their words; the rest are left for the reader.
Method, caveats and older numbers: [docs/evaluation.md](docs/evaluation.md).

## More

- [docs/usage.md](docs/usage.md): the API in full, options, book text.
- [docs/how-it-works.md](docs/how-it-works.md): the order of readings, counters, the flavour rule,
  names across a book, certainty, cue words.
- [docs/training.md](docs/training.md): building a reading-model table from your own library.
- [docs/evaluation.md](docs/evaluation.md): scoring yourself, gold sets, older measurements.
- [TRADEOFFS.md](TRADEOFFS.md): what each reading rule breaks, and the way out.

## Tests

`python -m unittest` (the Sudachi tests skip without SudachiPy) and `node --test js/*.test.js`.

## Licence

BSD 3-Clause (LICENSE), except `kanji-readings.json` (KANJIDIC2) and `jmdict-pairs.json.gz`
(JMdict), which are CC BY-SA 4.0 (EDRDG).
The public table is trained on Aozora Bunko and Tatoeba (CC BY 2.0 FR). See NOTICE.
