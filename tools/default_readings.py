"""Builds yurigana/default-readings.tsv: Sudachi readings that human readings replace, given
instead when nothing else gives one (source 'default', next to the hand-picked
readings.HAND_DEFAULTS): 身体 しんたい → からだ, 時 じ → とき, 実 じつ → み, 下 もと → した.

  python tools/default_readings.py aozora_dataset.zip jpn_transcriptions.tsv.bz2 JMdict_e.gz --known LIST

From NDL Lab's huriganacorpus-aozora (human readings of Aozora Bunko's public-domain works,
https://github.com/ndl-lab/huriganacorpus-aozora), Tatoeba's transcriptions (CC BY 2.0 FR)
and JMdict (EDRDG, CC BY-SA 4.0, http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz).

Reader(known=LIST), without this table, reads LINES lines of each NDL work and Tatoeba's
modern sentences (half a and B1; B2 is left for reporting). Where its reading is Sudachi's
(source 'dictionary') for an unconjugated word, (form, Sudachi's reading) counts the gold
readings. One-kanji affixes are left out (readings.glued: next to kanji or digits, or after
katakana: 郵便局側 is not 側 そば, ダウンロード時 not 時 とき); Reader skips the table there.

NDL nominates: on its training authors (crc32 of the author % 5 in 2-4; 0 is evaluate.py's
NDL test set, never read here), R is MIN_R+ of a pair's occurrences from MIN_AUTHORS+ authors,
SHARE+ of them, GAIN+ more than Sudachi's, and JMdict lists R for the form. NDL's text is
99.8% pre-1946 and yurigana targets post-war Japanese, so modern text decides: a pair is kept
only when, on Tatoeba alone, R is right MODERN_NET+ more times than Sudachi's reading and
MODERN+ of the times it changes it (the hand-picked defaults' bar, one stricter since NDL chose
the pairs). Readings only older text uses (都 みやこ, 側 そば, 表 おもて) stay out. The NDL dev
authors' counts (% 5 == 1) are kept in the table for reference. --counts caches the counts in
a JSON file (they take ~10 minutes).
"""
import argparse
import bz2
import gzip
import io
import json
import os
import re
import zipfile
import zlib
from collections import Counter, defaultdict
from multiprocessing import Pool
from xml.etree import ElementTree

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yurigana', 'default-readings.tsv')
MIN_R, SHARE, GAIN, MIN_AUTHORS, MODERN_NET, MODERN = 8, 0.6, 6, 3, 3, 0.9

_reader = None


def jmdict(path) -> dict:
    """form -> hiragana readings (not ik/ok/rk/sk; re_restr and re_nokanji applied)."""
    from yurigana.readings import to_hiragana
    xml = re.sub(rb'<re_inf>&(\w+);', rb'<re_inf>\1', gzip.open(path).read())
    found = defaultdict(set)
    for _, entry in ElementTree.iterparse(io.BytesIO(xml)):
        if entry.tag != 'entry':
            continue
        forms = [k.findtext('keb') for k in entry.iter('k_ele')]
        for r in entry.iter('r_ele'):
            if {'ik', 'ok', 'rk', 'sk'} & {i.text for i in r.iter('re_inf')} or r.find('re_nokanji') is not None:
                continue
            restr = {x.text for x in r.iter('re_restr')}
            for form in forms:
                if not restr or form in restr:
                    found[form].add(to_hiragana(r.findtext('reb')))
        entry.clear()
    return found


def ndl(archive, lines):
    """{'train': [...], 'dev': [...]}: gold sentences, `lines` per work, spread over it."""
    from yurigana.evaluate import ndl_lines
    out = {'train': [], 'dev': []}
    with zipfile.ZipFile(archive) as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            parts = info.filename.split('/')
            split = zlib.crc32(parts[1].encode()) % 5 if len(parts) > 2 else 0
            if not info.filename.endswith('.txt') or split == 0:
                continue
            found = list(ndl_lines(z.read(info).decode('utf-8', 'replace')))
            out['dev' if split == 1 else 'train'] += [{'text': t, 'spans': s, 'author': parts[1]}
                                                       for t, s in found[::max(1, len(found) // lines)][:lines]]
    return out


def tatoeba_modern(path):
    """Tatoeba's reviewed sentences of half a and B1 (half b without evaluate.py's B2 IDs)."""
    from yurigana.evaluate import B2_IDS, tatoeba_sentence
    from yurigana.fetch_tatoeba import half_of
    with gzip.open(B2_IDS, 'rt') as f:
        b2 = {int(line) for line in f if line.strip()}
    for line in bz2.open(path).read().decode('utf-8').splitlines():
        parts = line.split('\t')
        if len(parts) == 5 and parts[1] == 'jpn' and parts[3] and re.fullmatch(r'[\w.-]+', parts[3]) \
                and int(parts[0]) not in b2:
            sentence = tatoeba_sentence(int(parts[0]), parts[4])
            if sentence:
                yield sentence


def _init(known):
    global _reader
    import yurigana.reader as reader
    from yurigana.readings import HAND_DEFAULTS
    reader.DEFAULT_READINGS = HAND_DEFAULTS  # the table being built is not used to build it
    _reader = reader.Reader(known=known)


def _pairs(sentence):
    """((form, Sudachi's reading), gold readings) per word read with Sudachi's reading."""
    from yurigana.evaluate import _gold_readings
    from yurigana.readings import glued, to_hiragana
    text, spans = sentence['text'], sentence['spans']
    spans_at = {s['b']: s for s in spans}
    tokens = {t.begin: t for t in _reader.tokenizer.tokens(text)}
    out = []
    for w in _reader.read(text):
        token = tokens.get(w.start)
        if w.source != 'dictionary' or w.start not in spans_at or not token or token.surface() != w.form \
                or w.end != w.start + len(w.form) or glued(text, w.start, w.end):
            continue
        gold = _gold_readings(text, w.start, w.end, spans_at)
        if gold:
            out.append(((w.form, to_hiragana(token.reading_form())), gold))
    return out


def counts(pool, sentences, readings):
    """(form, Sudachi's reading) -> Counter: '' for Sudachi right, else the gold reading JMdict lists
    (the first; '?' when none); '#' + reading: how many authors gave it."""
    from yurigana.evaluate import fold
    found, authors = defaultdict(Counter), defaultdict(set)
    for sentence, pairs in zip(sentences, pool.imap(_pairs, sentences, chunksize=50)):
        for (form, sudachi), gold in pairs:
            if any(fold(g, True) == fold(sudachi, True) for g in gold):
                reading = ''
            else:
                reading = next((g for g in gold if g in readings.get(form, ())), '?')
            found[form, sudachi][reading] += 1
            authors[form, sudachi, reading].add(sentence.get('author'))
    for (form, sudachi, reading), names in authors.items():
        found[form, sudachi]['#' + reading] = len(names)
    return found


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('ndl', help='aozora_dataset.zip')
    p.add_argument('tatoeba', help='jpn_transcriptions.tsv.bz2')
    p.add_argument('jmdict', help='JMdict_e.gz')
    p.add_argument('--known', required=True, help="the reading list Reader is given (Jiten's frequency list)")
    p.add_argument('--lines', type=int, default=60, help='lines per NDL work')
    p.add_argument('--processes', type=int, default=4)
    p.add_argument('--counts', help='a JSON file: read the counts from it if it exists, else write them there')
    args = p.parse_args()
    if args.counts and os.path.exists(args.counts):
        with open(args.counts, encoding='utf-8') as f:
            found = {name: {tuple(k.split('\t')): Counter(v) for k, v in c.items()} for name, c in json.load(f).items()}
    else:
        readings = jmdict(args.jmdict)
        sets = ndl(args.ndl, args.lines)
        sets['tatoeba'] = list(tatoeba_modern(args.tatoeba))
        with Pool(args.processes, _init, (args.known,)) as pool:
            found = {name: counts(pool, sentences, readings) for name, sentences in sets.items()}
        if args.counts:
            with open(args.counts, 'w', encoding='utf-8') as f:
                json.dump({name: {'\t'.join(k): v for k, v in c.items()} for name, c in found.items()}, f, ensure_ascii=False)
    rows = []
    for (form, sudachi), c in found['train'].items():
        total = sum(n for r, n in c.items() if not r.startswith('#'))
        r, n = max(((r, n) for r, n in c.items() if r not in ('', '?') and not r.startswith('#')),
                   key=lambda x: x[1], default=('', 0))
        if n < MIN_R or n < SHARE * total or n - c[''] < GAIN or c['#' + r] < MIN_AUTHORS:
            continue
        dev, tatoeba = (found[s].get((form, sudachi), Counter()) for s in ('dev', 'tatoeba'))
        # yurigana targets post-war text: modern text alone must carry the pair (NDL only nominates it)
        if tatoeba[r] - tatoeba[''] >= MODERN_NET and tatoeba[r] >= MODERN * (tatoeba[r] + tatoeba['']):
            rows.append((form, sudachi, r, n, total, c['#' + r], dev[r], dev[''], tatoeba[r], tatoeba['']))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('# form\tSudachi\treading\ttrain: reading\ttrain: all\ttrain: authors\tdev: reading\tdev: Sudachi right'
                '\tTatoeba: reading\tTatoeba: Sudachi right\n'
                '# Built by tools/default_readings.py (see there); NDL huriganacorpus-aozora, Tatoeba, JMdict.\n')
        for row in sorted(rows):
            f.write('\t'.join(map(str, row)) + '\n')
    print(len(rows), 'pairs')


if __name__ == '__main__':
    main()
