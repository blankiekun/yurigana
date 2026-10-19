# Building a reading-model table

The committed table (`reading-model-public.json.gz`, 43 forms) is trained on public-domain
works from Aozora Bunko and half of Tatoeba's reviewed sentences. A table trained on your
own library reads far more forms (403 on one library of 19,000 books):

```sh
python -m yurigana.reading_context build LIBRARY STATE --dictionary jiten_freq_global.zip
```

`LIBRARY` is a folder of EPUBs and Aozora-style TXTs (a Calibre library works; the first
folder level is taken as the author, for the held-out split; books by Calibre's "Unknown" count
as one author per series or title), `STATE` where `reading-model.json.gz` goes; pass that file
to `Reader(tables=[...])`. `--books IDS` (a file of Calibre book ids, one per line) trains on
those books only; the output lists each book's rows. It needs a few GB of
memory and about half an hour per 20,000 books on 3 processes (`--processes`). Don't publish
a table built from copyrighted books.

The steps one by one (`mine`, `report`, `train`, `evaluate`) and how the public table was
built are in `yurigana/reading_context.py`'s docstring:

1. `python -m yurigana.fetch_aozora AOZORA` and `python -m yurigana.fetch_tatoeba TATOEBA`
   (Aozora works by the authors the NDL test set holds out are left out; half b is written as
   `b1` and `b2`, the gold sets' split);
2. `reading_context mine` each of `AOZORA`, `TATOEBA/a` and `TATOEBA/b1`;
3. `train` on the Aozora and half a rows together, `--priors` half a's rows;
4. `evaluate` on B1's rows with `--all --prune`, which keeps the forms B1 can score that read
   no worse than rules + Sudachi (forms with rules: and better than Sudachi where no rule
   fires). B2 stays unseen.

The committed table predates these two fetch fixes (T44 in [TRADEOFFS.md](../TRADEOFFS.md)).

The hand-written sentences in `readings-test.tsv` are a unit test of the context rules
(`tests/test_rule_rows.py`); add rows with every new rule.
