"""yurigana: readings of Japanese kanji words in context, from a book's own ruby, hand rules,
a small reading model and Sudachi. See README.md."""
from functools import lru_cache

from .reader import Reader, Word
from .readings import context_reading, ruby_reading
from .reading_model import PUBLIC_TABLE, RULE_FORMS, ReadingModel, load_tables
from .text import aozora_text, book_text

__all__ = ['furigana', 'Reader', 'Word', 'context_reading', 'ruby_reading', 'PUBLIC_TABLE', 'RULE_FORMS', 'ReadingModel',
           'load_tables', 'aozora_text', 'book_text']
__version__ = '0.5.9'


@lru_cache(maxsize=4)
def _reader(known):
    return Reader(known=known)


def furigana(text: str, known=None) -> str:
    """One sentence (or any text) with furigana: furigana('本を読んだ') → '本[ほん]を読[よ]んだ'.
    `known`: as Reader's (a path is cached, so repeated calls reuse one Reader)."""
    return (_reader(known) if known is None or isinstance(known, str) else Reader(known=known)).furigana(text)
