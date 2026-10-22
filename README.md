# yurigana

Readings of Japanese kanji words in context. Given a text, and the ruby (furigana) the
book prints if it has any, yurigana says how each kanji word is read there: 人気 as にんき
in この店は人気 and as ひとけ in 人気のない道. It also decides which of a book's ruby a reader
no longer needs (the JS package).

It was written for [chimimouryou](https://github.com/blankiekun/chimimouryou), a
self-hosted reader for Japanese books, where it gives the difficulty service's word lists
their readings and the reader its "Known" furigana style.

## Python

```sh
pip install "yurigana @ https://github.com/blankiekun/yurigana/archive/refs/tags/v0.5.5.tar.gz"
```

That installs SudachiPy and SudachiDict-core too (pinned: readings depend on its version). For
SudachiDict-full, install `yurigana[full]` and set `YURIGANA_SUDACHI_DICT=full` (or pass
`Reader(tokenizer=SudachiTokenizer('full'))`): it reads the sets below the same, within 0.1 point,
and takes about 120 MB more disk and 100-240 MB more memory. Then:

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
[Jiten's](https://jiten.moe/frequency-dictionaries), not included) replaces them; pairs Jiten's list
lacks (描く かく, 良い いい) come from the bundled, hand-checked `extra-readings.tsv`.

Bring your own dictionary: `Reader(terms=['my-dictionary.zip'])` reads Yomitan term dictionaries you
have (none is bundled) for words the list and JMdict both lack: coined compounds Sudachi splits, words it
doesn't know, ruby over them. Those readings are `source='terms'` and never shown
([how it works](docs/how-it-works.md#term-dictionaries-you-supply)).

Many processes, little memory: `reader.save('reader.ygp')` writes the tables a Reader built from its lists
and dictionaries to one file, and `Reader.load('reader.ygp')` opens it through mmap in no time, so processes
share its pages. With Jiten's list and JMnedict: 16 MB private memory per process instead of about 565 MB
(the 78 MB file and Sudachi's dictionary are shared), the same readings, reading about 13% slower.

For one sentence, `furigana` gives it back with readings in brackets:

```python
from yurigana import furigana

furigana('三本の取り扱いに注意して、十分に休んだ。')
# '三本[さんぼん]の取[と]り扱[あつか]いに注意[ちゅうい]して、十分[じゅうぶん]に休[やす]んだ。'
```

From the shell: `python -m yurigana 本を読んだ。`

## JavaScript: "Known" furigana

```sh
pnpm add github:blankiekun/yurigana#v0.5.5
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

The share of kanji words read right (%), with Jiten's list; **hard** is the same over words that list
reads two or more ways, where tokenisers actually differ. yurigana 0.5.0, measured 2026-10-20. Claude
Opus annotating the same sentences blind is a ceiling.

| | modern books | hard (442) | older books (NDL) | hard (912) | Tatoeba B2¹ | Joyo-Kanji-Yomi⁵ | wrong words per book⁴ |
|---|---|---|---|---|---|---|---|
| **yurigana** | **95.2** | **86.7** | **92.4**² | **89.5**² | **99.2**² | **98.9** | **about 280** |
| Sudachi | 93.3 | 78.5 | 91.0 | 86.6 | 94.3 | 97.4 | about 720 |
| GiNZA | 93.3 | 78.5 | 90.9 | 86.5 | 94.3 | 97.3 | about 740 |
| yomikata | 92.2 | 79.0 | 91.1 | 86.8 | 93.1 | 96.7 | about 920 |
| MeCab + unidic-lite | 91.9 | 76.7 | 90.7 | 86.0 | 93.3 | 96.9 | about 870 |
| MeCab + IPAdic | 86.5 | 71.7 | 87.5 | 83.2 | 97.1 | 95.5 | about 880 |
| pykakasi | 85.0 | 68.1 | 84.0 | 77.9 | 93.8 | 93.6 | about 1,310 |
| Claude Opus³ | 97.7 | 95.2 | 95.4 | 93.3 | – | – | – |
| DeBERTa-CRF (Hu et al.)⁶ | – | – | – | – | – | 99.6 | – |

Modern books: the books' own ruby over 1,811 clean words of post-war novels and light novels by
held-out authors (a private library). Older books: 300 sentences of NDL's huriganacorpus-aozora,
mostly pre-war (report only). Tatoeba B2's gold is MeCab + IPAdic machine furigana. What each
column measures, its biases and the footnotes: [docs/evaluation.md](docs/evaluation.md#the-readme-table).

The furigana yurigana marks as sure (sources `ruby`, `rule`, `model`, `only`, and number + counter spans
with certainty 1.0) are right 99.3% of the time on the modern books and cover 79% of their words; the rest are left for the reader.
With JMnedict as a name dictionary (`Reader(names='JMnedict.zip')`, not included), names read one way are
shown too: 99.2% right over 81% of the words (main 33f45a5, 2026-10-20).
Method, caveats and older numbers: [docs/evaluation.md](docs/evaluation.md).

## More

- [docs/usage.md](docs/usage.md): the API in full, options, book text.
- [docs/how-it-works.md](docs/how-it-works.md): the order of readings, counters, the flavour rule,
  names across a book, certainty, cue words.
- [docs/training.md](docs/training.md): building a reading-model table from your own library.
- [docs/evaluation.md](docs/evaluation.md): scoring yourself, gold sets, older measurements.
- [TRADEOFFS.md](TRADEOFFS.md): what each reading rule breaks, and the way out.
- [HIDDEN.md](HIDDEN.md): readings no longer shown as furigana, and what would show them again.

## Tests

`python -m unittest` (the Sudachi tests skip without SudachiPy), `node --test js/*.test.js` and `ruff check .`.
They include the regression list `eval/sanity.tsv` ([docs/evaluation.md](docs/evaluation.md#the-sanity-list)).

## Licence

Free for any use, commercial or not, open or closed, as long as you give credit (keep the copyright
notice in LICENSE and NOTICE). The code is BSD 3-Clause (LICENSE), except `kanji-readings.json` (KANJIDIC2), `jmdict-pairs.json.gz`
(JMdict), `ateji.tsv` (JMdict) and `extra-readings.tsv` (hand-checked against JMdict), which are CC BY-SA 4.0 (EDRDG): also usable commercially with credit, and changed copies
of those files stay CC BY-SA. Jiten's frequency list, which `known=` takes, is CC BY-SA 4.0 as well.
The public table is trained on Aozora Bunko and Tatoeba (CC BY 2.0 FR). See NOTICE.
