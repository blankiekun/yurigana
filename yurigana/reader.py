"""The one-call entry point: Reader().read(text, hints) gives each kanji word's reading."""
import gzip
import json
import math
import os
from collections import Counter
from typing import NamedTuple

from .readings import DEFAULT_READINGS, HAS_KANJI, _HIRAGANA_WORD, context_reading, ruby_reading, to_hiragana
from .reading_model import PUBLIC_TABLE, load_tables

JMDICT_PAIRS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jmdict-pairs.json.gz')


def jmdict_pairs(path: str = JMDICT_PAIRS) -> set:
    """The (form, reading) pairs of JMdict (tools/jmdict_pairs.py): the default reading list."""
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return {(form, r) for form, readings in json.load(f)['pairs'].items() for r in readings.split(' ')}


class Word(NamedTuple):
    start: int  # offset of the word's token in the text
    end: int
    form: str  # dictionary form (行った: 行く)
    reading: str | None  # hiragana, of the dictionary form; None when nothing gives one
    source: str  # 'ruby', 'rule', 'model', 'only' (the list has one reading), 'default' or 'dictionary' (Sudachi)
    certainty: float | None  # see the README; None when unknown


class Reader:
    """Readings of kanji words in context. The first that gives one wins: the book's ruby
    (`hints`), a context rule, the reading model, then Sudachi's dictionary reading.

    known: (form, reading) pairs a reading must be one of (a set, the keys of a dict, or the
        path of a rank-based Yomitan frequency list). Without one, JMdict's (jmdict_pairs).
    tables: reading-model tables built from your own library, tried before the public one;
        missing files are skipped.
    tokenizer: anything with tokens(text) like SudachiTokenizer (the default)."""

    def __init__(self, known=None, tables=(), tokenizer=None):
        if isinstance(known, str):
            from .yomitan import reading_ranks
            known = reading_ranks(known)
        self.known = jmdict_pairs() if known is None else known
        # Forms the list gives exactly one reading, a hiragana one (not ぺーじ for 頁).
        counts = Counter(form for form, reading in self.known)
        self.only = {form: reading for form, reading in self.known if counts[form] == 1
                     and _HIRAGANA_WORD.match(reading)}
        self.model = load_tables([*tables, PUBLIC_TABLE])
        if tokenizer is None:
            from .tokens import SudachiTokenizer
            tokenizer = SudachiTokenizer()
        self.tokenizer = tokenizer

    def read(self, text: str, hints=()) -> list:
        """A Word per token with kanji in `text`. `hints`: the ruby, (start, end, reading) offsets
        in `text`, as yurigana.text's aozora_text and book_text give them."""
        hint_at = {start: (end, reading) for start, end, reading in hints}
        tokens = list(self.tokenizer.tokens(text))
        words = []
        for i, token in enumerate(tokens):
            surface, form = token.surface(), token.dictionary_form()
            if not HAS_KANJI.search(surface):
                continue
            words.append(Word(token.begin, token.begin + len(surface), form,
                              *self._reading(text, tokens, i, surface, form, hint_at)))
        return words

    def _reading(self, text, tokens, i, surface, form, hint_at):
        begin = tokens[i].begin
        reading = hint_at and ruby_reading(hint_at, begin, surface, form, self.known)
        if reading:
            return reading, 'ruby', 1.0
        reading = context_reading(text, begin, surface, form, self.known)
        if reading:
            return reading, 'rule', 1.0
        reading = self.model and self.model.reading(text, tokens, i, form, self.known)
        if reading:
            return reading, 'model', round(self.model.posterior(form, self.model.context(text, tokens, i))[1], 3)
        # Sudachi's reading, of an unconjugated word only (a conjugated one reads its surface: 行っ).
        sudachi = to_hiragana(tokens[i].reading_form()) if surface == form else None
        only = self.only.get(form)
        if only and sudachi in (None, only):
            return only, 'only', 1.0
        default = DEFAULT_READINGS.get((form, sudachi))
        if default and (form, default) in self.known:
            return default, 'default', None
        entry = self.model and self.model.forms.get(form)
        if entry and sudachi in entry[0]:  # the reading's share in the table's prior
            priors = [math.exp(p) for p in entry[1]]
            return sudachi, 'dictionary', round(priors[entry[0].index(sudachi)] / sum(priors), 3)
        return sudachi, 'dictionary', None
