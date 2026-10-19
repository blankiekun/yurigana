"""Tests for yurigana.yomitan."""
import json
import os
import tempfile
import unittest
import zipfile

from yurigana.yomitan import reading_ranks


class YomitanTest(unittest.TestCase):
    def test_reading_ranks(self):
        path = os.path.join(tempfile.mkdtemp(), 'freq.zip')
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('index.json', json.dumps({'frequencyMode': 'rank-based'}))
            archive.writestr('term_meta_bank_1.json', json.dumps([
                ['人気', 'freq', {'reading': 'にんき', 'frequency': 3000}],
                ['人気', 'freq', {'reading': 'ひとけ', 'frequency': {'value': 30000}}],
                ['人気', 'freq', {'reading': 'にんき', 'frequency': 2000}], ['の', 'freq', 1]], ensure_ascii=False))
        self.assertEqual(reading_ranks(path), {('人気', 'にんき'): 2000, ('人気', 'ひとけ'): 30000})
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('index.json', json.dumps({'frequencyMode': 'occurrence-based'}))
        with self.assertRaises(ValueError):
            reading_ranks(path)


if __name__ == '__main__':
    unittest.main()
