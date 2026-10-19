"""Tests for yurigana.evaluate's scorer and gold converters (no tokeniser needed)."""
import unittest

from yurigana.evaluate import (_binomial_p, compare, items_of, metrics, ndl_lines, ndl_readings, score_sentence,
                               surface_reading, tatoeba_sentence)


def span(b, e, surface, reading, alts=()):
    return {'b': b, 'e': e, 'surface': surface, 'reading': reading, 'alts': list(alts)}


class ScoreTest(unittest.TestCase):
    def test_union_span(self):
        # gold 何 + 度, one token 何度: scored as なんど, both items right
        sentence = {'text': '何度も', 'spans': [span(0, 1, '何', 'なん'), span(1, 2, '度', 'ど')]}
        self.assertEqual(score_sentence(sentence, [(0, 2, 'なんど', None), (2, 3, 'も', None)]),
                         [('ok', True, True, False)] * 2)
        # gold 行 inside token 行った: the kana after it come along
        sentence = {'text': '行った', 'spans': [span(0, 1, '行', 'い')]}
        self.assertEqual(score_sentence(sentence, [(0, 3, 'いった', True)]), [('ok', True, True, True)])
        self.assertEqual(score_sentence(sentence, [(0, 3, 'おこなった', True)]), [('ok', False, False, True)])

    def test_alignment_failure_and_no_reading(self):
        # 達 has no gold: a token that swallows it can't be scored
        sentence = {'text': '子供達', 'spans': [span(0, 2, '子供', 'こども')]}
        self.assertEqual(score_sentence(sentence, [(0, 3, 'こどもたち', None)]), [('align', False, False, False)])
        self.assertEqual(score_sentence(sentence, [(0, 2, 'こども', None), (2, 3, 'たち', None)]), [('ok', True, True, False)])
        self.assertEqual(score_sentence(sentence, [(0, 2, None, None)])[0][0], 'none')

    def test_alts_small_kana_and_voicing(self):
        sentence = {'text': '明日', 'spans': [span(0, 2, '明日', 'あした', ['あす'])]}
        self.assertEqual(score_sentence(sentence, [(0, 2, 'アス', None)]), [('ok', True, True, False)])
        sentence = {'text': '三本', 'spans': [span(0, 1, '三', 'さん'), span(1, 2, '本', 'ぼん')]}
        # display is strict about voicing, the word list isn't
        self.assertEqual(score_sentence(sentence, [(0, 2, 'さんほん', None)]), [('ok', False, True, False)] * 2)
        self.assertEqual(score_sentence(sentence, [(0, 1, 'さん', None), (1, 2, 'ほん', None)]),
                         [('ok', True, True, False), ('ok', False, True, False)])
        sentence = {'text': '一緒', 'spans': [span(0, 2, '一緒', 'いっしょ')]}
        self.assertEqual(score_sentence(sentence, [(0, 2, 'いつしよ', None)]), [('ok', True, True, False)])

    def test_surface_reading(self):
        self.assertEqual(surface_reading('行っ', '行く', 'いく'), 'いっ')
        self.assertEqual(surface_reading('学校', '学校', 'がっこう'), 'がっこう')
        self.assertIsNone(surface_reading('行っ', '行く', None))
        self.assertIsNone(surface_reading('云っ', '言う', 'いう'))


class MetricsTest(unittest.TestCase):
    def test_values_and_intervals(self):
        sentences = [{'id': n, 'text': '方', 'spans': [span(0, 1, '方', 'ほう' if n % 2 else 'かた')]} for n in range(40)]
        items = items_of(sentences)
        # every ほう right, half the かた right
        results = [('ok', True, n % 2 == 1 or n % 4 == 0, n % 2 == 1) for n in range(40)]
        results = [(s, r, r, shown) for s, _, r, shown in results]
        m = metrics(items, results, len(sentences), rounds=200)
        self.assertAlmostEqual(m['word list'][0], 0.75)
        self.assertAlmostEqual(m['heteronym macro'][0], 0.75)  # (1.0 + 0.5) / 2
        self.assertAlmostEqual(m['shown precision'][0], 1.0)
        self.assertAlmostEqual(m['coverage'][0], 0.5)
        for name in ('word list', 'heteronym macro', 'coverage'):
            value, low, high = m[name]
            self.assertTrue(low <= value <= high and low < high, name)
        self.assertEqual(m['align fail'][0], 0)
        self.assertNotIn('shown precision', metrics(items, [(s, r, r, False) for s, r, _, _ in results], 40, rounds=10))

    def test_compare(self):
        old = {'sets': {'s': {'keys': ['1:0', '2:0', '3:0'], 'systems': {'ours': {'right': '100'}}}}}
        new = {'sets': {'s': {'keys': ['1:0', '2:0', '3:0'], 'systems': {'ours': {'right': '011'}}}}}
        compare(old, new)
        c = new['sets']['s']['compare']['ours']
        self.assertEqual((c['fixed'], c['broken']), (2, 1))
        self.assertAlmostEqual(_binomial_p(1, 3), 1.0)
        self.assertAlmostEqual(_binomial_p(0, 10), 2 / 1024)


class GoldTest(unittest.TestCase):
    def test_tatoeba(self):
        s = tatoeba_sentence(1, '[場所|ば|しょ]は[明日|あした]、[行|い]った')
        self.assertEqual(s['text'], '場所は明日、行った')
        self.assertEqual([(x['b'], x['e'], x['reading']) for x in s['spans']], [(0, 2, 'ばしょ'), (3, 5, 'あした'), (6, 7, 'い')])
        self.assertIsNone(tatoeba_sentence(2, '[壊れ|こわ'))

    def test_ndl(self):
        self.assertEqual(ndl_readings('両手', 'りょーて'), ['りょうて', 'りょおて'])
        self.assertIn('いう', ndl_readings('言う', 'ゆう'))
        self.assertIn('はなぢ', ndl_readings('鼻血', 'はなじ'))
        tsv = '行番号: 1\t\t\n夜の刀\t\t[入力文]\n\tよるの かたな\t[入力 読み]\n夜\tよる\t漢字\nの\tの\tひらがな\n\t \t分かち書き\n刀\tかたな\t漢字\n'
        self.assertEqual(list(ndl_lines(tsv)), [('夜の刀', [span(0, 1, '夜', 'よる'), span(2, 3, '刀', 'かたな')])])


if __name__ == '__main__':
    unittest.main()
