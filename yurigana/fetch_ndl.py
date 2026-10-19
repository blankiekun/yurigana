"""NDL Lab's huriganacorpus-aozora (https://github.com/ndl-lab/huriganacorpus-aozora) as
Aozora-style TXT for the committed reading model: OUT/<author>/<work>.txt, a reading as ruby
over every kanji word (｜名前《なまえ》), so `reading_context.py mine` takes each as gold.

The corpus is 1,944 public-domain Aozora Bunko works whose every kanji word was read from
Sapie's braille data, published under the Public Domain Mark 1.0. Fully labelled, it gives
training and dev gold for forms ruby rarely marks (the priors stay Tatoeba's: its shares are
literary). The works of the authors `yurigana.evaluate ndl` holds out (ndl_held_out) are left
out, so the NDL test set stays unseen, and so are PERIOD_AUTHORS: their period fiction
(時代物) reads words the old way, and yurigana targets post-war Japanese.

Braille readings are spoken style: とーじ is とうじ, せんせー せんせい. Where a long vowel
could be written two ways, the one the reading list (--dictionary) gives that kanji run is
taken, else the commoner spelling (evaluate.ndl_readings).

  python -m yurigana.fetch_ndl aozora_dataset.zip OUT --dictionary jiten_freq_global.zip
      aozora_dataset.zip: https://lab.ndl.go.jp/dataset/huriganacorpus/aozora_dataset.zip
"""
import argparse
import os
import re
import zipfile
from collections import defaultdict

from .evaluate import ndl_held_out, ndl_lines
from .readings import to_hiragana
from .yomitan import reading_ranks

PERIOD_AUTHORS = {'中里介山', '山本周五郎', '岡本綺堂', '野村胡堂', '林不忘'}
_KANJI_RUN = re.compile(r'^[一-鿿々〆ヶ]+')


def run_readings(known) -> dict:
    """Leading kanji run of each listed form -> its readings without the okurigana (行く いく: 行 い)."""
    runs = defaultdict(set)
    for term, reading in known:
        m = _KANJI_RUN.match(term)
        rest = to_hiragana(term[m.end():]) if m else None
        if m and reading.endswith(rest):
            runs[m.group()].add(reading[:len(reading) - len(rest)])
    return runs


def to_aozora(text: str, spans, runs) -> str:
    out, last = [], 0
    for span in spans:
        surface = span['surface']
        options = [span['reading']] + span['alts']  # ndl_readings: the spellings a braille reading stands for
        reading = next((r for r in options if r in runs.get(surface, ())), options[0])
        out += [text[last:span['b']], f'｜{surface}《{reading}》']
        last = span['e']
    return ''.join(out) + text[last:]


def main(archive: str, out: str, dictionary: str):
    runs = run_readings(reading_ranks(dictionary))
    works, held = 0, set()
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            parts = info.filename.split('/')
            if not info.filename.endswith('.txt') or len(parts) < 3:
                continue
            if ndl_held_out(parts[1]):
                held.add(parts[1])
                continue
            if parts[1] in PERIOD_AUTHORS:
                continue
            lines = [to_aozora(text, spans, runs) for text, spans in ndl_lines(z.read(info).decode('utf-8', 'replace'))]
            path = os.path.join(out, parts[1], '_'.join(parts[2:]))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
            works += 1
    print(f'{works} works written, {len(held)} held-out authors left out')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', help='aozora_dataset.zip')
    parser.add_argument('out')
    parser.add_argument('--dictionary', required=True, help="rank-based Yomitan frequency list, e.g. Jiten's")
    args = parser.parse_args()
    main(args.archive, args.out, args.dictionary)
