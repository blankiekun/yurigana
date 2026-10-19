"""Sudachi tokens with their offsets in the text, as the readings in context use them
(SudachiDict-full, split mode C)."""
import re

HAS_CONTENT = re.compile(r'[0-9A-Za-z぀-ヿ㐀-䶿一-鿿豈-﫿０-ｚ々]')


class Token:
    """The parts of a Sudachi morpheme the analysis uses. Morphemes keep their whole
    tokenizer result alive, which on very long books ran workers out of memory."""
    __slots__ = ('_surface', '_dictionary_form', '_normalized_form', '_pos', '_reading', 'begin')

    def __init__(self, surface: str, dictionary_form: str, normalized_form: str, pos: tuple, reading: str = '',
                 begin: int = 0):
        self.begin = begin  # offset in the analysed text
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


class SudachiTokenizer:
    """Content tokens (no punctuation or spaces) of a text, with their offsets in it."""

    def __init__(self, dictionary: str = 'full'):
        from sudachipy import Dictionary, SplitMode
        self.tokenizer = Dictionary(dict=dictionary).create(SplitMode.C)
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
