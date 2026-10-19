"""Tests for yurigana.readings: ruby and context rules."""
import unittest

from yurigana.readings import context_reading, ruby_reading


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


class ContextReadingTest(unittest.TestCase):
    known = {('人気', 'ひとけ'), ('人気', 'にんき'), ('明日', 'あした'), ('明日', 'あす'), ('上手', 'かみて'),
             ('今日', 'こんにち'), ('他', 'た')}

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

    def test_hitoke_needs_a_cue(self):
        for text in ('人気のない路地', '人気も無い', '人気が少ない', '人気が絶えた', '周囲に人気がない', '人気がない場所に',
                     '廊下は人気がなく静か', '夜の公園は人気がまったくなかった', '辺りに人気はなかった', '駐車場は人気がない', '事務所に人気がない'):
            self.assertEqual(self.reading(text, '人気'), 'ひとけ', text)
        self.assertEqual(self.reading('人気のない奴だ', '人気'), 'にんき')  # before the のない rule
        for text in ('この店は人気がない', '茨城県は人気がない', '海外では人気がない', '国内では人気がない', '人気がない',
                     'この作家はまだ人気がない', '作家は人気がない', '市場では人気がない', 'パン屋は人気がない',
                     '驚くほど人気がない', 'この店は全く人気がない', '北海道では人気がない', '長所は人気がないことだ'):
            self.assertIsNone(self.reading(text, '人気'), text)  # no cue: Sudachi's にんき

    def test_only_the_line_and_listed_readings(self):
        self.assertIsNone(self.reading('舞台の\n上手から', '上手'))
        self.assertIsNone(self.reading('人気\nのない', '人気'))
        self.assertIsNone(self.reading('人気のない', '人気', known={('人気', 'にんき')}))
        self.assertIsNone(self.reading('人気のない', '人気', known=()))  # no frequency list: no rules


if __name__ == '__main__':
    unittest.main()
