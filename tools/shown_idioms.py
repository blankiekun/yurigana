"""Builds yurigana/shown-idioms.tsv: phrases Reader._idioms shows (each kanji token's slice of JMdict's one
reading of the phrase, source `rule`) because training-author book ruby agrees with the slices.

  python tools/shown_idioms.py MINE_DIR... --known LIST [--share 0.97] [--min 10] [--out TSV]

MINE_DIR: `python -m yurigana.reading_context mine` output (occurrences.jsonl.gz) of a post-war library.
Only ruby'd occurrences of authors in tuning split 2 (reading_context.split_of); splits 1 and 0 are left
to check the table. Reader reads each occurrence's context with every phrase shown; where a phrase's slice
covers the ruby'd token, the occurrence fires for the phrase. A phrase is kept when it fires MIN+ times and
the slices match the ruby (voicing aside) SHARE+ of them. Columns: phrase, fires, right.
"""
import argparse
import gzip
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from yurigana import reader as R  # noqa: E402
from yurigana.reading_context import split_of  # noqa: E402

UNVOICE = str.maketrans('がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ', 'かきくけこさしすせそたちつてとはひふへほはひふへほ')


class _All:
    def __contains__(self, phrase):
        return True


class _Traced(R.Reader):
    """Records which phrase each Word _idioms touched comes from."""
    def _idiom(self, text, span, words, at, hint_at, counted):
        found = super()._idiom(text, span, words, at, hint_at, counted)
        for k, _, _ in found[1] if found else ():
            self.phrase_at[words[k].start] = found[0]
        return found

    def read(self, text, hints=(), carry=None):
        self.phrase_at = {}
        return super().read(text, hints, carry)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mine', nargs='+')
    ap.add_argument('--known', required=True)
    ap.add_argument('--share', type=float, default=0.97)
    ap.add_argument('--min', type=int, default=10)
    ap.add_argument('--limit', type=int, default=0, help='stop after this many ruby occurrences (testing)')
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yurigana', 'shown-idioms.tsv'))
    args = ap.parse_args()
    R.SHOWN_IDIOMS = _All()
    reader = _Traced(known=args.known)
    fires, right, seen = Counter(), Counter(), 0
    for d in args.mine:
        for line in gzip.open(os.path.join(d, 'occurrences.jsonl.gz'), 'rt', encoding='utf-8'):
            row = json.loads(line)
            if not row[3] or split_of(row[1]) != 2:
                continue
            seen += 1
            if args.limit and seen > args.limit:
                break
            before, surface, after = row[5]
            for w in reader.read(before + surface + after):
                if w.start == len(before) and w.source == 'rule' and w.start in reader.phrase_at:
                    phrase = reader.phrase_at[w.start]
                    fires[phrase] += 1
                    right[phrase] += w.reading.translate(UNVOICE) == row[3].translate(UNVOICE)
    kept = sorted(p for p in fires if fires[p] >= args.min and right[p] >= args.share * fires[p])
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(f'# phrase\tfires\tright: tools/shown_idioms.py (ruby share {args.share}+, {args.min}+ fires, split 2)\n')
        for p in kept:
            f.write(f'{p}\t{fires[p]}\t{right[p]}\n')
    print(len(kept), 'phrases', file=sys.stderr)


if __name__ == '__main__':
    main()
