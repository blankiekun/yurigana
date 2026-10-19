"""Tests for yurigana.Reader with a toy tokenizer (and Sudachi when installed)."""
import unittest

from yurigana import Reader, Word, aozora_text
from yurigana.reader import PlainReadings, rendaku
from yurigana.reading_model import ReadingModel, build_form
from yurigana.tokens import Token

try:
    import sudachipy  # noqa: F401
except ImportError:
    sudachipy = None

# word -> (dictionary form, Sudachi's reading in katakana, part of speech)
LEXICON = {'人気': ('人気', 'ニンキ', '名詞'), '人家': ('人家', 'ニンキ', '名詞'), 'のない': ('のない', '', '助詞'),
           '廊下': ('廊下', 'ロウカ', '名詞'), '宇宙': ('宇宙', 'ウチュウ', '名詞'), '行っ': ('行く', 'イッ', '動詞'),
           '学校': ('学校', 'ガッコウ', '名詞'), '私': ('私', 'ワタクシ', '代名詞'), 'た': ('た', 'タ', '助動詞'), 'がない': ('がない', '', '助詞'),
           '身の上': ('身の上', 'ミノウエ', '名詞'), '話': ('話', 'ハナシ', '名詞'), '彼': ('彼', 'カレ', '代名詞'),
           '一': ('一', 'イチ', '名詞'), '枚': ('枚', 'マイ', '名詞'), '日本': ('日本', 'ニッポン', '名詞'),
           'プレハブ': ('プレハブ', 'プレハブ', '名詞'), '小屋': ('小屋', 'コヤ', '名詞'), 'この': ('この', 'コノ', '連体詞'),
           '箱': ('箱', 'バコ', '名詞'), '深い': ('深い', 'ブカイ', '形容詞'), '沿い': ('沿い', 'ソイ', '接尾辞'),
           '睡眠不足': ('睡眠不足', 'スイミンフソク', '名詞'), '棚': ('棚', 'ダナ', '名詞')}


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

    def test_compounds_the_list_reads_as_one_word(self):
        known = {('身の上話', 'みのうえばなし'), ('身の上', 'みのうえ'), ('話', 'はなし'), ('彼の', 'かの'), ('彼', 'かれ'),
                 ('一枚', 'いちまい')}
        words = self.reader(known).read('身の上話。彼の話。一枚。')
        self.assertEqual(words[0], Word(0, 4, '身の上話', 'みのうえばなし', 'only', 1.0))
        self.assertEqual([w.form for w in words[1:]], ['彼', '話', '一', '枚'])  # no particles, no number + counter
        hints = []
        text = aozora_text('身の上《みのうえ》話', None, hints)
        self.assertEqual([w.form for w in self.reader(known).read(text, hints)], ['身の上', '話'])
        reader = self.reader(known)
        tokens = list(reader.tokenizer.tokens('身の上話'))
        self.assertIsNone(reader._compound(tokens, 0, {}, [(0, 3, 4, 'みのうえ', 'ばなし')]))  # inside a counter span

    def test_default_readings_replace_sudachis(self):
        words = self.reader({('日本', 'にほん'), ('日本', 'にっぽん')}).read('日本。')
        self.assertEqual(words[0], Word(0, 2, '日本', 'にほん', 'default', None))

    def test_defaults_batch_2(self):
        known = {('箱', 'はこ'), ('深い', 'ふかい'), ('沿い', 'ぞい')}
        words = self.reader(known).read('箱。深い。沿い。')
        self.assertEqual([w[3:5] for w in words], [('はこ', 'default'), ('ふかい', 'default'), ('ぞい', 'default')])

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

    def test_conjugated_word_takes_the_listed_reading_sudachi_says(self):
        reader = self.reader({('行く', 'いく'), ('行く', 'ゆく')})
        self.assertEqual(reader.read('行った。')[0], Word(0, 2, '行く', 'いく', 'dictionary', None))
        self.assertEqual(self.reader({('行く', 'ゆく'), ('行く', 'おこなう')}).read('行った。')[0][3:5], (None, 'dictionary'))

    def test_default_replaces_a_wrong_sudachi_reading(self):
        self.assertEqual(self.reader().read('私。')[0], Word(0, 1, '私', 'わたし', 'default', None))
        hints = []
        text = aozora_text('私《わたくし》', None, hints)
        self.assertEqual(self.reader().read(text, hints)[0][3:5], ('わたくし', 'ruby'))  # ruby still wins
        self.assertEqual(self.reader({('私', 'わたくし'), ('私', 'あたし')}).read('私。')[0][3:5],
                         ('わたくし', 'dictionary'))  # わたし not listed

    def test_rendaku_by_the_lists_compounds(self):
        known = {('小屋', 'こや'), ('棚', 'たな'), ('睡眠不足', 'すいみんぶそく'),
                 *((head + '小屋', reading + 'ごや') for head, reading in
                   (('犬', 'いぬ'), ('山', 'やま'), ('牛', 'うし'), ('馬', 'うま'), ('豚', 'ぶた')))}
        reader = self.reader(known)
        self.assertEqual([w[2:5] for w in reader.read('プレハブ小屋。この棚。睡眠不足。')],
                         [('小屋', 'ごや', 'only'), ('棚', 'たな', 'dictionary'), ('睡眠不足', 'すいみんぶそく', 'only')])
        self.assertEqual(reader.read('小屋。')[0].reading, 'こや')  # no first part
        self.assertEqual(reader.read('プレハブ棚。')[0].reading, 'だな')  # no listed compounds to go by: Sudachi's
        self.assertEqual(rendaku('たな'), 'だな')
        self.assertIsNone(rendaku('かぜ'))  # Lyman's law
        self.assertIsNone(rendaku('ろく'))

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

    def test_one_x(self):
        known = {('一昨日', 'おととい'): 7614, ('一昨日', 'いっさくじつ'): 7614, ('一日中', 'いちにちじゅう'): 5374,
                 ('一日', 'いちにち'): 1344, ('一日', 'ついたち'): 29440, ('一重', 'ひとえ'): 41973,
                 ('一重', 'いちえ'): 315317, ('一票', 'いっぴょう'): 30666, ('一章', 'かずあき'): 56197,
                 ('一千万', 'いっせんまん'): 39496, ('四月一日', 'わたぬき'): 100000}
        reader = Reader(known)
        for text, form, reading in (('一昨日来た。', '一昨日', 'おととい'), ('一日中家にいた。', '一日中', 'いちにちじゅう'),
                                    ('一日で読んだ。', '一日', 'いちにち'), ('四月一日に会う。', '一日', 'ついたち'),
                                    ('一重の着物', '一重', 'ひとえ'), ('清き一票を。', '一票', 'いっぴょう'),
                                    ('一千万の人', '一千万', 'いっせんまん'), ('一睨みした。', '一', 'ひと'),
                                    ('一ト月たった。', '一', 'ひ'), ('一と息入れた。', '一', 'ひ'), ('一たい何だ。', '一', 'いっ')):
            with self.subTest(text):
                self.assertIn((form, reading), [(w.form, w.reading) for w in reader.read(text)])
        self.assertNotIn('一章', [w.form for w in reader.read('一章を読む。')])  # a name's reading: not joined
        self.assertNotIn('四月一日', [w.form for w in reader.read('四月一日に会う。')])  # a date, not わたぬき


if __name__ == '__main__':
    unittest.main()
