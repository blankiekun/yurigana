"""Tests for yurigana.evaluate's scorer and gold converters (no tokeniser needed)."""
import importlib.util
import unittest

from yurigana.evaluate import (_binomial_p, compare, items_of, make_system, metrics, ndl_lines, ndl_readings,
                               score_sentence, surface_reading, tatoeba_sentence, yomikata_pieces)
from yurigana.evaluate import add_alts, item_tags, prediction_tokens, read_exclude, triage


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

    def test_token_cut_at_kanji_runs(self):
        # gold reads only 頃: a token 幼い頃 is cut at its kanji runs, where its kana place the cut one way
        sentence = {'text': '幼い頃は', 'spans': [span(2, 3, '頃', 'ころ')]}
        self.assertEqual(score_sentence(sentence, [(0, 3, 'おさないころ', True), (3, 4, 'は', None)]), [('ok', True, True, True)])
        self.assertEqual(score_sentence(sentence, [(0, 3, 'おさないこら', True), (3, 4, 'は', None)]), [('ok', False, False, True)])
        # 姉は母 あねははは could be cut あね|はは or あねは|は: scored as a whole, so the unlabelled 姉 fails alignment
        sentence = {'text': '姉は母', 'spans': [span(2, 3, '母', 'はは')]}
        self.assertEqual(score_sentence(sentence, [(0, 3, 'あねははは', None)]), [('align', False, False, False)])

    def test_unlabelled_numerals(self):
        # NDL gives 三 no reading: 三人 as one token is scored on 人, other unlabelled kanji still fail
        sentence = {'text': '三人', 'spans': [span(1, 2, '人', 'にん')]}
        self.assertEqual(score_sentence(sentence, [(0, 2, 'さんにん', None)]), [('ok', True, True, False)])
        self.assertEqual(score_sentence(sentence, [(0, 2, 'みたり', None)]), [('ok', False, False, False)])
        sentence = {'text': '達人', 'spans': [span(1, 2, '人', 'じん')]}
        self.assertEqual(score_sentence(sentence, [(0, 2, 'たつじん', None)]), [('align', False, False, False)])

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

    def test_overlapping_tokens(self):
        # a counter span (三本) next to its own tokens at the same start: scored as the span, in any order
        sentence = {'id': 7, 'text': '三本', 'spans': [span(0, 2, '三本', 'さんぼん')]}
        for tokens in ([(0, 2, 'さんぼん', True, 'rule'), (0, 1, 'さん', None), (1, 2, 'ほん', None)],
                       [(0, 1, 'さん', None), (1, 2, 'ほん', None), (0, 2, 'さんぼん', True, 'rule')]):
            self.assertEqual(score_sentence(sentence, tokens), [('ok', True, True, True)])

    def test_misses(self):
        sentence = {'id': 7, 'text': '三本', 'spans': [span(0, 2, '三本', 'さんぼん')]}
        misses = []
        score_sentence(sentence, [(0, 2, 'みもと', False, 'dictionary')], misses)
        score_sentence(sentence, [(0, 2, 'さんぼん', True, 'rule')], misses)
        self.assertEqual(misses, [(7, '三本', 'さんぼん', 'みもと', 'dictionary')])

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


class TagsTest(unittest.TestCase):
    RANKS = {('生', 'せい'): 1, ('生', 'なま'): 2, ('人', 'ひと'): 1, ('学校', 'がっこう'): 1}

    def test_tags(self):
        sentences = [{'id': 1, 'text': '生だ', 'spans': [span(0, 1, '生', 'なま')]},  # listed two ways: hard
                     {'id': 2, 'text': '学校', 'spans': [span(0, 1, '学', 'がく')]},  # 校 has no ruby: partial
                     {'id': 3, 'text': '三人', 'spans': [span(1, 2, '人', 'にん')]},  # numerals are no partial
                     {'id': 4, 'text': '海と宇宙', 'spans': [span(0, 1, '海', 'かい'),  # unlisted, KANJIDIC spells it
                                                         span(2, 4, '宇宙', 'そら')]}]  # gikun: not kanjidic_only
        tags = item_tags('s', sentences, self.RANKS)
        self.assertEqual(tags['listed'], [2, 0, 1, 0, 0])
        self.assertEqual(tags['partial'], '01000')
        self.assertEqual(tags['kanjidic_only'], '01010')  # 学 alone isn't listed either
        self.assertEqual(tags['number'], '00000')  # 人 itself holds no numeral; without Sudachi no 助数詞
        self.assertEqual(tags['clean'], '10101')
        self.assertEqual(tags['hard'], '10000')
        lemma = [{'id': 5, 'text': '生', 'spans': [{**span(0, 1, '生', 'せい'), 'lemma': '人'}]}]
        self.assertEqual(item_tags('s', lemma, self.RANKS)['listed'], [1])

    def test_exclude(self):
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.tsv', delete=False) as f:
            f.write('# set\tid\tsurface\ns\t1\t生\n')
        sentences = [{'id': 1, 'text': '生', 'spans': [span(0, 1, '生', 'なま')]}]
        tags = item_tags('s', sentences, self.RANKS, read_exclude(f.name))
        self.assertEqual((tags['excluded'], tags['clean'], tags['hard']), ('1', '0', '0'))

    def test_clean_and_hard_metrics(self):
        sentences = [{'id': n, 'text': '生', 'spans': [span(0, 1, '生', 'なま')]} for n in range(4)]
        items = items_of(sentences)
        results = [('ok', r, r, False) for r in (True, False, True, True)]
        m = metrics(items, results, 4, rounds=10, subsets={'clean': {'0:0', '1:0', '2:0'}, 'hard': {'1:0'}})
        self.assertAlmostEqual(m['word list'][0], 0.75)
        self.assertAlmostEqual(m['clean'][0], 2 / 3)
        self.assertAlmostEqual(m['hard'][0], 0.0)
        self.assertEqual((m['clean items'], m['hard items']), (3, 1))
        self.assertNotIn('clean', metrics(items, results, 4, rounds=10))

    def test_compare_subsets(self):
        old = {'sets': {'s': {'keys': ['1:0', '2:0', '3:0'], 'systems': {'ours': {'right': '100'}}}}}
        new = {'sets': {'s': {'keys': ['1:0', '2:0', '3:0'], 'systems': {'ours': {'right': '011'}},
                              'tags': {'clean': '011', 'hard': '001'}}}}
        compare(old, new)
        c = new['sets']['s']['compare']['ours']
        self.assertEqual((c['fixed'], c['broken']), (2, 1))
        self.assertEqual((c['clean']['fixed'], c['clean']['broken'], c['clean']['new']), (2, 0, 1.0))
        self.assertEqual((c['hard']['fixed'], c['hard']['old']), (1, 0.0))


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


class ReviewTest(unittest.TestCase):
    def test_prediction_tokens(self):
        sentence = {'text': '人気のない道', 'spans': [span(0, 2, '人気', 'ひとけ'), span(5, 6, '道', 'みち')]}
        tokens = prediction_tokens('人気[ヒトケ]のない道[どう]', sentence['text'])
        self.assertEqual(tokens[0], (0, 2, 'ひとけ', None))
        self.assertEqual(score_sentence(sentence, tokens), [('ok', True, True, False), ('ok', False, False, False)])
        self.assertIsNone(prediction_tokens('人気[ひとけ]の無い道[みち]', sentence['text']))
        self.assertEqual(score_sentence(sentence, None), [('align', False, False, False)] * 2)

    def test_alts(self):
        import tempfile
        sets = {'s': [{'id': 3, 'text': '明日', 'spans': [span(0, 2, '明日', 'あした')]}]}
        with tempfile.NamedTemporaryFile('w', suffix='.tsv', delete=False) as f:
            f.write('# set\tid\tsurface\treading\ns\t3\t明日\tアス\n')
        add_alts(sets, f.name)
        self.assertEqual(sets['s'][0]['spans'][0]['alts'], ['あす'])

    def test_triage(self):
        sentences = [{'id': n, 'text': '方', 'spans': [span(0, 1, '方', 'かた')]} for n in range(3)]
        right = {'ours': '010', 'a': '001', 'b': '001', 'c': '100'}
        readings = {'ours': [(0, 1, 'ほう'), (0, 1, 'かた'), (0, 1, None)],
                    'a': [(0, 1, 'ほう'), (0, 1, 'ほう'), (0, 1, 'かた')],
                    'b': [(0, 1, 'ほう'), (0, 1, 'ほう'), (0, 1, 'かた')],
                    'c': [(0, 1, 'かた'), (0, 1, 'みち'), (0, 1, 'みち')]}
        self.assertEqual(triage('s', sentences, right, readings), [
            ('gold', 's', 0, '方', 'かた', 'ほう', 'ours,a,b', 'ほう'),  # 3 of 4 agree against the gold
            # item 1: a, b agree on ほう, but 2 of 4 readings isn't a majority
            ('ours', 's', 2, '方', 'かた', 'かた', 'a,b', '')])  # ours gave none, 2 of 3 others right


class BaselineTest(unittest.TestCase):
    def test_yomikata_pieces(self):
        self.assertEqual(yomikata_pieces('{人気/ひとけ}のない{一日}'), [('人気', 'ひとけ'), ('一日', None)])

    def test_baselines_read_a_sentence(self):
        # ginza and yomikata live in their own environment (see the docstring): skipped elsewhere
        sentence = {'text': '人気のない道を歩いた。', 'spans': [span(0, 2, '人気', 'ひとけ'), span(5, 6, '道', 'みち'),
                                                         span(7, 8, '歩', 'ある')]}
        for system, module in (('ginza', 'ja_ginza'), ('yomikata', 'yomikata')):
            with self.subTest(system):
                if importlib.util.find_spec(module) is None:
                    self.skipTest(f'{module} is not installed')
                results = score_sentence(sentence, make_system(system)(sentence['text']))
                self.assertEqual([r[0] for r in results], ['ok'] * 3)
                self.assertTrue(results[1][2] and results[2][2])


if __name__ == '__main__':
    unittest.main()
