"""Readings in context for the forms whose readings are hardest to tell apart (間: あいだ/ま, 下:
した/もと…): per form, a logistic regression and a gradient-boosted tree ensemble over characters
and Sudachi tokens around the word, trained on Opus labels of library text (tools/form_model.py,
docs/training.md). The two models' probabilities are averaged; the reading is shown only when that
passes the form's threshold, chosen on held-back authors for 99.5% shown precision.

The file is gzipped JSON: {"version": 1, "forms": {form: entry}}, where an entry is
{"readings": [...], "threshold": t, "lr": [biases, {feature: weights}], "trees": [features,
[[nodes, leaves], ...]]} or, for a form the labels read one way, {"readings": [r], "p": p}.
Two readings have one weight and one tree per round (the second reading's log-odds), more have
one per reading. A tree node is [feature index, child if absent, child if present]; a child >= 0
is a node, -1 - k is leaf k.
"""
import gzip
import json
import math
import os

FORM_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'form-model.json.gz')
CHARS = 12  # characters on each side whose presence counts
GRAMS = 4  # characters on each side read as n-grams by position


def _token(t) -> tuple:
    pos = t.part_of_speech()
    pos = tuple(pos) + ('',) * 6  # Sudachi's has 6 parts
    return t.surface(), f'{pos[0]}-{pos[1]}', t.dictionary_form(), pos[5]


def features(text: str, tokens, i: int) -> list:
    """Features of tokens[i] within its line: the characters next to it, the two tokens before and
    after it (surface, part of speech, dictionary form after), and the token itself."""
    b = tokens[i].begin
    e = b + len(tokens[i].surface())
    line_start = text.rfind('\n', 0, b) + 1
    line_end = text.find('\n', e)
    if line_end < 0:
        line_end = len(text)
    left, right = text[max(line_start, b - CHARS):b], text[e:min(line_end, e + CHARS)]
    found = ['T=' + text[b:e]]
    for k in range(1, GRAMS + 1):
        found += ['L%d=%s' % (k, left[-k:] if len(left) >= k else '^'), 'R%d=%s' % (k, right[:k] if len(right) >= k else '$')]
    found += ['l=' + c for c in set(left)] + ['r=' + c for c in set(right)]
    before = [t for t in tokens[max(0, i - 2):i] if t.begin >= line_start]
    for k, t in enumerate(reversed(before)):
        s, p, _, _ = _token(t)
        found += ['P%d=%s' % (k, s), 'Pp%d=%s' % (k, p)]
    after = [t for t in tokens[i + 1:i + 3] if t.begin < line_end]
    for k, t in enumerate(after):
        s, p, d, _ = _token(t)
        found += ['N%d=%s' % (k, s), 'Np%d=%s' % (k, p), 'Nd%d=%s' % (k, d)]
    s, p, d, c = _token(tokens[i])
    return found + ['C=' + s, 'Cp=' + p, 'Cd=' + d, 'Cc=' + c]


def _softmax(scores: list) -> list:
    if len(scores) == 1:  # two readings: the second one's log-odds
        p = 1 / (1 + math.exp(-scores[0]))
        return [1 - p, p]
    top = max(scores)
    exps = [math.exp(s - top) for s in scores]
    total = sum(exps)
    return [x / total for x in exps]


def _tree(tree, present) -> float:
    nodes, leaves = tree
    k = 0
    while k >= 0:
        node = nodes[k]
        k = node[2] if node[0] in present else node[1]
    return leaves[-1 - k]


class FormModel:
    def __init__(self, forms: dict):
        self.forms = forms
        # feature -> index in the form's trees
        self._index = {form: {name: k for k, name in enumerate(e['trees'][0])} for form, e in forms.items() if 'trees' in e}

    @classmethod
    def load(cls, path: str = FORM_MODEL) -> 'FormModel':
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        if data.get('version') != 1:
            raise ValueError(f'{path}: unknown form model version')
        return cls(data['forms'])

    def __contains__(self, form) -> bool:
        return form in self.forms

    def probabilities(self, form: str, found: list) -> dict:
        """reading -> probability (the mean of the two models')."""
        entry = self.forms[form]
        readings = entry['readings']
        if 'p' in entry:
            return {readings[0]: entry['p']}
        biases, weights = entry['lr']
        scores = list(biases)
        for feature in found:
            w = weights.get(feature)
            if w:
                scores = [s + x for s, x in zip(scores, w)]
        lr = _softmax(scores)
        if 'trees' not in entry:
            return dict(zip(readings, lr))
        index, trees = self._index[form], entry['trees'][1]
        present = {index[f] for f in found if f in index}
        width = len(scores)
        sums = [0.0] * width
        for k, tree in enumerate(trees):
            sums[k % width] += _tree(tree, present)
        return {r: (a + b) / 2 for r, a, b in zip(readings, lr, _softmax(sums))}

    def reading(self, text: str, tokens, i: int, form: str) -> tuple:
        """(reading, probability, shown) for the word whose head token is tokens[i]."""
        probabilities = self.probabilities(form, features(text, tokens, i))
        best = max(probabilities, key=probabilities.get)
        p = probabilities[best]
        return best, p, p >= self.forms[form].get('threshold', 1.1)
