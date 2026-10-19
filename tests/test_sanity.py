"""The regression list eval/sanity.tsv (README, "The sanity list"): Reader().read on each row's
sentence, and the reading of the word(s) covering its span. A row that passes must keep
passing; a row marked xfail must keep failing until its mark is removed."""
import os
import sys
import unittest
from collections import Counter

from yurigana.readings import HAS_KANJI, to_hiragana

try:
    import sudachipy  # noqa: F401
except ImportError:
    sudachipy = None

SANITY = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'eval', 'sanity.tsv')
COLUMNS = ('sentence', 'span', 'reading', 'alts', 'kind', 'status', 'note')


def rows(path: str = SANITY) -> list:
    with open(path, encoding='utf-8') as f:
        lines = [(n, line.rstrip('\n').split('\t')) for n, line in enumerate(f, 1)
                 if line.strip() and not line.startswith('#')]
    assert tuple(lines[0][1]) == COLUMNS, lines[0]
    return [{**dict(zip(COLUMNS, line)), 'line': n} for n, line in lines[1:]]


def span_reading(words: list, text: str, span: str) -> str | None:
    """The reading of the word that is exactly the span's first occurrence (三本 as one Word), else
    the readings of the words inside it joined with its kana (三 + 本: さんほん, union-span scoring),
    else None (a word reaches past the span, or a kanji is left uncovered)."""
    start = text.find(span)
    end = start + len(span)
    exact = [w for w in words if (w.start, w.end) == (start, end)]
    if exact:
        return exact[0].reading
    reading, at = '', start
    for w in sorted(words, key=lambda w: (w.start, -w.end)):
        if w.end <= start or w.start >= end or w.start < at:
            continue
        gap = text[at:w.start]
        if w.end > end or w.reading is None or HAS_KANJI.search(gap):
            return None
        reading, at = reading + to_hiragana(gap) + w.reading, w.end
    return None if at == start or HAS_KANJI.search(text[at:end]) else reading + to_hiragana(text[at:end])


def outcome(reader, row: dict) -> tuple:
    """(passes, the reading given)."""
    got = span_reading(reader.read(row['sentence']), row['sentence'], row['span'])
    return got in {row['reading'], *filter(None, row['alts'].split('|'))}, got


@unittest.skipIf(sudachipy is None, 'needs SudachiPy')
class SanityListTest(unittest.TestCase):
    def test_rows_keep_their_status(self):
        from yurigana import Reader
        reader = Reader()
        table = rows()
        self.assertTrue(all(len(row) == len(COLUMNS) + 1 for row in table), 'a row without 7 columns')
        tally, broken, fixed = Counter(), [], []
        for row in table:
            n = row['line']
            self.assertIn(row['span'], row['sentence'], f'line {n}')
            passes, got = outcome(reader, row)
            xfail = row['status'] == 'xfail'
            tally[row['kind'], 'pass' if passes else 'fail'] += 1
            if passes == xfail:
                (fixed if passes else broken).append(f"  line {n}: {row['span']} {row['reading']}, got {got}"
                                                     f" ({row['sentence']})")
        print('\nsanity.tsv: ' + ', '.join(f'{kind} {tally[kind, "pass"]} pass / {tally[kind, "fail"]} fail'
                                           for kind in sorted({k for k, _ in tally})), file=sys.stderr)
        message = ''
        if broken:
            message += f'{len(broken)} rows stopped passing (fix it, or mark them xfail with a reason):\n'
            message += '\n'.join(broken) + '\n'
        if fixed:
            message += f'{len(fixed)} xfail rows pass now (remove their xfail mark):\n' + '\n'.join(fixed)
        if message:
            self.fail(message)

    def test_rows_are_well_formed(self):
        for row in rows():
            self.assertIn(row['kind'], ('frequent', 'counter', 'convention', 'probe'), row)
            self.assertIn(row['status'], ('', 'xfail'), row)


class SpanReadingTest(unittest.TestCase):
    def test_exact_word_then_words_inside(self):
        from yurigana import Word
        three, hon = Word(0, 1, '三', 'さん', 'dictionary', None), Word(1, 2, '本', 'ほん', 'dictionary', None)
        self.assertEqual(span_reading([three, hon], '三本ある', '三本'), 'さんほん')
        both = Word(0, 2, '三本', 'さんぼん', 'counter', None)
        self.assertEqual(span_reading([both, three, hon], '三本ある', '三本'), 'さんぼん')
        self.assertIsNone(span_reading([Word(0, 2, '本屋', 'ほんや', 'dictionary', None)], '本屋', '本'))
        self.assertIsNone(span_reading([three], '三本', '三本'))  # 本 left uncovered
        self.assertEqual(span_reading([Word(1, 2, '日', 'ひ', 'dictionary', None)], 'お日様', 'お日'), 'おひ')


if __name__ == '__main__':
    unittest.main()
