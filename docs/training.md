# Building a reading-model table

The committed table (`reading-model-public.json.gz`, 64 forms) is trained on public-domain
works from Aozora Bunko and half of Tatoeba's reviewed sentences (43 forms), and on generated
sentences (21 forms, below). A table trained on your
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

## Forms learnt from generated sentences

21 forms (素振り, 貴女, 素性, 前世, 鍛冶, 術, 潜る, 瞬く, 罰, 根, 否…) are learnt from Opus-written
modern sentences, 20 per reading (`tools/synthetic-sentences.tsv.gz`, not book text), after the recipe
of Hu et al. 2026 (arXiv 2609.19805): the model first said which of a form's listed readings are used
today, then wrote sentences for each. A sentence is a training row only where the form is its own token
that the table is asked about. The priors (`tools/synthetic-priors.tsv`) are the readings' shares in
bare text, estimated by EM on training-author books' occurrences without ruby, since balanced sentences
can't give them. `python tools/synthetic_table.py tools/synthetic-sentences.tsv.gz tools/synthetic-priors.tsv
--known jiten_freq_global.zip --write` rebuilds these entries. Each form was kept only where it read
library ruby right at least 90% of the times it changed a reading, on two sets of books, and broke nothing
on the evaluation sets (TRADEOFFS T100).

## Classifiers for the hardest forms

124 forms whose readings the table and the rules told apart worst (間, 下, 方, 家, 何, 表…) have their own
classifiers (`yurigana/form_model.py`, `form-model.json.gz`, TRADEOFFS T514): per form a logistic regression
over the characters around the word and its Sudachi neighbours. They only change readings the rest of the
pipeline leaves hidden (word lists): a shown word keeps its reading. They are trained on Opus labels of library
text (book text: the labels stay private, the weights are public):

```sh
OMP_NUM_THREADS=1 python tools/form_model.py LABELLED.jsonl [MORE.jsonl ...] --write
```

Each file holds one JSON row per occurrence (`text`, `b`, `form`, `label`, `author`, `held`). Held rows are
never trained on; val authors (`crc32('val:' + author) % 8 == 0`) set each form's threshold (99.5% right,
models trained without them; written to the file, unused while the classifiers show nothing), then the written
models learn from train and val authors. The features come from the tokens `Reader.read` uses, so training and
reading see the same ones (`tests/test_form_model.py`). It needs scikit-learn; reading doesn't. On held
authors' labels the Reader reads 94.75% of these occurrences right with them, 91.41% without.
