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
pip install "yurigana @ https://github.com/blankiekun/yurigana/archive/refs/tags/v0.5.0.tar.gz"
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

For one sentence, `furigana` gives it back with readings in brackets:

```python
from yurigana import furigana

furigana('三本の取り扱いに注意して、十分に休んだ。')
# '三本[さんぼん]の取[と]り扱[あつか]いに注意[ちゅうい]して、十分[じゅうぶん]に休[やす]んだ。'
```

From the shell: `python -m yurigana 本を読んだ。`

## JavaScript: "Known" furigana

```sh
pnpm add github:blankiekun/yurigana#v0.5.0
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

Clean word list accuracy (%): the share of kanji words whose reading is right, with Jiten's
list, leaving out the few items the gold itself makes unscorable (ruby over part of a word,
readings only KANJIDIC spells out); **hard** is the same over words Jiten's list reads two or
more ways, where tokenisers actually differ (about 60% of a book's words every one of them
reads right). yurigana 0.5.0 (scores measured on main 337e44b; #108 changes only `carry`), 2026-10-20, measured with SudachiDict-full (yurigana's and Sudachi's
rows; with core, yurigana's clean scores are the same and the others move by 0.1 at most), mode C, no term dictionaries; MeCab runs with
IPAdic and unidic-lite. Opus is Claude Opus annotating the same sentences blind, as a ceiling.

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

- **Modern books**: the books' own ruby (furigana) over 1,811 clean words in post-war novels and
  light novels by authors the tables never saw. The books are a private library, so this set
  isn't published.
- **Older books**: 300 sentences of NDL's huriganacorpus-aozora (human ruby, mostly pre-war
  Aozora Bunko texts), authors held out; 2,306 clean words.
- ¹ **Tatoeba B2**: 27,000 sentences. Its gold is MeCab + IPAdic machine furigana, so
  MeCab + IPAdic's score there is inflated, and yurigana's is saturated: most of its remaining
  misses are IPAdic's readings, not errors. Clean only; 32 transcription errors found on review are left
  out (`--exclude`).
- ² Slightly favours yurigana: the public table was trained on Aozora texts that include the NDL
  test authors, and pruned on all of Tatoeba's half b, B2 included (TRADEOFFS T44, until the table
  is rebuilt without them); #96's rules were picked from 12 of B2's disagreements (#97-#99 only report it).
- ³ One blind annotation run per set.
- ⁵ **Joyo-Kanji-Yomi** (JKYB-Parakeet revision, 13,536 sentences, MIT; Sarashina2.2-TTS, arXiv
  2606.25369): three native-checked sentences per reading of every Jōyō kanji, scored with its own
  toolkit (`jkyb-eval g2p`, the target kanji's reading). Every reading counts the same, so rare and
  literary readings (社 やしろ, 政 まつりごと) weigh far more than in real books: it measures coverage
  of the Jōyō table, not what a reader meets. MeCab here is unidic-lite (the paper's full UniDic:
  96.66; its Sudachi 97.32 matches ours).
- ⁶ The dictionary-constrained CRF over a character DeBERTa (about 100M parameters, trained on GPUs
  on 2.3M LLM-annotated sentences) of Hu, Zhan and Lin (arXiv 2609.19805): their published number,
  not run here (no code or model released). For scale, frontier LLMs score 99.4-99.85 in the paper.
- ⁴ Kanji words read wrong in a typical book: the median of 20 post-war library books has about
  19,000 kanji words (114,000 characters), times each system's error rate on plain sentences of
  held-out authors (1,000 sentences, 4,832 kanji words), scored against Claude Opus reading them
  blind (no Opus figure, since the labels are its own). That reference is itself about 1% wrong and
  favours systems that read the way Opus does, so the numbers are rough; the test gives no ruby, while a real book's ruby fixes many names and rare words;
  and a misread word counts each time it appears, so distinct wrong words are far fewer. Of the
  furigana yurigana marks as sure (about 14,900 a book), about 33 are wrong (0.2%). The Tatoeba and
  plain-sentence golds were rebuilt and reviewed on 2026-10-19 (accepted readings in `--alts`), which
  moved every system's numbers here, not only yurigana's.
- The library gold accepts a ruby span when Sudachi spells it (about 14% of its items), which adds
  about 0.7 points to Sudachi-based systems (yurigana, Sudachi, GiNZA, yomikata) and takes about 2
  from pykakasi; the ranking doesn't change without those items.

The furigana yurigana marks as sure (sources `ruby`, `rule`, `model`, `only`, and number + counter spans
with certainty 1.0) are right 99.3% of the time on the modern books and cover 79% of their words; the rest are left for the reader.
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

`python -m unittest` (the Sudachi tests skip without SudachiPy) and `node --test js/*.test.js`.
They include the regression list `eval/sanity.tsv` ([docs/evaluation.md](docs/evaluation.md#the-sanity-list)).

## Licence

Free for any use, commercial or not, open or closed, as long as you give credit (keep the copyright
notice in LICENSE and NOTICE). The code is BSD 3-Clause (LICENSE), except `kanji-readings.json` (KANJIDIC2), `jmdict-pairs.json.gz`
(JMdict), `ateji.tsv` (JMdict) and `extra-readings.tsv` (hand-checked against JMdict), which are CC BY-SA 4.0 (EDRDG): also usable commercially with credit, and changed copies
of those files stay CC BY-SA. Jiten's frequency list, which `known=` takes, is CC BY-SA 4.0 as well.
The public table is trained on Aozora Bunko and Tatoeba (CC BY 2.0 FR). See NOTICE.
