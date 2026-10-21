"""The one-call entry point: Reader().read(text, hints) gives each kanji word's reading."""
import gzip
import json
import math
import os
import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping

from .compounds import _HEAD_SURFACE, _NUMERAL, Compounds, _end
from .counters import COUNTERS, ONE_THOUSAND, is_hatachi, is_kin, is_year, shown as counter_shown, number_reading, number_value, spans as counter_spans
from .kana import (HAS_KANJI, HIRAGANA_WORD, KANA_READING, UNVOICED, VOICED, is_kanji, long_vowels, rendaku, small_kana, spelling,
                   to_hiragana)
from .readings import (conjugated_reading, context_reading, default_kept, glued, goes, may_be_potential, right_lemma, ruby_reading,
                       split_suffix, split_token, surface_reading, unlisted_reading)
from .rules import (VOICED_AFTER_NOUN, CONTEXT_RULES, DEFAULT_READINGS, GLUED_BEFORE, GLUED_CHECKED, HAND_DEFAULTS, MODEL_FIX, MODEL_UNSHOWN,
                    SHOWN_DEFAULTS, TOP_READINGS)
from .reading_model import PUBLIC_TABLE, load_tables
from .tokens import Token, Word
from .yomitan import dominant_checked, dominant_readings, extra_readings, name_readings, preferred, term_readings

KANJI_READINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanji-readings.json')
JMDICT_PAIRS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jmdict-pairs.json.gz')
ATEJI = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ateji.tsv')


def ateji_readings(path: str = ATEJI) -> dict:
    """ateji.tsv: loanwords spelt in kanji (無問題 モーマンタイ) -> their reading in hiragana."""
    with open(path, encoding='utf-8') as f:
        return {x[0]: to_hiragana(x[1].strip()) for x in (line.split('\t') for line in f if not line.startswith('#'))
                if len(x) > 1}


def jmdict_readings(path: str = JMDICT_PAIRS) -> dict:
    """form -> JMdict's readings of it, in JMdict's order (tools/jmdict_pairs.py), with ー
    spelled out (ぎょーざ: ぎょうざ, as lists spell it)."""
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return {form: [long_vowels(r) for r in readings.split(' ')]
                for form, readings in json.load(f)['pairs'].items()}


_ALL_KANJI = re.compile(r'^[㐀-䶿一-鿿豈-﫿々]+$')
_UNITS = re.compile('[十百千万億兆]')
_ONE_UNIT = re.compile('一百|^[万億兆]')
# 一 with the rest of a native word in kana: 一ト月, 一と息 (ひ, と), 一しずく (ひと), 一たい (いっ)
_ONE_KANA = (('ひ', re.compile(r'[トと](?![〇一二三四五六七八九十百千万言云書])[㐀-䶿一-鿿豈-﫿]')),
             ('ひと', re.compile('しずく|すくみ|やすみ|そろい|かど|しきり|すじ|きわ')),
             ('いっ', re.compile('たい|パイ|ぱい|ペン|ぺん|そう')))


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


# Ruby over a name that is a pronoun or a word for here/there is flavour (鈴木《あいつ》, 東京《こっち》, 東大《うち》),
# never the name's reading.
_PRONOUNS = frozenset('あいつ こいつ そいつ どいつ やつ おれ おまえ かれ かのじょ あのこ あのひと わたし わたくし あたし ぼく '
                      'ここ そこ あそこ こちら そちら あちら こっち そっち あっち こつち そつち あつち うち'.split())
# Common words whose ruby `carry` carries like a name's (T441): the book's 妾《わらわ》 is its later bare 妾 too.
_CARRIED_WORDS = {'妾': 'わらわ'}


class _Any:
    """Every reading is known: no list given."""
    def __contains__(self, item):
        return True


_UNVOICED = UNVOICED  # chimimouryou's jiten/service.py imports it (until it imports kana.UNVOICED)
# 入れ not after a noun or お (用具入れ, お入れになる) and before a quote's or sentence's end or と言う (「入れ」,
# 入れと言わんばかり): 入る's imperative.
_HAIRE = re.compile(r'(?<![お御ァ-ヺー㐀-䶿一-鿿々A-Za-zＡ-Ｚａ-ｚ])$')
_HAIRE_AFTER = re.compile(r'(?:[」』）)！!。…―─]|と(?:言|い|云)|$)')
_LETTER = re.compile('[A-Za-zＡ-Ｚａ-ｚ]')  # a class or group's letter before 組 (Ａ組 ぐみ, T253)
# A count of times or steps before a noun (一回|部屋, 一歩|部屋): not a compound's first part.
# After a kanji Sudachi took for a noun or suffix, the rest of an adjective (T281): 酷すぎる, 熱そう, 酷いっ (a
# one-kanji adjective's stem), 強ェ, 痛ぇ (a slang adjective spelt with a small ェ; Sudachi knows 強え, 痛え).
_STEM_AFTER = re.compile('すぎ|過ぎ|そう|い[っッーぃィ～〜]')
_STEM_KANJI = re.compile('[㐀-䶿一-鿿豈-﫿々]{1,3}')
# Tails voiced after a first part (a noun ending in kanji or katakana) though the list's compounds don't show it 4
# times in 5: those after a verb's stem (繰り返し, 見通し, 取り皿) or a prefix (お返し) unvoiced, or too few (勢揃い):
# オウム返し, 予定通り, ドヤ顔, 魔力切れ, 勉強机, 甘味処, 美人揃い (T282).
_VOICED_TAILS = frozenset(tuple(pair.split(':')) for pair in (
    '揃い:そろい 返し:かえし 通り:とおり 顔:かお 切れ:きれ 机:つくえ 帰り:かえり 皿:さら 開き:ひらき 処:ところ 走り:はしり '
    '座り:すわり 疲れ:つかれ 替わり:かわり 心:こころ 稽古:けいこ').split())
_ACTION_COUNT = re.compile(r'^[0-9０-９〇一二三四五六七八九十百何数]+[回歩度]$')


def _compound_head(pos) -> bool:
    """Whether a token with part of speech `pos` can be the first part of a compound whose next token voices
    (パン|好き, いつも|通り, 泣き|顔): a noun, pronoun, adverb, prefix, verb stem or adjective stem."""
    return pos[0] in ('名詞', '代名詞', '副詞', '接頭辞') or pos[0] == '動詞' and pos[5].startswith('連用形') \
        or pos[0] == '形容詞' and pos[5].startswith('語幹')


def _one_voicing_apart(a: str, b: str) -> bool:
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    return len(a) == len(b) and len(diff) == 1 and diff[0][0].translate(UNVOICED) == diff[0][1].translate(UNVOICED)


# Sudachi picks between two entries by context (秋桜 コスモス/アキザクラ); the list has only one
_KEEP_SUDACHI = frozenset({'秋桜'})
_E_TO_U = dict(zip('えけげせてねべめれ', 'うくぐすつぬぶむる'))


def _potential_of(form: str, reading: str, known) -> bool:
    """Whether `reading` of `form` is the potential of a listed godan verb (弾ける ひける: 弾く ひく)."""
    if len(form) < 3 or not form.endswith('る') or not reading.endswith('る') or len(reading) < 3:
        return False
    u = _E_TO_U.get(form[-2]), _E_TO_U.get(reading[-2])
    return bool(u[0]) and u[0] == u[1] and (form[:-2] + u[0], reading[:-2] + u[1]) in known


_I_TO_U = dict(zip('いきぎしちにびみり', 'うくぐすつぬぶむる'))
_SHOWN_DEFAULT = dict(SHOWN_DEFAULTS)
_COUNT_NAME = re.compile('数[^字]|[一二三四五六七八九十百千万]{2,}')


def _split_name(a, b, reading: str) -> dict:
    """{token start: reading} for ruby over two tokens, split where Sudachi's reading of one of
    them ends or starts it (姫野|芽衣 ひめのめい: ひめの + めい), or {}."""
    for known, first in ((to_hiragana(a.reading_form()), True), (to_hiragana(b.reading_form()), False)):
        if known and len(reading) > len(known) and (reading.startswith(known) if first else reading.endswith(known)):
            cut = len(known) if first else len(reading) - len(known)
            return {a.begin: reading[:cut], b.begin: reading[cut:]}
    return {}


class PlainReadings:
    """(form, reading) is known when the reading is spelled by the form's kanji readings (on and
    kun of 常用/人名用 kanji, KANJIDIC2) and its kana, with rendaku and a final っ: the JS
    isPlainReading. The ruby check without a list, after JMdict's pairs: gikun (そら over 宇宙) doesn't pass."""

    def __init__(self, path: str = KANJI_READINGS):
        with open(path, encoding='utf-8') as f:
            self.readings = {k: v.split(' ') for k, v in json.load(f).items()}

    @staticmethod
    def _variants(reading: str):
        for start in reading[0] + VOICED.get(reading[0], ''):
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


class _TermPairs:
    """(form, reading) pairs of Reader.terms, as a `known` for ruby_reading."""
    def __init__(self, terms):
        self.terms = terms

    def __contains__(self, item):
        return item[1] in self.terms.get(item[0], ())


class Reader(Compounds):
    """Readings of kanji words in context. The first that gives one wins: the book's ruby
    (`hints`), a context rule, the reading model, then Sudachi's dictionary reading.

    known: (form, reading) pairs a reading must be one of (a set, the keys of a dict, or the
        path of a rank-based Yomitan frequency list). Without one, JMdict's pairs (the bundled
        jmdict-pairs.json.gz), and ruby may also be a plain reading of its kanji (PlainReadings).
    tables: reading-model tables built from your own library, tried before the public one;
        missing files are skipped.
    tokenizer: anything with tokens(text) like SudachiTokenizer (the default).
    terms: paths of Yomitan term dictionaries you supply (a str is one), for words of 2+ characters the
        list and JMdict both lack: ruby over one, a reading where Sudachi has none, and compounds
        Sudachi splits, where Sudachi has no reading or reads the compound otherwise (source 'terms', never
        shown). Earlier dictionaries' readings come first.
    names: paths of Yomitan name dictionaries (JMnedict; a str is one). Last of all: they never change a
        reading, only show one nothing else would (source 'dictionary', Sudachi's 固有名詞) when the
        dictionaries read the name that one way only (姫路 ひめじ). Not other words (今日 こんにち there)."""

    def __init__(self, known=None, tables=(), tokenizer=None, terms=(), names=()):
        if isinstance(known, str):
            from .yomitan import reading_ranks
            known = reading_ranks(known)
        jmdict = jmdict_readings()
        if known is None:  # no list: JMdict's pairs, extra-readings.tsv's, and ruby that spells its kanji (names: 柚木 ゆき)
            known = {(form, reading) for form, readings in jmdict.items() for reading in readings} | extra_readings()
            self.plain = PlainReadings()
        else:
            self.plain = None
        self.known = known
        # The list's hiragana readings per form, and the forms it gives exactly one.
        self.readings = defaultdict(list)
        for form, reading in known or ():
            if HIRAGANA_WORD.match(reading):
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
            if form[:1] == '一' and len(readings) > 1 and ranks and form not in CONTEXT_RULES:
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
            if len(readings) > 1 and len(form) > 2 and ranks and form not in CONTEXT_RULES:
                best, second = preferred({r: ranks[form, r] for r in readings}, self.jmdict.get(form, ()))
                top = {spelling(r) for r in readings if ranks[form, r] == ranks[form, best]} if best else ()
                if (best in self.jmdict.get(form, ()) and second >= 3 * ranks[form, best] and len(top) == 1
                        and (form, best) in plain):
                    self.ranked[form] = best
                elif best and _ALL_KANJI.match(form) and form in self.jmdict:
                    # a top rank shared by readings of a kanji compound: JMdict's first, when it is the only one
                    # the kanji spell (曽祖父 そうそふ, not ひいじじ, ひじじ) (T91)
                    first = self.jmdict[form][0]
                    tied = [r for r in readings if ranks[form, r] == ranks[form, best]]
                    if len(top) > 1 and first in tied and [r for r in tied if (form, r) in plain] == [first]:
                        self.ranked[form] = first
        self._jmdict_all = jmdict
        self._plain_check = self.plain or PlainReadings()
        # Term dictionaries' readings of forms the list and JMdict lack, those the kanji spell (PlainReadings) or
        # that have a kanji it doesn't know: not gikun (a user-made dictionary's flavour reading,
        # a loanword over kanji)
        self.terms = {}
        for path in [terms] if isinstance(terms, str) else terms:
            for form, readings in term_readings(path).items():
                if len(form) > 1 and form not in self.readings and form not in jmdict:
                    unknown = any(is_kanji(c) and c not in self._plain_check.readings for c in form)
                    kept = [r for r in readings if r not in self.terms.get(form, ()) and (unknown or (form, r) in self._plain_check)]
                    if kept:
                        self.terms[form] = self.terms.get(form, []) + kept
        self._term_pairs = _TermPairs(self.terms)
        merged = {}
        for path in [names] if isinstance(names, str) else names:
            for form, readings in name_readings(path).items():
                merged[form] = merged.get(form, set()) | readings
        self.names = {form: next(iter(r)) for form, r in merged.items() if len(r) == 1}
        self._finish(tables, tokenizer)

    # Reader.save's tables: name -> (encode, decode) of the values; pair tables are keyed `form \t reading`.
    _LISTS = ('readings', 'jmdict', '_jmdict_all', 'terms')
    _STRINGS = ('single', 'only', 'one_x', 'jmdict_one', 'ranked', 'names')

    def save(self, path: str) -> None:
        """Write the tables built from the lists and dictionaries to one file for Reader.load: a worker that
        loads it parses nothing and shares the file's pages with other processes (yurigana/packed.py)."""
        from . import packed
        if not isinstance(self.known, (dict, set, frozenset)):
            raise TypeError('Reader.save needs `known` as a set or dict')
        ranked = isinstance(self.known, Mapping)
        tables = {'known': {f'{f}\t{r}': str(v) if ranked else '' for (f, r), v in
                            (self.known.items() if ranked else ((pair, '') for pair in self.known))}}
        tables |= {name: {k: ' '.join(v) for k, v in getattr(self, name).items()} for name in self._LISTS}
        tables |= {name: dict(getattr(self, name)) for name in self._STRINGS}
        tables['tails'] = {f'{f}\t{r}': f'{v} {u}' for (f, r), (v, u) in self._tail_counts().items()}
        tables['kanji_index'] = {r: ''.join(sorted(kanji)) for r, kanji in self._kanji_by_reading().items()}
        packed.write(path, tables, {'ranked': ranked, 'plain': self.plain is not None, 'source': _source_hash()})

    @classmethod
    def load(cls, path: str, tables=(), tokenizer=None) -> 'Reader':
        """A Reader from Reader.save's file; `tables` and `tokenizer` as in Reader()."""
        from .packed import Decoded, Packed, PairMap, PairSet
        pack = Packed(path)
        if pack.meta.get('source') != _source_hash():
            raise ValueError(f'{path} was saved by another version of yurigana: build the Reader and save it again')
        self = cls.__new__(cls)
        self.known = PairMap(pack.table('known')) if pack.meta['ranked'] else PairSet(pack.table('known'))
        for name in cls._LISTS:
            setattr(self, name, Decoded(pack.table(name), _split))
        for name in cls._STRINGS:
            setattr(self, name, pack.table(name))
        self._tails = PairMap(pack.table('tails'), _counts)
        self._kanji_index = Decoded(pack.table('kanji_index'), set)
        self.plain = PlainReadings() if pack.meta['plain'] else None
        self._plain_check = self.plain or PlainReadings()
        self._term_pairs = _TermPairs(self.terms)
        self._finish(tables, tokenizer)
        return self

    def _finish(self, tables, tokenizer):
        self.model = load_tables([*tables, PUBLIC_TABLE])
        self.dominant = dominant_readings()
        self.dominant_checked = dominant_checked()
        self.ateji = ateji_readings()
        self._ateji_re = re.compile('|'.join(sorted(map(re.escape, self.ateji), key=len, reverse=True)))
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
        common word (hiragana ruby once isn't assumed for its later bare heteronyms) except
        妾《わらわ》, and no more after ruby over the form that isn't taken (flavour, katakana,
        a pronoun or here/there: 東京《こっち》) or that differs. A name of 2+ characters rubied
        after bare use takes the reading at its earlier bare occurrences in the same text too."""
        hint_at = {start: (end, reading) for start, end, reading in hints}
        tokens = self._adjectives(list(self.tokenizer.tokens(text)), text)
        covering, parts = {}, {}
        if carry is not None:
            for start, end, reading in hints:
                covering.update((k, reading) for k in range(start, end))
            for a, b in zip(tokens, tokens[1:]):
                end, reading = hint_at.get(a.begin, (None, ''))
                if end == _end(b) and _end(a) == b.begin and HIRAGANA_WORD.match(reading):
                    parts.update(_split_name(a, b, reading))
        words, pending = [], defaultdict(list)
        next_token = 0
        counted = list(counter_spans(text, tokens))
        for i, token in enumerate(tokens):
            if i < next_token:
                continue
            compound = self._compound(tokens, i, hint_at, counted, text)
            if compound:
                next_token, word = compound
                words.append(word)
                continue
            split = split_token(text, token.begin, token.surface())
            if split and not any(s < _end(token) and e > token.begin for s, (e, _) in hint_at.items()):
                end, form, reading, shown = split
                words.append(Word(token.begin, end, form, reading, 'rule' if shown else 'dictionary', 1.0 if shown else None))
                continue
            surface, form = token.surface(), token.dictionary_form()
            if form != surface and unicodedata.normalize('NFKC', surface) == form:
                form = surface  # full-width digits Sudachi's lemma writes half-width (１人: 1人), not a conjugation
            if not HAS_KANJI.search(surface):
                continue
            form = right_lemma(text, token.begin, form, token.begin + len(surface))
            if form == '行う' and surface == '行っ' and token.begin not in hint_at and goes(text, tokens, i):
                form = '行く'  # read いっ below, not shown (T432)
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
            if reading and source not in ('ruby', 'counter', 'book') and not (source == 'rule' and VOICED_AFTER_NOUN.get(form) == reading):
                reading = self._voicing(tokens, i, form, reading)
            end = token.begin + len(surface)
            if (source == 'dictionary' and certainty == 0.0 and reading and token.part_of_speech()[1] != '固有名詞'
                    and self._parts_reading(form, reading)
                    and not any(s < end and e > token.begin for s, (e, _) in hint_at.items())):
                source, certainty = 'rule', 1.0
            if (source == 'dictionary' and form == surface and reading and self.names.get(form) == reading
                    and token.part_of_speech()[1] == '固有名詞'  # not glued to kanji or digits: 一日|中海岸 is 一日中 海岸
                    and not any(is_kanji(c) or c.isdigit() for c in text[max(token.begin - 1, 0):token.begin] + text[end:end + 1])
                    and not any(s < end and e > token.begin for s, (e, _) in hint_at.items())):  # nor under partial ruby
                source, certainty = 'only', 1.0
            words.append(Word(token.begin, token.begin + len(surface), form, reading, source, certainty))
            if carry is not None and len(form) > 1:
                if carry.get(form) and form in pending and HIRAGANA_WORD.match(carry[form]):
                    # a name rubied after bare use: its earlier bare occurrences in this text too
                    for k in pending.pop(form):
                        words[k] = words[k]._replace(reading=carry[form], source='book', certainty=1.0)
                elif form not in carry and source not in ('ruby', 'book') and self._is_name(token, surface, form):
                    pending[form].append(len(words) - 1)
        # A number and its counter: one Word for the span (三本 さんぼん); the counter's own Word
        # keeps the counter's plain reading (本 ほん), as source 'counter', never 'only' with a
        # certainty its reading in the span doesn't have. Ruby over any of it wins.
        at = {w.start: n for n, w in enumerate(words)}
        token_at = {t.begin: t for t in tokens}
        first_at = {t.begin: t for t in reversed(tokens)}
        for start, number_end, end, number, counter in counted:
            if any(s < end and e > start for s, (e, _) in hint_at.items()):
                continue
            if number == 'ふた' and text[max(0, start - 2):start] == '真っ':  # 真っ二つ まっぷたつ (T461)
                number = 'ぷた'
                if start in at and words[at[start]].reading == 'ふた':
                    words[at[start]] = words[at[start]]._replace(reading='ぷた')
            # shown (certainty 1.0) unless the counter or span is often read otherwise, or Sudachi took it for a name
            sure = counter_shown(text[start:end], text[number_end:end], text[end:end + 2], text[max(0, start - 2):start]) and not (
                start in token_at and token_at[start].part_of_speech()[1] == '固有名詞')
            word = Word(start, end, text[start:end], number + (counter or ''), 'counter', 1.0 if sure else None)
            if start in at and words[at[start]].end == end:  # one token (三軒 みのき, 一回 いちかい)
                words[at[start]] = word
            else:
                words.append(word)
            if counter and number_end in at and words[at[number_end]].end == end:
                own = words[at[number_end]]
                plain = COUNTERS.get(first_at[number_end].normalized_form())
                reading = {'ぶん': own.reading, 'ぶ': 'ぶ', 'ま': 'ま'}.get(counter, plain[0] if plain else own.reading)
                words[at[number_end]] = own._replace(reading=reading, source='counter', certainty=None)
        # A loanword spelt in kanji that Sudachi cuts in pieces (無問題 = 無 む + 問題 もんだい, shown `only`):
        # one Word with the loanword's reading, never shown, where it starts and ends on token edges and has no ruby
        begins, ends = {t.begin for t in tokens}, {_end(t) for t in tokens}
        for m in self._ateji_re.finditer(text):
            start, end = m.span()
            if (start in begins and end in ends and end not in {_end(t) for t in tokens if t.begin == start}
                    and not any(s < end and e > start for s, (e, _) in hint_at.items())):
                words = [w for w in words if w.end <= start or w.start >= end]
                words.append(Word(start, end, m.group(), self.ateji[m.group()], 'dictionary', 0.0))
        words = [w._replace(source='rule', certainty=1.0) if w.source == 'default' and (w.form, w.reading) in SHOWN_DEFAULTS
                 and not (w.end - w.start == 1 and (glued(text, w.start, w.end) or re.match('[ァ-ヺー]', text[w.end:w.end + 1])))
                 else w for w in words]
        words = self._idioms(text, tokens, words, hint_at, counted)
        words.sort(key=lambda w: (w.start, -w.end))
        return words

    def _checked(self, form, reading, source, certainty):
        """Certainty hygiene for a reading not from ruby: one that isn't hiragana or ー (Sudachi's
        reading of a word it doesn't know is its surface, 於) is None; a reading the list doesn't
        give for the form gets certainty 0."""
        if source in ('ruby', 'book'):
            return reading, source, certainty
        if reading and not KANA_READING.match(reading):
            return None, source, None
        if (reading and (form, reading) not in self.known and (form, reading) not in self._term_pairs
                and not (source == 'rule' and VOICED_AFTER_NOUN.get(form) == reading)):  # a listed reading's rendaku (T460)
            certainty = 0.0
        return reading, source, certainty

    def _own(self, part):
        """The reading a part is shown with on its own: the list's only one, or a shown default."""
        own = self.only.get(part) or _SHOWN_DEFAULT.get(part)
        if own:
            return own
        cache = self.__dict__.setdefault('_own_cache', {})
        if part not in cache:
            cache[part] = None
            words = self.read(part)
            if len(words) == 1 and words[0].start == 0 and words[0].end == len(part) and words[0].form == part \
                    and words[0].source in ('only', 'rule', 'model'):
                cache[part] = words[0].reading
        return cache[part]

    def _verb_own(self, verb, whole=False, compound=True):
        """A verb's own reading: listed only, its potential (会える: 会う あう), or a compound verb's
        parts (歌い継ぐ: 歌う うたい + 継ぐ つぐ), each part read as it is on its own."""
        own = not whole and self._own(verb)
        if own:
            return own
        # not 為せる: also 為る's causative (させる)
        if len(verb) > 2 and verb[-1] == 'る' and verb[-2] in _E_TO_U and verb[0] != '為':
            base = self._own(verb[:-2] + _E_TO_U[verb[-2]])
            if base and base[-1] == _E_TO_U[verb[-2]]:
                return base[:-1] + verb[-2] + 'る'
        if compound:
            for k in range(1, len(verb) - 1):
                head, tail = verb[:k], verb[k:]
                if not is_kanji(tail[0]) or not (is_kanji(head[-1]) or head[-1] in _I_TO_U or head[-1] in _E_TO_U):
                    continue
                rest = self._verb_own(tail, compound=False)
                if not rest:
                    continue
                for lemma, cut in ((head[:-1] + _I_TO_U[head[-1]], 1) if head[-1] in _I_TO_U else (None, 0), (head + 'る', 0)):
                    first = lemma and self._own(lemma)
                    if first and first.endswith(lemma[len(head) - cut:]) and not is_kanji(head[-1]):
                        return (first[:-1] + head[-1] if cut else first[:-1]) + rest
        return None

    def _parts_reading(self, form, reading) -> bool:
        """Whether Sudachi's reading of a form the list lacks is its parts' own readings joined, without
        voicing: a kanji compound (女性陣 じょせい + じん) or a verb form (会える, 歌い継ぐ)."""
        if form in self.readings or reading not in self._jmdict_all.get(form, (reading,)):
            return False
        if _ALL_KANJI.match(form) and len(form) > 1:
            tails = self._tail_counts()

            def joined(i):
                if i == len(form):
                    yield ''
                for j in range(len(form) if i == 0 else len(form) + 1, i, -1):
                    own = self._own(form[i:j])
                    if own and (i == 0 or not rendaku(own) or tails.get((form[i:j], own), (0, 0))[0] == 0):
                        yield from (own + rest for rest in joined(j))
            return reading in set(joined(0))
        if re.fullmatch('[㐀-䶿一-鿿豈-﫿々]+[ぁ-ゖ]*[㐀-䶿一-鿿豈-﫿々]*[ぁ-ゖ]+', form) and form[-1] in _E_TO_U.values():
            return self._verb_own(form, whole=True) == reading
        return False

    def _is_name(self, token, surface, form) -> bool:
        """A name for `carry`: a 固有名詞 token or a form the list doesn't know, not a number."""
        unlisted = not isinstance(self.known, _Any) and form not in self.readings
        return surface == form and not _NUMERAL.match(surface) and (unlisted or token.part_of_speech()[1] == '固有名詞')

    def _carried(self, text, tokens, i, surface, form, hint_at, covering, parts, carry):
        """_reading with the book's ruby over names carried (Reader.read's `carry`)."""
        begin, end = tokens[i].begin, _end(tokens[i])
        name = self._is_name(tokens[i], surface, form)
        under = {covering[k] for k in range(begin, end) if k in covering}
        name = name or form in _CARRIED_WORDS
        if not under:
            if name and carry.get(form):
                return carry[form], 'book', 1.0
            return self._reading(text, tokens, i, surface, form, hint_at)
        found = self._reading(text, tokens, i, surface, form, hint_at)
        if found[1] != 'ruby' and name:
            # A name's hiragana ruby, listed or not: names take nanori and invented readings (信雄
            # のぶかつ, 柚木 ゆき), which a kanji-spelling check (PlainReadings) refuses
            reading = ruby_reading(hint_at, begin, surface, form, _Any()) or parts.get(begin)
            if reading:  # ruby set in large kana (劉《りゆう》): Sudachi's or the list's small-kana reading
                reading = next((r for r in small_kana(reading) if r == found[0] or (form, r) in self.known), reading)
            found = (reading, 'ruby', 1.0) if reading and reading not in _PRONOUNS else found
        if found[1] == 'ruby':
            if name:  # two readings, or a word's other one: none
                carry[form] = found[0] if carry.get(form, found[0]) == found[0] == _CARRIED_WORDS.get(form, found[0]) else None
        elif hint_at.get(begin, (None,))[0] == end or not all(HIRAGANA_WORD.match(r) for r in under):
            carry[form] = None  # flavour over the form: carry nothing more for it
        return found

    def _adjectives(self, tokens, text):
        """Tokens with a kanji noun or suffix that is an adjective's stem (_STEM_AFTER) made that adjective, as
        Sudachi reads the kanji plus い (酷すぎる: 酷い ひど, not 酷 こく) or plus え (強ェ: 強え つえぇ, not 強 きょう);
        only where that gives one adjective token and, for い, the list has the adjective."""
        out, drop = [], None
        for token in tokens:
            if token.begin == drop:
                continue  # the small ェ, now in the adjective
            surface = token.surface()
            end = token.begin + len(surface)
            tail = text[end:end + 1]
            if _STEM_KANJI.fullmatch(surface) and token.part_of_speech()[0] != '形容詞' and (
                    tail in ('ェ', 'ぇ') or len(surface) == 1 and _STEM_AFTER.match(text, end) and surface + 'い' in self.readings):
                small = tail in ('ェ', 'ぇ')
                after = next((t for t in tokens if t.begin == end), None)
                whole = list(self.tokenizer.tokens(surface + ('え' if small else 'い')))
                if (len(whole) == 1 and whole[0].part_of_speech()[0] == '形容詞' and len(whole[0].surface()) == len(surface) + 1
                        and not (small and after and after.surface() != tail)):
                    adjective = whole[0]
                    token = Token(surface + tail if small else surface, adjective.dictionary_form(), adjective.normalized_form(),
                                  adjective.part_of_speech(), adjective.reading_form()[:-1] + (tail if small else ''), token.begin)
                    drop = end if small else None
            out.append(token)
        return out

    def _reading(self, text, tokens, i, surface, form, hint_at):
        begin = tokens[i].begin
        reading = hint_at and (ruby_reading(hint_at, begin, surface, form, self.known)
                               or self.plain and ruby_reading(hint_at, begin, surface, form, self.plain))
        if reading:
            return reading, 'ruby', 1.0
        reading = hint_at and form in self.terms and ruby_reading(hint_at, begin, surface, form, self._term_pairs)
        if reading:
            return reading, 'terms', None
        if form == '行く' and tokens[i].dictionary_form() == '行う':  # readings.goes (T432)
            return 'いく', 'dictionary', None
        # A number Sudachi reads digit by digit (六百 ろくひゃく, 三千 さんせん); 一千 (いっせん) and
        # a bare 万 (数万, 何千万: not いちまん) are left alone.
        if surface == '十':  # an age or a count of ten (十も年下, 九つか十の子): とお (CONTEXT_RULES)
            reading = context_reading(text, begin, surface, form, self.known)
            if reading:
                return reading, 'rule', 1.0
        hatachi = surface == '二十' and is_hatachi(text[:begin], text[begin + 2:begin + 6])
        if hatachi:
            return ('はたち', 'rule', 1.0) if hatachi == 'shown' else ('はたち', 'dictionary', None)
        if surface == '金' and is_kin(text, begin):
            return 'きん', 'dictionary', None
        value = _UNITS.search(surface) and not _ONE_UNIT.search(surface) and number_value(surface)
        if surface in ('1日', '１日') and not re.search('月 ?$', text[:begin]):  # Sudachi's ついたち is a date, after a month
            return 'いちにち', 'rule', 1.0
        if '〇' in surface[1:] and surface[0] != '〇':  # digit by digit with 〇 (六八〇, 二〇〇): the number, not れい
            value = number_value(surface)
        if is_year(surface, text[:begin]):  # 昭和二三年: 23, not にさん
            value = number_value(surface)
        if value and tokens[i].part_of_speech()[1] == '数詞':
            return number_reading(value, bool(ONE_THOUSAND.search(surface))), 'counter', None
        if surface == '一' and tokens[i].part_of_speech()[1] == '数詞':
            after = text[begin + 1:begin + 4]
            for one, kana in _ONE_KANA:
                if kana.match(after):
                    return one, 'rule', 1.0
            following = tokens[i + 1] if i + 1 < len(tokens) and tokens[i + 1].begin == begin + 1 else None
            if following and following.part_of_speech()[0] == '動詞' and HAS_KANJI.search(following.surface()):
                return 'ひと', 'rule', 1.0  # 一 + a verb's stem: 一睨み, 一撫で
        if form == '入れ' and _HAIRE.search(text[max(0, begin - 6):begin]) and _HAIRE_AFTER.match(text, begin + 2):
            return 'はいれ', 'dictionary', None  # 「入れ」: 入る's imperative; the list reads the noun 入れ いれ only (T251)
        previous = tokens[i - 1] if i and tokens[i - 1].begin + len(tokens[i - 1].surface()) == begin else None
        reading = context_reading(text, begin, surface, form, self.known, previous and previous.part_of_speech())
        if reading:
            return reading, 'rule', 1.0
        reading = split_suffix(text, begin, surface, to_hiragana(tokens[i].reading_form()), tokens[i].part_of_speech(),
                               previous and previous.part_of_speech())
        if reading and (form, reading) in self.known:
            return reading, 'default', None
        reading = self.model and self.model.reading(text, tokens, i, form, self.known)
        if reading:
            certainty = round(self.model.posterior(form, self.model.context(text, tokens, i))[1], 3)
            for before, after, given, shown in MODEL_FIX.get((form, reading), ()):  # T250
                if (not before or before.search(text[max(0, begin - 12):begin])) and (not after or after.match(text, _end(tokens[i]))):
                    return given, 'model' if shown else 'dictionary', certainty if given == reading else None
            # Forms whose readings the model often gets wrong keep its reading but aren't shown (T150).
            return reading, 'dictionary' if form in MODEL_UNSHOWN else 'model', certainty
        # Sudachi's reading, of an unconjugated word only (a conjugated one reads its surface: 行っ).
        sudachi = to_hiragana(tokens[i].reading_form()) if surface == form else None
        only = self.only.get(form)
        # A name the list reads one way but JMdict doesn't have: a guess between a name's readings
        # (麻里 あさざと, 隆治 たかじ), not shown; Sudachi's reading, which is the same, stays for word lists
        if only and tokens[i].part_of_speech()[1] == '固有名詞' and form not in self.jmdict:
            only = None
        # A count Sudachi reads as a name, with a reading neither JMdict nor the list gives the form
        # (数人 かずひと, 三百 みつお): JMdict's reading, the list's best of them. Only counts: other name
        # tokens that are also words are mostly names (最上さん, 高木, 金子, 月火 つきひ).
        name = tokens[i].part_of_speech()[1] == '固有名詞' and _COUNT_NAME.fullmatch(form)
        if name and sudachi and form in self.jmdict and sudachi not in self.readings[form] + self.jmdict[form]:
            if only in self.jmdict[form]:
                return only, 'only', 1.0
            ranks = self.known if isinstance(self.known, Mapping) else {}
            return min(self.jmdict[form], key=lambda r: ranks.get((form, r), math.inf)), 'dictionary', None
        if only and surface != form and _shared_conjugation(surface, form, self.readings, self.known if isinstance(self.known, Mapping) else None):
            only = None  # 行っ: 行う おこなっ or 行く いっ (Sudachi picks the lemma)
        if only and may_be_potential(text, begin, form):
            only = None  # 部屋には入れない: はいれる (入る) or いれる
        # 癖 glued after a noun or a verb's stem is くせ, ぐせ or へき (逃げ癖, 貧乏癖, 収集癖): not shown (T254).
        if only and form == '癖' and previous and (_HEAD_SURFACE.match(previous.surface()[-1]) and previous.part_of_speech()[0] == '名詞'
                                                   or previous.part_of_speech()[0] == '動詞' and previous.part_of_speech()[5].startswith('連用形')):
            return only, 'dictionary', None
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
                return self._dominant(text, tokens[i], form, reading, previous=previous)
            # The list has no reading for the form (potential 泳げる, ら抜き 来れる, 文語 思ふ): Sudachi's.
            reading = not self.readings.get(form) and unlisted_reading(surface, form, to_hiragana(tokens[i].reading_form()))
            term = not (reading and KANA_READING.match(reading)) and self._term_reading(form, None)
            if term and surface_reading(surface, form, term, ''):  # Sudachi has none (嘲笑っ): the term dictionaries'
                return term, 'terms', None
            if reading:
                return reading, 'dictionary', None
        default, listed = DEFAULT_READINGS.get((form, sudachi)), True
        if not default and sudachi and 'にっぽん' in sudachi and '日本' in form:
            # 日本 is にほん in Sudachi's compounds and phrases too (日本一, 日本の伝統), unless the list
            # reads the form only with にっぽん (日本銀行, 日本男児).
            default, listed = sudachi.replace('にっぽん', 'にほん'), form in self.readings
        if default and ((form, sudachi) not in HAND_DEFAULTS or (form, sudachi) in GLUED_CHECKED) \
                and glued(text, begin, begin + len(surface), (form, sudachi) not in GLUED_BEFORE):
            default = None  # the table's readings are of words on their own (郵便局側 is がわ)
        if default and ((form, default) in self.known or not listed) and not default_kept(text, begin, begin + len(surface), form):
            return default, 'default', None
        reading = self._unlisted_sudachi(tokens[i], form, sudachi)
        if reading:
            return reading, 'dictionary', None
        reading = surface == form and not (sudachi and KANA_READING.match(sudachi)) and self._term_reading(form, None)
        if reading:
            return reading, 'terms', None
        entry = self.model and self.model.forms.get(form)
        if entry and sudachi in entry[0]:  # the reading's share in the table's prior
            priors = [math.exp(p) for p in entry[1]]
            return self._dominant(text, tokens[i], form, sudachi, round(priors[entry[0].index(sudachi)] / sum(priors), 3), previous)
        return self._dominant(text, tokens[i], form, sudachi, previous=previous)

    def _dominant(self, text, token, form, reading, certainty=None, previous=None):
        """Sudachi's reading (or the listed one it conjugates from) as `dictionary`, or as `only` where
        dominant-readings.tsv (or TOP_READINGS) gives it as the form's reading in bare post-war text and the token stands alone:
        not glued to a kanji, digit or katakana word (日 in 二日酔い, 族 in ドラゴン族; a longer token with a kanji or digit
        next to it, part of a compound Sudachi split: 一|文字 もんじ, 背筋|運動 はいきん), not a name, and a surface the
        reading spells (not the classical 若かり). Pairs admitted on bare-text evidence (dominant_checked) are also
        not shown right after a noun, adverb, prefix or verb stem, where they may be a compound's voiced tail
        (パン好き ずき, いつも通り どおり, ソファ代わり がわり)."""
        begin, end = token.begin, token.begin + len(token.surface())
        if (self.dominant.get(form, TOP_READINGS.get(form)) != reading or token.part_of_speech()[1] == '固有名詞' or glued(text, begin, end)
                or end - begin > 1 and any(is_kanji(c) or c.isdigit() for c in text[max(begin - 1, 0):begin] + text[end:end + 1])
                or not surface_reading(token.surface(), form, reading, text[end:end + 3])
                or (form in self.dominant_checked or form in TOP_READINGS) and previous and _compound_head(previous.part_of_speech())):
            return reading, 'dictionary', certainty
        return reading, 'only', 1.0

    def _unlisted_sudachi(self, token, form, sudachi) -> str | None:
        """The list's top reading of a form when Sudachi's reading of it is neither listed nor
        JMdict's (七五三 ななごさん, 氷室 ひょうしつ, 欠片 けっぺん). Not when JMdict has Sudachi's
        reading (上辺 じょうへん, 大罪 たいざい: the list lacks a reading), when Sudachi's is a listed one
        unvoiced (越え こえ, listed ごえ: the place decides, _voicing), names, two numerals (四三 is
        よんじゅうさん, not しそう) and one-character forms (国 こく after a name, 妾 わたし, 臭 におい:
        Sudachi's is usually right there), nor when another listed form with one of its kanji reads
        Sudachi's way (無性 むしょう as 無償, 朝陽 あさひ as 朝日: JMdict lacks a reading, Sudachi knows it)."""
        listed = self.readings.get(form)
        own = self.jmdict.get(form)
        if (len(form) < 2 or len(form) == 2 and _NUMERAL.match(form) or not listed or not own or not sudachi
                or token.part_of_speech()[1] == '固有名詞' or sudachi in own
                or (token.normalized_form(), sudachi) in self.known  # an okurigana variant's (幼ない おさない, T77)
                or any(spelling(r) == spelling(sudachi) or _one_voicing_apart(sudachi, r)
                       and sudachi.translate(UNVOICED) == sudachi for r in listed)
                or _potential_of(form, sudachi, self.known)  # 弾ける ひける, can play (弾く ひく)
                or form[-1:] == sudachi[-1:] == 'す' and (form[:-1] + 'する', sudachi[:-1] + 'する') in self.known  # 徹す てっす
                or form in _KEEP_SUDACHI
                or form[-1:] == 'う' and sudachi[-2:-1] in 'おこごそぞとどのぼもよろ'  # 買うて こう: Kansai u-onbin
                or 'ー' in sudachi  # a loanword's (麦酒 びーる): JMdict spells those in katakana
                or set(form) & self._kanji_by_reading().get(sudachi, set())):
            return None
        ranks = self.known if isinstance(self.known, Mapping) else {}
        return preferred({r: ranks.get((form, r), 0) for r in listed}, own)[0]

    def _kanji_by_reading(self) -> dict:
        """{reading: the kanji of the list's forms read that way}, built once."""
        if getattr(self, '_kanji_index', None) is None:
            self._kanji_index = defaultdict(set)
            for form, readings in self.readings.items():
                for reading in readings:
                    self._kanji_index[reading].update(c for c in form if is_kanji(c))
        return self._kanji_index

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
        plain = reading[0].translate(UNVOICED) + reading[1:]
        pos = prev and prev.part_of_speech()
        # A first part: a noun ending in kanji or katakana right before it; not a number or counter
        # (一|箱, 時間|話), an adverbial or adjectival noun (今|風呂, いい加減|部屋), kana (こと|好き)
        # or a prefix (お|菓子).
        if (pos and _end(prev) == token.begin and pos[0] == '名詞' and pos[1] != '数詞'
                and (pos[2] not in ('副詞可能', '形状詞可能', '助数詞可能') and _HEAD_SURFACE.match(prev.surface()[-1])
                     and not _ACTION_COUNT.match(prev.surface()) or _LETTER.fullmatch(prev.surface()))):
            if token.part_of_speech()[0] not in ('名詞', '接尾辞'):
                return reading
            if (form, plain) in _VOICED_TAILS and plain in listed:
                return rendaku(plain)
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


_KANJI_RUN = re.compile(r'[㐀-䶿一-鿿豈-﫿々〆ヶ]+')


def _source_hash() -> str:
    """The package's code and data, which Reader.save's tables are derived from."""
    import hashlib
    here, digest = os.path.dirname(os.path.abspath(__file__)), hashlib.sha256()
    for name in sorted(os.listdir(here)):
        if name.endswith(('.py', '.tsv', '.json', '.gz')):
            with open(os.path.join(here, name), 'rb') as f:
                digest.update(name.encode() + b'\0' + f.read())
    return digest.hexdigest()


def _split(value: str) -> list:
    return value.split(' ')


def _counts(value: str) -> tuple:
    return tuple(map(int, value.split(' ')))


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
