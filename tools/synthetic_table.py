"""Table entries for forms the public table learns from generated sentences (TRADEOFFS T100).

  python tools/synthetic_table.py tools/synthetic-sentences.tsv.gz tools/synthetic-priors.tsv \
      --known jiten_freq_global.zip [--write]

synthetic-sentences.tsv.gz: form, reading, sentence (Opus-written modern sentences, 20 per reading, not book
text). A sentence is a row only where the form is its own token that the table would be asked about (no
compound, counter span or context rule over it), as reading_context mines ruby. synthetic-priors.tsv: form and
`reading share` pairs, the readings' shares in bare text (EM on training-author books' occurrences without ruby,
as reading_context.em_priors): balanced generated sentences can't give them. Prints each form's rows per
reading; --write replaces those forms' entries in reading-model-public.json.gz (other forms untouched)."""
import argparse
import gzip
import json
import math
import os
from collections import Counter, defaultdict

from yurigana.reader import Reader
from yurigana.reading_model import PUBLIC_TABLE, RULE_FORMS, build_form, features, token_window

MIN_ROWS = 8  # rows a reading needs
MIN_COUNT = 2  # a feature's count over the form's rows (reading_context: 3, on far more rows)


def rows(reader, path):
    """(form, reading, features) per sentence whose form the table would read."""
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            form, reading, text = line.rstrip('\n').split('\t')
            words = reader.read(text)
            tokens = list(reader.tokenizer.tokens(text))
            for i, t in enumerate(tokens):
                if form not in (t.dictionary_form(), t.normalized_form()):
                    continue
                end = t.begin + len(t.surface())
                over = [w for w in words if w.start <= t.begin and w.end >= end]
                if not any(w.source == 'counter' for w in over) and any(
                        w.start == t.begin and w.end == end and w.form == form and w.source != 'rule' for w in over):
                    yield form, reading, features(token_window(tokens, i, 0, len(text)))
                break


def entries(reader, sentences, priors):
    counts = defaultdict(lambda: defaultdict(lambda: [0, Counter()]))
    for form, reading, found in rows(reader, sentences):
        c = counts[form][reading]
        c[0] += 1
        c[1].update(found)
    table = {}
    for form, shares in priors.items():
        per = {r: counts[form][r] for r in shares}
        assert all(n >= MIN_ROWS for n, _ in per.values()), (form, {r: n for r, (n, _) in per.items()})
        total = Counter()
        for _, c in per.values():
            total.update(c)
        vocabulary = [f for f, n in total.most_common(200) if n >= MIN_COUNT]
        entry = build_form({r: c for r, (_, c) in per.items()}, vocabulary, [0.0] * len(per))
        entry[1] = [round(math.log(shares[r]), 3) for r in entry[0]]
        table[form] = entry
        print(form, {r: n for r, (n, _) in per.items()})
    return table


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('sentences')
    p.add_argument('priors')
    p.add_argument('--known', required=True, help="rank-based Yomitan frequency list (Jiten's)")
    p.add_argument('--write', action='store_true')
    a = p.parse_args()
    priors = {}
    with open(a.priors, encoding='utf-8') as f:
        for line in f:
            if not line.startswith('#'):
                form, *pairs = line.split()
                priors[form] = {r: float(s) for r, s in zip(pairs[::2], pairs[1::2])}
    table = entries(Reader(known=a.known), a.sentences, priors)
    if a.write:
        with gzip.open(PUBLIC_TABLE, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        data['forms'].update(table)
        data['ruleForms'] = sorted(set(data['ruleForms']) | (RULE_FORMS & set(table)))
        with gzip.open(PUBLIC_TABLE + '.tmp', 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        os.replace(PUBLIC_TABLE + '.tmp', PUBLIC_TABLE)
        print(f'{PUBLIC_TABLE}: {len(data["forms"])} forms')
