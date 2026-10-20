"""The one-call entry point: Reader().read(text, hints) gives each kanji word's reading."""
import gzip
import json
import math
import os
import re
from collections import defaultdict
from typing import NamedTuple

from .counters import COUNTERS, is_year, number_reading, number_value, spans as counter_spans
from .readings import _CONTEXT_RULES, DEFAULT_READINGS, MODEL_UNSHOWN, GLUED_CHECKED, HAND_DEFAULTS, HAS_KANJI, glued, _HIRAGANA_WORD, conjugated_reading, context_reading, default_kept, is_kanji, ruby_reading, surface_reading, to_hiragana, unlisted_reading
from .reading_model import PUBLIC_TABLE, load_tables
from .yomitan import extra_readings, preferred

KANJI_READINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanji-readings.json')
JMDICT_PAIRS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jmdict-pairs.json.gz')


def jmdict_readings(path: str = JMDICT_PAIRS) -> dict:
    """form -> JMdict's readings of it, in JMdict's order (tools/jmdict_pairs.py), with ー
    spelled out (ぎょーざ: ぎょうざ, as lists spell it)."""
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return {form: [_long_vowels(r) for r in readings.split(' ')]
                for form, readings in json.load(f)['pairs'].items()}


_VOWEL = {**dict.fromkeys('あかさたなはまやらわがざだばぱぁゃゎ', 'あ'), **dict.fromkeys('いきしちにひみりぎじぢびぴぃ', 'い'),
          **dict.fromkeys('うくすつぬふむゆるぐずづぶぷぅゅ', 'う'), **dict.fromkeys('えけせてねへめれげぜでべぺぇ', 'い'),
          **dict.fromkeys('おこそとのほもよろごぞどぼぽぉょ', 'う')}


def _long_vowels(reading: str) -> str:
    """ー as the kana it stands for after a kana: o-row う, e-row い (こんぺいとー: こんぺいとう)."""
    return re.sub('(?<=(.))ー', lambda m: _VOWEL.get(m.group(1), 'ー'), reading)


def _spelling(reading: str) -> str:
    """One spelling of a reading's sounds: ー spelled out, づ ず and ぢ じ alike (みかづき, みかずき)."""
    return _long_vowels(reading).replace('づ', 'ず').replace('ぢ', 'じ')


_NUMERAL = re.compile(r'^[0-9０-９〇一二三四五六七八九十百千万億兆]+$')
_MAX_COMPOUND = 4  # tokens
_KANJI_RUN = re.compile(r'[㐀-䶿一-鿿豈-﫿々〆ヶ]+')
_KANA_READING = re.compile(r'^[ぁ-ゖー]+$')  # loanwords keep ー: ラーメン屋 らーめんや
_UNITS = re.compile('[十百千万億兆]')
_ONE_UNIT = re.compile('一百|^[万億兆]')
# 一 with the rest of a native word in kana: 一ト月, 一と息 (ひ, と), 一しずく (ひと), 一たい (いっ)
_ONE_KANA = (('ひ', re.compile(r'[トと](?![〇一二三四五六七八九十百千万言云書])[㐀-䶿一-鿿豈-﫿]')),
             ('ひと', re.compile('しずく|すくみ|やすみ|そろい|かど|しきり|すじ|きわ')),
             ('いっ', re.compile('たい|パイ|ぱい|ペン|ぺん|そう')))


class Word(NamedTuple):
    start: int  # offset of the word's token in the text
    end: int
    form: str  # dictionary form (行った: 行く)
    reading: str | None  # hiragana, of the dictionary form; None when nothing gives one
    source: str  # 'ruby', 'rule', 'model', 'only' (the list has one reading), 'default', 'dictionary' (Sudachi),
    # 'book' (a name's ruby earlier in the book, see Reader.read's `carry`)
    # or 'counter' (a number + counter span, 三本, over the tokens' own Words, and the counter in it)
    certainty: float | None  # see docs/how-it-works.md; None when unknown


def _shared_conjugation(surface, form, readings, ranks) -> bool:
    """Whether a っ-form (行っ, 通っ, 放っ) is also that of another listed verb with another reading, not
    5 times rarer in the list (行く いく, 通る とおる, 放る ほうる; not 分かつ for 分かっ): Sudachi's lemma
    is then a guess. Without ranks, any such verb."""
    if not surface.endswith('っ') or len(surface) < 2:
        return False
    stem = surface[:-1]
    mine = readings.get(form, ())
    best = min((ranks.get((form, r), 0) for r in mine), default=0) if ranks else 0
    others = [stem + end for end in ('う', 'つ', 'る') + (('く',) if stem.endswith('行') else ()) if stem + end != form]
    return any(r not in mine and (not ranks or ranks.get((other, r), 0) <= 5 * best)
               for other in others for r in readings.get(other, ()))


def _end(token):
    return token.begin + len(token.surface())


# Ruby over a name that is a pronoun is flavour (鈴木《あいつ》), never the name's reading.
_PRONOUNS = frozenset('あいつ こいつ そいつ どいつ やつ おれ おまえ かれ かのじょ あのこ あのひと わたし わたくし あたし ぼく'.split())


class _Any:
    """Every reading is known: no list given."""
    def __contains__(self, item):
        return True


_VOICED = {'か': 'が', 'き': 'ぎ', 'く': 'ぐ', 'け': 'げ', 'こ': 'ご', 'さ': 'ざ', 'し': 'じ', 'す': 'ず',
           'せ': 'ぜ', 'そ': 'ぞ', 'た': 'だ', 'ち': 'ぢ', 'つ': 'づ', 'て': 'で', 'と': 'ど', 'は': 'ばぱ',
           'ひ': 'びぴ', 'ふ': 'ぶぷ', 'へ': 'べぺ', 'ほ': 'ぼぽ'}
_UNVOICED = str.maketrans({v: k for k, vs in _VOICED.items() for v in vs})
_VOICED_OBSTRUENT = re.compile('[がぎぐげござじずぜぞだぢづでどばびぶべぼ]')
_HEAD_SURFACE = re.compile('[ァ-ヺー㐀-䶿一-鿿豈-﫿々]')


def _one_voicing_apart(a: str, b: str) -> bool:
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    return len(a) == len(b) and len(diff) == 1 and diff[0][0].translate(_UNVOICED) == diff[0][1].translate(_UNVOICED)


def _split_name(a, b, reading: str) -> dict:
    """{token start: reading} for ruby over two tokens, split where Sudachi's reading of one of
    them ends or starts it (姫野|芽衣 ひめのめい: ひめの + めい), or {}."""
    for known, first in ((to_hiragana(a.reading_form()), True), (to_hiragana(b.reading_form()), False)):
        if known and len(reading) > len(known) and (reading.startswith(known) if first else reading.endswith(known)):
            cut = len(known) if first else len(reading) - len(known)
            return {a.begin: reading[:cut], b.begin: reading[cut:]}
    return {}


def rendaku(reading: str) -> str | None:
    """The reading voiced at its start (たな → だな), or None: it can't voice, or Lyman's law
    (a voiced obstruent later in it, かぜ) keeps it from voicing."""
    voiced = _VOICED.get(reading[:1], '')[:1]
    return voiced and not _VOICED_OBSTRUENT.search(reading[1:]) and voiced + reading[1:] or None


class PlainReadings:
    """(form, reading) is known when the reading is spelled by the form's kanji readings (on and
    kun of 常用/人名用 kanji, KANJIDIC2) and its kana, with rendaku and a final っ: the JS
    isPlainReading. The ruby check without a list, after JMdict's pairs: gikun (そら over 宇宙) doesn't pass."""

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
        path of a rank-based Yomitan frequency list). Without one, JMdict's pairs (the bundled
        jmdict-pairs.json.gz), and ruby may also be a plain reading of its kanji (PlainReadings).
    tables: reading-model tables built from your own library, tried before the public one;
        missing files are skipped.
    tokenizer: anything with tokens(text) like SudachiTokenizer (the default)."""

    def __init__(self, known=None, tables=(), tokenizer=None):
        if isinstance(known, str):
            from .yomitan import reading_ranks
            known = reading_ranks(known)
        jmdict = jmdict_readings()
        if known is None:  # no list: JMdict's pairs, and ruby that spells its kanji (names: 柚木 ゆき)
            known = {(form, reading) for form, readings in jmdict.items() for reading in readings}
            self.plain = PlainReadings()
        else:
            self.plain = None
        self.known = known
        # The list's hiragana readings per form, and the forms it gives exactly one.
        self.readings = defaultdict(list)
        for form, reading in known or ():
            if _HIRAGANA_WORD.match(reading):
                self.readings[form].append(reading)
        # JMdict's readings of the list's forms: a check on the list (names, parser noise) and the
        # order of readings it ranks the same
        self.jmdict = {form: jmdict[form] for form in self.readings if form in jmdict}
        # The list's single readings; `only` (certainty 1.0) when JMdict gives the form that reading
        # too, or has no entry for the form (声がけ こえかけ, 振り幅 しんぷく, 卵型 らんけい in Jiten's list).
        # extra-readings.tsv's pairs don't count for `single` (the voicing of compounds' tails), unless a
        # default gives one (刺青 いれずみ); a form with one is never `only`, though: the extra reading is
        # standard too, so the list's own isn't sure (描く えがく is shown only where a rule reads it).
        extra = extra_readings() - {(form, r) for (form, _), r in DEFAULT_READINGS.items()}
        own = {form: [r for r in readings if (form, r) not in extra] for form, readings in self.readings.items()}
        self.single = {form: readings[0] for form, readings in own.items() if len(readings) == 1}
        self.only = {form: r for form, r in self.single.items() if r in self.jmdict.get(form, (r,))
                     and set(self.readings[form]) == {r}}
        self._tails = None
        # 一X whose ひと…/いっ… reading the list ranks 3+ times above its others (一重 ひとえ, not いちえ):
        # read so when Sudachi splits it 一|X; not forms with context rules (一行 いっこう/いちぎょう)
        ranks = known if isinstance(known, dict) else {}
        self.one_x = {}
        for form, readings in self.readings.items():
            if form[:1] == '一' and len(readings) > 1 and ranks and form not in _CONTEXT_RULES:
                best, second = preferred({r: ranks[form, r] for r in readings}, self.jmdict.get(form, ()))
                if best and best[:2] in ('ひと', 'いっ') and second >= 3 * ranks[form, best]:
                    self.one_x[form] = best
        # 3+-character compounds Sudachi splits that the list doesn't give one reading (_joined): JMdict's
        # one reading of a form the list lacks (羅甸語 らてんご, 水餃子 すいぎょうざ), and the list's reading
        # of a form it ranks 3+ times above its others (力尽く ちからずく, 須弥山 しゅみせん)
        self.jmdict_one = {} if self.plain else {form: readings[0] for form, readings in jmdict.items()
                                                 if len(readings) == 1 and len(form) > 2 and form not in self.readings}
        # (a top rank shared only by spellings of one reading: 三日月 みかづき = みかずき, not 小姑 こじゅうと =
        # こじゅうとめ; and one its kanji spell: the list ranks 真正面 まとも first, books read ましょうめん)
        self.ranked = {}
        plain = PlainReadings() if ranks else None
        for form, readings in self.readings.items():
            if len(readings) > 1 and len(form) > 2 and ranks and form not in _CONTEXT_RULES:
                best, second = preferred({r: ranks[form, r] for r in readings}, self.jmdict.get(form, ()))
                top = {_spelling(r) for r in readings if ranks[form, r] == ranks[form, best]} if best else ()
                if (best in self.jmdict.get(form, ()) and second >= 3 * ranks[form, best] and len(top) == 1
                        and (form, best) in plain):
                    self.ranked[form] = best
        self.model = load_tables([*tables, PUBLIC_TABLE])
        if tokenizer is None:
            from .tokens import SudachiTokenizer
            tokenizer = SudachiTokenizer()
        self.tokenizer = tokenizer

    def segments(self, text: str, hints=()) -> list:
        """`text` cut into (piece, reading of the piece or None): each kanji run with the reading of
        its surface, okurigana and everything else as is (読んだ: [('読', 'よ'), ('んだ', None)])."""
        out, pos = [], 0
        for word in sorted(self.read(text, hints), key=lambda w: (w.start, -w.end)):
            if word.start < pos or word.reading is None:
                continue  # inside a longer word (a counter span's own tokens), or no reading
            surface = text[word.start:word.end]
            reading = surface_reading(surface, word.form, word.reading, text[word.end:word.end + 3])
            if reading is None:
                continue
            if pos < word.start:
                out.append((text[pos:word.start], None))
            out += split_reading(surface, reading)
            pos = word.end
        return out + [(text[pos:], None)] if pos < len(text) else out

    def furigana(self, text: str, hints=()) -> str:
        """`text` with each kanji run's reading after it in brackets: 本を読んだ → 本[ほん]を読[よ]んだ."""
        return ''.join(piece if reading is None else f'{piece}[{reading}]' for piece, reading in self.segments(text, hints))

    def read(self, text: str, hints=(), carry=None) -> list:
        """A Word per token with kanji in `text`. `hints`: the ruby, (start, end, reading) offsets
        in `text`, as yurigana.text's aozora_text and book_text give them.

        carry: a dict, to carry the book's ruby over a name to its later bare occurrences (books
        give a name's reading once): pass {} for a whole book in one text, or the same dict for
        each of a book's texts in order (read() fills it). Only names: a 固有名詞 token or a form
        the list doesn't know, whose hiragana ruby is then taken even when unlisted, also from
        ruby over a two-token full name (姫野芽衣《ひめのめい》: 姫野 ひめの, 芽衣 めい); never a
        common word (hiragana ruby once isn't assumed for its later bare heteronyms), and no
        more after ruby over the form that isn't taken (flavour, katakana) or that differs."""
        hint_at = {start: (end, reading) for start, end, reading in hints}
        tokens = list(self.tokenizer.tokens(text))
        covering, parts = {}, {}
        if carry is not None:
            for start, end, reading in hints:
                covering.update((k, reading) for k in range(start, end))
            for a, b in zip(tokens, tokens[1:]):
                end, reading = hint_at.get(a.begin, (None, ''))
                if end == _end(b) and _end(a) == b.begin and _HIRAGANA_WORD.match(reading):
                    parts.update(_split_name(a, b, reading))
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
            # A lemma the list lacks that is a listed form plus kana (可愛いく: lemma 可愛いい かわいい,
            # its 可愛 read かわ, so the surface came out かわいく): read as that form (可愛い), whose kanji
            # hold the kana, with the lemma's reading when the list gives it (not 終る → 終わる, nor
            # an unconjugated 先き, whose kana would be read twice).
            normalized, lemma = token.normalized_form(), None
            if (surface != form and form not in self.readings and form.startswith(normalized)
                    and re.fullmatch('[ぁ-ゖ]+', form[len(normalized):])):
                lemma = unlisted_reading(surface, form, to_hiragana(token.reading_form()))
                if (normalized, lemma) in self.known and normalized in self.readings:
                    form = normalized
                else:
                    lemma = None
            # An okurigana variant the list reads one way and Sudachi with the reading of its normalized form
            # (幼なく: the list's 幼ない いとけない, Sudachi's おさなく, 幼い おさない): Sudachi's, not the list's only.
            variant = None
            if (not lemma and form in self.single and normalized != form and normalized in self.readings
                    and re.search('[ぁ-ゖ]', surface)):  # not a bare stem Sudachi cut off a compound (割|引致)
                variant = unlisted_reading(surface, form, to_hiragana(token.reading_form()))
                if variant == self.single[form] or (normalized, variant) not in self.known:
                    variant = None
            if carry is None:
                reading, source, certainty = self._checked(form, *self._reading(text, tokens, i, surface, form, hint_at))
            else:
                reading, source, certainty = self._checked(form, *self._carried(text, tokens, i, surface, form, hint_at,
                                                                                 covering, parts, carry))
            if reading is None and lemma:
                reading, source = lemma, 'dictionary'
            if variant and source == 'only':
                reading, source, certainty = self._checked(form, variant, 'dictionary', None)
            if reading and source not in ('ruby', 'counter', 'book'):
                reading = self._voicing(tokens, i, form, reading)
            words.append(Word(token.begin, token.begin + len(surface), form, reading, source, certainty))
        # A number and its counter: one Word for the span (三本 さんぼん); the counter's own Word
        # keeps the counter's plain reading (本 ほん), as source 'counter', never 'only' with a
        # certainty its reading in the span doesn't have. Ruby over any of it wins.
        at = {w.start: n for n, w in enumerate(words)}
        for start, number_end, end, number, counter in counted:
            if any(s < end and e > start for s, (e, _) in hint_at.items()):
                continue
            word = Word(start, end, text[start:end], number + (counter or ''), 'counter', None)
            if start in at and words[at[start]].end == end:  # one token (三軒 みのき, 一回 いちかい)
                words[at[start]] = word
            else:
                words.append(word)
            if counter and number_end in at and words[at[number_end]].end == end:
                own = words[at[number_end]]
                plain = COUNTERS.get(next(t.normalized_form() for t in tokens if t.begin == number_end))
                reading = {'ぶん': own.reading, 'ぶ': 'ぶ', 'ま': 'ま'}.get(counter, plain[0] if plain else own.reading)
                words[at[number_end]] = own._replace(reading=reading, source='counter', certainty=None)
        words.sort(key=lambda w: (w.start, -w.end))
        return words

    def _compound(self, tokens, i, hint_at, counted=()):
        """(next token, Word) for 2-4 adjacent tokens from i (the longest) whose joined form the list gives one
        reading: 三|日|月 みかづき, 身の上|話 みのうえばなし, 一|石|二鳥 いっせきにちょう. Left out:
        spans with particles or ending in kana (the list has phrases such as 彼の かの), spans with
        ruby, a number and its counter (一|枚, or any span inside one of `counted`, the counter spans,
        which read() reads) and spans next to a number (１|日|中, 第|一, 一対|一). The Word is `only` when
        JMdict has the joined form with that reading, else `dictionary` (names, list noise)."""
        if not self.single or not HAS_KANJI.search(tokens[i].surface()):
            return None
        if i and _NUMERAL.match(tokens[i - 1].surface()) and _end(tokens[i - 1]) == tokens[i].begin:
            return None
        for n in range(min(_MAX_COMPOUND, len(tokens) - i), 1, -1):
            span = tokens[i:i + n]
            begin, end = span[0].begin, _end(span[-1])
            if (any(_end(a) != b.begin for a, b in zip(span, span[1:]))
                    or any(t.part_of_speech()[0] in ('助詞', '助動詞') for t in span)
                    or not HAS_KANJI.search(span[-1].surface()) or _NUMERAL.match(span[-1].surface())
                    or (i + n < len(tokens) and _NUMERAL.match(tokens[i + n].surface())
                        and _end(span[-1]) == tokens[i + n].begin)  # 一対|一 isn't いっつい
                    or (n == 2 and _NUMERAL.match(span[0].surface()) and span[0].surface() != '一')
                    or (_NUMERAL.match(span[0].surface()) and span[1].surface() == '月')  # a date: 四月一日 isn't わたぬき
                    or any(start in hint_at for start in range(begin, end))
                    or any(s <= begin and end <= e for s, _, e, _, _ in counted)):
                continue
            form = ''.join(t.surface() for t in span[:-1]) + span[-1].dictionary_form()
            reading = self.single.get(form)
            if n == 2 and span[0].surface() == '一':
                # 一|X: only the sound changes Sudachi's split misses (一|思い ひとおもい, 一|票 いっぴょう);
                # the list's いち… for such pairs is mostly names (一章 かずあき) or kun guesses (一城 いちしろ)
                if not (reading and reading[:2] in ('ひと', 'いっ')):
                    reading = None
                    if form in self.one_x:
                        return i + n, Word(begin, end, form, self.one_x[form], 'default', None)
            joined = not reading and self._joined(span, form)
            if joined:
                reading = joined
            if reading and self._particle_inserted(span, reading):
                reading = None  # お腹|空く is おなか|すく, not おなかがすく: が isn't in the text
            if reading:
                if joined:
                    return i + n, Word(begin, end, form, reading, 'only' if form in self.jmdict_one else 'default', None)
                # a joined form JMdict lacks is mostly a name or noise (三日後 みひりあ, 利根川 さねがわ): not shown
                if form in self.jmdict and form in self.only:
                    return i + n, Word(begin, end, form, reading, 'only', 1.0)
                return i + n, Word(begin, end, form, reading, 'dictionary', None)
            # Sudachi's split of a word it doesn't keep whole: 一昨|日 いっさく|ひ is おととい
            default = DEFAULT_READINGS.get((form, ''.join(to_hiragana(t.reading_form()) for t in span)))
            if default and (form, default) in self.known:
                return i + n, Word(begin, end, form, default, 'default', None)
        return None

    def _joined(self, span, form: str) -> str | None:
        """The reading of a span the list doesn't join: JMdict's one reading of a form the list lacks
        (羅甸|語 らてんご), or the list's reading of a form it ranks 3+ times above its others (Reader.ranked).
        Only forms of 3+ characters (two-kanji ones are mostly other words or names: 家|中 いえじゅう,
        日|南 ひなみ, 御|霊 ごりょう), without verb or adjective tokens (入り|方 isn't いりがた), not over
        a number (counters.py reads those: 二十|年 isn't はたとせ) but for a ranked form of 3+ tokens
        (三|日|月 みかづき), and not when Sudachi's tokens already read the span a way the list gives."""
        reading = self.ranked.get(form) or self.jmdict_one.get(form)
        number = any(t.part_of_speech()[1] == '数詞' or _NUMERAL.match(t.surface()) for t in span)
        if (not reading or number and (form not in self.ranked or len(span) < 3)
                or any(t.part_of_speech()[0] in ('動詞', '形容詞') for t in span)):
            return None
        surface = ''.join(t.surface() for t in span)
        sudachi = _long_vowels(''.join(to_hiragana(t.reading_form()) for t in span))  # こーひー: JMdict's こうひい
        if any(surface_reading(surface, form, r) == sudachi for r in (reading, *self.readings.get(form, ()))):
            return None
        return reading

    def _particle_inserted(self, span, reading: str) -> bool:
        """The reading is the tokens' readings with a particle the text doesn't write between two
        of them (お腹|空く: おなか が すく; JMdict lists such phrases: お腹空く おなかがすく). Not a
        reading that only starts with a particle's kana (世知|辛い せち|がらい)."""
        prefix = ''
        for a, b in zip(span, span[1:]):
            prefix += to_hiragana(a.reading_form())
            rest = reading[len(prefix) + 1:]
            if reading.startswith(prefix) and reading[len(prefix):len(prefix) + 1] in tuple('がのをにはとへ') and any(
                    r and rest.startswith(r) for r in (to_hiragana(b.reading_form()), *self.readings.get(b.dictionary_form(), ()))):
                return True
        return False

    def _checked(self, form, reading, source, certainty):
        """Certainty hygiene for a reading not from ruby: one that isn't hiragana or ー (Sudachi's
        reading of a word it doesn't know is its surface, 於) is None; a reading the list doesn't
        give for the form gets certainty 0."""
        if source in ('ruby', 'book'):
            return reading, source, certainty
        if reading and not _KANA_READING.match(reading):
            return None, source, None
        if reading and (form, reading) not in self.known:
            certainty = 0.0
        return reading, source, certainty

    def _carried(self, text, tokens, i, surface, form, hint_at, covering, parts, carry):
        """_reading with the book's ruby over names carried (Reader.read's `carry`)."""
        begin, end = tokens[i].begin, _end(tokens[i])
        unlisted = not isinstance(self.known, _Any) and form not in self.readings
        name = surface == form and not _NUMERAL.match(surface) and (unlisted or tokens[i].part_of_speech()[1] == '固有名詞')
        under = {covering[k] for k in range(begin, end) if k in covering}
        if not under:
            if name and carry.get(form):
                return carry[form], 'book', 1.0
            return self._reading(text, tokens, i, surface, form, hint_at)
        found = self._reading(text, tokens, i, surface, form, hint_at)
        if found[1] != 'ruby' and name:
            # A name's hiragana ruby, listed or not: names take nanori and invented readings (信雄
            # のぶかつ, 柚木 ゆき), which a kanji-spelling check (PlainReadings) refuses
            reading = ruby_reading(hint_at, begin, surface, form, _Any()) or parts.get(begin)
            found = (reading, 'ruby', 1.0) if reading and reading not in _PRONOUNS else found
        if found[1] == 'ruby':
            if name:
                carry[form] = found[0] if carry.get(form, found[0]) == found[0] else None  # two readings: none
        elif hint_at.get(begin, (None,))[0] == end or not all(_HIRAGANA_WORD.match(r) for r in under):
            carry[form] = None  # flavour over the form: carry nothing more for it
        return found

    def _reading(self, text, tokens, i, surface, form, hint_at):
        begin = tokens[i].begin
        reading = hint_at and (ruby_reading(hint_at, begin, surface, form, self.known)
                               or self.plain and ruby_reading(hint_at, begin, surface, form, self.plain))
        if reading:
            return reading, 'ruby', 1.0
        # A number Sudachi reads digit by digit (六百 ろくひゃく, 三千 さんせん); 一千 (いっせん) and
        # a bare 万 (数万, 何千万: not いちまん) are left alone.
        value = _UNITS.search(surface) and not _ONE_UNIT.search(surface) and number_value(surface)
        if is_year(surface, text[:begin]):  # 昭和二三年: 23, not にさん
            value = number_value(surface)
        if value and tokens[i].part_of_speech()[1] == '数詞':
            return number_reading(value, '一千' in surface), 'counter', None
        if surface == '一' and tokens[i].part_of_speech()[1] == '数詞':
            after = text[begin + 1:begin + 4]
            for one, kana in _ONE_KANA:
                if kana.match(after):
                    return one, 'rule', 1.0
            following = tokens[i + 1] if i + 1 < len(tokens) and tokens[i + 1].begin == begin + 1 else None
            if following and following.part_of_speech()[0] == '動詞' and HAS_KANJI.search(following.surface()):
                return 'ひと', 'rule', 1.0  # 一 + a verb's stem: 一睨み, 一撫で
        previous = tokens[i - 1] if i and tokens[i - 1].begin + len(tokens[i - 1].surface()) == begin else None
        reading = context_reading(text, begin, surface, form, self.known, previous and previous.part_of_speech())
        if reading:
            return reading, 'rule', 1.0
        reading = self.model and self.model.reading(text, tokens, i, form, self.known)
        if reading:
            certainty = round(self.model.posterior(form, self.model.context(text, tokens, i))[1], 3)
            # Forms whose readings the model often gets wrong keep its reading but aren't shown (T150).
            return reading, 'dictionary' if form in MODEL_UNSHOWN else 'model', certainty
        # Sudachi's reading, of an unconjugated word only (a conjugated one reads its surface: 行っ).
        sudachi = to_hiragana(tokens[i].reading_form()) if surface == form else None
        only = self.only.get(form)
        # A name the list reads one way but JMdict doesn't have: a guess between a name's readings
        # (麻里 あさざと, 隆治 たかじ), not shown; Sudachi's reading, which is the same, stays for word lists
        if only and tokens[i].part_of_speech()[1] == '固有名詞' and form not in self.jmdict:
            only = None
        if only and surface != form and _shared_conjugation(surface, form, self.readings, self.known if isinstance(self.known, dict) else None):
            only = None  # 行っ: 行う おこなっ or 行く いっ (Sudachi picks the lemma)
        # Sudachi's voicing inside a compound is sometimes wrong (睡眠不足 ふそく, listed ぶそく).
        if only and (sudachi in (None, only) or (len(form) > 2 and tokens[i].part_of_speech()[1] != '固有名詞'
                                                 and _one_voicing_apart(sudachi, only))):
            return only, 'only', 1.0
        if surface != form:  # the listed reading that conjugates to Sudachi's reading of the surface
            reading = conjugated_reading(surface, form, to_hiragana(tokens[i].reading_form()), self.readings.get(form, ()))
            default = reading and DEFAULT_READINGS.get((form, reading))
            if default and (form, default) in self.known and not default_kept(text, begin, begin + len(surface), form):
                return default, 'default', None
            if reading:
                return reading, 'dictionary', None
            # The list has no reading for the form (potential 泳げる, ら抜き 来れる, 文語 思ふ): Sudachi's.
            reading = not self.readings.get(form) and unlisted_reading(surface, form, to_hiragana(tokens[i].reading_form()))
            if reading:
                return reading, 'dictionary', None
        default, listed = DEFAULT_READINGS.get((form, sudachi)), True
        if not default and sudachi and 'にっぽん' in sudachi and '日本' in form:
            # 日本 is にほん in Sudachi's compounds and phrases too (日本一, 日本の伝統), unless the list
            # reads the form only with にっぽん (日本銀行, 日本男児).
            default, listed = sudachi.replace('にっぽん', 'にほん'), form in self.readings
        if default and ((form, sudachi) not in HAND_DEFAULTS or (form, sudachi) in GLUED_CHECKED) \
                and glued(text, begin, begin + len(surface)):
            default = None  # the table's readings are of words on their own (郵便局側 is がわ)
        if default and ((form, default) in self.known or not listed) and not default_kept(text, begin, begin + len(surface), form):
            return default, 'default', None
        entry = self.model and self.model.forms.get(form)
        if entry and sudachi in entry[0]:  # the reading's share in the table's prior
            priors = [math.exp(p) for p in entry[1]]
            return sudachi, 'dictionary', round(priors[entry[0].index(sudachi)] / sum(priors), 3)
        return sudachi, 'dictionary', None

    def _voicing(self, tokens, i, form, reading):
        """The reading voiced or not by its place (rendaku); names keep theirs. After a compound's
        first part (プレハブ|小屋 ごや, 縮緬|細工 ざいく), a noun is voiced when the list's compounds
        ending in it read it voiced 4 times in 5 (and 5+ times); other words (イチゴ好き?: ずき, or
        a dropped particle) keep theirs. Anywhere else, a word Sudachi voiced (この箱 ばこ, 一番深い
        ぶかい) is unvoiced when the list gives it only unvoiced."""
        token, prev = tokens[i], tokens[i - 1] if i else None
        if token.part_of_speech()[1] == '固有名詞':
            return reading
        listed = self.readings.get(form, ())
        plain = reading[0].translate(_UNVOICED) + reading[1:]
        pos = prev and prev.part_of_speech()
        # A first part: a noun ending in kanji or katakana right before it; not a number or counter
        # (一|箱, 時間|話), an adverbial or adjectival noun (今|風呂, いい加減|部屋), kana (こと|好き)
        # or a prefix (お|菓子).
        if (pos and _end(prev) == token.begin and pos[0] == '名詞' and pos[1] != '数詞'
                and pos[2] not in ('副詞可能', '形状詞可能', '助数詞可能') and _HEAD_SURFACE.match(prev.surface()[-1])):
            if token.part_of_speech()[0] not in ('名詞', '接尾辞'):
                return reading
            voiced, unvoiced = self._tail_counts().get((form, plain), (0, 0))
            return rendaku(plain) if voiced >= 5 and voiced >= 4 * unvoiced and plain in listed else reading
        return plain if plain != reading and plain in listed and reading not in listed else reading

    def _tail_counts(self):
        """{(form, reading): [voiced, unvoiced]}: how the list's one-reading compounds ending in
        a listed form read it (本棚 ほんだな: 棚 voiced)."""
        if self._tails is None:
            self._tails = defaultdict(lambda: [0, 0])
            for form, reading in self.single.items():
                for k in range(1, len(form)):
                    for tail in self.readings.get(form[k:], ()):
                        voiced = rendaku(tail)
                        if voiced and len(reading) > len(tail):
                            if reading.endswith(voiced):
                                self._tails[form[k:], tail][0] += 1
                            elif reading.endswith(tail):
                                self._tails[form[k:], tail][1] += 1
            self._tails = dict(self._tails)
        return self._tails


def split_reading(surface: str, reading: str) -> list:
    """A word's reading spread over its kanji runs, kana as is: 取り扱い, とりあつかい →
    [('取', 'と'), ('り', None), ('扱', 'あつか'), ('い', None)]; the whole word when the kana don't line up."""
    parts = [part for part in re.split(f'({_KANJI_RUN.pattern})', surface) if part]
    pattern = ''.join('(.+?)' if _KANJI_RUN.fullmatch(part) else f'(?:{re.escape(to_hiragana(part))})' for part in parts)
    match = re.fullmatch(pattern, to_hiragana(reading))
    if not match:
        return [(surface, reading)]
    found = iter(match.groups())
    return [(part, next(found)) if _KANJI_RUN.fullmatch(part) else (part, None) for part in parts]
