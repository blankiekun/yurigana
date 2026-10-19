"""Tests for yurigana.Reader with a toy tokenizer (and Sudachi when installed)."""
import unittest

from yurigana import Reader, Word, aozora_text
from yurigana.reader import PlainReadings
from yurigana.reading_model import ReadingModel, build_form
from yurigana.tokens import Token

try:
    import sudachipy  # noqa: F401
except ImportError:
    sudachipy = None

# word -> (dictionary form, Sudachi's reading in katakana, part of speech)
LEXICON = {'人気': ('人気', 'ニンキ', '名詞'), '人家': ('人家', 'ニンキ', '名詞'), 'のない': ('のない', '', '助詞'),
           '廊下': ('廊下', 'ロウカ', '名詞'), '宇宙': ('宇宙', 'ウチュウ', '名詞'), '行っ': ('行く', 'イッ', '動詞'),
           '学校': ('学校', 'ガッコウ', '名詞'), '私': ('私', 'ワタクシ', '代名詞'), 'た': ('た', 'タ', '助動詞'), 'がない': ('がない', '', '助詞')}


class ToyTokenizer:
    def tokens(self, text):
        i = 0
        while i < len(text):
            word = next((w for w in sorted(LEXICON, key=len, reverse=True) if text.startswith(w, i)), text[i])
            form, reading, pos = LEXICON.get(word, (word, '', '助詞'))
            if word not in '。、\n':
                yield Token(word, form, form, (pos,) + ('*',) * 5, reading, i)
            i += len(word)


def entry(hitoke_feature):
    """A table entry that reads ひとけ before `hitoke_feature`, にんき otherwise."""
    from collections import Counter
    import math
    return build_form({'ひとけ': Counter({hitoke_feature: 50}), 'にんき': Counter({'R1:は': 50})},
                      [hitoke_feature, 'R1:は'], [math.log(0.4), math.log(0.6)])


class ReaderTest(unittest.TestCase):
    def reader(self, known=None):
        reader = Reader(known, tokenizer=ToyTokenizer())
        reader.model = ReadingModel({'人家': entry('R1:がない')})
        return reader

    def test_sources_in_order(self):
        hints = []
        text = aozora_text('宇宙《うちゅう》の人気のない廊下。\n人家がない。\n人家。', None, hints)
        words = self.reader().read(text, hints)
        self.assertEqual(words[0], Word(0, 2, '宇宙', 'うちゅう', 'ruby', 1.0))
        self.assertEqual(words[1][3:5], ('ひとけ', 'rule'))
        self.assertEqual(words[2], Word(8, 10, '廊下', 'ろうか', 'dictionary', None))
        self.assertEqual(words[3][3:5], ('ひとけ', 'model'))
        self.assertGreater(words[3].certainty, 0.7)
        self.assertEqual(words[4], Word(19, 21, '人家', 'にんき', 'dictionary', 0.6))  # its share in the table's prior

    def test_flavour_ruby_is_never_a_reading(self):
        for marked in ('宇宙《そら》', '宇宙《ソラ》'):
            hints = []
            text = aozora_text(marked, None, hints)
            self.assertEqual(self.reader().read(text, hints)[0][3:5], ('うちゅう', 'dictionary'))

    def test_a_list_gives_only_readings_and_limits_ruby(self):
        known = {('人気', 'にんき'), ('人気', 'ひとけ'), ('行く', 'いく'), ('廊下', 'ろうか'), ('人家', 'にんき'),
                 ('人家', 'ひとけ')}
        reader = self.reader(known)
        words = reader.read('学校へ行った。廊下。')
        self.assertEqual([w[2:5] for w in words], [('学校', 'がっこう', 'dictionary'), ('行く', 'いく', 'only'),
                                                    ('廊下', 'ろうか', 'only')])
        self.assertEqual(reader.read('人家。')[0][3:6], ('にんき', 'dictionary', 0.6))
        hints = []
        text = aozora_text('人気《ひとき》', None, hints)
        self.assertEqual(reader.read(text, hints)[0][3:5], ('にんき', 'dictionary'))  # not listed

    def test_default_replaces_a_wrong_sudachi_reading(self):
        self.assertEqual(self.reader().read('私。')[0], Word(0, 1, '私', 'わたし', 'default', None))
        hints = []
        text = aozora_text('私《わたくし》', None, hints)
        self.assertEqual(self.reader().read(text, hints)[0][3:5], ('わたくし', 'ruby'))  # ruby still wins
        self.assertEqual(self.reader({('私', 'わたくし'), ('私', 'あたし')}).read('私。')[0][3:5],
                         ('わたくし', 'dictionary'))  # わたし not listed

    def test_plain_readings(self):
        plain = PlainReadings()
        for pair in (('人間', 'にんげん'), ('学校', 'がっこう'), ('人々', 'ひとびと'), ('お茶', 'おちゃ'), ('行く', 'いく')):
            self.assertIn(pair, plain)
        for pair in (('宇宙', 'そら'), ('今日', 'きょう'), ('お茶', 'ちゃ'), ('本気', 'まじ')):
            self.assertNotIn(pair, plain)


@unittest.skipUnless(sudachipy, 'needs SudachiPy and SudachiDict-full')
class SudachiReaderTest(unittest.TestCase):
    def test_defaults(self):
        hints = []
        text = aozora_text('夜の公園は人気がなく、静かだった。｜宇宙《そら》を見る。\n学校へ行《い》った。', None, hints)
        words = {w.form: w for w in Reader().read(text, hints)}
        self.assertEqual(words['人気'][3:5], ('ひとけ', 'rule'))
        self.assertEqual(words['宇宙'][3:5], ('うちゅう', 'dictionary'))
        self.assertEqual(words['行く'][3:5], ('いく', 'ruby'))
        self.assertEqual(text[words['公園'].start:words['公園'].end], '公園')


if __name__ == '__main__':
    unittest.main()
