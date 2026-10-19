"""Tests for the public table's data: fetch_ndl (NDL's corpus as ruby) and fetch_aozora's held-out authors."""
import unittest

from yurigana import fetch_aozora, fetch_ndl
from yurigana.evaluate import ndl_held_out, ndl_lines

NDL = '\n'.join(['行番号: 1', '名前は通り。\t\t[入力文]', '\tなまえわ とーり。\t[入力 読み]',
                 '名前\tなまえ\t漢字', 'は\tわ\tひらがな', '通\tとー\t漢字', 'り\tり\tひらがな', '。\t。\t記号'])


def person(sei, mei, role='著者'):
    return {'作品ID': '1', '作品著作権フラグ': 'なし', '人物著作権フラグ': 'なし', '文字遣い種別': '新字新仮名',
            'テキストファイルURL': 'x.zip', '人物ID': sei, '姓': sei, '名': mei, '役割フラグ': role}


class NdlTest(unittest.TestCase):
    def test_every_kanji_word_becomes_ruby_with_the_listed_spelling(self):
        runs = fetch_ndl.run_readings({('名前', 'なまえ'): 1, ('通り', 'とおり'): 1})
        self.assertEqual(runs['通'], {'とお'})
        (text, spans), = ndl_lines(NDL)
        # とー is とう by default; the list's 通り とおり picks とお
        self.assertEqual(fetch_ndl.to_aozora(text, spans, runs), '｜名前《なまえ》は｜通《とお》り。')
        self.assertEqual(fetch_ndl.to_aozora(text, spans, {}), '｜名前《なまえ》は｜通《とう》り。')


class AozoraTest(unittest.TestCase):
    def test_names_are_written_as_ndl_names_its_folders(self):
        self.assertEqual(fetch_aozora.ndl_name(person('吉川', '英治')), '吉川英治')
        self.assertEqual(fetch_aozora.ndl_name(person('アンデルセン', 'ハンス・クリスチャン')),
                         'アンデルセン_ハンス・クリスチャン')

    def test_works_of_the_ndl_test_authors_are_left_out(self):
        self.assertTrue(ndl_held_out('吉川英治'))
        self.assertFalse(ndl_held_out('夏目漱石'))
        self.assertEqual(len(fetch_aozora.public_domain_works([person('夏目', '漱石')])), 1)
        self.assertEqual(fetch_aozora.public_domain_works([person('吉川', '英治')]), {})
        # a held-out translator doesn't matter, only the author
        self.assertEqual(len(fetch_aozora.public_domain_works([person('夏目', '漱石'), person('吉川', '英治', '翻訳者')])), 1)


if __name__ == '__main__':
    unittest.main()
