"""Readings of kanji words in context: the book's ruby (ruby_reading) and hand rules for
forms whose reading depends on the words around them (context_reading).

`known` is the set of (written form, hiragana reading) pairs a reading must be one of,
e.g. the keys of a Yomitan frequency list's readings (yurigana.yomitan.reading_ranks).
Anything with `__contains__` works.
"""
import re

from .kana import HAS_KANJI, HIRAGANA_WORD, is_kanji, small_kana, to_hiragana  # noqa: F401 (HAS_KANJI: evaluate.py, chimimouryou)
from .rules import CONTEXT_RULES, DEFAULT_KEEP, IKU_AFTER, IKU_IDIOM, IKU_MEANS, IKU_PATH, SPLIT_TOKENS, WRONG_LEMMA


def ruby_reading(hints: dict, begin: int, surface: str, form: str, known) -> str | None:
    """The book's ruby as the reading of a word whose head token starts at `begin`: ruby over that
    token (one span or adjacent per-kanji spans, 人《ひと》気《け》), or over its kanji stem when the
    rest is kana (行《い》った: the ruby plus the lemma's okurigana, いく), in hiragana, and a
    reading listed for the form (`known`), as written or with
    large kana made small (いつしよ, see kana.small_kana). Flavour ruby (マジ over 本気, そら over
    宇宙) is never a reading."""
    token_end, end, reading = begin + len(surface), begin, ''
    while end < token_end and end in hints and hints[end][0] > end:
        end, part = hints[end]
        reading += part
    if end == begin or end > token_end or not HIRAGANA_WORD.match(reading):
        return None
    tail = ''
    if end < token_end:
        base = surface[:end - begin]
        if not form.startswith(base) or any(is_kanji(c) for c in surface[end - begin:] + form[len(base):]):
            return None  # ruby over part of a compound (魚《うお》市場), or a lemma spelled differently
        tail = form[len(base):]
    for candidate in (reading, *small_kana(reading)):
        if (form, candidate + tail) in known:
            return candidate + tail
    return None


def split_token(text: str, begin: int, surface: str):
    """(end, form, reading, shown) of SPLIT_TOKENS's first entry for the token `surface` at `begin`, else None."""
    line = max(text.rfind('\n', 0, begin) + 1, begin - 12)
    for before, after, span, form, reading, shown in SPLIT_TOKENS.get(surface, ()):
        if (not before or before.search(text[line:begin])) and (not after or after.match(text, begin + len(surface))):
            return begin + (span or len(surface)), form, reading, shown
    return None


def right_lemma(text: str, begin: int, form: str, end: int | None = None) -> str:
    """The word a token at text[begin:end] with Sudachi's lemma `form` is (WRONG_LEMMA), else `form`."""
    fix = WRONG_LEMMA.get(form)
    if fix and (fix[1] and fix[1].search(text[max(text.rfind('\n', 0, begin) + 1, begin - 24):begin])
                or fix[2] and end is not None and fix[2].match(text, end)):
        return fix[0]
    return form


# 入れる is also 入る's potential (はいれる: 部屋には入れない, 中に入れた; books' ruby はいれる 34% in a clause without
# を): not `only` there, unless the 入れ is imperative, volitional, causative or passive, before a giving or
# trying verb (入れてくれ, 入れておく), or after 手に, 口に… (T242).
_CLAUSE = re.compile(r'[、。「」『』！？!?（）()\n…―─]')
_PUT_AFTER = re.compile(r'よ|ろ|させ|さす|られ|て(?:くれ|くだ|下さ|もら|貰|あげ|上げ|やる|やっ|ほし|欲し|お|置|み|見)')
_PUT_INTO = re.compile(r'(?:手|口|耳|目|頭|視界|視野|念頭|考慮|計算|勘定|懐|射程|ポケット|鞄|カバン|袋|箱)[にへ](?:は|も)?$')


def may_be_potential(text: str, begin: int, form: str) -> bool:
    """Whether 入れる at `begin` may be 入る's potential はいれる (see above)."""
    if form != '入れる' or not text.startswith('入れ', begin):
        return False
    clause = _CLAUSE.split(text[max(0, begin - 40):begin])[-1]
    return 'を' not in clause and not _PUT_INTO.search(clause) and not _PUT_AFTER.match(text, begin + 2)


def goes(text: str, tokens: list, i: int) -> bool:
    """Whether 行っ at tokens[i], Sudachi's 行う, is 行く (rules.IKU_*, T432)."""
    begin = tokens[i].begin
    clause = _CLAUSE.split(text[max(0, begin - 40):begin])[-1]
    if 'を' in clause:
        return bool(IKU_PATH.search(clause) or text.startswith('たり', begin + 2) and IKU_AFTER.match(text, begin + 2))
    if IKU_AFTER.match(text, begin + 2) or IKU_IDIOM.search(clause):
        return True
    k = i - 1  # the particle before, past は, も, でも… (病院にも行った, トイレにでも行った)
    while k >= 0 and tokens[k].begin + len(tokens[k].surface()) == tokens[k + 1].begin and (
            tokens[k].surface() in ('は', 'も', 'でも', 'だけ', 'さえ') or tokens[k].surface() == 'で' and tokens[k].part_of_speech()[0] == '助動詞'):
        k -= 1
    if k < 0 or tokens[k].begin + len(tokens[k].surface()) != tokens[k + 1].begin or tokens[k].part_of_speech()[1] != '格助詞':
        return False
    particle = tokens[k].surface()
    return particle in ('に', 'へ', 'まで') or particle == 'で' and bool(IKU_MEANS.search(text, 0, tokens[k].begin))


def default_kept(text: str, begin: int, end: int, form: str) -> bool:
    """Whether DEFAULT_KEEP keeps Sudachi's reading of `form` at text[begin:end]."""
    keep = DEFAULT_KEEP.get(form)
    return bool(keep and (keep[0].search(text[max(0, begin - 12):begin]) or keep[1].match(text, end)))




# One-kanji nouns Sudachi takes as a suffix (接尾辞) after a word no suffix attaches to: a function word,
# an adverb, a verb or a time word (一日中雨 う, いつ家 や, いつも君 くん, 矢は的 てき, 一度下 か, 立ち店 てん):
# the noun's own reading. Not after nouns, names and counters (豪雨, 佐藤家, 田中君, 一号店, 五番街, 画面下);
# 君 not after a verb's stem (指示待ち君) or a letter (Ａ君), 的 only after a particle, adverb or 連体詞 (アタシ的に).
SPLIT_SUFFIX = {('雨', 'う'): 'あめ', ('家', 'か'): 'いえ', ('家', 'や'): 'いえ', ('君', 'くん'): 'きみ',
                ('的', 'てき'): 'まと', ('下', 'か'): 'した', ('店', 'てん'): 'みせ', ('街', 'がい'): 'まち',
                ('車', 'しゃ'): 'くるま', ('石', 'せき'): 'いし'}
_NO_SUFFIX_POS = {'助詞', '助動詞', '代名詞', '副詞', '動詞', '連体詞', '接続詞', '感動詞', '補助記号'}
_SPLIT_POS = {'的': {'助詞', '副詞', '連体詞'}, '君': _NO_SUFFIX_POS - {'動詞'}}
_SPLIT_EDGE = {'的': '「『（(、。！？!?▼'}  # a 的 after a quote or space is the suffix (「暫定」的に, タイミング？　的には)
_TIME_SPAN = re.compile(r'(?:日中|晩中|週間|時間|日間|度)$')


def split_suffix(text: str, begin: int, surface: str, sudachi: str, pos, previous_pos) -> str | None:
    """SPLIT_SUFFIX's reading of a suffix token `surface` at text[begin:], given its part of speech
    and the previous adjacent token's (None at the start or after a space)."""
    reading = SPLIT_SUFFIX.get((surface, sudachi))
    if not reading or pos[0] != '接尾辞' or (surface == '的' and text.startswith('な', begin + 1)):
        return None
    if previous_pos is None or previous_pos[0] == '補助記号':  # after punctuation: only a sentence's or quote's edge
        before = text[begin - 1:begin]                         # (not Ａ君, ○○君, 『剣聖』君, 「暫定」的, ……君)
        return reading if (before or surface != '的') and before in _SPLIT_EDGE.get(surface, '「」『（）()、。，！？!?▼〝《》 \u3000\n') else None
    if previous_pos[0] in _SPLIT_POS.get(surface, _NO_SUFFIX_POS):
        return reading
    if surface != '的' and (tuple(previous_pos[1:3]) == ('普通名詞', '副詞可能') or _TIME_SPAN.search(text[:begin])):
        return reading
    return None


def glued(text: str, begin: int, end: int, after_too: bool = True) -> bool:
    """Whether a one-character word text[begin:end] is an affix Sudachi split off: a kanji or digit
    right before or after it, or a katakana word before it (郵便局側, 今学期, 3位, ダウンロード時),
    where default-readings.tsv's readings (側 そば, 今 いま, 位 くらい, 時 とき) don't hold.
    after_too=False: only what comes before counts."""
    before, after = text[max(begin - 1, 0):begin], text[end:end + 1] if after_too else ''
    return end - begin == 1 and (any(is_kanji(c) or c.isdigit() for c in before + after) or bool(re.match('[ァ-ヺー]', before)))


_CONTEXT = 12  # characters looked at on each side


_ELDER = {'兄': 'にい', '姉': 'ねえ'}
_HONORIFIC = re.compile('様|さま|ちゃま')


def context_reading(text: str, begin: int, surface: str, form: str, known, previous_pos=None) -> str | None:
    """The reading CONTEXT_RULES give a word whose head token `surface` starts at `begin` in
    `text`, if `known` lists it for the form (as in ruby_reading). previous_pos: the part of
    speech of the token ending where the word starts, if any (人 after a place name is じん)."""
    if form == '人' and previous_pos and tuple(previous_pos[1:3]) == ('固有名詞', '地名') and (form, 'じん') in known:
        return 'じん'
    # 家 is け after a family name (佐藤家, 伊達家) or a kanji proper noun (藤和家); Sudachi says か. Not after a
    # given name (景家 かげいえ) or a kana one (めぐみん家, 鶴屋さん家: ち).
    if form == '家' and previous_pos and (tuple(previous_pos[1:4]) == ('固有名詞', '人名', '姓') or tuple(
            previous_pos[1:3]) == ('固有名詞', '一般') and re.fullmatch(r'[一-鿿々]+', text[max(0, begin - 4):begin][-2:])) \
            and (form, 'け') in known:
        return 'け'
    # 金 as a suffix Sudachi split off a kanji noun or prefix (委託金, 援助金, 大金): きん, whatever follows
    # (委託金を払う); not after adverbs and pronouns (結構金を使った, 俺金ねえよ: かね).
    if form == '金' and previous_pos and (form, 'きん') in known and (
            previous_pos[0] == '接頭辞' and is_kanji(text[begin - 1:begin])
            or previous_pos[:2] == ('名詞', '普通名詞') and previous_pos[2] in ('一般', 'サ変可能', '形状詞可能')
            and all(is_kanji(c) for c in text[max(0, begin - 2):begin]) and begin >= 2):
        return 'きん'
    # 気味 is ぎみ as a suffix: right after a noun (風邪気味) or a verb's 連用形 (太り気味); Sudachi says きみ.
    if form == '気味' and previous_pos and (form, 'ぎみ') in known and (
            previous_pos[0] in ('名詞', '接尾辞') and previous_pos[2] != '副詞可能'
            or previous_pos[0] == '動詞' and ''.join(previous_pos[5:6]).startswith('連用形')
            # 押され気味, not ようで気味が悪い
            or previous_pos[0] == '助動詞' and ''.join(previous_pos[5:6]).startswith('連用形') and text[begin - 1] != 'で'
            and not re.match('[がの]?(?:悪|わる)', text[begin + len(surface):])):
        return 'ぎみ'
    # お兄様, お姉さま: にい, ねえ after the prefix お before 様 (T283); Sudachi says あに, あね. Without お (兄様) it is
    # either (にいさま, あにさま).
    if form in _ELDER and previous_pos and previous_pos[0] == '接頭辞' and text[begin - 1:begin] in ('お', '御') \
            and _HONORIFIC.match(text, begin + len(surface)) and (form, _ELDER[form]) in known:
        return _ELDER[form]
    rules = CONTEXT_RULES.get(form)
    if not rules:
        return None
    end = begin + len(surface)
    line_end = text.find('\n', end)
    before = text[max(text.rfind('\n', 0, begin) + 1, begin - _CONTEXT):begin]
    after = text[end:min(end + _CONTEXT, line_end if line_end >= 0 else len(text))]
    for reading, before_rule, after_rule, both in rules:
        hits = (bool(before_rule and before_rule.search(before)), bool(after_rule and after_rule.match(after)))
        if (all(hits) if both else any(hits)) and (form, reading) in known:
            return reading
    return None


_LARGE = str.maketrans('ぁぃぅぇぉっゃゅょゎ', 'あいうえおつやゆよわ')


def conjugated_reading(surface: str, form: str, sudachi: str, readings) -> str | None:
    """The one reading of `form` among `readings` whose stem, with the surface's kana after it,
    is Sudachi's reading of the conjugated `surface` (`sudachi`, hiragana; small kana not
    told apart): 行っ read いっ is 行く いく, not ゆく. None when none or several match.
    来る's stem is read き, こ or く."""
    stem, okurigana = re.fullmatch(r'(.*?)([ぁ-ゖ]*)', form).groups()
    tail = surface[len(stem):]
    if not stem or not surface.startswith(stem) or not re.fullmatch(r'[ぁ-ゖァ-ヺー]*', tail):
        return None
    tail = to_hiragana(tail)
    if form == '来る' and 'くる' in readings and sudachi[:1] in ('き', 'こ', 'く') and sudachi[1:] == tail:
        return 'くる'
    matches = [r for r in readings if r.endswith(okurigana) and len(r) > len(okurigana)
               and (r[:len(r) - len(okurigana)] + tail).translate(_LARGE) == sudachi.translate(_LARGE)]
    return matches[0] if len(matches) == 1 else None


def unlisted_reading(surface: str, form: str, sudachi: str) -> str | None:
    """The dictionary form's reading from Sudachi's reading of the conjugated `surface`, for a form
    the list has no reading for: 泳げ (泳げる), およげ → およげる; 思ひ (思ふ), おもひ → おもふ. The
    stem's reading plus the form's okurigana, so surface_reading gives `sudachi` back. None when
    the surface isn't the stem plus kana or Sudachi's reading doesn't end in that kana."""
    stem, okurigana = re.fullmatch(r'(.*?)([ぁ-ゖ]*)', form).groups()
    tail = surface[len(stem):]
    if not stem or not surface.startswith(stem) or (tail and not _KANA_TAIL.fullmatch(tail)):
        return None
    tail = to_hiragana(tail)
    if not sudachi or len(sudachi) <= len(tail) or not sudachi.endswith(tail):
        return None
    return sudachi[:len(sudachi) - len(tail)] + okurigana


_KANA_TAIL = re.compile(r'[ぁ-ゖァ-ヺーゝゞヽヾ]+')
# 来る's stem by what follows it: こ before the 未然形/命令形 endings (来ない, 来なきゃ, 来よう, 来い,
# 来られる, 来まい, 来ねえ), く before る/れば/りゃ, き otherwise (来た, 来ます, 来て, 来ながら, 来なさい).
_KO = re.compile(r'な[いくかけき]|まい|[いうよさらずぬねんれ]')


def surface_reading(surface: str, form: str, reading: str | None, after: str = '') -> str | None:
    """The reading of a token's surface from its dictionary form's: 行った, 行く, いく → いった.
    `after`: the text right after the token, for 来る, whose stem is read き, こ or く (来た きた)."""
    if reading is None or surface == form:
        return reading
    stem, okurigana = re.match(r'^(.*?)([ぁ-ゖ]*)$', form).groups()
    rest = surface[len(stem):]
    if not (stem and surface.startswith(stem) and reading.endswith(okurigana) and (not rest or _KANA_TAIL.fullmatch(rest))):
        return None
    if form == '来る' and reading == 'くる':
        kana = to_hiragana(rest + (_KANA_TAIL.match(after) or [''])[0])
        return ('く' if re.match(r'る|れ[ばど]|りゃ', kana) else 'こ' if _KO.match(kana) else 'き') + to_hiragana(rest)
    return reading[:len(reading) - len(okurigana)] + to_hiragana(rest)
