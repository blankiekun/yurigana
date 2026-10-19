import unittest

from yurigana import furigana
from yurigana.reader import split_reading


class SplitReadingTest(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split_reading('取り扱い', 'とりあつかい'), [('取', 'と'), ('り', None), ('扱', 'あつか'), ('い', None)])
        self.assertEqual(split_reading('読ん', 'よん'), [('読', 'よ'), ('ん', None)])
        self.assertEqual(split_reading('学校', 'がっこう'), [('学校', 'がっこう')])
        self.assertEqual(split_reading('人々', 'ひとびと'), [('人々', 'ひとびと')])

    def test_kana_that_do_not_line_up_keep_the_whole_word(self):
        self.assertEqual(split_reading('読ん', 'よみ'), [('読ん', 'よみ')])


class FuriganaTest(unittest.TestCase):
    def test_sentence(self):
        self.assertEqual(furigana('本を読んだ。'), '本[ほん]を読[よ]んだ。')
        self.assertEqual(furigana('学校へ行った。'), '学校[がっこう]へ行[い]った。')

    def test_counter_span_once(self):  # 三本 is one span over its own tokens: bracketed once
        self.assertEqual(furigana('鉛筆を三本買った。'), '鉛筆[えんぴつ]を三本[さんぼん]買[か]った。')

    def test_text_without_kanji(self):
        self.assertEqual(furigana('ひらがなだけ。'), 'ひらがなだけ。')


if __name__ == '__main__':
    unittest.main()
