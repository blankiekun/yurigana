"""Words over several tokens: compounds Sudachi splits that the list or JMdict reads one way
(三|日|月 みかづき) and phrases with a kana token inside (歩|を|進める), mixed into Reader."""
import re

from .kana import HAS_KANJI, KANA_READING, is_kanji, long_vowels, rendaku, spelling, to_hiragana
from .readings import context_reading, surface_reading
from .rules import DEFAULT_READINGS, NOT_JOINED, SHOWN_IDIOMS
from .tokens import Word

_NUMERAL = re.compile(r'^[0-9０-９〇一二三四五六七八九十百千万億兆]+$')
_HEAD_SURFACE = re.compile('[ァ-ヺー㐀-䶿一-鿿豈-﫿々]')
_DEMONSTRATIVE = re.compile('^[こそあど](?:の|んな|ういう)$')
_MAX_COMPOUND = 4  # tokens
# Numeral compounds _numeral_idiom leaves split: counts (八文字 はちもじ, not はちもんじ, N文字 in the code; 八歳児
# はっさいじ, not やつご) and a list reading books don't ruby (十二神将: じゅうにしんしょう 28 of 28 in library ruby)
_NOT_IDIOMS = {'八歳児', '十二神将'}


def _end(token):
    return token.begin + len(token.surface())


def _spelled(span, reading: str) -> bool:
    """Whether the tokens' readings spell the reading, each after the first voiced or not (利根|川 とねがわ),
    each before the last ending in っ or not (学|校 がっこう)."""
    pattern = ''
    for k, t in enumerate(span):
        part = long_vowels(to_hiragana(t.reading_form()))
        forms = {part, k and rendaku(part) or part}
        if k < len(span) - 1:
            forms |= {f[:-1] + 'っ' for f in forms if f[-1:] in tuple('くつちき')}
        if k and part[:1] in 'はひふへほ':  # after っ (一|藩 いっぱん)
            forms.add(chr(ord(part[0]) + 2) + part[1:])
        pattern += '(?:' + '|'.join(map(re.escape, forms)) + ')'
    return bool(re.fullmatch(pattern, long_vowels(reading)))


class Compounds:
    """Reader's methods that read several tokens as one word (Reader.read, Reader._idioms)."""

    def _compound(self, tokens, i, hint_at, counted=(), text=''):
        """(next token, Word) for 2-4 adjacent tokens from i (the longest) whose joined form the list gives one
        reading: 三|日|月 みかづき, 身の上|話 みのうえばなし, 一|石|二鳥 いっせきにちょう. Left out:
        spans with particles or ending in kana (the list has phrases such as 彼の かの), spans with
        ruby, a number and its counter (一|枚, or any span inside one of `counted`, the counter spans,
        which read() reads) and spans next to a number (１|日|中, 第|一, 一対|一), but for numeral compounds
        (_numeral_idiom: 十|中|八九). The Word is `only` when
        JMdict has the joined form with that reading, else `dictionary` (names, list noise)."""
        if not self.single or not HAS_KANJI.search(tokens[i].surface()):
            return None
        if i and _NUMERAL.match(tokens[i - 1].surface()) and _end(tokens[i - 1]) == tokens[i].begin:
            return None
        for n in range(min(_MAX_COMPOUND, len(tokens) - i), 1, -1):
            span = tokens[i:i + n]
            begin, end = span[0].begin, _end(span[-1])
            # a numeral compound the list and JMdict read one way (十|中|八九 じっちゅうはっく, 三|白眼, 四|人組);
            # not ending in one kanji, mostly a counter (二十|年 isn't はたとせ)
            idiom = len(span[-1].surface()) > 1 and self._numeral_idiom(span)
            if (any(_end(a) != b.begin for a, b in zip(span, span[1:]))
                    or any(t.part_of_speech()[0] in ('助詞', '助動詞') for t in span)
                    or not HAS_KANJI.search(span[-1].surface()) or _NUMERAL.match(span[-1].surface()) and not idiom
                    or (i + n < len(tokens) and _NUMERAL.match(tokens[i + n].surface())
                        and _end(span[-1]) == tokens[i + n].begin)  # 一対|一 isn't いっつい
                    or (n == 2 and _NUMERAL.match(span[0].surface()) and span[0].surface() != '一' and not idiom)
                    or (_NUMERAL.match(span[0].surface()) and span[1].surface() == '月')  # a date: 四月一日 isn't わたぬき
                    or any(start in hint_at for start in range(begin, end))
                    or any(s <= begin and end <= e for s, _, e, _, _ in counted)):
                continue
            form = ''.join(t.surface() for t in span[:-1]) + span[-1].dictionary_form()
            if form in NOT_JOINED and NOT_JOINED[form].match(text, end):
                continue
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
            term = not reading and len(form) > 2 and span[-1].surface() == span[-1].dictionary_form() and not any(
                t.part_of_speech()[0] in ('動詞', '形容詞') or _NUMERAL.match(t.surface()) for t in span) and self._term_reading(
                form, long_vowels(''.join(to_hiragana(t.reading_form()) for t in span)))
            if term:
                reading = term
            if reading and self._particle_inserted(span, reading):
                reading = None  # お腹|空く is おなか|すく, not おなかがすく: が isn't in the text
            if reading:
                rule = text and context_reading(text, begin, form, form, self.known)
                if rule:  # a joined form with context rules (三つ目: みっつめ, the ordinal, unless eyes)
                    return i + n, Word(begin, end, form, rule, 'rule', 1.0)
                if joined:
                    return i + n, Word(begin, end, form, reading, 'only' if form in self.jmdict_one else 'default', None)
                if term:
                    return i + n, Word(begin, end, form, reading, 'terms', None)
                # a joined form JMdict lacks is mostly a name or noise (利根川 さねがわ): not shown; over a number
                # the tokens can't spell (三日後 みひりあ), noise: not taken (names split into words, 沙|倉 さくら, stay)
                if form not in self.jmdict and any(t.part_of_speech()[1] == '数詞' for t in span) and not _spelled(span, reading):
                    continue
                if form in self.jmdict and form in self.only:
                    return i + n, Word(begin, end, form, reading, 'only', 1.0)
                return i + n, Word(begin, end, form, reading, 'dictionary', None)
            # A noun split before its last kanji, then 前 (朝|食前, 大|戦前): the noun, then まえ; not inside
            # a longer word (再|現前|化 さいげんぜんか)
            head = form[:-1]
            if (n == 2 and form[-1] == '前' and len(span[1].surface()) > 1 and form not in self.readings
                    and head in self.only and all(map(is_kanji, head)) and not (text[end:end + 1] and is_kanji(text[end]))):
                return i + n, Word(begin, end, form, self.only[head] + 'まえ', 'default', None)
            # Sudachi's split of a word it doesn't keep whole: 一昨|日 いっさく|ひ is おととい
            default = DEFAULT_READINGS.get((form, ''.join(to_hiragana(t.reading_form()) for t in span)))
            if default and (form, default) in self.known:
                return i + n, Word(begin, end, form, default, 'default', None)
        return None

    def _numeral_idiom(self, span) -> bool:
        """Whether the span is a compound of 3+ kanji with a numeral token that the list reads one way,
        JMdict too, and the tokens don't: 十|中|八九 じっちゅうはっく, 三|白眼 さんぱくがん, 四|人組 よにんぐみ."""
        form = ''.join(t.surface() for t in span)
        reading = self.only.get(form)
        return bool(len(form) > 2 and all(map(is_kanji, form)) and reading and form in self.jmdict
                    and not form.endswith('文字') and form not in _NOT_IDIOMS
                    and any(_NUMERAL.match(t.surface()) for t in span)
                    and ''.join(to_hiragana(t.reading_form()) for t in span) != reading)

    def _idioms(self, text, tokens, words, hint_at, counted):
        """Phrases JMdict reads one way over 2-8 tokens with a kana token inside (歩|を|進める ほをすすめる,
        放っ|て|おく, 一|か|八|か): each kanji token's Word takes its slice of the phrase's reading, when the slice
        is a plain (PlainReadings, rendaku) or listed reading of the token; one Word per token, so word lists keep
        their rows. Not shown (`default`, certainty None); ruby, rules and counters win. Left out: phrases the list
        reads otherwise (or two ways, where the tokens read one), the tail of a longer word, a noun after a modifier, starting in a particle or, over two tokens, ending in one (外|に isn't ほかに), NOT_JOINED's (頭を振る: あたま too)."""
        at = {w.start: k for k, w in enumerate(words)}
        i = 0
        while i < len(tokens):
            found = None
            # not the tail of a longer word (書き|甲斐|が|ある: がい, not かいがある; a kana noun before a verb doesn't
            # glue: そのまま|放っ), nor a noun + case particle with a modifier right before it, which is meant literally
            # (大きな|音|を|上げ: おと); not after a demonstrative (その|身|を|捩る よじる), and compounds and noun-の-noun
            # phrases stay (大きな金ダライ かな, 従順な神の僕 しもべ)
            prev = tokens[i - 1] if i and _end(tokens[i - 1]) == tokens[i].begin else None
            pos, head = prev and prev.part_of_speech()[0], tokens[i].part_of_speech()[0]
            glued = prev and (pos in ('動詞', '形容詞', '接頭辞') or pos in ('名詞', '代名詞', '形状詞', '接尾辞')
                              and (head in ('名詞', '接尾辞') or _HEAD_SURFACE.match(prev.surface()[-1])))
            modified = prev and head == '名詞' and (pos == '連体詞' and not _DEMONSTRATIVE.match(prev.surface())
                                                   or prev.surface() == 'な' and pos == '助動詞')
            for n in range(min(8, len(tokens) - i), 1, -1) if not glued else ():
                span = tokens[i:i + n]
                if modified and span[1].surface() in ('を', 'が', 'に', 'で', 'と') and span[1].part_of_speech()[0] == '助詞':
                    continue
                found = self._idiom(text, span, words, at, hint_at, counted)
                if found and (found[0] in SHOWN_IDIOMS or any((f, r) != (words[k].form, words[k].reading) for k, r, f in found[1])):
                    break
                found = None
            if not found:
                i += 1
                continue
            phrase, found = found
            shown = phrase in SHOWN_IDIOMS
            for k, reading, form in found:
                same = (form, reading) == (words[k].form, words[k].reading)
                if not same or shown and words[k].source not in ('only', 'rule', 'model'):
                    words[k] = words[k]._replace(form=form, reading=reading, source='rule' if shown else 'default',
                                                 certainty=1.0 if shown else None)
            i += n
        return words

    def _idiom(self, text, span, words, at, hint_at, counted):
        """(phrase, [(index in words, reading, form)]) for the kanji tokens' Words in `span`, or None."""
        kana = [bool(KANA_READING.match(to_hiragana(t.surface()))) for t in span]
        begin, end = span[0].begin, _end(span[-1])
        if (not any(kana) or all(kana)
                or span[0].part_of_speech()[0] in ('助詞', '助動詞')
                or len(span) < 3 and span[-1].part_of_speech()[0] in ('助詞', '助動詞')
                or any(_end(a) != b.begin for a, b in zip(span, span[1:]))):
            return None
        form = ''.join(t.surface() for t in span[:-1]) + span[-1].dictionary_form()
        readings = self._jmdict_all.get(form)
        if (not readings or len(readings) != 1 or form in NOT_JOINED and NOT_JOINED[form].match(text, end)
                or form in self.readings and readings[0] not in self.readings[form]  # the list reads it otherwise
                or any(s < end and e > begin for s, (e, _) in hint_at.items())
                or any(s < end and e > begin for s, _, e, _, _ in counted)):
            return None
        plain = self._plain_check
        parts = [t.surface() for t in span[:-1]] + [span[-1].dictionary_form()]

        def align(k, pos):  # each token's slice of the reading, the first way that fits
            if k == len(parts):
                return [] if pos == len(readings[0]) else None
            if kana[k]:
                own = to_hiragana(parts[k])
                rest = readings[0].startswith(own, pos) and align(k + 1, pos + len(own))
                return None if rest is None or rest is False else [own] + rest
            stops = [len(readings[0])] if k == len(parts) - 1 else range(pos + 1, len(readings[0]))
            for stop in stops:
                piece = readings[0][pos:stop]
                if (parts[k], piece) in self.known or (parts[k], piece) in plain:
                    rest = align(k + 1, stop)
                    if rest is not None:
                        return [piece] + rest
            return None
        pieces = align(0, 0)
        if pieces is None:
            return None
        if len(self.readings.get(form, ())) > 1:
            # the list reads it two ways (他愛もない たあい/たわい): left as is where the tokens read it one of them
            current = []
            for k, t in enumerate(span):
                w = words[at[t.begin]] if t.begin in at else None
                current.append(to_hiragana(parts[k]) if kana[k] else w and w.reading and (
                    w.reading if k == len(span) - 1 else surface_reading(t.surface(), w.form, w.reading)) or '?')
            if spelling(''.join(current)) in {spelling(r) for r in self.readings[form]}:
                return None
        changes = []
        for k, (t, piece) in enumerate(zip(span, pieces)):
            if kana[k]:
                continue
            w = words[at[t.begin]] if t.begin in at else None
            if not w or w.end != _end(t) or w.source in ('ruby', 'rule', 'counter', 'book'):
                return None  # a Word over several tokens, or a sure reading: leave the phrase
            surface = t.surface()
            if k == len(span) - 1 or surface == w.form:
                if surface != w.form and piece.endswith('いい'):
                    return None  # いい doesn't conjugate: 寝つきが良く is よく
                if w.form == parts[k]:
                    changes.append((at[t.begin], piece, w.form))
                continue
            if surface_reading(surface, w.form, w.reading) == piece:
                changes.append((at[t.begin], w.reading, w.form))
                continue
            # a conjugated token: its lemma's listed reading (or another verb's: 放っ is 放る's, ほうっ) that gives the slice
            stem = surface[:-1] if surface.endswith('っ') else None
            lemmas = [w.form] + ([stem + e for e in 'うつる' if stem + e != w.form] if stem else [])
            hit = next(((r, f) for f in lemmas for r in self.readings.get(f, ()) if surface_reading(surface, f, r) == piece), None)
            if not hit:
                return None
            changes.append((at[t.begin], *hit))
        return form, changes

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
        sudachi = long_vowels(''.join(to_hiragana(t.reading_form()) for t in span))  # こーひー: JMdict's こうひい
        if any(surface_reading(surface, form, r) == sudachi for r in (reading, *self.readings.get(form, ()))):
            return None
        return reading

    def _term_reading(self, form, sudachi) -> str | None:
        """The term dictionaries' reading of a form the list and JMdict lack (Reader.terms), where it isn't
        Sudachi's: their one reading, or the first when Sudachi has none (a word it doesn't know)."""
        readings = self.terms.get(form)
        if not readings or sudachi and spelling(sudachi) in map(spelling, readings):
            return None
        return readings[0] if len(readings) == 1 or not (sudachi and KANA_READING.match(sudachi)) else None

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
