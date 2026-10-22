import unittest

from yurigana.era import PREWAR_READINGS, book_era
from yurigana.reader import Reader

MODERN = '「マジで？」スマホの画面を確認すると、状況はかなりヤバい感じだった。俺はメッセージを送った。' * 300
PREWAR = '彼は此の停車場の傍に立って、暫く黙然としていた。やがて其の男は往来の方へ往ってしまった。私は何だか淋しい気がした。' * 250


class TestEra(unittest.TestCase):
    def test_book_era(self):
        self.assertEqual(book_era(MODERN), 'modern')
        self.assertEqual(book_era(PREWAR), 'prewar')
        self.assertEqual(book_era(PREWAR[:5000]), 'modern')  # too short to tell

    def test_prewar_readings(self):
        self.assertEqual(PREWAR_READINGS['血肉', 'ちにく'], 'けつにく')
        reader = Reader()
        modern, prewar = (next(w for w in reader.read('血肉となる。', era=era) if w.form == '血肉') for era in (None, 'prewar'))
        self.assertEqual((modern.reading, prewar.reading, prewar.source), ('ちにく', 'けつにく', 'default'))
        hinted = next(w for w in reader.read('血肉となる。', hints=[(0, 2, 'ちにく')], era='prewar') if w.form == '血肉')
        self.assertEqual(hinted.reading, 'ちにく')  # ruby wins


if __name__ == '__main__':
    unittest.main()
