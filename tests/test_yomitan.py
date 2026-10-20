"""Tests for yurigana.yomitan."""
import json
import os
import tempfile
import unittest
import zipfile

import math

from yurigana.yomitan import extra_readings, preferred, reading_ranks, with_extra_readings


class YomitanTest(unittest.TestCase):
    def test_reading_ranks(self):
        path = os.path.join(tempfile.mkdtemp(), 'freq.zip')
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('index.json', json.dumps({'frequencyMode': 'rank-based'}))
            archive.writestr('term_meta_bank_1.json', json.dumps([
                ['人気', 'freq', {'reading': 'にんき', 'frequency': 3000}],
                ['人気', 'freq', {'reading': 'ひとけ', 'frequency': {'value': 30000}}],
                ['人気', 'freq', {'reading': 'にんき', 'frequency': 2000}], ['の', 'freq', 1]], ensure_ascii=False))
        self.assertEqual(reading_ranks(path), {('人気', 'にんき'): 2000, ('人気', 'ひとけ'): 30000})  # no extra pair for 人気
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('index.json', json.dumps({'frequencyMode': 'occurrence-based'}))
        with self.assertRaises(ValueError):
            reading_ranks(path)

    def test_extra_readings_rank_after_the_terms_own(self):
        ranks = {('描く', 'えがく'): 949, ('良い', 'よい'): 131, ('良い', 'えい'): 857}
        extra = {('描く', 'かく'), ('良い', 'いい'), ('良い', 'よい'), ('未知', 'みち')}
        self.assertEqual(with_extra_readings(ranks, extra),
                         {**ranks, ('描く', 'かく'): 950, ('良い', 'いい'): 858})  # 未知: not in the list
        self.assertEqual(preferred({'えがく': 949, 'かく': 950}), ('えがく', 950))
        self.assertIn(('描く', 'かく'), extra_readings())
        self.assertTrue(all(len(pair) == 2 and all(pair) for pair in extra_readings()))

    def test_preferred_treats_tied_readings_as_one_group(self):
        self.assertEqual(preferred({'にんき': 1463, 'ひとけ': 46242}), ('にんき', 46242))
        # Jiten ranks the word: its readings tie; JMdict's order decides, else nothing does
        self.assertEqual(preferred({'ゆう': 25, 'いう': 25}, ['いう', 'ゆう']), ('いう', math.inf))
        self.assertEqual(preferred({'かしら': 263, 'あたま': 263, 'とう': 12404}, ['とう', 'あたま', 'かしら']),
                         ('あたま', 12404))
        self.assertEqual(preferred({'けとば': 244, 'ことば': 244, 'ことのは': 197387}), (None, 197387))
        self.assertEqual(preferred({}), (None, math.inf))


if __name__ == '__main__':
    unittest.main()
