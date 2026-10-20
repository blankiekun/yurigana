"""Tests for yurigana.counters: readings of a number + counter."""
import unittest

from yurigana import Reader, Word, aozora_text
from yurigana.counters import number_reading, number_value, reading
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
    ('一', '歩', 'ほ', 'いっぽ'), ('三', '歩', 'ほ', 'さんぽ'), ('二', '歩', 'ほ', 'にほ'),
    ('三', '尺', 'しゃく', 'さんじゃく'), ('一', '周', 'しゅう', 'いっしゅう'), ('三', '貫', 'かん', 'さんがん'),
    ('四', '畳', 'じょう', 'よじょう'), ('八', '分目', 'ふんめ', 'はちぶんめ'), ('二', '粒', 'つぶ', 'ふたつぶ'),
    ('二三', '日', 'にち', 'にさんにち'), ('三四', '日', 'にち', 'さんよっか'), ('四五', '人', 'にん', 'しごにん'),
    ('五六', '本', 'ぽん', 'ごろっぽん'), ('一', '間', '', 'いっけん'),
]

# The acceptance grid, written by hand from standard counter grammar (not from any corpus):
# counter (with Sudachi's reading of it) -> readings for 1-10, 100, 1000 and 何; '-' where it doesn't apply.
NUMBERS = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千', '何']
DIGITS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '100', '1000']
GRID = {
    ('本', 'ぽん'): 'いっぽん にほん さんぼん よんほん ごほん ろっぽん ななほん はっぽん きゅうほん じゅっぽん ひゃっぽん せんぼん なんぼん',
    ('匹', 'ひき'): 'いっぴき にひき さんびき よんひき ごひき ろっぴき ななひき はっぴき きゅうひき じゅっぴき ひゃっぴき せんびき なんびき',
    ('杯', 'ばい'): 'いっぱい にはい さんばい よんはい ごはい ろっぱい ななはい はっぱい きゅうはい じゅっぱい ひゃっぱい せんばい なんばい',
    ('分', 'ふん'): 'いっぷん にふん さんぷん よんぷん ごふん ろっぷん ななふん はっぷん きゅうふん じゅっぷん ひゃっぷん せんぷん なんぷん',
    ('回', 'かい'): 'いっかい にかい さんかい よんかい ごかい ろっかい ななかい はっかい きゅうかい じゅっかい ひゃっかい せんかい なんかい',
    ('個', 'こ'): 'いっこ にこ さんこ よんこ ごこ ろっこ ななこ はっこ きゅうこ じゅっこ ひゃっこ せんこ なんこ',
    ('冊', 'さつ'): 'いっさつ にさつ さんさつ よんさつ ごさつ ろくさつ ななさつ はっさつ きゅうさつ じゅっさつ ひゃくさつ せんさつ なんさつ',
    ('歳', 'さい'): 'いっさい にさい さんさい よんさい ごさい ろくさい ななさい はっさい きゅうさい じゅっさい ひゃくさい せんさい なんさい',
    ('階', 'かい'): 'いっかい にかい さんがい よんかい ごかい ろっかい ななかい はっかい きゅうかい じゅっかい ひゃっかい せんがい なんがい',
    ('軒', 'けん'): 'いっけん にけん さんげん よんけん ごけん ろっけん ななけん はっけん きゅうけん じゅっけん ひゃっけん せんげん なんげん',
    ('足', 'そく'): 'いっそく にそく さんぞく よんそく ごそく ろくそく ななそく はっそく きゅうそく じゅっそく ひゃくそく せんぞく なんぞく',
    ('頭', 'とう'): 'いっとう にとう さんとう よんとう ごとう ろくとう ななとう はっとう きゅうとう じゅっとう ひゃくとう せんとう なんとう',
    ('枚', 'まい'): 'いちまい にまい さんまい よんまい ごまい ろくまい ななまい はちまい きゅうまい じゅうまい ひゃくまい せんまい なんまい',
    ('人', 'にん'): 'ひとり ふたり さんにん よにん ごにん ろくにん しちにん はちにん きゅうにん じゅうにん ひゃくにん せんにん なんにん',
    ('日', 'にち'): 'いちにち ふつか みっか よっか いつか むいか なのか ようか ここのか とおか ひゃくにち せんにち なんにち',
    ('時', 'じ'): 'いちじ にじ さんじ よじ ごじ ろくじ しちじ はちじ くじ じゅうじ - - なんじ',
    ('年', 'ねん'): 'いちねん にねん さんねん よねん ごねん ろくねん ななねん はちねん きゅうねん じゅうねん ひゃくねん せんねん なんねん',
    ('月', 'がつ'): 'いちがつ にがつ さんがつ しがつ ごがつ ろくがつ しちがつ はちがつ くがつ じゅうがつ - - なんがつ',
    ('週', 'しゅう'): 'いっしゅう にしゅう さんしゅう よんしゅう ごしゅう ろくしゅう ななしゅう はっしゅう きゅうしゅう じゅっしゅう ひゃくしゅう せんしゅう なんしゅう',
    ('円', 'えん'): 'いちえん にえん さんえん よえん ごえん ろくえん ななえん はちえん きゅうえん じゅうえん ひゃくえん せんえん なんえん',
    ('度', 'ど'): 'いちど にど さんど よんど ごど ろくど ななど はちど きゅうど じゅうど ひゃくど せんど なんど',
    ('台', 'だい'): 'いちだい にだい さんだい よんだい ごだい ろくだい ななだい はちだい きゅうだい じゅうだい ひゃくだい せんだい なんだい',
    ('着', 'ちゃく'): 'いっちゃく にちゃく さんちゃく よんちゃく ごちゃく ろくちゃく ななちゃく はっちゃく きゅうちゃく じゅっちゃく ひゃくちゃく せんちゃく なんちゃく',
    ('泊', 'はく'): 'いっぱく にはく さんぱく よんはく ごはく ろっぱく ななはく はっぱく きゅうはく じゅっぱく ひゃっぱく せんぱく なんぱく',
    ('寸', 'すん'): 'いっすん にすん さんずん よんすん ごすん ろくすん ななすん はっすん きゅうすん じゅっすん ひゃくすん せんずん なんずん',
    ('銭', 'せん'): 'いっせん にせん さんせん よんせん ごせん ろくせん ななせん はっせん きゅうせん じゅっせん ひゃくせん せんせん なんせん',
    ('間', 'けん'): 'いっけん にけん さんげん よんけん ごけん ろっけん ななけん はっけん きゅうけん じゅっけん ひゃっけん せんげん なんげん',
    ('晩', 'ばん'): 'ひとばん ふたばん さんばん よんばん ごばん ろくばん ななばん はちばん きゅうばん じゅうばん ひゃくばん せんばん なんばん',
    ('件', 'けん'): 'いっけん にけん さんけん よんけん ごけん ろっけん ななけん はっけん きゅうけん じゅっけん ひゃっけん せんけん なんけん',
}


class CounterReadingTest(unittest.TestCase):
    def test_cases(self):
        for number, counter, sudachi, expected in CASES:
            with self.subTest(number + counter):
                got = reading(number, counter, sudachi)
                self.assertEqual(got[0] + (got[1] or ''), expected)

    def test_grid(self):
        for (counter, sudachi), row in GRID.items():
            for numbers in (NUMBERS, DIGITS):
                for number, expected in zip(numbers, row.split()):
                    if expected == '-':
                        continue
                    with self.subTest(number + counter):
                        got = reading(number, counter, sudachi, '', '後')  # 後: a bare 十分 is minutes only with a cue
                        self.assertEqual(got and got[0] + (got[1] or ''), expected)

    def test_split(self):
        self.assertEqual(reading('三', '本'), ('さん', 'ぼん'))
        self.assertEqual(reading('一', '人'), ('ひとり', None))  # doesn't split

    def test_date(self):
        self.assertEqual(reading('一', '日', 'にち', '四月'), ('ついたち', None))
        self.assertEqual(reading('一', '日', 'にち', '毎日'), ('いち', 'にち'))
        self.assertEqual(reading('二', '日', 'か'), ('ふつ', 'か'))

    def test_era_year(self):
        # After an era name two kanji digits are the year, not "two or three"
        self.assertEqual(reading('二三', '年', 'ねん', '昭和'), ('にじゅうさん', 'ねん'))
        self.assertEqual(reading('四五', '年', 'ねん', '生まれは明治'), ('よんじゅうご', 'ねん'))
        self.assertEqual(reading('二三', '年', 'ねん', 'ここ'), ('にさん', 'ねん'))
        self.assertEqual(reading('二三', '日', 'にち', '平成'), ('にじゅうさん', 'にち'))

    def test_hitoma(self):
        # 一間 is one room next to a room or lodging word, else a length (いっけん)
        self.assertEqual(reading('一', '間', 'けん', '六畳'), ('ひと', 'ま'))
        self.assertEqual(reading('一', '間', 'けん', '', 'の部屋'), ('ひと', 'ま'))
        self.assertEqual(reading('一', '間', 'けん', '', 'を借りて'), ('ひと', 'ま'))
        self.assertEqual(reading('一', '間', 'けん', '旅館の', 'に通'), ('ひと', 'ま'))
        self.assertEqual(reading('一', '間', 'けん', '', 'ほど離'), ('いっ', 'けん'))
        self.assertEqual(reading('三', '間', 'けん', '', 'の部屋'), ('さん', 'げん'))

    def test_bu(self):
        # 分 as a tenth: pairs, after 割/寸/両, before 咲き/目/通り; minutes and fractions otherwise
        self.assertEqual(reading('五', '分', 'ふん', '', '五分'), ('ご', 'ぶ'))
        self.assertEqual(reading('三', '分', 'ふん', '七分', 'に'), ('さん', 'ぶ'))
        self.assertEqual(reading('七', '分', 'ふん', '', '三分'), ('しち', 'ぶ'))
        self.assertEqual(reading('五', '分', 'ぶん', '三割', 'だ'), ('ご', 'ぶ'))
        self.assertEqual(reading('三', '分', 'ふん', 'まだ', '咲き'), ('さん', 'ぶ'))
        self.assertEqual(reading('五', '分', 'ふん', '', '待った'), ('ご', 'ふん'))
        self.assertEqual(reading('三', '分', 'ぶん', '', 'の一'), ('さん', 'ぶん'))
        self.assertEqual(reading('１０', '分', 'ぶん', '徒歩', 'のところ'), ('じゅっ', 'ぷん'))  # Sudachi's ぶん: minutes
        self.assertEqual(reading('十', '分', 'ぶん', '', 'の理解'), ('じゅう', 'ぶん'))  # 十分 じゅうぶん
        self.assertEqual(reading('十', '分', 'ふん', '', 'には'), ('じゅう', 'ぶん'))  # Sudachi split 十分 "enough"
        self.assertEqual(reading('十', '分', 'ふん', '', '待った'), ('じゅう', 'ぶん'))  # no cue: "enough" is far more common
        self.assertEqual(reading('十', '分', 'ふん', '', 'ほど歩'), ('じゅっ', 'ぷん'))
        self.assertEqual(reading('十', '分', 'ふん', '三時', 'に着'), ('じゅっ', 'ぷん'))
        self.assertEqual(reading('十', '分', 'ふん', '二', '待った'), ('じゅっ', 'ぷん'))  # part of 二十分

    def test_number_reading(self):
        for value, expected in ((600, 'ろっぴゃく'), (800, 'はっぴゃく'), (3000, 'さんぜん'), (650, 'ろっぴゃくごじゅう')):
            self.assertEqual(number_reading(value), expected)
        self.assertEqual(number_reading(10 ** 7, one_thousand=True), 'いっせんまん')  # written 一千万
        self.assertEqual(reading('一千万', '円', 'えん'), ('いっせんまん', 'えん'))

    def test_not_a_counter(self):
        self.assertIsNone(reading('三', '犬'))
        self.assertIsNone(reading('十三', '月', 'がつ'))  # no 13th month
        self.assertIsNone(reading('一', '月', 'つき'))  # ひとつき: not a month name
        self.assertIsNone(reading('三・五', '本'))
        self.assertIsNone(reading('七', '間', 'ま'))  # rooms: ななま
        self.assertIsNone(reading('一二', '人', 'にん'))  # ひとりふたり, not split
        self.assertIsNone(reading('二', '升', 'しょう', '', '目'))  # 升目 ますめ

    def test_number_value(self):
        for written, value in (('三十五', 35), ('一九九九', 1999), ('３万５千', 35000), ('十', 10), ('百二', 102),
                               ('二億', 2 * 10 ** 8), ('0', None)):
            self.assertEqual(number_value(written), value)


# surface -> (dictionary form = normalized form, Sudachi's reading, part of speech)
LEXICON = {'三': ('三', 'サン', ('名詞', '数詞')), '一': ('一', 'イチ', ('名詞', '数詞')),
           '本': ('本', 'ポン', ('接尾辞', '名詞的')), '匹': ('匹', 'ヒキ', ('接尾辞', '名詞的')), '対': ('対', 'タイ', ('名詞', '普通名詞')),
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
        self.assertEqual(words[3], Word(3, 4, '本', 'ほん', 'counter', None))  # the counter keeps its plain reading

    def test_counter_is_never_only_in_a_span(self):
        reader = Reader({('匹', 'ひき'), ('犬', 'いぬ')}, tokenizer=ToyTokenizer())
        self.assertEqual(reader.read('匹')[0][3:5], ('ひき', 'only'))
        words = reader.read('一匹')
        self.assertEqual([w[2:5] for w in words], [('一匹', 'いっぴき', 'counter'), ('一', 'いち', 'dictionary'),
                                                    ('匹', 'ひき', 'counter')])

    def test_one_on_one_and_names(self):
        words = self.reader().read('一対一。三軒')
        self.assertFalse([w for w in words if w.form == '一対'])
        self.assertIn(Word(4, 6, '三軒', 'さんげん', 'counter', None), words)

    def test_ruby_wins(self):
        hints = []
        text = aozora_text('三本《さんほん》の', None, hints)
        self.assertNotIn('counter', [w.source for w in self.reader().read(text, hints)])


@unittest.skipUnless(sudachipy, 'needs SudachiPy and SudachiDict-core')
class SudachiCounterTest(unittest.TestCase):
    def test_sentences(self):
        reader = Reader()
        for text, span, expected in (('鉛筆を三本買った。', '三本', 'さんぼん'), ('犬が一匹いる。', '一匹', 'いっぴき'),
                                     ('ビールを八杯飲んだ。', '八杯', 'はっぱい'), ('三階に住む。', '三階', 'さんがい'),
                                     ('四月一日に会おう。', '四月', 'しがつ'), ('一日中寝た。', '一日', 'いちにち'),
                                     ('10分待った。', '10分', 'じゅっぷん'), ('一回やってみた。', '一回', 'いっかい'),
                                     ('一列に並ぶ。', '一列', 'いちれつ'), ('三十分待った。', '三十分', 'さんじゅっぷん'),
                                     ('二三日休む。', '二三日', 'にさんにち'), ('一晩泊まる。', '一晩', 'ひとばん'),
                                     ('二十日に帰る。', '二十日', 'はつか'), ('三軒の家', '三軒', 'さんげん'), ('三分の一', '三分', 'さんぶん')):
            with self.subTest(text):
                words = [(w.form, w.reading) for w in reader.read(text) if w.source == 'counter']
                self.assertEqual(words[0], (span, expected))
        self.assertIn(('分', 'ぶん'), words)  # 三分の一: the fraction's 分 keeps ぶん
        words = [(w.form, w.reading, w.source) for w in reader.read('六百ページと五分五分の勝負')]
        self.assertIn(('六百', 'ろっぴゃく', 'counter'), words)  # a number alone: not Sudachi's ろくひゃく
        self.assertIn(('五分', 'ごぶ', 'counter'), words)
        self.assertNotIn('counter', [w.source for w in reader.read('数万の人')[:2]])  # 万 alone isn't いちまん
        words = reader.read('一人で十分です。')  # lexicalised: one token each, left alone
        self.assertNotIn('counter', [w.source for w in words])


if __name__ == '__main__':
    unittest.main()
