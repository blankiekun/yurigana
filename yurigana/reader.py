"""The one-call entry point: Reader().read(text, hints) gives each kanji word's reading."""
import json
import math
import os
import re
from collections import defaultdict
from typing import NamedTuple

from .counters import COUNTERS, spans as counter_spans
from .readings import DEFAULT_READINGS, HAS_KANJI, _HIRAGANA_WORD, conjugated_reading, context_reading, is_kanji, ruby_reading, to_hiragana
from .reading_model import PUBLIC_TABLE, load_tables

KANJI_READINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanji-readings.json')


_NUMERAL = re.compile(r'^[0-9０-９〇一二三四五六七八九十百千万億兆]+$')
_MAX_COMPOUND = 4  # tokens


class Word(NamedTuple):
    start: int  # offset of the word's token in the text
    end: int
    form: str  # dictionary form (行った: 行く)
    reading: str | None  # hiragana, of the dictionary form; None when nothing gives one
    source: str  # 'ruby', 'rule', 'model', 'only' (the list has one reading), 'default', 'dictionary' (Sudachi)
    # or 'counter' (a number + counter span, 三本, over the tokens' own Words, and the counter in it)
    certainty: float | None  # see the README; None when unknown


def _end(token):
    return token.begin + len(token.surface())


class _Any:
    """Every reading is known: no list given."""
    def __contains__(self, item):
        return True


_VOICED = {'か': 'が', 'き': 'ぎ', 'く': 'ぐ', 'け': 'げ', 'こ': 'ご', 'さ': 'ざ', 'し': 'じ', 'す': 'ず',
           'せ': 'ぜ', 'そ': 'ぞ', 'た': 'だ', 'ち': 'ぢ', 'つ': 'づ', 'て': 'で', 'と': 'ど', 'は': 'ばぱ',
           'ひ': 'びぴ', 'ふ': 'ぶぷ', 'へ': 'べぺ', 'ほ': 'ぼぽ'}


class PlainReadings:
    """(form, reading) is known when the reading is spelled by the form's kanji readings (on and
    kun of 常用/人名用 kanji, KANJIDIC2) and its kana, with rendaku and a final っ: the JS
    isPlainReading. The ruby check without a list: gikun (そら over 宇宙) and jukujikun don't pass."""

    def __init__(self, path: str = KANJI_READINGS):
        with open(path, encoding='utf-8') as f:
            self.readings = {k: v.split(' ') for k, v in json.load(f).items()}

    @staticmethod
    def _variants(reading: str):
        for start in reading[0] + _VOICED.get(reading[0], ''):
            word = start + reading[1:]
            yield word
            if len(word) > 1 and word[-1] in 'つちくき':
                yield word[:-1] + 'っ'

    def __contains__(self, item) -> bool:
        base, reading = item

        def match(i: int, j: int) -> bool:
            if i == len(base):
                return j == len(reading)
            char = base[i]
            if not is_kanji(char) and char != '々':
                return reading[j:j + 1] == to_hiragana(char) and match(i + 1, j + 1)
            own = self.readings.get(base[i - 1] if char == '々' and i > 0 else char, ())
            return any(reading.startswith(form, j) and match(i + 1, j + len(form))
                       for r in own for form in self._variants(r))
        return match(0, 0)


class Reader:
    """Readings of kanji words in context. The first that gives one wins: the book's ruby
    (`hints`), a context rule, the reading model, then Sudachi's dictionary reading.

    known: (form, reading) pairs a reading must be one of (a set, the keys of a dict, or the
        path of a rank-based Yomitan frequency list). Without one, ruby must be a plain reading
        of its kanji (PlainReadings) and rules and the model are trusted.
    tables: reading-model tables built from your own library, tried before the public one;
        missing files are skipped.
    tokenizer: anything with tokens(text) like SudachiTokenizer (the default)."""

    def __init__(self, known=None, tables=(), tokenizer=None):
        if isinstance(known, str):
            from .yomitan import reading_ranks
            known = reading_ranks(known)
        self.known = _Any() if known is None else known
        self.ruby_known = PlainReadings() if known is None else known
        # The list's hiragana readings per form, and the forms it gives exactly one.
        self.readings = defaultdict(list)
        for form, reading in known or ():
            if _HIRAGANA_WORD.match(reading):
                self.readings[form].append(reading)
        self.only = {form: readings[0] for form, readings in self.readings.items() if len(readings) == 1}
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
        next_token = 0
        counted = list(counter_spans(text, tokens))
        for i, token in enumerate(tokens):
            if i < next_token:
                continue
            compound = self._compound(tokens, i, hint_at, counted)
            if compound:
                next_token, word = compound
                words.append(word)
                continue
            surface, form = token.surface(), token.dictionary_form()
            if not HAS_KANJI.search(surface):
                continue
            words.append(Word(token.begin, token.begin + len(surface), form,
                              *self._reading(text, tokens, i, surface, form, hint_at)))
        # A number and its counter: one Word for the span (三本 さんぼん); the counter's own Word
        # keeps the counter's plain reading (本 ほん), as source 'counter', never 'only' with a
        # certainty its reading in the span doesn't have. Ruby over any of it wins.
        at = {w.start: n for n, w in enumerate(words)}
        for start, number_end, end, number, counter in counted:
            if any(s < end and e > start for s, (e, _) in hint_at.items()):
                continue
            words.append(Word(start, end, text[start:end], number + (counter or ''), 'counter', None))
            if counter and number_end in at and words[at[number_end]].end == end:
                own = words[at[number_end]]
                plain = COUNTERS.get(next(t.normalized_form() for t in tokens if t.begin == number_end))
                words[at[number_end]] = own._replace(reading=plain[0] if plain and counter != 'ぶん' else own.reading, source='counter',
                                                     certainty=None)
        words.sort(key=lambda w: (w.start, -w.end))
        return words

    def _compound(self, tokens, i, hint_at, counted=()):
        """(next token, Word) for 2-4 adjacent tokens from i (the longest) whose joined form the list gives one
        reading: 三|日|月 みかづき, 身の上|話 みのうえばなし, 一|石|二鳥 いっせきにちょう. Left out:
        spans with particles or ending in kana (the list has phrases such as 彼の かの), spans with
        ruby, a number and its counter (一|枚, or any span inside one of `counted`, the counter spans,
        which read() reads) and spans next to a number (１|日|中, 第|一)."""
        if not self.only or not HAS_KANJI.search(tokens[i].surface()):
            return None
        if i and _NUMERAL.match(tokens[i - 1].surface()) and _end(tokens[i - 1]) == tokens[i].begin:
            return None
        for n in range(min(_MAX_COMPOUND, len(tokens) - i), 1, -1):
            span = tokens[i:i + n]
            begin, end = span[0].begin, _end(span[-1])
            if (any(_end(a) != b.begin for a, b in zip(span, span[1:]))
                    or any(t.part_of_speech()[0] in ('助詞', '助動詞') for t in span)
                    or not HAS_KANJI.search(span[-1].surface()) or _NUMERAL.match(span[-1].surface())
                    or (n == 2 and _NUMERAL.match(span[0].surface()))
                    or any(start in hint_at for start in range(begin, end))
                    or any(s <= begin and end <= e for s, _, e, _, _ in counted)):
                continue
            form = ''.join(t.surface() for t in span[:-1]) + span[-1].dictionary_form()
            if form in self.only:
                return i + n, Word(begin, end, form, self.only[form], 'only', 1.0)
        return None

    def _reading(self, text, tokens, i, surface, form, hint_at):
        begin = tokens[i].begin
        reading = hint_at and ruby_reading(hint_at, begin, surface, form, self.ruby_known)
        if reading:
            return reading, 'ruby', 1.0
        previous = tokens[i - 1] if i and tokens[i - 1].begin + len(tokens[i - 1].surface()) == begin else None
        reading = context_reading(text, begin, surface, form, self.known, previous and previous.part_of_speech())
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
        if surface != form:  # the listed reading that conjugates to Sudachi's reading of the surface
            reading = conjugated_reading(surface, form, to_hiragana(tokens[i].reading_form()), self.readings.get(form, ()))
            if reading:
                return reading, 'dictionary', None
        default = DEFAULT_READINGS.get((form, sudachi))
        if default and (form, default) in self.known:
            return default, 'default', None
        entry = self.model and self.model.forms.get(form)
        if entry and sudachi in entry[0]:  # the reading's share in the table's prior
            priors = [math.exp(p) for p in entry[1]]
            return sudachi, 'dictionary', round(priors[entry[0].index(sudachi)] / sum(priors), 3)
        return sudachi, 'dictionary', None
