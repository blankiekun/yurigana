import os
import unittest
from unittest import mock

from yurigana.tokens import sudachi_dictionary


class DictionaryTest(unittest.TestCase):
    def test_core_unless_chosen(self):
        with mock.patch.dict(os.environ, {'YURIGANA_SUDACHI_DICT': ''}):
            self.assertEqual(sudachi_dictionary(), 'core')
        with mock.patch.dict(os.environ, {'YURIGANA_SUDACHI_DICT': 'full'}):
            self.assertEqual(sudachi_dictionary(), 'full')
            self.assertEqual(sudachi_dictionary('small'), 'small')  # the argument wins


if __name__ == '__main__':
    unittest.main()
