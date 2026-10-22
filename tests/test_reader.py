"""Tests for yurigana.Reader with a toy tokenizer (and Sudachi when installed)."""
import json
import os
import tempfile
import unittest
import zipfile

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
           '身体': ('身体', 'シンタイ', '名詞'), '鬼': ('鬼', 'キ', '名詞'), '擦る': ('擦る', 'スル', '動詞'), '素': ('素', 'モト', '名詞'), '善': ('善', 'ゼン', '名詞'),
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

    def test_extra_readings_cost_the_only_reading(self):
        # 擦る: a list giving only こする; an extra-readings.tsv pair (made up here) keeps it `single` but not `only`
        from unittest import mock
        with mock.patch('yurigana.reader.extra_readings', return_value={('擦る', 'する')}):
            reader = self.reader({('擦る', 'こする'), ('擦る', 'する')})
        self.assertEqual((reader.single, reader.only), ({'擦る': 'こする'}, {}))
        self.assertEqual(self.reader({('擦る', 'こする'), ('擦る', 'する')}).only, {})

    def test_casual_spellings_dont_cost_the_only_reading(self):
        # the list's casual spellings of JMdict's reading (T510); other readings JMdict lacks still count (鳥 ちょう)
        from yurigana.kana import colloquial
        reader = self.reader({('長い', 'ながい'), ('長い', 'なっがい'), ('当たり前', 'あたりまえ'), ('当たり前', 'あたりめえ'),
                              ('雰囲気', 'ふんいき'), ('雰囲気', 'ふいんき'), ('鳥', 'とり'), ('鳥', 'ちょう'),
                              ('三つ目', 'みつめ'), ('三つ目', 'みっつめ')})
        self.assertEqual(reader.only, {'長い': 'ながい', '当たり前': 'あたりまえ', '雰囲気': 'ふんいき'})
        for casual, standard in [('きずく', 'きづく'), ('ぜいいん', 'ぜんいん'), ('なげえ', 'ながい'), ('おんなじ', 'おなじ'),
                                 ('いきよい', 'いきおい'), ('ほおって', 'ほうって'), ('しろと', 'しろうと')]:
            self.assertTrue(colloquial(casual, standard), casual)
        for other, standard in [('ちょう', 'とり'), ('が', 'かわ'), ('はらえ', 'はらい'), ('なかのいい', 'なかのよい'), ('り', 'りん')]:
            self.assertFalse(colloquial(other, standard), other)

    def test_shared_conjugation(self):
        from yurigana.reader import _shared_conjugation
        readings = {'行う': ['おこなう'], '行く': ['いく', 'ゆく'], '分かる': ['わかる'], '分かつ': ['わかつ'], '待つ': ['まつ']}
        ranks = {('行う', 'おこなう'): 668, ('行く', 'いく'): 50, ('分かる', 'わかる'): 278, ('分かつ', 'わかつ'): 19788}
        self.assertTrue(_shared_conjugation('行っ', '行う', readings, ranks))
        self.assertFalse(_shared_conjugation('分かっ', '分かる', readings, ranks))  # 分かつ is 70 times rarer
        self.assertFalse(_shared_conjugation('待っ', '待つ', readings, ranks))
        self.assertFalse(_shared_conjugation('行う', '行う', readings, ranks))

    def test_sources_in_order(self):
        hints = []
        text = aozora_text('宇宙《うちゅう》の人気のない廊下。\n人家がない。\n人家。', None, hints)
        reader = self.reader()
        reader.known = reader.known | {('人家', 'ひとけ'), ('人家', 'にんき')}  # the toy model's readings
        reader.jmdict = {**reader.jmdict, '人家': ['じんか', 'にんき']}  # the toy tokenizer's reading isn't JMdict's
        words = reader.read(text, hints)
        self.assertEqual(words[0], Word(0, 2, '宇宙', 'うちゅう', 'ruby', 1.0))
        self.assertEqual(words[1][3:5], ('ひとけ', 'rule'))
        self.assertEqual(words[2], Word(8, 10, '廊下', 'ろうか', 'only', 1.0))  # JMdict's one reading
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

    def test_jmdict_checks_the_list(self):
        known = {('廊下', 'ろうげ'), ('室子', 'さやこ'), ('学校', 'がっこう'), ('彼話', 'かのわ'), ('身の上話', 'みのうえばなし')}
        reader = self.reader(known)
        # 廊下 ろうげ isn't JMdict's; 室子 isn't in JMdict at all (the list's reading stays, `only` unless Sudachi tags it a name)
        self.assertEqual(reader.only, {'室子': 'さやこ', '学校': 'がっこう', '彼話': 'かのわ', '身の上話': 'みのうえばなし'})
        self.assertEqual(reader.read('廊下')[0][3:5], ('ろうか', 'dictionary'))
        # a joined form JMdict lacks is joined, but not shown
        self.assertEqual(reader.read('彼話')[0], Word(0, 2, '彼話', 'かのわ', 'dictionary', None))
        self.assertEqual(reader.read('身の上話')[0], Word(0, 4, '身の上話', 'みのうえばなし', 'only', 1.0))

    def test_default_readings_replace_sudachis(self):
        words = self.reader({('日本', 'にほん'), ('日本', 'にっぽん')}).read('日本。')
        self.assertEqual(words[0], Word(0, 2, '日本', 'にほん', 'default', None))
        # from default-readings.tsv (NDL's ruby): fiction's からだ, when the list has it
        self.assertEqual(self.reader({('身体', 'からだ'), ('身体', 'しんたい')}).read('身体。')[0].reading, 'からだ')
        self.assertEqual(self.reader({('身体', 'しんたい')}).read('身体。')[0].reading, 'しんたい')

    def test_defaults_batch_2(self):
        known = {('箱', 'はこ'), ('深い', 'ふかい'), ('沿い', 'ぞい')}
        words = self.reader(known).read('箱。深い。沿い。')
        self.assertEqual([w[3:5] for w in words], [('はこ', 'rule'), ('ふかい', 'default'), ('ぞい', 'default')])

    def test_shown_defaults(self):
        # SHOWN_DEFAULTS (T320) are shown, source rule; a one-character one not glued or before katakana
        known = {('他', 'ほか'), ('他', 'た'), ('都', 'みやこ'), ('都', 'と'), ('身体', 'からだ'), ('身体', 'しんたい')}
        reader = Reader(known)
        self.assertEqual(reader.read('身体が熱い。')[0][3:6], ('からだ', 'rule', 1.0))
        self.assertEqual([w[3:5] for w in reader.read('この都を守る。') if w.form == '都'], [('みやこ', 'default')])  # not shown
        self.assertEqual([w[3:5] for w in reader.read('他クラスの子。') if w.form == '他'], [('ほか', 'default')])

    def test_defaults_from_opus_nominations(self):
        known = {('擦る', 'こする'), ('擦る', 'する'), ('素', 'す'), ('素', 'もと')}
        words = self.reader(known).read('擦る。素。')
        self.assertEqual([w[3:5] for w in words if w.form in ('擦る', '素')], [('こする', 'default'), ('す', 'default')])
        # only Sudachi's reading of the plain form is replaced: the list must give the new one
        self.assertEqual(self.reader({('擦る', 'する')}).read('擦る。')[0].reading, 'する')

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
        self.assertEqual(read('宇宙《うちゅう》。宇宙。', {})[1], ('うちゅう', 'only'))
        self.assertEqual(read('柚木《ゆき》。柚木《ユキ》。柚木。', {})[2], ('ゆずき', 'dictionary'))
        self.assertEqual(read('柚木《ゆき》。柚木《ゆず》。柚木。', {})[2], ('ゆずき', 'dictionary'))
        self.assertEqual(read('柚木《あいつ》。柚木。', {}), [('ゆずき', 'dictionary')] * 2)
        self.assertEqual(read('柚木《こっち》。柚木。', {}), [('ゆずき', 'dictionary')] * 2)
        # a name rubied after bare use: its earlier bare occurrences in the same text too (2+ characters)
        self.assertEqual(read('柚木。柚木《ゆき》。柚木。', {}), [('ゆき', 'book'), ('ゆき', 'ruby'), ('ゆき', 'book')])
        self.assertEqual(read('柚木。柚木《ゆき》。', None)[0], ('ゆずき', 'dictionary'))
        self.assertEqual(read('柚木。柚木《ゆき》。柚木《ゆず》。', {})[0], ('ゆき', 'book'))
        # large kana in a name's ruby (old-style typesetting) take the small-kana reading
        self.assertEqual(read('劉《りゆう》。劉。', {}), [('りゅう', 'ruby'), ('りゅう', 'book')])
        # 妾《わらわ》 is carried like a name; another of its readings isn't
        self.assertEqual(read('妾《わらわ》は。妾は。', {})[1][1], 'book')
        self.assertEqual(read('妾《わらわ》は。妾は。', {})[1][0], 'わらわ')
        self.assertNotEqual(read('妾《めかけ》は。妾は。', {})[1][1], 'book')
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
            self.assertEqual(self.reader().read(text, hints)[0][3:5], ('うちゅう', 'only'))

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
        self.assertEqual(reader.read('行った。')[0], Word(0, 2, '行く', 'いく', 'only', 1.0))  # dominant-readings.tsv
        self.assertEqual(self.reader({('行く', 'ゆく'), ('行く', 'おこなう')}).read('行った。')[0][3:5], (None, 'dictionary'))

    def test_conjugated_word_the_list_lacks_takes_sudachis_reading(self):
        reader = self.reader({('泳ぐ', 'およぐ')})
        self.assertEqual(reader.read('泳げた。')[0], Word(0, 2, '泳げる', 'およげる', 'rule', 1.0))  # not listed; shown: 泳ぐ's only reading

    def test_default_replaces_a_wrong_sudachi_reading(self):
        self.assertEqual(self.reader().read('私。')[0], Word(0, 1, '私', 'わたし', 'rule', 1.0))  # SHOWN_DEFAULTS
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
        # 小屋 is VOICED_AFTER_NOUN's (T460) now
        self.assertEqual([w[2:5] for w in reader.read('プレハブ小屋。この棚。睡眠不足。')],
                         [('小屋', 'ごや', 'rule'), ('棚', 'たな', 'dictionary'), ('睡眠不足', 'すいみんぶそく', 'only')])
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
        # a name JMdict lacks: the list's one reading is a guess between a name's readings, so not shown (T42)
        self.assertEqual(words[0][2:4], ('健', 'けん'))
        self.assertEqual(words[0].source, 'dictionary')
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


@unittest.skipUnless(sudachipy, 'needs SudachiPy and SudachiDict-core')
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

    def test_parts_reading_is_shown(self):
        # a form the list lacks, read as its parts are read alone: a kanji compound, a potential, a compound verb
        reader = Reader()
        words = {w.form: w[2:] for t in ('女性陣が集まった。', '彼に会えるなら歌い継ぐ。', '為せる。') for w in reader.read(t)}
        self.assertEqual(words['女性陣'], ('女性陣', 'じょせいじん', 'rule', 1.0))
        self.assertEqual(words['会える'], ('会える', 'あえる', 'rule', 1.0))
        self.assertEqual(words['歌い継ぐ'], ('歌い継ぐ', 'うたいつぐ', 'rule', 1.0))
        self.assertEqual(words['為せる'][2:], ('dictionary', 0.0))  # also 為る's causative: not shown

    def test_glued_table(self):
        # a made-up glued table: forms Sudachi cuts into words, each word taking its slice, never shown
        path = os.path.join(tempfile.mkdtemp(), 'glued.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'水竜': 'すいりゅう', '炎弾': 'えんだん', '竜炎': 'りゅうほむら'}, f, ensure_ascii=False)
        known = {('水', 'みず'), ('竜', 'りゅう'), ('炎', 'ほのお'), ('弾', 'たま'), ('弾', 'だん')}
        reader = Reader(known=known, glued=path)
        words = {w.form: w[3:] for w in reader.read('巨大な水竜が炎弾を放った。')}
        self.assertEqual(words['水'], ('すい', 'default', None))
        self.assertEqual(words['竜'], ('りゅう', 'only', 1.0))  # its slice is its own reading: left as is
        self.assertEqual(words['炎'], ('えん', 'default', None))
        # ruby over the form wins; a reading no slice spells (ほむら isn't a reading of 炎 here) isn't taken
        self.assertEqual(reader.read('水竜だ', [(0, 2, 'みずりゅう')])[0].reading, 'みず')
        self.assertEqual([w.reading for w in reader.read('竜炎だ')], [w.reading for w in Reader(known=known).read('竜炎だ')])
        # a missing file is skipped; the shipped table (glued-readings.json, which has 水竜) still applies
        self.assertEqual(Reader(known=known, glued=path + '.missing').read('水竜')[0].reading, 'すい')

    def test_term_dictionary(self):
        # a made-up Yomitan term dictionary: words the list and JMdict lack (source 'terms', never shown)
        path = os.path.join(tempfile.mkdtemp(), 'terms.zip')
        rows = [['女剣豪', 'おんなけんごう'], ['女騎士団', 'おんなきしだん'], ['鬩霆', 'げきてい'], ['剣豪', 'つるぎ']]
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('index.json', json.dumps({'title': 'test', 'format': 3}))
            archive.writestr('term_bank_1.json', json.dumps([row + ['', '', 0, [], 0, ''] for row in rows], ensure_ascii=False))
        known = {('剣豪', 'けんごう'), ('女', 'おんな'), ('女', 'じょ'), ('騎士', 'きし')}
        reader = Reader(known=known, terms=path)
        self.assertNotIn('剣豪', reader.terms)  # listed
        # a compound Sudachi splits (女|剣豪 じょけんごう): one Word with the dictionary's reading
        self.assertIn(('女剣豪', 'おんなけんごう', 'terms', None), [w[2:] for w in reader.read('女剣豪が来た。')])
        # one the tokens already read that way stays split (word lists keep their rows)
        self.assertNotIn('女騎士団', [w.form for w in reader.read('女騎士団が来た。')])
        # a word Sudachi has no reading for, and ruby over it the dictionary gives (other ruby isn't taken)
        self.assertIn(('鬩霆', 'げきてい', 'terms', None), [w[2:] for w in reader.read('彼は鬩霆した。')])
        self.assertIn(('鬩霆', 'げきてい', 'terms', None), [w[2:] for w in reader.read('彼は鬩霆した。', [(2, 4, 'げきてい')])])
        self.assertEqual(reader.read('彼は鬩霆した。', [(2, 4, 'かみなり')])[1].reading, 'げきてい')
        # without dictionaries, nothing changes
        self.assertNotIn('terms', [w.source for w in Reader(known=known).read('女剣豪が鬩霆した。')])

    def test_name_dictionary(self):
        # JMnedict's shape (yomitan-import): the readings are the glosses. Shows a name nothing else shows when the
        # dictionaries read it one way only, and that way; never changes a reading, never other words (今日)
        folder = tempfile.mkdtemp()

        def names(name, rows):
            path = os.path.join(folder, name)
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('index.json', json.dumps({'title': 'JMnedict', 'format': 3}))
                archive.writestr('term_bank_1.json', json.dumps([[form, '', 'place', '', 0, readings, 1, '']
                                                                 for form, readings in rows], ensure_ascii=False))
            return path
        one = names('one.zip', [['姫路', ['ひめじ']], ['今日', ['こんにち']], ['玲奈', ['れいな', 'れな']]])
        known = {('姫路', 'ひめじ'), ('姫路', 'ひめろ'), ('玲奈', 'れいな'), ('玲奈', 'れな')}

        def word(reader, text):
            return next((w.form, w.reading, w.source) for w in reader.read(text) if w.form == text[:2])
        self.assertEqual(word(Reader(known=known), '姫路に行った。')[2], 'dictionary')
        reader = Reader(known=known, names=one)
        self.assertEqual(word(reader, '姫路に行った。'), ('姫路', 'ひめじ', 'only'))
        self.assertEqual(word(reader, '玲奈が笑う。')[2], 'dictionary')  # two readings
        self.assertNotEqual(word(reader, '今日は晴れ。')[1:], ('こんにち', 'only'))
        # nor under the author's ruby over part of it
        self.assertEqual(next(w.source for w in reader.read('姫路に行った。', [(0, 1, 'ひ')]) if w.form == '姫路'), 'dictionary')
        # malformed rows of an uploaded dictionary are skipped; a gloss that is a string isn't read per character
        path = os.path.join(folder, 'bad.zip')
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('index.json', json.dumps({'title': 'bad', 'format': 3}))
            archive.writestr('term_bank_1.json', json.dumps([[], ['姫路'], 5, None, {'a': 1}, ['姫路', '', '', '', 0, None],
                                                             ['姫路', '', '', '', 0, 'ひめじ']], ensure_ascii=False))
        self.assertEqual(Reader(known=known, names=path).names, {})
        # two dictionaries that read a name differently: neither shows it
        other = names('other.zip', [['姫路', ['ひめろ']]])
        self.assertEqual(word(Reader(known=known, names=[one, other]), '姫路に行った。')[2], 'dictionary')

    def test_dominant_readings(self):
        # dominant-readings.tsv: a form the list reads several ways is shown where Sudachi reads it the dominant way
        # and the token stands alone; not inside a compound Sudachi split (一|文字 いちもんじ, 背筋|運動 はいきん)
        reader = Reader()
        read = lambda text: {w.form: (w.reading, w.source) for w in reader.read(text)}
        self.assertEqual(read('俺は目を閉じた。')['目'], ('め', 'only'))
        self.assertEqual(read('ご両親は元気？')['両親'], ('りょうしん', 'only'))
        self.assertEqual(read('口を一文字に結ぶ。')['文字'][1], 'dictionary')
        self.assertEqual(read('背筋運動をした。')['背筋'][1], 'dictionary')
        # pairs admitted on labelled bare text (T430): not after a word that can head a compound (パン好き ずき)
        self.assertEqual(read('パンが好きだ。')['好き'], ('すき', 'only'))
        self.assertEqual(read('私パン好きだし。')['好き'][1], 'dictionary')
        self.assertEqual(read('ソファ代わりに使う。')['代わり'][1], 'dictionary')
        reader.dominant = {}
        self.assertEqual(read('俺の目は青い。')['目'][1], 'dictionary')

    def test_phrases_jmdict_reads_one_way(self):
        # T360: each kanji token of a phrase JMdict reads one way takes its slice of that reading, not shown;
        # not phrases books also read literally (NOT_JOINED), the tail of a longer word, or under ruby
        reader = Reader()
        read = lambda text, hints=(): [(w.form, w.reading, w.source) for w in reader.read(text, hints)]
        self.assertIn(('歩', 'ほ', 'default'), read('彼は歩を進めた。'))
        # T435: phrases in shown-idioms.tsv are shown (`rule`); a word already shown keeps its source
        self.assertIn(('異', 'い', 'rule'), read('異を唱える者'))
        self.assertIn(('首', 'くび', 'only'), read('彼は首を傾げた。'))  # TOP_READINGS (T447)
        self.assertIn(('目', 'め', 'only'), read('俺は目を閉じた。'))
        self.assertIn(('持す', 'じす', 'default'), read('満を持して登場した。'))
        self.assertIn(('頭', 'あたま', 'dictionary'), read('彼は頭を振った。'))
        self.assertIn(('甲斐', 'がい', 'dictionary'), read('からかい甲斐がある。'))
        self.assertIn(('歩', 'ふ', 'ruby'), read('歩を進めた。', [(0, 1, 'ふ')]))
        # a modifier right before the noun: literal (大きな音を上げて: おと); a kana noun before a verb doesn't glue
        self.assertIn(('音', 'おと', 'only'), read('大きな音を上げて車が走った。'))  # TOP_READINGS (T447)
        self.assertIn(('音', 'おと', 'only'), read('不気味な音を上げた。'))
        self.assertIn(('放る', 'ほうる', 'default'), read('そのまま放っておく。'))

    def test_okurigana_variant(self):
        # the list reads 幼ない only いとけない; Sudachi reads it おさない, the reading of its normalized form 幼い
        reader = Reader(known={('幼ない', 'いとけない'), ('幼い', 'おさない'), ('幼い', 'いとけない')})
        for text in ('まだ幼なくて', '幼ない子供だった。'):
            self.assertEqual(reader.read(text)[0][2:5], ('幼ない', 'おさない', 'dictionary'), text)
        self.assertIn('幼[おさ]なく', reader.furigana('まだ幼なくて'))

    def test_verbs_sudachi_takes_for_another(self):
        # T240-T242: 降りる after rain is 降る; 弾ける ひける after an instrument, はじける elsewhere; 入れる may be はいれる
        reader = Reader(known={('降りる', 'おりる'): 5, ('降る', 'ふる'): 5, ('降る', 'くだる'): 9, ('弾ける', 'はじける'): 5,
                               ('弾ける', 'ひける'): 9, ('入れる', 'いれる'): 5, ('入る', 'はいる'): 5})
        def word(text, start):
            return next(w for w in reader.read(text) if w.start == start)[2:5]
        self.assertEqual(word('雨は降り続けた。', 2), ('降る', 'ふる', 'rule'))
        self.assertEqual(word('電車を降りた。', 3), ('降りる', 'おりる', 'only'))
        self.assertEqual(word('ギターが弾けない。', 4), ('弾ける', 'ひける', 'rule'))
        self.assertEqual(word('泡が弾けた。', 2)[1], 'はじける')
        self.assertEqual(word('中には入れない。', 3), ('入れる', 'はいれる', 'dictionary'))  # T546
        self.assertEqual(word('中に入れた。', 2), ('入れる', 'いれる', 'dictionary'))
        self.assertEqual(word('中に入れてある。', 2), ('入れる', 'いれる', 'only'))  # T545
        self.assertEqual(word('気合入れていこう。', 2), ('入れる', 'いれる', 'only'))
        self.assertEqual(word('中に入れないで。', 2), ('入れる', 'いれる', 'dictionary'))
        self.assertEqual(word('箱にお茶を入れた。', 5), ('入れる', 'いれる', 'only'))
        self.assertEqual(word('手に入れた。', 2), ('入れる', 'いれる', 'only'))

    def test_split_tokens(self):
        # T271-T274: one Sudachi token that is another word here (SPLIT_TOKENS); ruby over the token wins
        reader = Reader(known={('話す', 'はなす'): 5, ('話', 'はなし'): 5, ('主に', 'おもに'): 5, ('解する', 'かいする'): 5})
        self.assertIn('話[はなし]して', reader.furigana('後でお話してもいい？'))
        self.assertIn('話[はな]しします', reader.furigana('後でお話しします。'))
        self.assertEqual(reader.read('騎士は主に忠誠を誓った。')[1][2:5], ('主', 'あるじ', 'rule'))
        self.assertEqual(reader.read('これは主に子供が使う。')[0][2:5], ('主に', 'おもに', 'only'))
        self.assertEqual(reader.read('声の主に目を向けた。')[1][2:5], ('主に', 'おもに', 'dictionary'))
        self.assertIn('解[げ]せない', reader.furigana('どうにも解せない。'))
        self.assertEqual(reader.read('意味を解せない。')[1][2:5], ('解する', 'かいする', 'only'))
        self.assertEqual(reader.read('騎士は主に忠誠を誓った。', [(3, 5, 'おもに')])[1][2:5], ('主に', 'おもに', 'ruby'))
        # T370: お供します is お + 供 とも + する; 供する without お is きょうする
        reader = Reader(known={('供', 'とも'): 5, ('供する', 'きょうする'): 5})
        self.assertIn('供[とも]します', reader.furigana('私もお供します。'))
        self.assertEqual(reader.read('食事を供した。')[1][2:5], ('供する', 'きょうする', 'only'))

    def test_lemmas_sudachi_takes_for_another_word(self):
        # T280: 宿する is 宿す (やどす), 欲す is 欲する (the list's ほりす is noise), 欲し before が is 欲しい
        reader = Reader(known={('宿す', 'やどす'): 5, ('宿す', 'しゅくす'): 9, ('宿する', 'しゅくする'): 9,
                               ('欲す', 'ほりす'): 9, ('欲する', 'ほっする'): 5, ('欲しい', 'ほしい'): 5})
        def word(text, form):
            return next(w for w in reader.read(text) if w.form.startswith(form[0]))[2:5]
        self.assertEqual(word('その身に宿した力', '宿')[:2], ('宿す', 'やどす'))
        self.assertEqual(word('彼が欲したのは力だ。', '欲'), ('欲する', 'ほっする', 'only'))
        self.assertEqual(word('子供がおもちゃを欲しがる。', '欲'), ('欲しい', 'ほしい', 'only'))
        self.assertEqual(word('平和を欲している。', '欲'), ('欲する', 'ほっする', 'only'))
        # T533: 通っ that Sudachi takes for 通う after 筋が, 火が…: 通る, shown though 通う shares the っ-form
        reader = Reader(known={('通う', 'かよう'): 5, ('通る', 'とおる'): 5})
        self.assertEqual(word('男の話は筋が通っている。', '通'), ('通る', 'とおる', 'only'))
        self.assertEqual(word('学校に通っている。', '通')[:2], ('通う', 'かよう'))
        # T547: a test passed, a name one goes by, a way just gone through
        self.assertEqual(word('書類選考に通った。', '通'), ('通る', 'とおる', 'only'))
        self.assertEqual(word('彼女は優等生で通っている。', '通'), ('通る', 'とおる', 'only'))
        self.assertEqual(word('バスで通っている。', '通')[:2], ('通う', 'かよう'))
        # T548: 行っ that Sudachi takes for 行く after an action noun as topic or object: 行う, not shown
        reader = Reader(known={('行く', 'いく'): 1, ('行う', 'おこなう'): 9})
        self.assertEqual(word('募集は行っておりません。', '行'), ('行う', 'おこなう', 'dictionary'))
        self.assertEqual(word('旅行は行った。', '行')[:2], ('行く', 'いく'))
        self.assertEqual(word('調査は東京に行ってきた。', '行')[:2], ('行く', 'いく'))

    def test_line_veto(self):
        # T534: 弾く's はじく rule doesn't fire with music elsewhere in the paragraph
        reader = Reader(known={('弾く', 'はじく'): 5, ('弾く', 'ひく'): 5})
        def word(text):
            return next(w for w in reader.read(text) if w.form == '弾く')[2:5]
        self.assertEqual(word('指で弾いた。'), ('弾く', 'はじく', 'rule'))
        self.assertNotEqual(word('演奏会の曲を、指で弾いた。')[2], 'rule')

    def test_adjective_stems(self):
        # T281: Sudachi's noun before すぎる or an emphatic い, and before a small ェ, is the adjective
        reader = Reader(known={('酷', 'こく'): 5, ('酷い', 'ひどい'): 5, ('強', 'きょう'): 5, ('強い', 'つよい'): 5,
                               ('熱', 'ねつ'): 5, ('熱い', 'あつい'): 5, ('手', 'て'): 5})
        self.assertIn('酷[ひど]すぎる', reader.furigana('それは酷すぎる話だ。'))
        self.assertIn('強[つえ]ェぞ', reader.furigana('こいつは強ェぞ。'))
        self.assertIn('痛[いて]ぇな', reader.furigana('ああ、痛ぇな。'))
        self.assertIn('熱[ねつ]さえ', reader.furigana('熱さえ下がれば'))  # not さ before え
        self.assertEqual(reader.read('手ぇ出すな。')[0][2:4], ('手ぇ', 'て'))  # 手え isn't an adjective: Sudachi's
        self.assertEqual(next(w for w in reader.read('酷だ。') if w.form == '酷').reading, 'こく')

    def test_compound_tails_after_a_head(self):
        # T282: tails voiced after a noun though the list's compounds are mixed (オウム返し; 繰り返し is a verb's stem)
        known = {('返し', 'かえし'): 5, ('恩返し', 'おんがえし'): 5, ('裏返し', 'うらがえし'): 5, ('倍返し', 'ばいがえし'): 5,
                 ('燕返し', 'つばめがえし'): 5, ('鼠返し', 'ねずみがえし'): 5, ('繰り返し', 'くりかえし'): 5,
                 ('取り返し', 'とりかえし'): 5, ('折り返し', 'おりかえし'): 5, ('揺り返し', 'ゆりかえし'): 5,
                 ('照り返し', 'てりかえし'): 5, ('揃い', 'そろい'): 5, ('美人', 'びじん'): 5, ('オウム', 'おうむ'): 5}
        reader = Reader(known=known)
        self.assertIn('オウム返[がえ]し', reader.furigana('オウム返しに言った。'))
        self.assertIn('揃[ぞろ]い', reader.furigana('美人揃いのチーム'))
        self.assertIn('揃[そろ]い', reader.furigana('靴が揃いだ。'))

    def test_unlisted_sudachi_reading(self):
        # Sudachi's ひょうしつ is neither listed nor JMdict's: the list's top reading, not shown
        reader = Reader(known={('氷室', 'ひむろ'): 5, ('上辺', 'うわべ'): 5, ('国', 'くに'): 5})
        self.assertEqual(reader.read('氷室に入る。')[0][2:5], ('氷室', 'ひむろ', 'dictionary'))
        # JMdict reads it じょうへん too: the list lacks a reading, Sudachi's stays
        self.assertEqual(reader.read('三角形の上辺を測る。')[1][3], 'じょうへん')
        # another form's reading (無性 むしょう, 無償) stays
        reader = Reader(known={('弾ける', 'はじける'): 5, ('弾く', 'ひく'): 5, ('無性', 'むせい'): 5, ('無償', 'むしょう'): 5})
        self.assertEqual(next(w for w in reader.read('無性に腹が立つ。') if w.form == '無性').reading, 'むしょう')
        # a する verb's godan form (徹す てっす, 徹する) stays
        reader = Reader(known={('徹す', 'とおす'): 5, ('徹する', 'てっする'): 5})
        self.assertEqual(next(w for w in reader.read('眼光紙背に徹す。') if w.form == '徹す').reading, 'てっす')
        reader = Reader(known={('買う', 'かう'): 5})  # Kansai 買うて is こうて
        self.assertEqual(next(w for w in reader.read('パン買うてくるわ。') if w.form == '買う').reading, 'こう')
        reader = Reader(known={('国', 'くに'): 5})
        # one-character forms keep Sudachi's (国 after a name is こく)
        self.assertNotEqual(next(w for w in reader.read('バシュルク国は広い。') if w.form == '国').reading, 'くに')

    def test_defaults(self):
        hints = []
        text = aozora_text('夜の公園は人気がなく、静かだった。｜宇宙《そら》を見る。\n学校へ行《い》った。', None, hints)
        words = {w.form: w for w in Reader().read(text, hints)}
        self.assertEqual(words['人気'][3:5], ('ひとけ', 'rule'))
        self.assertEqual(words['宇宙'][3:5], ('うちゅう', 'only'))
        self.assertEqual(words['行く'][3:5], ('いく', 'ruby'))
        self.assertEqual(text[words['公園'].start:words['公園'].end], '公園')

    def test_ateji_runs(self):
        # a loanword spelt in kanji that Sudachi cuts in pieces: one Word, never shown, not over ruby
        reader = Reader()
        self.assertIn(Word(0, 3, '無問題', 'もーまんたい', 'dictionary', 0.0), reader.read('無問題だよ。'))
        hints = []
        text = aozora_text('無《む》問題だよ。', None, hints)
        self.assertNotIn('無問題', [w.form for w in reader.read(text, hints)])
        self.assertFalse({'東家', '立直', '満貫', '加油'} & set(reader.ateji))  # mahjong terms, native pieces

    def test_post_war_rules_are_shown(self):
        # read by a context rule, not HAND_DEFAULTS, so chimimouryou shows them (evaluate.SHOWN)
        reader = Reader()
        for text, form, reading in (('異世界に転生した。', '転生', 'てんせい'), ('とてもお優しい御方です。', '御方', 'おかた')):
            word = next(w for w in reader.read(text) if w.form == form)
            self.assertEqual(word[3:5], (reading, 'rule'), text)
        self.assertEqual(next(w for w in reader.read('輪廻転生を信じる。') if w.form == '転生').reading, 'てんしょう')
        # T283: お兄様, お姉さま; 兄様 alone stays Sudachi's
        words = [w for w in reader.read('お兄様とお姉さまと兄様') if w.form in ('兄', '姉')]
        self.assertEqual([w[3:5] for w in words], [('にい', 'rule'), ('ねえ', 'rule'), ('あに', 'dictionary')])

    def test_compounds_the_list_doesnt_give_one_reading(self):
        known = {('力尽く', 'ちからずく'): 9000, ('力尽く', 'ちからづく'): 9000, ('力', 'ちから'): 300,
                 ('三日月', 'みかづき'): 17920, ('三日月', 'みかずき'): 17920, ('三日月', 'みかげ'): 144990,
                 ('曽祖父', 'ひいじじ'): 59755, ('曽祖父', 'そうそふ'): 59755, ('小姑', 'こじゅうと'): 40000,
                 ('小姑', 'こじゅうとめ'): 200000, ('入り方', 'いりがた'): 30000, ('入り方', 'はいりかた'): 100000}
        reader = Reader(known)
        joined = {w.form: w[3:5] for w in reader.read('力尽くで三日月を見た。羅甸語の本。')}
        self.assertEqual(joined['力尽く'], ('ちからずく', 'default'))  # ranked 3+ times above its others
        self.assertEqual(joined['三日月'], ('みかづき', 'rule'))  # shown (SHOWN_DEFAULTS)  # みかずき is its other spelling
        self.assertEqual(joined['羅甸語'], ('らてんご', 'only'))  # not in the list: JMdict's one reading
        # top readings that differ: JMdict's first when it is the only one the kanji spell (そうそふ, not ひいじじ) (T91)
        self.assertIn(('曽祖父', 'そうそふ', 'default'), [w[2:5] for w in reader.read('曽祖父の家。')])
        # two kanji (小|姑), a verb token (入り|方): not joined
        for text, form in (('小姑がいる。', '小姑'), ('気合いの入り方。', '入り方')):
            self.assertNotIn(form, [w.form for w in reader.read(text)], text)

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

    def test_one_x_ties_go_by_jmdict(self):
        # Jiten ranks a word, so its readings tie; JMdict lists ひとり first
        reader = Reader({('一人', 'ひとり'): 300, ('一人', 'いちにん'): 300}, tokenizer=ToyTokenizer())
        self.assertEqual(reader.one_x, {'一人': 'ひとり'})


if __name__ == '__main__':
    unittest.main()
