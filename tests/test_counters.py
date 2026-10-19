"""Tests for yurigana.counters: readings of a number + counter."""
import unittest

from yurigana import Reader, Word, aozora_text
from yurigana.counters import number_value, reading
from yurigana.tokens import Token

try:
    import sudachipy  # noqa: F401
except ImportError:
    sudachipy = None

# number, counter (Sudachi's normalized form), Sudachi's reading of the counter, expected reading
CASES = [
    ('一', '対', 'たい', 'いっつい'), ('三', '本', 'ぽん', 'さんぼん'), ('六', '本', 'ぽん', 'ろっぽん'),
    ('一', '本', 'ぽん', 'いっぽん'), ('二', '本', 'ぽん', 'にほん'), ('十', '本', 'ぽん', 'じゅっぽん'),
    ('千', '本', '', 'せんぼん'), ('何', '本', '', 'なんぼん'), ('一', '匹', 'ひき', 'いっぴき'),
    ('三', '匹', 'ひき', 'さんびき'), ('八', '杯', 'ばい', 'はっぱい'), ('三', '杯', 'ばい', 'さんばい'),
    ('一', '発', 'はつ', 'いっぱつ'), ('三', '泊', 'はく', 'さんぱく'), ('二', '泊', 'はく', 'にはく'),
    ('三', '階', 'かい', 'さんがい'), ('何', '階', 'かい', 'なんがい'), ('一', '階', 'かい', 'いっかい'),
    ('三', '軒', '', 'さんげん'), ('六', '回', 'かい', 'ろっかい'), ('百', '回', 'かい', 'ひゃっかい'),
    ('八', '個', 'こ', 'はっこ'), ('一', '冊', 'さつ', 'いっさつ'), ('六', '冊', 'さつ', 'ろくさつ'),
    ('一', '歳', 'さい', 'いっさい'), ('二十', '歳', 'さい', 'はたち'), ('20', '歳', 'さい', 'はたち'),
    ('二十五', '歳', 'さい', 'にじゅうごさい'), ('三', '足', 'そく', 'さんぞく'), ('一', '羽', 'わ', 'いちわ'),
    ('三', '羽', 'わ', 'さんば'), ('六', '羽', 'わ', 'ろっぱ'), ('一', '枚', 'まい', 'いちまい'),
    ('四', '枚', 'まい', 'よんまい'), ('一', '分', 'ふん', 'いっぷん'), ('四', '分', 'ふん', 'よんぷん'),
    ('五', '分', 'ふん', 'ごふん'), ('三十', '分', 'ふん', 'さんじゅっぷん'), ('三', '分', 'ぶん', 'さんぶん'),
    ('四', '時', 'じ', 'よじ'), ('七', '時', 'じ', 'しちじ'), ('九', '時', 'じ', 'くじ'),
    ('十四', '時', 'じ', 'じゅうよじ'), ('九', '時間', 'じかん', 'くじかん'), ('四', '人', 'にん', 'よにん'),
    ('1', '人', 'にん', 'ひとり'), ('2', '人', 'にん', 'ふたり'), ('二十一', '人', 'にん', 'にじゅういちにん'),
    ('四', '月', 'がつ', 'しがつ'), ('七', '月', 'がつ', 'しちがつ'), ('九', '月', 'がつ', 'くがつ'),
    ('十一', '月', 'がつ', 'じゅういちがつ'), ('何', '月', 'がつ', 'なんがつ'), ('二', '日', 'か', 'ふつか'),
    ('八', '日', 'か', 'ようか'), ('十', '日', 'か', 'とおか'), ('十四', '日', 'にち', 'じゅうよっか'),
    ('二十', '日', 'か', 'はつか'), ('二十四', '日', 'にち', 'にじゅうよっか'), ('十七', '日', 'にち', 'じゅうしちにち'),
    ('一', '日', 'にち', 'いちにち'), ('三', '日間', 'かかん', 'みっかかん'), ('四', '年', 'ねん', 'よねん'),
    ('1999', '年', 'ねん', 'せんきゅうひゃくきゅうじゅうきゅうねん'), ('四', '円', 'えん', 'よえん'),
    ('３万', '円', 'えん', 'さんまんえん'), ('三百', '円', 'えん', 'さんびゃくえん'), ('８００', '円', 'えん', 'はっぴゃくえん'),
    ('三千', '円', 'えん', 'さんぜんえん'), ('一', '箇月', 'かげつ', 'いっかげつ'), ('六', '箇月', 'かげつ', 'ろっかげつ'),
    ('一', '台', 'だい', 'いちだい'), ('何', '匹', 'ひき', 'なんびき'), ('幾', '人', 'にん', 'いくにん'),
    ('六百', '本', 'ぽん', 'ろっぴゃっぽん'), ('一兆', '円', 'えん', 'いっちょうえん'), ('8', '頭', 'とう', 'はっとう'),
]


class CounterReadingTest(unittest.TestCase):
    def test_cases(self):
        for number, counter, sudachi, expected in CASES:
            with self.subTest(number + counter):
                got = reading(number, counter, sudachi)
                self.assertEqual(got[0] + (got[1] or ''), expected)

    def test_split(self):
        self.assertEqual(reading('三', '本'), ('さん', 'ぼん'))
        self.assertEqual(reading('一', '人'), ('ひとり', None))  # doesn't split

    def test_date(self):
        self.assertEqual(reading('一', '日', 'にち', '四月'), ('ついたち', None))
        self.assertEqual(reading('一', '日', 'にち', '毎日'), ('いち', 'にち'))
        self.assertEqual(reading('二', '日', 'か'), ('ふつ', 'か'))

    def test_not_a_counter(self):
        self.assertIsNone(reading('三', '犬'))
        self.assertIsNone(reading('十三', '月', 'がつ'))  # no 13th month
        self.assertIsNone(reading('一', '月', 'つき'))  # ひとつき: not a month name
        self.assertIsNone(reading('三・五', '本'))

    def test_number_value(self):
        for written, value in (('三十五', 35), ('一九九九', 1999), ('３万５千', 35000), ('十', 10), ('百二', 102),
                               ('二億', 2 * 10 ** 8), ('0', None)):
            self.assertEqual(number_value(written), value)


# surface -> (dictionary form = normalized form, Sudachi's reading, part of speech)
LEXICON = {'三': ('三', 'サン', ('名詞', '数詞')), '一': ('一', 'イチ', ('名詞', '数詞')),
           '本': ('本', 'ポン', ('接尾辞', '名詞的')), '対': ('対', 'タイ', ('名詞', '普通名詞')),
           '人': ('人', 'ニン', ('接尾辞', '名詞的')), '犬': ('犬', 'イヌ', ('名詞', '普通名詞')),
           '三軒': ('三軒', 'ミノキ', ('名詞', '固有名詞', '人名', '姓'))}


class ToyTokenizer:
    def tokens(self, text):
        i = 0
        while i < len(text):
            word = next((w for w in sorted(LEXICON, key=len, reverse=True) if text.startswith(w, i)), text[i])
            form, reading_, pos = LEXICON.get(word, (word, '', ('助詞', '*')))
            if word not in '。、':
                yield Token(word, form, form, (pos + ('*',) * 6)[:6], reading_, i)
            i += len(word)


class ReaderCounterTest(unittest.TestCase):
    def reader(self):
        return Reader(tokenizer=ToyTokenizer())

    def test_span_word(self):
        words = self.reader().read('犬が三本の')
        self.assertIn(Word(2, 4, '三本', 'さんぼん', 'counter', None), words)
        self.assertEqual([w.form for w in words], ['犬', '三本', '三', '本'])
        self.assertEqual(words[3].reading, 'ほん')  # the counter keeps its plain reading

    def test_one_on_one_and_names(self):
        words = self.reader().read('一対一。三軒')
        self.assertFalse([w for w in words if w.form == '一対'])
        self.assertIn(Word(4, 6, '三軒', 'さんげん', 'counter', None), words)

    def test_ruby_wins(self):
        hints = []
        text = aozora_text('三本《さんほん》の', None, hints)
        self.assertNotIn('counter', [w.source for w in self.reader().read(text, hints)])


@unittest.skipUnless(sudachipy, 'needs SudachiPy and SudachiDict-full')
class SudachiCounterTest(unittest.TestCase):
    def test_sentences(self):
        reader = Reader()
        for text, span, expected in (('鉛筆を三本買った。', '三本', 'さんぼん'), ('犬が一匹いる。', '一匹', 'いっぴき'),
                                     ('ビールを八杯飲んだ。', '八杯', 'はっぱい'), ('三階に住む。', '三階', 'さんがい'),
                                     ('四月一日に会おう。', '四月', 'しがつ'), ('一日中寝た。', '一日', 'いちにち'),
                                     ('三分の一', '三分', 'さんぶん'), ('10分待った。', '10分', 'じゅっぷん'),
                                     ('二十日に帰る。', '二十日', 'はつか'), ('三軒の家', '三軒', 'さんげん')):
            with self.subTest(text):
                words = [w for w in reader.read(text) if w.source == 'counter']
                self.assertEqual([(w.form, w.reading) for w in words], [(span, expected)])
        words = reader.read('一人で十分です。')  # lexicalised: one token each, left alone
        self.assertNotIn('counter', [w.source for w in words])


if __name__ == '__main__':
    unittest.main()
