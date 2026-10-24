"""Sudachi tokens with their offsets in the text, as the readings in context use them
(SudachiDict-core unless chosen otherwise, split mode C), and the Words read from them."""
import os
import re
from typing import NamedTuple

HAS_CONTENT = re.compile(r'[0-9A-Za-z぀-ヿ㐀-䶿一-鿿豈-﫿０-ｚ々]')


class Word(NamedTuple):
    start: int  # offset of the word's token in the text
    end: int
    form: str  # dictionary form (行った: 行く)
    reading: str | None  # hiragana, of the dictionary form; None when nothing gives one
    source: str  # 'ruby', 'rule', 'model', 'only' (the list has one reading), 'default', 'dictionary' (Sudachi),
    # 'book' (a name's ruby earlier in the book, see Reader.read's `carry`), 'terms' (a term dictionary you
    # supplied, Reader's `terms`, for a word the list and JMdict lack)
    # or 'counter' (a number + counter span, 三本, over the tokens' own Words, and the counter in it)
    certainty: float | None  # see docs/how-it-works.md; None when unknown


class Token:
    """The parts of a Sudachi morpheme the analysis uses. Morphemes keep their whole
    tokenizer result alive, which on very long books ran workers out of memory."""
    __slots__ = ('_surface', '_dictionary_form', '_normalized_form', '_pos', '_reading', 'begin', 'end')

    def __init__(self, surface: str, dictionary_form: str, normalized_form: str, pos: tuple, reading: str = '',
                 begin: int = 0):
        self.begin = begin  # offset in the analysed text
        self.end = begin + len(surface)
        self._surface = surface
        self._dictionary_form = dictionary_form
        self._normalized_form = normalized_form
        self._pos = pos
        self._reading = reading

    def surface(self) -> str:
        return self._surface

    def dictionary_form(self) -> str:
        return self._dictionary_form

    def normalized_form(self) -> str:
        return self._normalized_form

    def part_of_speech(self) -> tuple:
        return self._pos

    def reading_form(self) -> str:
        return self._reading


def sudachi_dictionary(dictionary: str | None = None) -> str:
    """The SudachiDict to load: `dictionary`, else $YURIGANA_SUDACHI_DICT, else core (small, full
    or core; full and small need their package: pip install "yurigana[full]")."""
    return dictionary or os.environ.get('YURIGANA_SUDACHI_DICT') or 'core'


class SudachiTokenizer:
    """Content tokens (no punctuation or spaces) of a text, with their offsets in it."""

    def __init__(self, dictionary: str | None = None):
        from sudachipy import Dictionary, SplitMode
        self.tokenizer = Dictionary(dict=sudachi_dictionary(dictionary)).create(SplitMode.C)
        self._pos_by_id: dict[int, tuple] = {}

    def tokens(self, text: str):
        # Sudachi limits input size; paragraphs are short, long ones are cut at sentence ends.
        offset = 0
        for paragraph in text.split('\n'):
            start = offset
            offset += len(paragraph) + 1
            while paragraph:
                chunk = paragraph[:5000]
                if len(paragraph) > 5000:
                    cut = max(chunk.rfind(c) for c in '。！？')
                    chunk = paragraph[: cut + 1] if cut > 0 else chunk
                paragraph = paragraph[len(chunk):]
                chunk_start, start = start, start + len(chunk)
                for morpheme in self.tokenizer.tokenize(chunk):
                    pos_id = morpheme.part_of_speech_id()
                    pos = self._pos_by_id.get(pos_id) or self._pos_by_id.setdefault(pos_id, morpheme.part_of_speech())
                    surface = morpheme.surface()
                    if pos[0] not in ('補助記号', '空白') and HAS_CONTENT.search(surface):
                        yield Token(surface, morpheme.dictionary_form(), morpheme.normalized_form(), pos,
                                    morpheme.reading_form(), chunk_start + morpheme.begin())
