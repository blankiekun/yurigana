"""Builds yurigana/dominant-readings.tsv: forms Jiten's list reads several ways (so not `only`) whose
Sudachi reading is, where nothing else reads them, the reading in post-war text (俺 おれ, 声 こえ, 言葉 ことば).
Reader shows that reading (source 'only') where the token stands alone (Reader._dominant).

  python tools/dominant_readings.py MINE_DIR... --known LIST [--skip BOOKS] [--out TSV]

MINE_DIR: `python -m yurigana.reading_context mine` output (occurrences.jsonl.gz) of a post-war library.
Training authors only (reading_context.split_of != 0); --skip lists book paths to leave out (one per line:
held-out sets, pre-war books). Reader(known=LIST) without this table reads each occurrence's context; where
it would give Sudachi's reading as 'dictionary' with the guards of Reader._dominant passing, the occurrence
"fires" for (form, that reading). Books are split in two halves by crc32 of the path. A pair is kept when
its form's most firing reading is it, it fires MIN_FIRES+ times on ruby'd occurrences of each half and is
the ruby's reading SHARE+ of them in each, and JMdict gives the form that reading. Book ruby favours
unusual readings (authors ruby the unexpected one), so ruby precision understates bare-text precision.
Columns: ruby fires and right per half, bare (unruby'd) occurrences firing and all bare occurrences.
"""
import argparse
import gzip
import json
import os
import random
import sys
import zlib
from collections import Counter, defaultdict
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from yurigana.reader import Reader, jmdict_readings  # noqa: E402
from yurigana.reading_context import split_of  # noqa: E402
from yurigana.yomitan import extra_readings  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yurigana', 'dominant-readings.tsv')
MIN_BARE = 30  # unruby'd occurrences of a form, to be a candidate
CAP_RUBY, CAP_BARE = 1500, 300  # occurrences read per form
MIN_FIRES, SHARE = 10, 0.97  # per half
# Left out on Tatoeba B1 and the plain DEV set (shown and wrong 2+ times): the second reading is standard too
# Kept below SHARE by hand: 12 bare firing occurrences each, all right; the ruby that fires wrong is literary or
# flavour (男 お, 時間 とき, 本気 まじ, 少女 おとめ, 答え いらえ, 連中 れんじゅう, 両親 ふたおや, 将来 さき, 日々 にちにち,
# 底 てい, 親 しん, 客 きやく, 自然 じねん, 父 てて, 背筋 はいきん before 運動)
CHECKED = set('男 時間 本気 少女 答え 連中 両親 将来 日々 底 親 客 自然 父 背筋'.split())
DROPPED = {'洗濯機': 'せんたっき 5 of 8', '他': 'た (その他, 他に) 3 of 43'}
_UNVOICED = str.maketrans('がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ', 'かきくけこさしすせそたちつてとはひふへほはひふへほ')


class _Probe(Reader):
    """Reader whose _dominant marks every reading that would be shown if it were the form's dominant one."""
    def _dominant(self, text, token, form, reading, certainty=None):
        found = super()._dominant(text, token, form, reading, certainty)
        self.dominant[form] = reading
        shown = super()._dominant(text, token, form, reading, certainty)[1] == 'only'
        del self.dominant[form]
        return found[0], 'candidate' if shown else found[1], found[2]


_reader = None


def _init(known):
    global _reader
    _reader = _Probe(known=known)
    _reader.dominant = {}


def _read(row):
    form, label, before, surface, after, half = row
    text = before + surface + after
    try:
        word = next((w for w in _reader.read(text) if w.start == len(before)), None)
    except Exception:
        word = None
    if not word or word.source != 'candidate' or not word.reading:
        return form, label, None, None, half
    plain = word.reading[:1].translate(_UNVOICED) + word.reading[1:]  # 声 ごえ fires for こえ
    key = plain if plain in _reader.readings.get(form, ()) else word.reading
    return form, label, key, word.reading, half


def rows(dirs, skip, keep=None):
    for d in dirs:
        with gzip.open(os.path.join(d, 'occurrences.jsonl.gz'), 'rt', encoding='utf-8') as f:
            for line in f:
                row = json.loads(line)
                path, author, form, label = row[:4]
                if (keep is None or form in keep) and split_of(author) != 0 and path not in skip:
                    yield form, label or '', *row[5], zlib.crc32(path.encode()) % 2


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('dirs', nargs='+')
    parser.add_argument('--known', required=True)
    parser.add_argument('--skip', help='book paths to leave out, one per line')
    parser.add_argument('--out', default=OUT)
    parser.add_argument('--rejected', help='also write the candidates the gates leave out, with their counts')
    parser.add_argument('--processes', type=int, default=3)
    args = parser.parse_args()
    skip = set(open(args.skip, encoding='utf-8').read().splitlines()) if args.skip else set()
    bare = Counter(r[0] for r in rows(args.dirs, skip) if not r[1])
    keep = {form for form, n in bare.items() if n >= MIN_BARE}
    random.seed(1)
    sample, seen = defaultdict(list), Counter()
    for r in rows(args.dirs, skip, keep):  # a uniform sample per form and kind (reservoir)
        kind = (r[0], bool(r[1]))
        cap = CAP_RUBY if r[1] else CAP_BARE
        seen[kind] += 1
        if len(sample[kind]) < cap:
            sample[kind].append(r)
        elif (j := random.randrange(seen[kind])) < cap:
            sample[kind][j] = r
    fires, right, bare_fires = Counter(), Counter(), Counter()
    with Pool(args.processes, _init, (args.known,)) as pool:
        for form, label, key, reading, half in pool.imap_unordered(
                _read, (r for v in sample.values() for r in v), chunksize=200):
            if key and label:
                fires[form, key, half] += 1
                right[form, key, half] += label == reading
            elif key:
                bare_fires[form, key] += 1
    jmdict = jmdict_readings()
    extra = {form for form, _ in extra_readings()}  # never `only` (良い いい, 夜 よ): their list reading isn't sure
    total = Counter()
    for (form, key, _), n in fires.items():
        total[form, key] += n
    best = {}
    for (form, key), n in total.items():  # the form's most firing reading
        if n > total.get((form, best.get(form)), 0):
            best[form] = key
    lines, rejected = [], []
    for form, key in best.items():
        counts = [fires[form, key, h] for h in (0, 1)], [right[form, key, h] for h in (0, 1)]
        share = bare_fires[form, key] / max(1, min(seen[form, False], CAP_BARE))
        line = (-seen[form, False] * share, form, key, *counts[0], *counts[1], bare_fires[form, key], min(seen[form, False], CAP_BARE))
        if form not in extra and form not in DROPPED and key in jmdict.get(form, ()) and all(
                n >= MIN_FIRES and (r >= SHARE * n or form in CHECKED) for n, r in zip(*counts)):
            lines.append(line)
        else:
            rejected.append(line)
    if args.rejected:
        with open(args.rejected, 'w', encoding='utf-8') as out:
            for _, *line in sorted(rejected):
                out.write('\t'.join(map(str, line)) + '\n')
    with open(args.out, 'w', encoding='utf-8') as out:
        out.write('# form\treading\truby fires a\truby fires b\tright a\tright b\tbare firing\tbare read\n'
                  '# Built by tools/dominant_readings.py (see there) from training-author post-war book ruby; '
                  'ordered by bare occurrences shown.\n')
        for _, *line in sorted(lines):
            out.write('\t'.join(map(str, line)) + '\n')
    print(len(lines), 'pairs', file=sys.stderr)


if __name__ == '__main__':
    main()
