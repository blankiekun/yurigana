import os
import tempfile
import unittest
from unittest import mock

from yurigana import Reader
from yurigana.packed import Packed, PairMap, write

from .test_reader import ToyTokenizer

TEXTS = ('人気のない廊下。', '私は学校に行った。', 'プレハブ小屋。この箱。', '日本一の身体。', '柚木と姫野芽衣。')


class PackedTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, 'reader.ygp')

    def test_tables(self):
        table = {f'語{i}': f'よみ{i}' for i in range(500)} | {'': 'empty key', 'x': ''}
        write(self.path, {'a': table, 'empty': {}, 'pairs': {'人気\tにんき': '3'}})
        packed = Packed(self.path)
        a = packed.table('a')
        self.assertEqual(dict(a.items()), table)
        self.assertEqual(list(a), list(table))  # the dict's order
        self.assertEqual((len(a), a['x'], a.get('語7'), a.get('無'), 'x' in a, None in a), (502, '', 'よみ7', None, True, False))
        with self.assertRaises(KeyError):
            a['無']
        self.assertEqual((len(packed.table('empty')), packed.table('empty').get('a')), (0, None))
        pairs = PairMap(packed.table('pairs'))
        self.assertEqual((pairs[('人気', 'にんき')], ('人気', None) in pairs, pairs.get(('人気', 'ひとけ'), 0)), (3, False, 0))

    def test_other_version(self):
        Reader({('人気', 'にんき')}, tokenizer=ToyTokenizer()).save(self.path)
        with mock.patch('yurigana.reader._source_hash', return_value='other'):
            with self.assertRaises(ValueError):
                Reader.load(self.path, tokenizer=ToyTokenizer())

    def test_not_packed(self):
        with open(self.path, 'wb') as f:
            f.write(b'{}')
        with self.assertRaises(ValueError):
            Packed(self.path)

    def check(self, reader):
        reader.save(self.path)
        loaded = Reader.load(self.path, tokenizer=ToyTokenizer())
        for text in TEXTS:
            self.assertEqual(loaded.read(text), reader.read(text), text)
        for name in (*Reader._LISTS, *Reader._STRINGS):
            self.assertEqual(dict(getattr(loaded, name).items()), dict(getattr(reader, name)), name)
        self.assertEqual(set(loaded.known), set(reader.known))
        self.assertEqual({k: list(v) for k, v in loaded._tail_counts().items()}, reader._tail_counts())
        return loaded

    def test_ranked_list(self):
        known = {('人気', 'にんき'): 1, ('人気', 'ひとけ'): 5, ('廊下', 'ろうか'): 2, ('小屋', 'こや'): 3,
                 ('棚', 'たな'): 4, ('本棚', 'ほんだな'): 6, ('箱', 'はこ'): 7}
        loaded = self.check(Reader(known, tokenizer=ToyTokenizer()))
        self.assertEqual(loaded.known[('人気', 'ひとけ')], 5)

    def test_set_and_no_list(self):
        self.check(Reader({('人気', 'にんき'), ('廊下', 'ろうか')}, tokenizer=ToyTokenizer()))
        loaded = self.check(Reader(tokenizer=ToyTokenizer()))  # JMdict's pairs
        self.assertIsNotNone(loaded.plain)
