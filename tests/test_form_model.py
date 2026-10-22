"""Tests for yurigana.form_model and its training tool (tools/form_model.py)."""
import importlib.util
import os
import unittest
from unittest import mock

from yurigana.form_model import FormModel, features

try:
    import sudachipy  # noqa: F401
except ImportError:
    sudachipy = None

TOOL = os.path.join(os.path.dirname(__file__), '..', 'tools', 'form_model.py')


class FormModelTest(unittest.TestCase):
    def test_probabilities(self):
        # two readings: one weight, the second reading's log-odds
        model = FormModel({'間': {'readings': ['あいだ', 'ま'], 'threshold': 0.9, 'lr': [[-1.0], {'R1=に': [2.0]}]}})
        self.assertAlmostEqual(model.probabilities('間', ['R1=に', 'L1=の'])['ま'], 0.731059, places=5)
        self.assertAlmostEqual(model.probabilities('間', [])['あいだ'], 0.731059, places=5)
        three = FormModel({'下': {'readings': ['した', 'しも', 'もと'], 'lr': [[0.0, 0.0, 0.0], {'L1=の': [1.0, 0.0, 1.0]}]}})
        p = three.probabilities('下', ['L1=の'])
        self.assertAlmostEqual(p['した'], p['もと'])
        self.assertAlmostEqual(sum(p.values()), 1.0)
        self.assertEqual(FormModel({'一度': {'readings': ['いちど'], 'p': 0.99, 'threshold': 0.98}}).probabilities('一度', []),
                         {'いちど': 0.99})

    def test_committed_model_loads(self):
        model = FormModel.load()
        self.assertIn('間', model)
        for form, entry in model.forms.items():
            p = model.probabilities(form, [])
            self.assertAlmostEqual(sum(p.values()), 1.0 if 'p' not in entry else entry['p'], places=6, msg=form)


@unittest.skipIf(sudachipy is None, 'Sudachi not installed')
class FeaturesTest(unittest.TestCase):
    def test_tool_reads_the_runtime_features(self):
        from yurigana import Reader
        spec = importlib.util.spec_from_file_location('form_model_tool', TOOL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        reader = Reader()
        texts = ['その声の主の名を僕は呼んだ。', '一行目\n二人の間に、少し距離がある。窓の下で待つ。', '「良い家だな」と彼は日本の風を描いた。']
        asked = 0
        for text in texts:
            seen = []
            real = reader.form_model.reading

            def spy(text_, tokens, i, form):
                seen.append((tokens[i].begin, features(text_, tokens, i)))
                return real(text_, tokens, i, form)
            with mock.patch.object(reader.form_model, 'reading', spy):
                reader.read(text)
            asked += len(seen)
            for b, found in seen:
                self.assertEqual(tool.row_features(reader, text, b), found)
        self.assertGreater(asked, 3)
        self.assertIn('Pp1=名詞-普通名詞', tool.row_features(reader, texts[1], texts[1].index('間')))
        self.assertIn('L1=^', tool.row_features(reader, texts[1], texts[1].index('二')))  # the line starts the window

    def test_shown_words_unchanged(self):
        # the classifiers change hidden readings only: every shown Word is the one without them (T514)
        from yurigana import Reader
        from yurigana.evaluate import SHOWN
        reader = Reader()
        texts = ['木の下で二人の間に座った。', '彼は頭を振り、中に入れた。', '今日は一日中家にいた。金五百両を渡す。', '日本の上の方に表がある。']
        hidden = 0
        for text in texts:
            words = reader.read(text)
            classifier, reader.form_model = reader.form_model, FormModel({})
            plain = reader.read(text)
            reader.form_model = classifier
            self.assertEqual([w for w in words if w.source in SHOWN or w.source == 'counter'],
                             [w for w in plain if w.source in SHOWN or w.source == 'counter'], text)
            hidden += sum(a != b for a, b in zip(words, plain))
        self.assertGreater(hidden, 0)


if __name__ == '__main__':
    unittest.main()
