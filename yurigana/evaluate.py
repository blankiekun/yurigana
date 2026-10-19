"""How often yurigana reads kanji words right, next to other tokenisers' readings, on gold sets.

  python -m yurigana.evaluate tatoeba OUT [--source jpn_transcriptions.tsv.bz2]
      Tatoeba's reviewed transcriptions as gold sets: OUT/tatoeba-b1.jsonl (tune here) and
      OUT/tatoeba-b2.jsonl (report here). Half b (fetch_tatoeba.half_of; half a trains the public
      table) is split by the committed ID list tatoeba-b2-ids.txt.gz, so new sentences never
      join B2. Downloads the transcriptions unless --source is given.
  python -m yurigana.evaluate ndl aozora_dataset.zip OUT [--lines 100]
      NDL Lab's huriganacorpus-aozora (https://github.com/ndl-lab/huriganacorpus-aozora) as
      OUT/ndl-test.jsonl: the works of held-out authors (crc32 of the name % 5 == 0), up to
      --lines lines each, spread over the work.
  python -m yurigana.evaluate SET.jsonl ... [--known jiten_freq_global.zip] [--systems ours,sudachi-C|all]
                              [--compare old.json] [--out report.json] [--bootstrap 1000] [--misses misses.tsv]
      Scores each system on each set; a markdown table per set on stdout.
      --predictions NAME=FILE (repeatable) scores other annotators' output as system NAME: FILE
      holds `ID | text with 漢字[かな]` lines (the furigana LLMs write), each bracketed kanji run a
      token with its reading, every other character its own; a line whose text without the
      brackets isn't the gold text (or a missing line) fails alignment on all its items.
      --alts FILE adds accepted readings to the gold without editing it: TSV set, id, surface, reading.
      --triage FILE writes a review queue as TSV (kind, set, id, surface, gold, majority reading,
      systems, ours): `gold` where --agree (2) or more systems, a majority of those giving a
      reading, agree on one reading the gold rejects (candidate gold errors); `ours` where ours
      is wrong and as many of the others, a majority, are right (candidate fixes). Never gold.

Gold sets are JSONL, one sentence per line: {"id", "text", "spans": [{"b", "e", "surface",
"reading", "lemma", "alts"}]}: `reading` is the hiragana of text[b:e] as written (行 in 行った:
い), `alts` other accepted readings, `lemma` optional (the dictionary form, used to group
readings when given). Every span whose surface has kanji and no digits or latin is an item.

Scoring is by union span: the smallest stretch where the gold spans and the system's tokens
both start and end (何度 as one token against gold 何 + 度 is scored as なんど). The gold
reading of that stretch is its spans' readings with the kana between them; the system's is
its tokens' readings. An item fails alignment when the stretch holds a kanji or other
non-kana character no gold span reads (a token swallowed an unlabelled kanji), except kanji
numerals, which match any reading (NDL gives 漢数字 no kana: 三人 is scored on 人). Small kana are
folded everywhere (ゃ = や); `display` is strict about voicing (さんぼん ≠ さんほん: furigana
must be right), the other metrics fold it, as word lists do.

Systems (`--systems all` runs every one installed; the others are skipped with a note):
ours (yurigana.Reader with --known, the shipped pipeline), sudachi-A/B/C (SudachiDict-full),
mecab-ipadic and mecab-unidic (fugashi; UniDic full when the unidic package's dictionary is
downloaded, else unidic-lite), pykakasi. `pip install "yurigana[eval]"` installs them.
ginza (spaCy + ja_ginza; Sudachi readings through GiNZA's own model) and yomikata (a BERT model
for 130 heteronyms, then MeCab + UniDic) can't share an environment with yurigana's SudachiPy
0.7 (GiNZA wants <0.7, yomikata pins torch 1.13 and Python 3.10), so they run from a second
environment with yurigana on PYTHONPATH:
  pip install spacy ja-ginza
  pip install --no-deps yomikata && pip install torch transformers fugashi unidic jaconv speach pynvml rich
  python -m unidic download && python -m yomikata download

Metrics, each with a 95% interval from a bootstrap over sentences:
- word list: share of items read right (voicing folded), over all kanji words;
- display: the same, strict about voicing;
- w/o both-standard: word list without forms with two standard readings (BOTH_STANDARD);
- heteronym micro/macro: forms (lemma, else surface) with 2+ gold readings of MIN_GOLD+
  items each; macro is the mean over forms of the mean accuracy per reading;
- align fail: items whose stretch couldn't be scored (counted wrong above);
- no reading: items the system gives no reading (counted wrong above): Reader.read gives
  a conjugated word none unless the list has one reading for it or a rule or the model does;
  chimimouryou then uses the book's most common reading of the word;
- shown precision and coverage (ours only): the readings the reader would show as furigana
  (source only, rule or model: hiragana and listed), how often they are right (display) and
  what share of items they cover.

Tatoeba's gold is machine furigana made with MeCab + IPAdic, mostly never corrected: where
IPAdic and UniDic disagree it sides with IPAdic about 4 times in 5. MeCab + IPAdic's lead
there is partly that, not accuracy.
"""
import argparse
import bz2
import gzip
import itertools
import json
import math
import os
import random
import re
import sys
import time
import zlib
from collections import Counter, defaultdict

from .readings import HAS_KANJI, surface_reading, to_hiragana

HERE = os.path.dirname(os.path.abspath(__file__))
B2_IDS = os.path.join(HERE, 'tatoeba-b2-ids.txt.gz')
SYSTEMS = ('ours', 'sudachi-A', 'sudachi-B', 'sudachi-C', 'mecab-ipadic', 'mecab-unidic', 'pykakasi', 'ginza',
           'yomikata')
BOTH_STANDARD = frozenset('明日 日本 私 昨日 一昨日 明後日 一昨年 今年 何故 他'.split())
SHOWN = ('only', 'rule', 'model')  # the sources chimimouryou shows as furigana
MIN_GOLD = 5
NOTES = []  # which dictionary a system ran with
TATOEBA_NOTE = ("Tatoeba's gold is machine furigana made with MeCab + IPAdic, mostly never corrected, "
                "so MeCab + IPAdic's lead there is partly an artefact.")

_KANA = re.compile(r'^[ぁ-ゖァ-ヺーゝゞヽヾ]+$')
_NUMERALS = frozenset('〇一二三四五六七八九十百千万億兆')
_SMALL = str.maketrans('ぁぃぅぇぉっゃゅょゎゕゖ', 'あいうえおつやゆよわかけ')
_VOICING = str.maketrans('がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽゔ', 'かきくけこさしすせそたちつてとはひふへほはひふへほう')


def fold(reading: str, voicing: bool) -> str:
    reading = to_hiragana(reading).translate(_SMALL)
    # shortcut: voicing is folded on every kana, not only at a morpheme's start; fine for scoring
    return reading.translate(_VOICING) if voicing else reading


# ---------------------------------------------------------------------------- systems
# Each returns tokens(text) -> [(start, end, reading of text[start:end] or None, shown or None[, source])].

def _ours(known):
    from .reader import Reader
    reader = Reader(known=known)
    return lambda text: [(w.start, w.end, surface_reading(text[w.start:w.end], w.form, w.reading, text[w.end:w.end + 3]), w.source in SHOWN,
                          w.source) for w in reader.read(text)]


def _sudachi(mode):
    from sudachipy import Dictionary, SplitMode
    tokenizer = Dictionary(dict='full').create(getattr(SplitMode, mode))
    return lambda text: [(m.begin(), m.end(), to_hiragana(m.reading_form()) or None, None) for m in tokenizer.tokenize(text)]


def _in_order(text, pieces):
    """(start, end, reading, None) of each (surface, reading) found in order in text: MeCab and
    kakasi drop spaces."""
    out, pos = [], 0
    for surface, reading in pieces:
        start = text.find(surface, pos) if surface else -1
        if start >= 0:
            pos = start + len(surface)
            out.append((start, pos, to_hiragana(reading) if reading else None, None))
    return out


def _mecab(dictionary):
    import fugashi
    if dictionary == 'ipadic':
        import ipadic
        tagger = fugashi.GenericTagger(ipadic.MECAB_ARGS)
        reading = lambda w: w.feature[7] if len(w.feature) > 7 and w.feature[7] != '*' else None  # noqa: E731
    else:
        try:
            import unidic
            full = os.path.exists(os.path.join(unidic.DICDIR, 'dicrc'))
        except ImportError:
            full = False
        tagger = fugashi.Tagger(f'-d "{unidic.DICDIR}"') if full else fugashi.Tagger()
        NOTES.append(f"mecab-unidic: {'UniDic' if full else 'unidic-lite'}")
        reading = lambda w: w.feature.kana or None  # noqa: E731
    return lambda text: _in_order(text, [(w.surface, reading(w)) for w in tagger(text)])


def _pykakasi():
    import pykakasi
    kakasi = pykakasi.kakasi()
    return lambda text: _in_order(text, [(item['orig'], item['hira']) for item in kakasi.convert(text)])


def _ginza():
    import spacy
    nlp = spacy.load('ja_ginza')

    def tokens(text):
        return [(t.idx, t.idx + len(t.text), to_hiragana(t.morph.get('Reading')[0]) if t.morph.get('Reading') else None,
                 None) for t in nlp(text)]
    return tokens


_RUBY = re.compile(r'\{([^{}/]+)(?:/([^{}]+))?\}')


def yomikata_pieces(marked: str):
    """(base, reading or None) of each {base/reading} or {base} group of yomikata's output."""
    return [(m[1], m[2]) for m in _RUBY.finditer(marked)]


def _yomikata():
    import unicodedata
    from yomikata.dbert import dBert
    from yomikata.dictionary import Dictionary
    bert, dictionary = dBert(), Dictionary('unidic')
    surfaces = list(bert.heteronyms)

    def tokens(text):
        marked = bert.furigana(text) if any(s in text for s in surfaces) else text
        if _RUBY.sub(r'\1', marked) != unicodedata.normalize('NFKC', text):
            marked = text  # BERT truncated or [UNK]ed the sentence: dictionary readings only
        return _in_order(text, yomikata_pieces(dictionary.furigana(marked)))
    return tokens



def make_system(name: str, known=None):
    kind, _, arg = name.partition('-')
    factory = {'ours': lambda: _ours(known), 'sudachi': lambda: _sudachi(arg), 'mecab': lambda: _mecab(arg),
               'pykakasi': _pykakasi, 'ginza': _ginza, 'yomikata': _yomikata}.get(kind)
    if factory is None or name not in SYSTEMS:
        raise ValueError(f'unknown system {name}; known: {", ".join(SYSTEMS)}')
    return factory()


# ---------------------------------------------------------------------------- scoring

_DIGIT_OR_LATIN = re.compile(r'[0-9A-Za-z０-９Ａ-Ｚａ-ｚ]')


def is_item(surface: str) -> bool:
    """A kanji word: digits and latin (６月) are left out, since yurigana gives them no reading."""
    return bool(HAS_KANJI.search(surface)) and not _DIGIT_OR_LATIN.search(surface)


def units(spans, tokens):
    """Merged (start, end) stretches where gold spans and tokens overlap, i.e. the smallest spans
    on whose edges both line up."""
    out = []
    for b, e in sorted([(s['b'], s['e']) for s in spans] + [(t[0], t[1]) for t in tokens]):
        if out and b < out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([b, e])
    return out


def _gold_readings(text, b, e, spans_at):
    """Every gold reading of text[b:e] (a span's reading or alts, kana between spans as written);
    None when a character there is neither kana nor read by a span."""
    parts, i = [], b
    while i < e:
        span = spans_at.get(i)
        if span and span['e'] <= e:
            parts.append([span['reading'], *span.get('alts', ())])
            i = span['e']
        elif _KANA.match(text[i]):
            parts.append([text[i]])
            i += 1
        elif text[i] in _NUMERALS:
            parts.append(['*'])  # any reading
            i += 1
        else:
            return None
    return [''.join(p) for p in itertools.islice(itertools.product(*parts), 64)]


def _reads(reading, gold, voicing):
    """Whether reading is one of the gold readings, folded; a * there stands for any reading."""
    reading = fold(reading, voicing)
    return any(re.fullmatch('.+'.join(map(re.escape, fold(g, voicing).split('*'))), reading) for g in gold)


def _system_reading(text, b, e, tokens_at):
    """(reading of text[b:e] from the tokens, shown, sources): None when a token there has none."""
    out, shown, sources, i = [], [], [], b
    while i < e:
        token = tokens_at.get(i)
        if token and token[1] <= e:
            surface = text[i:token[1]]
            if _KANA.match(surface):
                out.append(surface)
            elif token[2] is None:
                return None, False, token[4:]
            else:
                out.append(token[2])
                shown.append(token[3])
                sources += token[4:]
            i = token[1]
        elif _KANA.match(text[i]):
            out.append(text[i])
            i += 1
        else:
            return None, False, sources
    return ''.join(out), bool(shown) and all(shown), sources


def score_sentence(sentence, tokens, misses=None, readings=None):
    """One result per item (span with kanji): (status 'ok' | 'none' | 'align', display right,
    word list right, shown); all 'align' when tokens is None. Stretches read wrong are appended
    to misses as (id, stretch, gold readings, system reading, sources), each item's (start, end,
    reading) of its stretch to readings."""
    text, spans = sentence['text'], sentence['spans']
    if tokens is None:
        n = sum(is_item(s['surface']) for s in spans)
        if readings is not None:
            readings += [None] * n
        return [('align', False, False, False)] * n
    spans_at = {s['b']: s for s in spans}
    tokens_at = {}
    for t in tokens:  # the longest token at a start: a counter span (三本) over its own tokens
        if t[1] > tokens_at.get(t[0], (0, -1))[1]:
            tokens_at[t[0]] = t
    results = {}
    for b, e in units(spans, tokens):
        inside = [s for s in spans if b <= s['b'] < e and is_item(s['surface'])]
        if not inside:
            continue
        gold = _gold_readings(text, b, e, spans_at)
        reading, shown, sources = _system_reading(text, b, e, tokens_at) if gold else (None, False, ())
        if not gold:
            result = ('align', False, False, False)
        elif reading is None:
            result = ('none', False, False, shown)
        else:
            result = ('ok', _reads(reading, gold, False), _reads(reading, gold, True), shown)
        if misses is not None and not result[2]:
            misses.append((sentence.get('id', ''), text[b:e], '/'.join(gold or ()), reading or '', ','.join(sources)))
        for s in inside:
            results[s['b']] = result, (b, e, reading)
    if readings is not None:
        readings += [results[s['b']][1] for s in spans if is_item(s['surface'])]
    return [results[s['b']][0] for s in spans if is_item(s['surface'])]


def items_of(sentences):
    """(sentence index, item key, form, folded gold reading) per item, in order."""
    return [(n, f"{s.get('id', n)}:{span['b']}", span.get('lemma') or span['surface'], fold(span['reading'], True))
            for n, s in enumerate(sentences) for span in s['spans'] if is_item(span['surface'])]


def _binomial_p(k: int, n: int) -> float:
    """Exact two-sided sign test (McNemar on the discordant pairs)."""
    if n == 0:
        return 1.0
    k = min(k, n - k)
    log = [math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) - n * math.log(2) for i in range(k + 1)]
    return min(1.0, 2 * sum(math.exp(x) for x in log))


def metrics(items, results, sentences: int, rounds: int = 1000, seed: int = 0) -> dict:
    """Each metric as [value, low, high] (95% bootstrap interval over sentences)."""
    readings = defaultdict(Counter)
    for _, _, form, gold in items:
        readings[form][gold] += 1
    hetero = {f for f, c in readings.items() if sum(n >= MIN_GOLD for n in c.values()) >= 2}
    shown_any = any(r[3] for r in results)
    ratios = {  # metric: (counts, is right) per item
        'word list': lambda it, r: (True, r[2]),
        'display': lambda it, r: (True, r[1]),
        'w/o both-standard': lambda it, r: (it[2] not in BOTH_STANDARD, r[2]),
        'heteronym micro': lambda it, r: (it[2] in hetero, r[2]),
        'align fail': lambda it, r: (True, r[0] == 'align'),
        'no reading': lambda it, r: (True, r[0] == 'none'),
        **({'shown precision': lambda it, r: (r[3], r[1]), 'coverage': lambda it, r: (True, r[3])} if shown_any else {}),
    }
    sums = {}
    for name, f in ratios.items():
        num, den = [0] * sentences, [0] * sentences
        for it, r in zip(items, results):
            counts, right = f(it, r)
            if counts:
                den[it[0]] += 1
                num[it[0]] += bool(right)
        sums[name] = (num, den)
    cells = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # (form, gold) -> sentence -> [right, n]
    for it, r in zip(items, results):
        if it[2] in hetero and readings[it[2]][it[3]] >= MIN_GOLD:
            cell = cells[it[2], it[3]][it[0]]
            cell[0] += r[2]
            cell[1] += 1

    def macro(weight):
        by_form = defaultdict(list)
        for (form, _), per in cells.items():
            n = sum(weight(s) * c[1] for s, c in per.items())
            if n:
                by_form[form].append(sum(weight(s) * c[0] for s, c in per.items()) / n)
        means = [sum(v) / len(v) for v in by_form.values()]
        return sum(means) / len(means) if means else None

    def ratio(num, den, idx=None):
        if idx is None:
            n, d = sum(num), sum(den)
        else:
            n, d = sum(map(num.__getitem__, idx)), sum(map(den.__getitem__, idx))
        return n / d if d else None

    point = {name: ratio(*nd) for name, nd in sums.items()}
    point['heteronym macro'] = macro(lambda s: 1)
    rng, draws = random.Random(seed), defaultdict(list)
    for _ in range(rounds):
        idx = rng.choices(range(sentences), k=sentences)
        for name, nd in sums.items():
            draws[name].append(ratio(*nd, idx))
        weights = Counter(idx)
        draws['heteronym macro'].append(macro(weights.__getitem__))
    out = {}
    for name, value in point.items():
        values = sorted(v for v in draws[name] if v is not None)
        low, high = (values[int(0.025 * len(values))], values[min(len(values) - 1, int(0.975 * len(values)))]) \
            if values else (None, None)
        out[name] = [value, low, high]
    out['items'] = len(items)
    out['heteronym forms'] = len({f for f, _ in cells})
    return out


# ---------------------------------------------------------------------------- report

COLUMNS = ('word list', 'display', 'w/o both-standard', 'heteronym micro', 'heteronym macro', 'align fail',
           'no reading', 'shown precision', 'coverage')


def _pct(m):
    if not m or m[0] is None:
        return '–'
    if m[1] is None:  # --bootstrap 0
        return f'{m[0] * 100:.1f}'
    return f'{m[0] * 100:.1f} ({m[1] * 100:.1f}–{m[2] * 100:.1f})'


def markdown(report: dict) -> str:
    lines = []
    for name, data in report['sets'].items():
        any_system = next(iter(data['systems'].values()), {})
        lines += [f"### {name}: {data['items']} items in {data['sentences']} sentences, "
                  f"{any_system.get('metrics', {}).get('heteronym forms', 0)} heteronym forms", '',
                  '| system | ' + ' | '.join(COLUMNS) + ' |', '|---|' + '---|' * len(COLUMNS)]
        for system, result in data['systems'].items():
            lines.append(f'| {system} | ' + ' | '.join(_pct(result['metrics'].get(c)) for c in COLUMNS) + ' |')
        for system, c in data.get('compare', {}).items():
            lines.append(f"\n{system} vs {report['compare']}: {c['fixed']} fixed, {c['broken']} broken "
                         f"(McNemar p = {c['p']:.3g}), word list {c['old'] * 100:.1f} → {c['new'] * 100:.1f}")
        if name.startswith('tatoeba'):
            lines.append('\n' + TATOEBA_NOTE)
        lines.append('')
    lines += [f'- {note}' for note in report['notes']]
    return '\n'.join(lines)


def compare(old: dict, new: dict):
    for name, data in new['sets'].items():
        before = old.get('sets', {}).get(name)
        if not before:
            continue
        old_keys = dict(zip(before['keys'], range(len(before['keys']))))
        for system, result in data['systems'].items():
            past = before['systems'].get(system)
            if not past:
                continue
            pairs = [(past['right'][old_keys[k]], result['right'][i]) for i, k in enumerate(data['keys']) if k in old_keys]
            fixed = sum(a == '0' and b == '1' for a, b in pairs)
            broken = sum(a == '1' and b == '0' for a, b in pairs)
            data.setdefault('compare', {})[system] = {
                'fixed': fixed, 'broken': broken, 'p': _binomial_p(fixed, fixed + broken),
                'old': sum(a == '1' for a, _ in pairs) / max(len(pairs), 1),
                'new': sum(b == '1' for _, b in pairs) / max(len(pairs), 1)}


_FURIGANA = re.compile(r'([㐀-䶿一-鿿豈-﫿々〆ヶ]+)\[([^\[\]]+)\]')


def prediction_tokens(annotated: str, text: str):
    """Tokens from 漢字[かな] furigana: each bracketed run with its reading, every other character
    its own token; None when the annotation without brackets isn't text."""
    out, plain, pos = [], '', 0
    for m in [*_FURIGANA.finditer(annotated), None]:
        for c in annotated[pos:m.start() if m else len(annotated)]:
            out.append((len(plain), len(plain) + 1, c, None))
            plain += c
        if m:
            out.append((len(plain), len(plain) + len(m[1]), to_hiragana(m[2]), None))
            plain, pos = plain + m[1], m.end()
    return out if plain == text else None


def predictions_system(path: str):
    with open(path, encoding='utf-8') as f:
        lines = dict(line.rstrip('\n').split(' | ', 1) for line in f if ' | ' in line)
    return lambda s: prediction_tokens(lines.get(str(s.get('id')), '').strip(), s['text'])


def add_alts(sets: dict, path: str):
    """Merges `set, id, surface, reading` rows into the matching spans' alts."""
    with open(path, encoding='utf-8') as f:
        for row in f:
            if not row.strip() or row.startswith('#'):
                continue
            name, sid, surface, reading = row.rstrip('\n').split('\t')
            spans = [sp for s in sets.get(name, ()) if str(s.get('id')) == sid for sp in s['spans'] if sp['surface'] == surface]
            if not spans:
                print(f'--alts: no {surface} in {name} {sid}', file=sys.stderr)
            for sp in spans:
                sp['alts'] = [*sp.get('alts', ()), to_hiragana(reading)]


def triage(name, sentences, right, readings, agree=2):
    """Review rows (see the docstring) from each system's right flags and (start, end, reading) per item."""
    rows, others = [], [s for s in right if s != 'ours']
    spans = [(s, sp) for s in sentences for sp in s['spans'] if is_item(sp['surface'])]
    for i, (s, sp) in enumerate(spans):
        gold = '/'.join([sp['reading'], *sp.get('alts', ())])
        groups = defaultdict(list)
        for system in right:
            r = readings[system][i]
            if r and r[2] is not None:
                groups[r[0], r[1], fold(r[2], True)].append(system)
        ours = readings.get('ours', [None] * len(spans))[i]
        ours = ours[2] or '' if ours else ''
        if groups:
            key, members = max(groups.items(), key=lambda g: len(g[1]))
            given = sum(map(len, groups.values()))
            if len(members) >= agree and 2 * len(members) > given and right[members[0]][i] == '0':
                rows.append(('gold', name, s.get('id'), sp['surface'], gold, readings[members[0]][i][2],
                             ','.join(members), ours))
        good = [x for x in others if right[x][i] == '1']
        if 'ours' in right and right['ours'][i] == '0' and len(good) >= agree and 2 * len(good) > len(others):
            rows.append(('ours', name, s.get('id'), sp['surface'], gold,
                         Counter(readings[x][i][2] for x in good).most_common(1)[0][0], ','.join(good), ours))
    return rows


def evaluate(paths, systems, known=None, rounds=1000, misses=None, predictions=(), alts=None, review=None, agree=2):
    sets = {}
    for path in paths:
        with open(path, encoding='utf-8') as f:
            sets[os.path.basename(path).removesuffix('.jsonl')] = [json.loads(line) for line in f if line.strip()]
    if alts:
        add_alts(sets, alts)
    report = {'sets': {}, 'notes': []}
    made = {}
    for system in systems:
        try:
            made[system] = (lambda f: lambda s: f(s['text']))(make_system(system, known))
        except ImportError as error:
            how = ('a second environment: see the docstring of yurigana/evaluate.py' if system in ('ginza', 'yomikata')
                   else 'pip install "yurigana[eval]"')
            report['notes'].append(f'{system} skipped: {error.name} is not installed ({how})')
    for system, path in predictions:
        made[system] = predictions_system(path)
    report['notes'] += NOTES
    for name, sentences in sets.items():
        items = items_of(sentences)
        data = report['sets'][name] = {'sentences': len(sentences), 'items': len(items), 'systems': {},
                                       'keys': [it[1] for it in items]}
        read = {}
        for system, tokens in made.items():
            start = time.time()
            missed, read[system] = [], []
            results = [r for s in sentences for r in score_sentence(s, tokens(s), missed, read[system])]
            if misses is not None:
                misses += [(name, system, *m) for m in missed]
            data['systems'][system] = {'metrics': metrics(items, results, len(sentences), rounds),
                                       'seconds': round(time.time() - start, 1),
                                       'right': ''.join('1' if r[2] else '0' for r in results)}
            print(f'{name} {system}: {time.time() - start:.0f} s', file=sys.stderr, flush=True)
        if review is not None:
            review += triage(name, sentences, {x: r['right'] for x, r in data['systems'].items()}, read, agree)
    return report


# ---------------------------------------------------------------------------- gold sets

def _write(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')


_BRACKET = re.compile(r'\[([^\[\]|]+)((?:\|[^\[\]|]*)+)\]')


def tatoeba_sentence(sentence_id: int, transcription: str):
    """{id, text, spans} from Tatoeba's [場所|ば|しょ] / [明日|あした] markup; None if it's broken."""
    text, spans, last = [], [], 0
    for m in _BRACKET.finditer(transcription):
        text.append(transcription[last:m.start()])
        base, readings = m.group(1), m.group(2).split('|')[1:]
        reading = ''.join(r or c for r, c in zip(readings, base)) if len(readings) == len(base) else ''.join(readings)
        b = sum(map(len, text))
        spans.append({'b': b, 'e': b + len(base), 'surface': base, 'reading': to_hiragana(reading)})
        text.append(base)
        last = m.end()
    text = ''.join(text) + transcription[last:]
    return None if '[' in text or '|' in text or not spans else {'id': sentence_id, 'text': text, 'spans': spans}


def convert_tatoeba(out, source=None):
    from .fetch_tatoeba import _get, half_of
    raw = bz2.open(source).read().decode('utf-8') if source else _get('jpn_transcriptions.tsv.bz2')
    with gzip.open(B2_IDS, 'rt') as f:
        b2 = {int(line) for line in f if line.strip()}
    halves = {'b1': [], 'b2': []}
    for line in raw.splitlines():
        parts = line.split('\t')
        if len(parts) != 5:
            continue
        sentence_id, lang, _, user, transcription = parts
        # only reviewed ones (fetch_tatoeba's rule); they still started as MeCab + IPAdic output
        if lang != 'jpn' or not user or not re.fullmatch(r'[\w.-]+', user) or half_of(int(sentence_id)) != 'b':
            continue
        sentence = tatoeba_sentence(int(sentence_id), transcription)
        if sentence:
            halves['b2' if int(sentence_id) in b2 else 'b1'].append(sentence)
    os.makedirs(out, exist_ok=True)
    for half, rows in halves.items():
        _write(os.path.join(out, f'tatoeba-{half}.jsonl'), sorted(rows, key=lambda r: r['id']))
        print(f'tatoeba-{half}: {len(rows)} sentences')


_ROW = {v: 'aiueo'[i] for i, row in enumerate(('あかさたなはまやらわがざだばぱぁゃ', 'いきしちにひみりぎじぢびぴぃ',
                                                'うくすつぬふむゆるぐずづぶぷぅゅ', 'えけせてねへめれげぜでべぺぇ',
                                                'おこそとのほもよろをごぞどぼぽぉょ')) for v in row}
_LONG = {'a': 'あ', 'i': 'い', 'u': 'う', 'e': 'いえ', 'o': 'うお'}


def ndl_readings(surface: str, reading: str) -> list:
    """NDL's readings are spoken style (braille): ー for long vowels, ゆう for 言う, じ/ず for ぢ/づ.
    Every written reading it can stand for, most likely first."""
    out = ['']
    for c in reading:
        if c == 'ー' and out[0]:
            out = [o + v for o in out for v in _LONG.get(_ROW.get(o[-1]), 'ー')]
        else:
            out = [o + c for o in out]
    if surface.startswith('言') and reading.startswith('ゆ'):
        out += ['い' + o[1:] for o in out]
    out += [o.replace('じ', 'ぢ').replace('ず', 'づ') for o in out if 'じ' in o or 'ず' in o]
    return list(dict.fromkeys(out))[:16]


def ndl_lines(content: str):
    """(text, spans) per line of one huriganacorpus-aozora TSV: a 行番号 row, the line ([入力文]),
    its reading, then one row per segment (segment, reading, kind)."""
    text, segments = None, []
    for row in content.replace('\r', '').split('\n') + ['行番号']:
        fields = row.split('\t')
        if row.startswith('行番号'):
            if text and segments and ''.join(s for s, _, _ in segments) == text:
                spans, b = [], 0
                for segment, reading, kind in segments:
                    if kind == '漢字' and HAS_KANJI.search(segment) and re.fullmatch(r'[ぁ-ゖー]+', reading):
                        first, *alts = ndl_readings(segment, reading)
                        spans.append({'b': b, 'e': b + len(segment), 'surface': segment, 'reading': first, 'alts': alts})
                    b += len(segment)
                if spans and len(text) <= 5000:
                    yield text, spans
            text, segments = None, []
        elif len(fields) == 3 and fields[2] == '[入力文]':
            text = fields[0]
        elif text is not None and len(fields) == 3 and fields[0] and not fields[2].startswith('['):
            segments.append(tuple(fields))


def ndl_held_out(author: str) -> bool:
    return zlib.crc32(author.encode()) % 5 == 0


def convert_ndl(archive, out, lines_per_work=100):
    import zipfile
    rows, authors = [], set()
    with zipfile.ZipFile(archive) as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            parts = info.filename.split('/')
            if not info.filename.endswith('.txt') or len(parts) < 3 or not ndl_held_out(parts[1]):
                continue
            authors.add(parts[1])
            lines = list(ndl_lines(z.read(info).decode('utf-8', 'replace')))
            step = max(1, len(lines) // lines_per_work)
            for n, (text, spans) in enumerate(lines[::step][:lines_per_work]):
                rows.append({'id': f'{parts[1]}/{parts[2]}/{n}', 'text': text, 'spans': spans})
    os.makedirs(out, exist_ok=True)
    _write(os.path.join(out, 'ndl-test.jsonl'), rows)
    print(f'ndl-test: {len(rows)} lines from {len(authors)} held-out authors')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['tatoeba']:
        p = argparse.ArgumentParser(prog='yurigana.evaluate tatoeba')
        p.add_argument('out')
        p.add_argument('--source', help='jpn_transcriptions.tsv.bz2 (default: download it)')
        args = p.parse_args(argv[1:])
        return convert_tatoeba(args.out, args.source)
    if argv[:1] == ['ndl']:
        p = argparse.ArgumentParser(prog='yurigana.evaluate ndl')
        p.add_argument('archive', help='aozora_dataset.zip from ndl-lab/huriganacorpus-aozora')
        p.add_argument('out')
        p.add_argument('--lines', type=int, default=100, help='lines per work')
        args = p.parse_args(argv[1:])
        return convert_ndl(args.archive, args.out, args.lines)
    p = argparse.ArgumentParser(prog='yurigana.evaluate', description=__doc__.split('\n\n')[0])
    p.add_argument('sets', nargs='+', help='gold JSONL files')
    p.add_argument('--known', help='reading list for ours (e.g. jiten_freq_global.zip); without one, none')
    p.add_argument('--systems', default='ours', help=f'comma-separated, or all: {",".join(SYSTEMS)}')
    p.add_argument('--compare', help='an earlier --out report: paired changes per item')
    p.add_argument('--out', help='write the report (metrics and per-item results) as JSON')
    p.add_argument('--bootstrap', type=int, default=1000, help='bootstrap rounds for the intervals')
    p.add_argument('--misses', help='write the stretches read wrong as TSV: set, system, id, stretch, gold, reading, source')
    p.add_argument('--predictions', action='append', default=[], metavar='NAME=FILE',
                   help='score `ID | 漢字[かな]` lines as system NAME (repeatable)')
    p.add_argument('--alts', help='TSV of accepted readings (set, id, surface, reading) merged into the gold')
    p.add_argument('--triage', help='write candidate gold errors and fixes for ours as TSV')
    p.add_argument('--agree', type=int, default=2, help='systems that must agree for --triage')
    args = p.parse_args(argv)
    systems = SYSTEMS if args.systems == 'all' else [s for s in args.systems.split(',') if s]
    misses = [] if args.misses else None
    review = [] if args.triage else None
    predictions = [x.split('=', 1) for x in args.predictions]
    report = evaluate(args.sets, systems, args.known, args.bootstrap, misses, predictions, args.alts, review, args.agree)
    if args.triage:
        with open(args.triage, 'w', encoding='utf-8') as f:
            f.write('kind\tset\tid\tsurface\tgold\tmajority\tsystems\tours\n')
            f.writelines('\t'.join(map(str, r)) + '\n' for r in review)
        print(f"triage: {sum(r[0] == 'gold' for r in review)} gold, {sum(r[0] == 'ours' for r in review)} ours",
              file=sys.stderr)
    if args.misses:
        with open(args.misses, 'w', encoding='utf-8') as f:
            f.writelines('\t'.join(map(str, m)) + '\n' for m in misses)
    if args.compare:
        with open(args.compare, encoding='utf-8') as f:
            compare(json.load(f), report)
        report['compare'] = os.path.basename(args.compare)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False)
    print(markdown(report))


if __name__ == '__main__':
    main()
