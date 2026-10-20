# Evaluation

Current numbers are in the [README](../README.md#how-it-compares). This page is the method, the caveats and older measurements.

Known trade-offs (what each reading change breaks, and the way out) are listed in [TRADEOFFS.md](../TRADEOFFS.md).

yurigana targets post-war Japanese (modern fiction, light novels, everyday text). A new default or
context rule needs majority support from post-war text: tune on Tatoeba (B1), judge on modern sets,
and when NDL's ruby nominates it, check its split by the author's era (most of NDL's held-out
authors wrote before 1946, 17% of it is Genji) and leave it out if most of its support is pre-war,
period or classical. Rules kept from earlier that only such text supports are tagged
"period-justified" in TRADEOFFS.md.

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

## Clean and hard

With `--known`, every item gets tags from the gold and the list alone (`--classes FILE` writes
them as TSV, keys only), and two metrics join word list:

- **clean**: word list without the items the gold makes unscorable or doubtful. `partial` is
  ruby over part of a word (a kanji next to the span that no span reads, as ruby over 学 alone
  in 学校): no tokeniser can line up with it, so every system loses it. `kanjidic_only` is a
  form the list doesn't have whose reading only its kanji's KANJIDIC readings spell out:
  mostly names and invented on'yomi, where the book's ruby is the only source anyone has.
  `--exclude FILE` (`set, id, surface` per line) drops gold noise found on review, such as
  Tatoeba's IPAdic artefacts; nothing is excluded automatically, since agreement between
  systems would make the gold depend on them.
- **hard**: clean over the forms the list reads two or more ways (`listed >= 2`), where
  systems actually differ.

Why: on the modern books about 60% of items are read right by every tokeniser (yurigana,
Sudachi, GiNZA, MeCab + UniDic) and by Opus. Those are free points for all of them, so word
list squeezes every gap: in the audit that added these metrics, yurigana vs Sudachi was 1.1
points on word list and 4.8 on hard, Opus vs yurigana 3.4 and 11.9. Clean moves every system
up by about the same amount (about +1 point on the modern books) and changes no ranking; it
only stops charging everyone for the gold's artefacts. Hard is the column to read for a
reading change; it is about a quarter of a book set's items, so its intervals are wider.

Left in on purpose: items where yurigana, Sudachi and Opus agree on a reading the book's ruby
rejects. In book ruby these are nearly always real author readings, not gold errors (on
Tatoeba they are mostly IPAdic's: there `--exclude` is the way). Names Sudachi tags 固有名詞
stay in too (the `proper` tag, for breakdowns): they are shown as furigana like any word.

The tags use Sudachi-C (SudachiDict-full) for the word over a span. The second environment
(GiNZA, yomikata) has a SudachiPy that can't read that dictionary, so its own tags would fall
back to the lemma or surface (a note in the report says so). `--tags REPORT.json` takes every
set's tags from an earlier report instead (same sets, same item keys, or it stops naming the
set), which is how the README's GiNZA and yomikata rows are made:

    python -m yurigana.evaluate SETS... --known jiten_freq_global.zip --systems all --out main.json
    PYTHONPATH=. /path/to/second-env/python -m yurigana.evaluate SETS... --systems ginza,yomikata --tags main.json

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

## The sanity list

`eval/sanity.tsv` is a regression list of 902 rows, checked by `tests/test_sanity.py` in CI. Each
row is a sentence, a span in it, the expected reading and other accepted ones (`alts`, `|`
between them). The test runs `Reader().read` on the sentence (no ruby, no reading list) and
compares the reading of the word that is exactly the span, else the readings of the words inside
it joined with its kana (三 + 本 gives さんほん). Kinds:

- `frequent` (500): the most frequent forms of Tatoeba's half a that its transcriptions read one
  way 90%+ of 10+ times, ordered by Jiten's frequency list (used only to choose them); expected is
  JMdict's only reading with a priority tag, else half a's majority; one half-a sentence each, or a hand-written one
  where half a's sentence joins the form into a JMdict compound (10 rows).
- `counter` (333): numbers 1-10, 百, 千 and 何 with 25 counters, and a few dates, written from
  standard grammar (いっぽん, さんびき, なんばい, ついたち, はつか).
- `convention` (20): words with two standard readings (明日 あした/あす, 家 いえ/うち).
- `probe` (49): numbers with counters in real Tatoeba sentences.

Rows the reader gets wrong are marked `xfail` in the `status` column, with what it gives in the
note, so the list measures progress. The test fails when a passing row starts failing or an
`xfail` row starts passing, and prints the pass counts per kind. When a change fixes rows,
remove their `xfail`; when it breaks one on purpose (the old reading was wrong, or a better rule
costs it), mark it `xfail` and say why in the note, or correct its expected reading or alts, in
the same pull request, so the waiver is reviewed with it.

`tools/sanity_list.py` built the list (Tatoeba's `jpn_transcriptions.tsv.bz2`, `JMdict_e.gz`,
optionally `--rank jiten_freq_global.zip`); since then it is edited by hand, so don't rerun it
over it.

## Older measurements

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
They are for 0.1. Since then, the default readings ([how it works](how-it-works.md)) and a wider 何 rule
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
