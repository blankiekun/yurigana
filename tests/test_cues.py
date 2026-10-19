import re
import unittest

from yurigana import cues


class CuesTest(unittest.TestCase):
    def test_words(self):
        self.assertEqual(cues.words(cues.INSECT, 'ぐう', '三味線'), '(?:三味線|ぐう|虫)')
        self.assertTrue(re.fullmatch(cues.words(cues.PLACE - {'駅'}), '広場'))
        self.assertFalse(re.fullmatch(cues.words(cues.PLACE - {'駅'}), '駅'))

    def test_classes_are_plain_words(self):
        for name, value in vars(cues).items():
            if isinstance(value, frozenset):
                for word in value:
                    self.assertRegex(word, r'^[ぁ-ゖァ-ヺー一-鿿々]+$', name)
