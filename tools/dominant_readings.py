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
Columns: ruby fires and right per half, bare (unruby'd) occurrences firing and all bare occurrences, and for
pairs admitted below SHARE on labelled bare text (BARE_CHECKED) those labels.
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
# Admitted at SHARE_BARE (ruby understates the default reading: authors ruby the unusual one) when Opus-labelled bare
# firing occurrences of held-back books (split 1, 40 per form) are all right ('?' lines, two readings plausible, left
# out): {form: 'right/labelled'}, written as the ninth column. 120 forms labelled (T430); the rest of the 0.90 tier
# is rare and mostly literary.
# Reader doesn't show them right after a noun, adverb, prefix or verb stem (voiced compound tails: パン好き ずき).
SHARE_BARE = 0.90
BARE_CHECKED = dict(x.split(':') for x in '''
気:40/40 顔:40/40 入る:40/40 心:40/40 先:40/40 来る:40/40 行く:38/38 好き:40/40 外:40/40 子:39/39 前:40/40 逆:40/40 道:40/40
人:39/39 水:40/40 怒る:38/38 代わり:40/40 色:40/40 火:40/40 我:40/40 一方:40/40 仲間:40/40 裏:40/40 一言:40/40 支える:40/40 時:40/40
事:40/40 酒:40/40 骨:40/40 夏:40/40 下手:40/40 頰:39/39 神:40/40 着替える:40/40 愛:40/40 緑:40/40 己:40/40 表面:40/40 妻:40/40
町:40/40 波:40/40 頬:40/40 顎:39/39 人数:40/40 城:40/40 輪:40/40 王:40/40 所:40/40 初め:40/40 誘い:38/38 袋:40/40 毛:40/40
停止:40/40 草:40/40 共通:40/40 温かい:39/39 親しい:40/40 宿す:39/39 呪い:40/40 埋まる:39/39 勝ち:40/40 地下:40/40 破れる:40/40 夜中:40/40
数:40/40 静寂:40/40 泡:40/40 羽:40/40 忠実:40/40 橋:40/40 黄色:40/40 造り:40/40 幾度:40/40 無礼:40/40 青春:40/40 翌朝:40/40 振り:40/40
支え:40/40 瓶:39/39 無人:40/40 執着:40/40 境:40/40 束ねる:40/40 荷:40/40 愛想:40/40 大金:40/40 暖かい:40/40 音色:40/40 殻:40/40
中指:40/40 汁:40/40 毎年:39/39 鈴:40/40 旅人:40/40 鈍い:40/40 兄さん:40/40 比:40/40 半日:40/40 職:40/40 家系:40/40 多々:40/40 新:38/38
功:40/40 各国:40/40 型:40/40 何処:40/40
'''.split())
DROPPED = {'洗濯機': 'せんたっき 5 of 8', '他': 'た (その他, 他に) 3 of 43'}
_UNVOICED = str.maketrans('がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ', 'かきくけこさしすせそたちつてとはひふへほはひふへほ')


class _Probe(Reader):
    """Reader whose _dominant marks every reading that would be shown if it were the form's dominant one."""
    def _dominant(self, text, token, form, reading, certainty=None, previous=None):
        found = super()._dominant(text, token, form, reading, certainty, previous)
        self.dominant[form] = reading
        shown = super()._dominant(text, token, form, reading, certainty, previous)[1] == 'only'
        del self.dominant[form]
        return found[0], 'candidate' if shown else found[1], found[2]


_reader = None


def _init(known):
    global _reader
    _reader = _Probe(known=known)
    _reader.dominant = {}
    _reader.dominant_checked = set(BARE_CHECKED)  # the voicing guard they get in Reader


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
            lines.append(line + (BARE_CHECKED.get(form, ''),))  # measured with the guard: keep it
        elif form not in extra and form not in DROPPED and key in jmdict.get(form, ()) and form in BARE_CHECKED and all(
                n >= MIN_FIRES and r >= SHARE_BARE * n for n, r in zip(*counts)):
            lines.append(line + (BARE_CHECKED[form],))
        else:
            rejected.append(line)
    if args.rejected:
        with open(args.rejected, 'w', encoding='utf-8') as out:
            for _, *line in sorted(rejected):
                out.write('\t'.join(map(str, line)) + '\n')
    with open(args.out, 'w', encoding='utf-8') as out:
        out.write('# form\treading\truby fires a\truby fires b\tright a\tright b\tbare firing\tbare read\tbare labelled right\n'
                  '# Built by tools/dominant_readings.py (see there) from training-author post-war book ruby; '
                  'ordered by bare occurrences shown.\n')
        for _, *line in sorted(lines):
            out.write('\t'.join(map(str, line)).rstrip('\t') + '\n')
    print(len(lines), 'pairs', file=sys.stderr)


if __name__ == '__main__':
    main()
