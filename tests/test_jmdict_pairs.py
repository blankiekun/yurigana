"""Tests for tools/jmdict_pairs.py on a tiny JMdict."""
import importlib.util
import os
import unittest

spec = importlib.util.spec_from_file_location(
    'jmdict_pairs', os.path.join(os.path.dirname(__file__), '..', 'tools', 'jmdict_pairs.py'))
jmdict_pairs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jmdict_pairs)

XML = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE JMdict [
<!ENTITY rk "rarely used kana form">
<!ENTITY ok "out-dated or obsolete kana usage">
<!ENTITY rK "rarely used kanji form">
<!ENTITY n "noun (common) (futsuumeishi)">
]>
<JMdict>
<entry><k_ele><keb>煙草</keb></k_ele><k_ele><keb>莨</keb><ke_inf>&rK;</ke_inf></k_ele>
<r_ele><reb>たばこ</reb></r_ele><r_ele><reb>タバコ</reb></r_ele>
<r_ele><reb>えんそう</reb><re_restr>煙草</re_restr></r_ele>
<r_ele><reb>けむくさ</reb><re_inf>&rk;</re_inf></r_ele>
<r_ele><reb>シガー</reb><re_nokanji/></r_ele>
<sense><pos>&n;</pos></sense></entry>
<entry><r_ele><reb>ありがとう</reb></r_ele></entry>
<entry><k_ele><keb>てふ</keb></k_ele><r_ele><reb>ちょう</reb><re_inf>&ok;</re_inf></r_ele></entry>
<entry><k_ele><keb>煙草</keb></k_ele><r_ele><reb>えんそう</reb></r_ele><r_ele><reb>けぶりぐさ</reb></r_ele></entry>
</JMdict>'''


class JmdictPairsTest(unittest.TestCase):
    def test_pairs(self):
        self.assertEqual(jmdict_pairs.pairs(XML.encode()), {
            '煙草': ['たばこ', 'えんそう', 'けぶりぐさ'],  # タバコ is たばこ; rare kana and nokanji left out
            '莨': ['たばこ'],  # a rare kanji form stays; えんそう is restricted to 煙草
        })


if __name__ == '__main__':
    unittest.main()
