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
           '睡眠不足': ('睡眠不足', 'スイミンフソク', '名詞'), '棚': ('棚', 'ダナ', '名詞'), '泳げ': ('泳げる', 'オヨゲ', '動詞'),
           '身体': ('身体', 'シンタイ', '名詞'), '鬼': ('鬼', 'キ', '名詞'), '善': ('善', 'ゼン', '名詞'),
           '日本一': ('日本一', 'ニッポンイチ', '名詞'), '日本銀行': ('日本銀行', 'ニッポンギンコウ', '名詞'),
           '日本の伝統': ('日本の伝統', 'ニッポンノデントウ', '名詞'), '気味': ('気味', 'キミ', '名詞'),
           '風邪': ('風邪', 'カゼ', ('名詞', '普通名詞', '一般', '*', '*', '*')),
           '太り': ('太る', 'フトリ', ('動詞', '一般', '*', '*', '五段-ラ行', '連用形-一般')), 'なる': ('なる', 'ナル', '動詞'),
           '柚木': ('柚木', 'ユズキ', ('名詞', '固有名詞', '人名', '姓', '*', '*')),
           '姫野': ('姫野', 'ヒメノ', ('名詞', '固有名詞', '人名', '姓', '*', '*')),
           '芽衣': ('芽衣', 'ガイ', ('名詞', '固有名詞', '人名', '名', '*', '*'))}


class ToyTokenizer:
    def tokens(self, text):
        i = 0
        while i < len(text):
            word = next((w for w in sorted(LEXICON, key=len, reverse=True) if text.startswith(w, i)), text[i])
            form, reading, pos = LEXICON.get(word, (word, '', '助詞'))
            if word not in '。、\n':
                yield Token(word, form, form, pos if isinstance(pos, tuple) else (pos,) + ('*',) * 5, reading, i)
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
        # from default-readings.tsv (NDL's ruby): fiction's からだ, when the list has it
        self.assertEqual(self.reader({('身体', 'からだ'), ('身体', 'しんたい')}).read('身体。')[0].reading, 'からだ')
        self.assertEqual(self.reader({('身体', 'しんたい')}).read('身体。')[0].reading, 'しんたい')

    def test_defaults_batch_2(self):
        known = {('箱', 'はこ'), ('深い', 'ふかい'), ('沿い', 'ぞい')}
        words = self.reader(known).read('箱。深い。沿い。')
        self.assertEqual([w[3:5] for w in words], [('はこ', 'default'), ('ふかい', 'default'), ('ぞい', 'default')])

    def test_oni_is_oni_alone_and_ki_glued(self):
        words = self.reader({('鬼', 'おに'), ('善', 'ぜん')}).read('鬼。善鬼。')
        self.assertEqual([w[3:5] for w in words if w.form == '鬼'], [('おに', 'default'), ('き', 'dictionary')])

    def test_nippon_in_compounds_is_nihon_unless_listed_only_so(self):
        known = {('日本一', 'にっぽんいち'), ('日本一', 'にほんいち'), ('日本銀行', 'にっぽんぎんこう')}
        words = self.reader(known).read('日本一。日本銀行。日本の伝統。')
        self.assertEqual([w[3:5] for w in words], [('にほんいち', 'default'), ('にっぽんぎんこう', 'only'),
                                                   ('にほんのでんとう', 'default')])

    def test_kimi_is_gimi_after_a_noun_or_a_verb_stem(self):
        words = self.reader({('気味', 'きみ'), ('気味', 'ぎみ')}).read('風邪気味。太り気味。なる気味。気味。')
        self.assertEqual([w[3:5] for w in words if w.form == '気味'], [('ぎみ', 'rule'), ('ぎみ', 'rule'), ('きみ', 'dictionary'),
                                                                     ('きみ', 'dictionary')])

    def test_a_names_ruby_is_carried_to_its_later_bare_occurrences(self):
        def read(marked, carry, known=None):
            hints = []
            text = aozora_text(marked, None, hints)
            return [w[3:5] for w in self.reader(known).read(text, hints, carry)]
        self.assertEqual(read('柚木《ゆき》。柚木。', None), [('ゆき', 'ruby'), ('ゆずき', 'dictionary')])
        self.assertEqual(read('柚木《ゆき》。柚木。', {}), [('ゆき', 'ruby'), ('ゆき', 'book')])
        # a name's ruby is taken even when its kanji don't spell it (only with carry: no change otherwise)
        self.assertEqual(read('柚木《ひなた》。柚木。', None)[0], ('ゆずき', 'dictionary'))
        self.assertEqual(read('柚木《ひなた》。柚木。', {}), [('ひなた', 'ruby'), ('ひなた', 'book')])
        carry = {}
        read('柚木《ゆき》。', carry)
        self.assertEqual(read('柚木。', carry), [('ゆき', 'book')])  # across a book's texts
        # never a common word, nor after flavour or a second reading
        self.assertEqual(read('宇宙《うちゅう》。宇宙。', {})[1], ('うちゅう', 'dictionary'))
        self.assertEqual(read('柚木《ゆき》。柚木《ユキ》。柚木。', {})[2], ('ゆずき', 'dictionary'))
        self.assertEqual(read('柚木《ゆき》。柚木《ゆず》。柚木。', {})[2], ('ゆずき', 'dictionary'))
        self.assertEqual(read('柚木《あいつ》。柚木。', {}), [('ゆずき', 'dictionary')] * 2)
        # ruby over a two-token full name, split where Sudachi's reading of one part fits
        self.assertEqual(read('姫野芽衣《ひめのめい》。芽衣。姫野芽衣。', {}),
                         [('ひめの', 'ruby'), ('めい', 'ruby'), ('めい', 'book'), ('ひめの', 'book'), ('めい', 'book')])
        self.assertEqual(read('姫野芽衣《ひめのめい》。芽衣。', None)[1:], [('がい', 'dictionary')] * 2)
        # a form the list doesn't know is read like a name; one it knows isn't
        known = {('人気', 'にんき'), ('人気', 'ひとけ')}
        self.assertEqual(read('人家《じんか》。人家。', {}, known), [('じんか', 'ruby'), ('じんか', 'book')])
        self.assertEqual(read('人気《ひとけ》。人気。', {}, known)[1][1], 'dictionary')

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

    def test_conjugated_word_the_list_lacks_takes_sudachis_reading(self):
        reader = self.reader({('泳ぐ', 'およぐ')})
        self.assertEqual(reader.read('泳げた。')[0], Word(0, 2, '泳げる', 'およげる', 'dictionary', 0.0))  # not listed

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

    def test_certainty_hygiene(self):
        name = ('名詞', '固有名詞', '人名', '名', '*', '*')
        noun = ('名詞', '普通名詞', '一般', '*', '*', '*')

        class Fixed:
            def tokens(self, text):
                return [Token('健', '健', '健', name, 'ケン', 0), Token('珈琲', '珈琲', '珈琲', noun, 'コーヒー', 1),
                        Token('鵝毛', '鵝毛', '鵝毛', noun, '鵝毛', 3), Token('廊下', '廊下', '廊下', noun, 'ロウカ', 5),
                        Token('学校', '学校', '学校', noun, 'ガッコウ', 7)]
        known = {('健', 'けん'), ('珈琲', 'コーヒー'), ('廊下', 'ろうか'), ('学校', 'がくこう')}
        words = Reader(known, tokenizer=Fixed()).read('健珈琲鵝毛廊下学校')
        self.assertEqual(words[0][2:], ('健', 'けん', 'only', 1.0))  # names keep their source
        self.assertEqual([w.reading for w in words[1:3]], ['こーひー', None])  # ー is kept; an unknown word's kanji is not
        self.assertEqual(words[3][3:], ('ろうか', 'only', 1.0))
        self.assertEqual(words[4][3:], ('がっこう', 'dictionary', 0.0))  # not a listed reading
        hints = []
        text = aozora_text('健《たけし》珈琲鵝毛廊下学校', None, hints)
        self.assertEqual(Reader(known | {('健', 'たけし')}, tokenizer=Fixed()).read(text, hints)[0][3:], ('たけし', 'ruby', 1.0))

    def test_plain_readings(self):
        plain = PlainReadings()
        for pair in (('人間', 'にんげん'), ('学校', 'がっこう'), ('人々', 'ひとびと'), ('お茶', 'おちゃ'), ('行く', 'いく')):
            self.assertIn(pair, plain)
        for pair in (('宇宙', 'そら'), ('今日', 'きょう'), ('お茶', 'ちゃ'), ('本気', 'まじ')):
            self.assertNotIn(pair, plain)


@unittest.skipUnless(sudachipy, 'needs SudachiPy and SudachiDict-full')
class SudachiReaderTest(unittest.TestCase):
    def test_lemma_with_extra_kana(self):
        # Sudachi's lemma for the misspelt 可愛いく is 可愛いい (可愛 read かわ); the list's 可愛い holds the い
        reader = Reader(known={('可愛い', 'かわいい'), ('可愛い', 'かあいい'), ('終わる', 'おわる')})
        self.assertIn('可愛[かわい]いくて', reader.furigana('子猫が可愛いくて仕方ない。'))
        word = next(w for w in reader.read('子猫が可愛いくて仕方ない。') if w.form.startswith('可愛'))
        self.assertEqual(word[2:4], ('可愛い', 'かわいい'))
        # an older okurigana (終る) is not the normalized form plus kana: left alone
        self.assertNotEqual(next(w for w in reader.read('仕事が終った。') if w.form.startswith('終')).form, '終わる')
        # nor a noun with older okurigana (先き): its surface is the lemma
        reader = Reader(known={('先', 'さき'), ('先', 'せん')})
        self.assertIn('先[さ]き', reader.furigana('一歩先きを行く。'))

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
