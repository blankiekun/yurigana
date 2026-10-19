"""Tests for fetch_aozora: the NDL test set's authors are left out of the public table's data."""
import unittest

from yurigana import fetch_aozora
from yurigana.evaluate import NDL_TEST_AUTHORS, ndl_held_out


def person(sei, mei, role='著者'):
    return {'作品ID': '1', '作品著作権フラグ': 'なし', '人物著作権フラグ': 'なし', '文字遣い種別': '新字新仮名',
            'テキストファイルURL': 'x.zip', '人物ID': sei, '姓': sei, '名': mei, '役割フラグ': role}


class AozoraTest(unittest.TestCase):
    def test_names_are_written_as_ndl_names_its_folders(self):
        self.assertEqual(fetch_aozora.ndl_name(person('吉川', '英治')), '吉川英治')
        self.assertEqual(fetch_aozora.ndl_name(person('アンデルセン', 'ハンス・クリスチャン')),
                         'アンデルセン_ハンス・クリスチャン')

    def test_works_of_the_ndl_test_authors_are_left_out(self):
        self.assertTrue(all(ndl_held_out(name) for name in NDL_TEST_AUTHORS))
        self.assertIn('吉川英治', NDL_TEST_AUTHORS)
        self.assertNotIn('夏目漱石', NDL_TEST_AUTHORS)
        self.assertEqual(len(fetch_aozora.public_domain_works([person('夏目', '漱石')])), 1)
        self.assertEqual(fetch_aozora.public_domain_works([person('吉川', '英治')]), {})
        # a held-out translator doesn't matter, only the author
        self.assertEqual(len(fetch_aozora.public_domain_works([person('夏目', '漱石'), person('吉川', '英治', '翻訳者')])), 1)


if __name__ == '__main__':
    unittest.main()
