"""readings-test.tsv's rows for forms with context rules, through Reader.read with each row's own
ruby and no reading list: a regression test, not an accuracy figure (the rules were written on
these sentences; accuracy is python -m yurigana.evaluate's job).

readings-test.tsv: book id or '-', sentence, form, character offset of the form in the sentence
(without the ruby markup), gold reading (several as a|b), source ('hand', or 'hand-ruby' with
the book's ruby in Aozora markup). Add rows with every new rule."""
import csv
import os
import unittest

try:
    import sudachipy  # noqa: F401
except ImportError:
    sudachipy = None

ROWS = os.path.join(os.path.dirname(__file__), '..', 'yurigana', 'readings-test.tsv')
# Read wrong today. A row that starts or stops failing changes this list on purpose.
KNOWN_MISSES = {
    ('今日', '今日、環境問題は世界共通の関心事となった。'),  # こんにち
    ('今日', '今日の若者は本を読まない。'),
    ('明日', '｜明日《あす》の天気は晴れです。'),  # without a list, jukujikun ruby isn't taken
    ('最中', 'ずっと気になっていた最中に手を伸ばした。'),  # もなか
    ('人気', '深夜の駅前は人気がまったくなかった。'),  # ひとけ
    ('市場', '魚市場はいつも賑わっている。'),  # one token 魚市場
    ('寒気', '強い寒気に襲われ、震えが止まらない。'),  # さむけ
    ('心中', '無理心中を図った。'),  # one token 無理心中
    ('一寸', '｜一寸《いつすん》ずつ前へ進む。'),  # large-kana ruby not in kanji-readings.json
}


@unittest.skipIf(sudachipy is None, 'needs SudachiPy')
class RuleRowsTest(unittest.TestCase):
    def test_rule_rows(self):
        from yurigana import Reader, aozora_text
        from yurigana.reading_model import RULE_FORMS
        reader, misses, rows = Reader(), set(), 0
        with open(ROWS, encoding='utf-8') as f:
            for row in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
                if row['form'] not in RULE_FORMS:
                    continue
                rows += 1
                hints = []
                text, offset = aozora_text(row['sentence'], None, hints), int(row['offset'])
                self.assertEqual(text[offset:offset + len(row['form'])], row['form'], row['sentence'])
                word = next((w for w in reader.read(text, hints) if w.start <= offset < w.end), None)
                if word is None or word.reading not in row['reading'].split('|'):
                    misses.add((row['form'], row['sentence']))
        self.assertGreater(rows, 150)
        self.assertEqual(misses, KNOWN_MISSES)


if __name__ == '__main__':
    unittest.main()
