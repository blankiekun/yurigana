"""Train yurigana/form-model.json.gz (form_model.py): per form, a logistic regression and a LightGBM
tree ensemble over the features form_model.features reads from yurigana's own tokens (TRADEOFFS T514).

  OMP_NUM_THREADS=1 python tools/form_model.py LABELLED.jsonl [LABELLED.jsonl ...] [--write]

LABELLED.jsonl: Opus labels of library text, one JSON row per occurrence with `text`, `b` (the word's
offset), `form`, `label` (its reading), `author` and `held`. They are book text: keep them out of git.
Held rows (`held`) are never trained on. Val authors (crc32('val:' + author) % 8 == 0) pick each form's
threshold: models trained on the other authors read them, and the threshold is the lowest probability
whose shown readings are right 99.5% of the time (at least MIN_SHOWN of them; else the form is never
shown). The written models are then trained on train and val authors. Needs scikit-learn and lightgbm
(training only: the runtime is pure Python)."""
import argparse
import gzip
import json
import os
import zlib
from collections import Counter, defaultdict

from yurigana.form_model import FORM_MODEL, FormModel, features
from yurigana.reader import Reader

PRECISION = 0.995
MIN_SHOWN = 20  # val readings a threshold must show
PRUNE = 0.01  # smaller LR weights are dropped
GBDT = dict(n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=5, colsample_bytree=0.5, reg_lambda=1.0,
            verbose=-1, n_jobs=4)
# Readings interchangeable in any context (the lead's judgement of the label sets, E1 "T1"): either is right.
SAME = [('行き交う', 'いきかう ゆきかう'), ('日本', 'にほん にっぽん'), ('格好', 'かっこう かっこ'), ('擦れる', 'すれる こすれる'),
        ('描く', 'えがく かく'), ('何故', 'なぜ なにゆえ'), ('未だ', 'いまだ まだ'), ('故郷', 'こきょう ふるさと'), ('皆', 'みな みんな'),
        ('良い', 'よい いい'), ('家', 'いえ うち'), ('瞑る', 'つぶる つむる'), ('得る', 'える うる')]
SAME = {(form, a): set(pair.split()) for form, pair in SAME for a in pair.split()}


def right(form, label, reading) -> bool:
    return reading == label or reading in SAME.get((form, label), ())


def label(r) -> str:
    return 'いな' if r['form'] == '否' and r['label'] == 'いなや' else r['label']  # や否や: the label took the や


def row_features(reader, text: str, b: int) -> list | None:
    """form_model.features of the token at offset b, from the tokens Reader.read uses."""
    tokens = reader._adjectives(list(reader.tokenizer.tokens(text)), text)
    i = next((i for i, t in enumerate(tokens) if t.begin == b), None)
    return None if i is None else features(text, tokens, i)


def fit(rows, trees=True):
    """(readings, LR, LightGBM) for rows of one form, or (readings, None, None) when they read one way."""
    from lightgbm import LGBMClassifier
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    readings = sorted({r['label'] for r in rows})
    if len(readings) < 2:
        return readings, None, None
    vectorizer = DictVectorizer()
    x = vectorizer.fit_transform([dict.fromkeys(r['f'], 1) for r in rows])
    y = [readings.index(r['label']) for r in rows]
    lr = LogisticRegression(C=1.0, max_iter=2000).fit(x, y)
    gbdt = trees and LGBMClassifier(**GBDT).fit(x.astype('float32'), y)
    return readings, vectorizer, (lr, gbdt)


def export(readings, vectorizer, models, n) -> dict:
    """A form_model entry; `n` rows behind a one-reading form."""
    if not models:
        return {'readings': readings, 'p': round((n + 1) / (n + 2), 4)}  # one reading seen: not certain from few rows
    lr, gbdt = models
    names = vectorizer.get_feature_names_out()
    weights = {}
    for k, name in enumerate(names):
        w = [float(c[k]) for c in lr.coef_]
        if max(map(abs, w)) >= PRUNE:
            weights[name] = [round(v, 2) for v in w]
    entry = {'readings': readings, 'lr': [[round(float(v), 3) for v in lr.intercept_], weights]}
    if not gbdt:
        return entry
    used, trees = {}, []
    for tree in gbdt.booster_.dump_model()['tree_info']:
        nodes, leaves = [], []

        def walk(node):
            if 'leaf_value' in node:
                leaves.append(round(node['leaf_value'], 3))
                return -len(leaves)
            assert node['decision_type'] == '<=' and 0 < node['threshold'] < 1, node  # presence features: 0 or 1
            k = len(nodes)
            nodes.append(None)
            # absent = 0: a 'Zero' missing type sends it the default way
            zero_left = node['default_left'] if node['missing_type'] == 'Zero' else True
            low, high = walk(node['left_child']), walk(node['right_child'])
            feature = used.setdefault(names[node['split_feature']], len(used))
            nodes[k] = [feature, low if zero_left else high, high]
            return k
        root = walk(tree['tree_structure'])
        trees.append([nodes, leaves] if root >= 0 else [[[-1, root, root]], leaves])  # a lone leaf
    return entry | {'trees': [list(used), trees]}


def threshold(form, scored) -> float:
    """The lowest probability whose readings at or above it are right PRECISION of the time."""
    best = 1.1
    scored = sorted(scored, key=lambda s: -s[0])
    wrong = 0
    for n, (p, ok) in enumerate(scored, 1):
        wrong += not ok
        if n >= MIN_SHOWN and wrong <= (1 - PRECISION) * n and (n == len(scored) or scored[n][0] < p):
            best = p
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('labelled', nargs='+')
    parser.add_argument('--write', action='store_true', help=f'write {FORM_MODEL}')
    parser.add_argument('--no-trees', action='store_true', help='logistic regression only')
    parser.add_argument('--out', help='write here instead')
    args = parser.parse_args()
    reader = Reader()
    by_form = defaultdict(list)
    skipped = 0
    for path in args.labelled:
        with open(path, encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                if r['held'] or not r['label'].strip('?'):
                    continue
                r['label'] = label(r)
                r['f'] = row_features(reader, r['text'], r['b'])
                if r['f'] is None:
                    skipped += 1
                    continue
                r['val'] = zlib.crc32(('val:' + r['author']).encode()) % 8 == 0
                by_form[r['form']].append(r)
    print(f'{sum(map(len, by_form.values()))} rows, {len(by_form)} forms, {skipped} without a token at b', flush=True)
    forms = {}
    for form, rows in sorted(by_form.items()):
        train, val = [r for r in rows if not r['val']], [r for r in rows if r['val']]
        model = FormModel({form: export(*fit(train, not args.no_trees), len(train))})
        scored = []
        for r in val:
            p = model.probabilities(form, r['f'])
            best = max(p, key=p.get)
            scored.append((p[best], right(form, r['label'], best)))
        readings, vectorizer, models = fit(rows, not args.no_trees)
        entry = export(readings, vectorizer, models, len(rows))
        if models:  # the pure Python reading of the export matches the libraries'
            x = vectorizer.transform([dict.fromkeys(r['f'], 1) for r in rows[:50]])
            expected = models[0].predict_proba(x)
            if models[1]:
                expected = (expected + models[1].predict_proba(x.astype('float32'))) / 2
            got = FormModel({form: entry})
            drift = max(abs(got.probabilities(form, r['f'])[c] - e[k]) for r, e in zip(rows, expected) for k, c in enumerate(readings))
            assert drift < 0.05, (form, drift)
        entry['threshold'] = round(threshold(form, scored), 4)
        forms[form] = entry
        shown = [ok for p, ok in scored if p >= entry['threshold']]
        print(f'{form}\t{len(rows)} rows\t{Counter(r["label"] for r in rows).most_common()}\tval acc '
              f'{sum(ok for _, ok in scored) / max(1, len(scored)):.3f}\tthreshold {entry["threshold"]}\tval shown {len(shown)}/{len(scored)}',
              flush=True)
    out = args.out or (FORM_MODEL if args.write else None)
    if out:
        with gzip.open(out, 'wt', encoding='utf-8') as f:
            json.dump({'version': 1, 'forms': forms}, f, ensure_ascii=False, separators=(',', ':'))
        print(f'{out}: {os.path.getsize(out) / 1e6:.2f} MB', flush=True)


if __name__ == '__main__':
    main()
