"""Tests for yurigana.readings: ruby and context rules."""
import unittest

from yurigana.readings import conjugated_reading, context_reading, ruby_reading


class RubyReadingTest(unittest.TestCase):
    def test_only_plain_readings_listed_by_jiten(self):
        known = {('人気', 'ひとけ'), ('人気', 'にんき'), ('本気', 'まじ'), ('本気', 'ほんき'), ('宇宙', 'うちゅう')}
        hints = {0: (2, 'ひとけ'), 3: (5, 'そら'), 6: (8, 'マジ'), 9: (11, 'まじ'), 12: (13, 'ひと')}
        self.assertEqual(ruby_reading(hints, 0, '人気', '人気', known), 'ひとけ')
        self.assertIsNone(ruby_reading(hints, 3, '宇宙', '宇宙', known))  # not a reading of 宇宙
        self.assertIsNone(ruby_reading(hints, 6, '本気', '本気', known))  # katakana: flavour
        self.assertEqual(ruby_reading(hints, 9, '本気', '本気', known), 'まじ')  # Jiten lists it (accepted hole)
        self.assertIsNone(ruby_reading(hints, 12, '人気', '人気', known))  # ruby over part of the token
        self.assertIsNone(ruby_reading(hints, 1, '気', '気', known))

    def test_per_kanji_ruby_is_joined(self):
        known = {('人気', 'ひとけ'), ('人気', 'にんき')}
        self.assertEqual(ruby_reading({0: (1, 'ひと'), 1: (2, 'け')}, 0, '人気', '人気', known), 'ひとけ')
        self.assertIsNone(ruby_reading({0: (1, 'ひと'), 1: (2, 'き')}, 0, '人気', '人気', known))  # not listed
        self.assertIsNone(ruby_reading({0: (1, 'ひと'), 1: (3, 'けの')}, 0, '人気', '人気', known))  # past the token
        self.assertIsNone(ruby_reading({0: (1, 'ひと'), 1: (2, 'ケ')}, 0, '人気', '人気', known))  # katakana part

    def test_ruby_over_the_kanji_stem(self):
        known = {('行く', 'いく'), ('行く', 'ゆく'), ('上手い', 'うまい'), ('歩く', 'あるく'), ('見上げる', 'みあげる'),
                 ('子ども', 'こども'), ('魚市場', 'うおいちば')}
        self.assertEqual(ruby_reading({0: (1, 'い')}, 0, '行っ', '行く', known), 'いく')  # 行《い》った
        self.assertEqual(ruby_reading({0: (1, 'ゆ')}, 0, '行か', '行く', known), 'ゆく')
        self.assertEqual(ruby_reading({0: (2, 'うま')}, 0, '上手く', '上手い', known), 'うまい')
        self.assertEqual(ruby_reading({0: (1, 'ある')}, 0, '歩く', '歩く', known), 'あるく')
        self.assertEqual(ruby_reading({0: (1, 'み'), 1: (2, 'あ')}, 0, '見上げ', '見上げる', known), 'みあげる')
        self.assertEqual(ruby_reading({0: (1, 'こ')}, 0, '子ども', '子ども', known), 'こども')
        self.assertIsNone(ruby_reading({0: (1, 'おこな')}, 0, '行っ', '行く', known))  # おこなく: not listed
        self.assertIsNone(ruby_reading({0: (1, 'うお')}, 0, '魚市場', '魚市場', known))  # kanji left: compound
        self.assertIsNone(ruby_reading({0: (1, 'い')}, 0, '云っ', '言う', {('言う', 'いう')}))  # lemma spelled apart

    def test_large_kana_ruby(self):
        known = {('一緒', 'いっしょ'), ('目下', 'もっか'), ('目下', 'めした'), ('勝つ', 'かつ'), ('喋る', 'しゃべる')}
        self.assertEqual(ruby_reading({0: (2, 'いつしよ')}, 0, '一緒', '一緒', known), 'いっしょ')
        self.assertEqual(ruby_reading({0: (2, 'もつか')}, 0, '目下', '目下', known), 'もっか')
        self.assertEqual(ruby_reading({0: (1, 'か')}, 0, '勝つ', '勝つ', known), 'かつ')  # exact first
        self.assertEqual(ruby_reading({0: (1, 'しやべ')}, 0, '喋っ', '喋る', known), 'しゃべる')  # stem and large kana
        self.assertIsNone(ruby_reading({0: (2, 'つか')}, 0, '目下', '目下', {('目下', 'っか')}))  # never a leading っ


class ConjugatedReadingTest(unittest.TestCase):
    def test_the_one_listed_reading_that_conjugates_to_sudachis(self):
        self.assertEqual(conjugated_reading('行っ', '行く', 'いっ', ['いく', 'ゆく']), 'いく')
        self.assertEqual(conjugated_reading('行か', '行く', 'ゆか', ['いく', 'ゆく']), 'ゆく')
        self.assertEqual(conjugated_reading('行っ', '行く', 'いつ', ['いく', 'ゆく']), 'いく')  # small kana folded
        self.assertEqual(conjugated_reading('早く', '早い', 'はやく', ['はやい', 'はやーい']), 'はやい')
        self.assertEqual(conjugated_reading('上っ', '上る', 'のぼっ', ['あがる', 'のぼる']), 'のぼる')
        self.assertIsNone(conjugated_reading('行っ', '行く', 'おこなっ', ['いく', 'ゆく']))  # none matches
        self.assertIsNone(conjugated_reading('言わ', '言う', 'いわ', []))
        self.assertIsNone(conjugated_reading('云っ', '言う', 'いっ', ['いう']))  # stem spelled apart

    def test_kuru(self):
        for surface, sudachi in (('来', 'き'), ('来', 'こ'), ('来よう', 'こよう'), ('来い', 'こい'), ('来れ', 'くれ')):
            self.assertEqual(conjugated_reading(surface, '来る', sudachi, ['きたる', 'くる']), 'くる', surface)
        self.assertIsNone(conjugated_reading('来', '来る', 'き', ['きたる']))  # くる not listed


class ContextReadingTest(unittest.TestCase):
    known = {('人気', 'ひとけ'), ('人気', 'にんき'), ('明日', 'あした'), ('明日', 'あす'), ('上手', 'かみて'),
             ('今日', 'こんにち'), ('他', 'た'), ('何', 'なに'), ('何', 'なん'),
             ('中', 'じゅう'), ('中', 'ちゅう'),
             ('種', 'しゅ'), ('下', 'した'), ('下', 'もと'), ('音', 'ね'), ('風', 'ふう'), ('風', 'かぜ')}

    def reading(self, text, form, surface=None, known=None):
        return context_reading(text, text.index(form), surface or form, form, self.known if known is None else known)

    def test_rules(self):
        self.assertEqual(self.reading('夜の公園は人気がなく、', '人気'), 'ひとけ')
        self.assertIsNone(self.reading('彼は人気者だ。', '人気'))  # Sudachi's reading stays
        self.assertEqual(self.reading('役者が舞台の上手から', '上手'), 'かみて')  # text before
        self.assertEqual(self.reading('今日に至るまで', '今日'), 'こんにち')
        self.assertEqual(self.reading('その他の項目', '他'), 'た')
        self.assertEqual(self.reading('明日は雨だ。', '明日'), 'あした')
        self.assertIsNone(self.reading('明日の日本を担う', '明日'))
        self.assertIsNone(self.reading('料理が上手だ', '上手'))

    def test_nani_before_ka_suru_and_verbs_nan_before_counters(self):
        for text in ('何か食べたい。', '何してるの？', '何？', '何食べる？'):
            self.assertEqual(self.reading(text, '何'), 'なに', text)
        for text in ('何ですか。', '何の話だ。', '何年も待った。', '何冊ある？', '何百人も来た。', '何曜日ですか。'):
            self.assertIsNone(self.reading(text, '何'), text)  # Sudachi's なん stays

    def test_juu_after_a_stretch_of_time_or_a_place(self):
        for text in ('一日中寝ていた。', '一晩中起きていた。', '今日中に出す。', '世界中に広まった。', '家中を探した。', '体中が痛い。'):
            self.assertEqual(self.reading(text, '中'), 'じゅう', text)
        for text in ('授業中に寝た。', '今週中に出す。', '数日中に届く。', '一両日中に決まる。', '箱の中に入れた。'):
            self.assertIsNone(self.reading(text, '中'), text)  # Sudachi's ちゅう/なか stays

    def test_common_homographs(self):
        cases = [('この種の本', '種', 'しゅ'), ('数種の気体', '種', 'しゅ'), ('種をまく', '種', None),
                 ('他の追随を許さない', '他', 'た'), ('他言語から', '他', 'た'), ('他の人', '他', None),
                 ('木の下で休む', '下', 'した'), ('先生の指導の下で学ぶ', '下', 'もと'), ('机の下に', '下', None),
                 ('琴の音が聞こえる', '音', 'ね'), ('ぐうの音も出ない', '音', 'ね'), ('雨の音', '音', None),
                 ('こんな風に書く', '風', 'ふう'), ('知らない風を装う', '風', 'ふう'), ('花びらが風に舞う', '風', 'かぜ'),
                 ('風が吹く', '風', 'かぜ'), ('西洋風の家', '風', None)]
        for text, form, reading in cases:
            self.assertEqual(self.reading(text, form), reading, text)

    def test_hitoke_needs_a_cue(self):
        for text in ('人気のない路地', '人気も無い', '人気が少ない', '人気が絶えた', '周囲に人気がない', '人気がない場所に',
                     '廊下は人気がなく静か', '夜の公園は人気がまったくなかった', '辺りに人気はなかった', '駐車場は人気がない', '事務所に人気がない'):
            self.assertEqual(self.reading(text, '人気'), 'ひとけ', text)
        self.assertEqual(self.reading('人気のない奴だ', '人気'), 'にんき')  # before the のない rule
        for text in ('この店は人気がない', '茨城県は人気がない', '海外では人気がない', '国内では人気がない', '人気がない',
                     'この作家はまだ人気がない', '作家は人気がない', '市場では人気がない', 'パン屋は人気がない',
                     '驚くほど人気がない', 'この店は全く人気がない', '北海道では人気がない', '長所は人気がないことだ'):
            self.assertIsNone(self.reading(text, '人気'), text)  # no cue: Sudachi's にんき

    def test_iru_after_ki_ni_and_jin_after_places(self):
        known = {('入る', 'いる'), ('入る', 'はいる'), ('人', 'じん'), ('人', 'ひと'), ('人', 'にん')}
        for text, reading in (('服が気に入っている', 'いる'), ('家族水入らずで', 'いる'), ('部屋に入った', None),
                              ('水が入らない', None)):
            begin = text.index('入')
            self.assertEqual(context_reading(text, begin, text[begin:begin + 2], '入る', known), reading, text)
        self.assertEqual(self.reading('カナダ人です', '人', known=known), 'じん')
        place = ('名詞', '固有名詞', '地名', '一般', '*', '*')
        self.assertEqual(context_reading('東京人は', 2, '人', '人', known, place), 'じん')
        self.assertIsNone(context_reading('東京人は', 2, '人', '人', known))
        self.assertIsNone(context_reading('東京人は', 2, '人', '人', known, ('名詞', '普通名詞', '一般', '*', '*', '*')))

    def test_only_the_line_and_listed_readings(self):
        self.assertIsNone(self.reading('舞台の\n上手から', '上手'))
        self.assertIsNone(self.reading('人気\nのない', '人気'))
        self.assertIsNone(self.reading('人気のない', '人気', known={('人気', 'にんき')}))
        self.assertIsNone(self.reading('人気のない', '人気', known=()))  # no frequency list: no rules


if __name__ == '__main__':
    unittest.main()
