"""Readings of a number followed by a counter (三本 さんぼん, 一匹 いっぴき, 八日 ようか).

Sudachi gives numbers and counters as separate tokens with fixed readings (三/さん + 本/ぽん), so
the sound changes between them are made here, from tables of standard Japanese counter grammar
(as in Wiktionary's "Appendix:Japanese counters" and the NHK pronunciation dictionary's usage):
gemination of 1, 6, 8, 10 and 100 before k, s, t and h counters (h becomes p), voicing after 3,
何, 千 and 万 (本 ぼん, 階 がい), the irregular day counts (ついたち … とおか, はつか) and each
counter's 4, 7 and 9 (四時 よじ, 七時 しちじ, 九時 くじ, 四月 しがつ).

Where a choice is common, one reading is given: 8 geminates (八本 はっぽん, not はちほん), 10 is
じゅっ (not じっ), 七人 is しちにん, 羽 is わ except after 3/何/千 (ば) and 6, 8, 10, 100 (っぱ).
Lexicalised words Sudachi keeps as one token (一人, 二十歳, 十分 じゅうぶん, 何本) are left alone."""
import re

_DIGIT = {c: i for i, c in enumerate('〇一二三四五六七八九')}
_DIGIT.update({c: i for i, c in enumerate('0123456789')})
_DIGIT.update({c: i for i, c in enumerate('０１２３４５６７８９')})
_UNIT = {'十': 10, '百': 100, '千': 1000}
_BIG = {'万': 10 ** 4, '億': 10 ** 8, '兆': 10 ** 12}
NUMERAL = re.compile('[〇一二三四五六七八九十百千万億兆0-9０-９]+|何|幾|何[十百千万]')

_KANA = {1: 'いち', 2: 'に', 3: 'さん', 4: 'よん', 5: 'ご', 6: 'ろく', 7: 'なな', 8: 'はち', 9: 'きゅう'}
_HUNDREDS = {1: 'ひゃく', 3: 'さんびゃく', 6: 'ろっぴゃく', 8: 'はっぴゃく'}
_THOUSANDS = {1: 'せん', 3: 'さんぜん', 8: 'はっせん'}
_QUESTION = {'何': ('なん', '何'), '幾': ('いく', '幾'), '何十': ('なんじゅう', 10), '何百': ('なんびゃく', 100),
             '何千': ('なんぜん', 1000), '何万': ('なんまん', 10 ** 4)}

# counter (Sudachi's normalized form) -> (plain reading, sound class, reading after 3/何/千/万, 4 7 9)
# class: k s t h gemination (h becomes p), w 羽, n none
_479 = ('よん', 'なな', 'きゅう')
_YO = ('よ', 'なな', 'きゅう')
_HOURS = ('よ', 'しち', 'く')
COUNTERS = {
    '本': ('ほん', 'h', 'ぼん', _479), '匹': ('ひき', 'h', 'びき', _479), '杯': ('はい', 'h', 'ばい', _479),
    '発': ('はつ', 'h', 'ぱつ', _479), '泊': ('はく', 'h', 'ぱく', _479), '版': ('はん', 'h', 'ぱん', _479),
    '編': ('へん', 'h', 'ぺん', _479), '分': ('ふん', 'h', 'ぷん', _479),
    '個': ('こ', 'k', None, _479), '回': ('かい', 'k', None, _479), '階': ('かい', 'k', 'がい', _479),
    '軒': ('けん', 'k', 'げん', _479), '件': ('けん', 'k', None, _479), '曲': ('きょく', 'k', None, _479),
    '巻': ('かん', 'k', None, _479), '箇月': ('かげつ', 'k', None, _479), '箇所': ('かしょ', 'k', None, _479),
    '冊': ('さつ', 's', None, _479), '歳': ('さい', 's', None, _479), '足': ('そく', 's', 'ぞく', _479),
    '週': ('しゅう', 's', None, _479), '週間': ('しゅうかん', 's', None, _479),
    '対': ('つい', 't', None, _479), '点': ('てん', 't', None, _479), '頭': ('とう', 't', None, _479),
    '通': ('つう', 't', None, _479),
    '羽': ('わ', 'w', 'ば', _479),
    '枚': ('まい', 'n', None, _479), '台': ('だい', 'n', None, _479), '度': ('ど', 'n', None, _479),
    '番': ('ばん', 'n', None, _479), '倍': ('ばい', 'n', None, _479), '秒': ('びょう', 'n', None, _479),
    '名': ('めい', 'n', None, _479), '円': ('えん', 'n', None, _YO), '年': ('ねん', 'n', None, _YO),
    '年間': ('ねんかん', 'n', None, _YO), '時': ('じ', 'n', None, _HOURS), '時間': ('じかん', 'n', None, _HOURS),
    '人': ('にん', 'n', None, ('よ', 'しち', 'きゅう')),
}
_GEMINATE = {'k': {1, 6, 8, 10, 100}, 'h': {1, 6, 8, 10, 100}, 's': {1, 8, 10}, 't': {1, 8, 10},
             'w': {6, 8, 10, 100}}
_VOICED_AFTER = {3, '何', 1000, 10 ** 4}
_P = str.maketrans('はひふへほわ', 'ぱぴぷぺぽぱ')
_DAYS = {2: 'ふつ', 3: 'みっ', 4: 'よっ', 5: 'いつ', 6: 'むい', 7: 'なの', 8: 'よう', 9: 'ここの', 10: 'とお', 20: 'はつ'}
_MONTH = ('し', 'しち', 'く')


def number_value(surface: str):
    """The value of a written number (三十五, 1999, ３万, 一九九九), or None."""
    total = section = 0
    digits = None
    for char in surface:
        if char in _DIGIT:
            digits = (digits or 0) * 10 + _DIGIT[char]
        elif char in _UNIT:
            section += (1 if digits is None else digits) * _UNIT[char]
            digits = None
        elif char in _BIG:
            total += (section + (digits or 0) or 1) * _BIG[char]
            section, digits = 0, None
        else:
            return None
    value = total + section + (digits or 0)
    return value if 0 < value < 10 ** 16 else None


def _elements(value: int):
    """[(kana, kind)]: the spoken parts of a number; kind is 1-9 for a final digit, else the unit."""
    out = []
    for big, name in ((10 ** 12, 'ちょう'), (10 ** 8, 'おく'), (10 ** 4, 'まん'), (1, '')):
        group = value // big % 10000
        if not group:
            continue
        for unit in (1000, 100, 10, 1):
            d = group // unit % 10
            if not d:
                continue
            if unit == 1000:
                out.append((_THOUSANDS.get(d) or _KANA[d] + 'せん', 1000))
            elif unit == 100:
                out.append((_HUNDREDS.get(d) or _KANA[d] + 'ひゃく', 100))
            elif unit == 10:
                out.append(('じゅう' if d == 1 else _KANA[d] + 'じゅう', 10))
            else:
                out.append((_KANA[d], d))
        if name:
            if name == 'ちょう':
                out[-1] = (_geminate(out[-1][0]) if out[-1][1] in (1, 8, 10) else out[-1][0], out[-1][1])
            out.append((name, big))
    return out


def _geminate(kana: str) -> str:
    return re.sub('(いち|ろく|はち|じゅう|ゃく)$', lambda m: {'いち': 'いっ', 'ろく': 'ろっ', 'はち': 'はっ',
                                                              'じゅう': 'じゅっ'}.get(m.group(1), 'ゃっ'), kana)


def _days(value, kana, kind, after_month: bool):
    """(number, counter) readings of a number of days or a date: 二日 ふつ + か."""
    if value == 1:
        return ('ついたち', None) if after_month else ('いち', 'にち')
    if value in _DAYS:
        return _DAYS[value], 'か'
    if kind == 4:
        return kana[:-2] + 'よっ', 'か'  # 十四日, 二十四日
    if kind in (7, 9):
        return kana[:-len(_KANA[kind])] + {7: 'しち', 9: 'く'}[kind], 'にち'
    return kana, 'にち'


def reading(number: str, counter: str, sudachi: str = '', before: str = ''):
    """(number's reading, counter's reading) for `number` followed by the counter token
    (`counter`: its normalized form, `sudachi`: Sudachi's reading of it in hiragana), or
    (reading of the whole, None) when it can't be split (一人 ひとり, 二十日 はつか), or None.
    `before`: the text before the number (月 there makes 一日 ついたち)."""
    if number in _QUESTION:
        kana, kind = _QUESTION[number]
        value = None
    else:
        value = number_value(number)
        if value is None:
            return None
        elements = _elements(value)
        kana, kind = ''.join(k for k, _ in elements), elements[-1][1]
    final = _KANA.get(kind) if isinstance(kind, int) and kind < 10 else None
    if counter == '日' and sudachi in ('にち', 'か') or counter == '日間' and sudachi in ('にちかん', 'かかん'):
        tail = 'かん' if counter == '日間' else ''
        if value is None:
            return kana, 'にち' + tail
        number, day = _days(value, kana, kind, before.endswith('月') and not tail)
        return number, day and day + tail
    if counter == '月':
        if sudachi != 'がつ' or not (kind == '何' or value and value <= 12):
            return None
        if kind in (4, 7, 9):
            kana = kana[:-len(final)] + _MONTH[(4, 7, 9).index(kind)]
        return kana, 'がつ'
    if counter == '分' and sudachi == 'ぶん':  # a fraction: 三分の一
        return kana, 'ぶん'
    if counter == '人' and value in (1, 2):
        return ('ひとり', 'ふたり')[value - 1], None
    if counter == '歳' and value == 20:
        return 'はたち', None
    if counter not in COUNTERS:
        return None
    plain, cls, voiced, four79 = COUNTERS[counter]
    if kind in (4, 7, 9):
        kana = kana[:-len(final)] + four79[(4, 7, 9).index(kind)]
    if kind in _GEMINATE.get(cls, ()):
        return _geminate(kana), plain.translate(_P) if cls in 'hw' else plain
    if voiced and kind in _VOICED_AFTER:
        return kana, voiced
    if counter == '分' and kind == 4:
        return kana, 'ぷん'
    return kana, plain


def _is_numeral(token) -> bool:
    # 八千, 三百 are also names in Sudachi: before a counter they are numbers
    return token.part_of_speech()[1] in ('数詞', '固有名詞') and bool(NUMERAL.fullmatch(token.surface()))


def spans(text: str, tokens: list):
    """(start, number end, end, number's reading, counter's reading) for each number + counter in
    `tokens` (Sudachi tokens of `text`); the number's reading is the whole span's and the counter's
    None when the reading doesn't split (一人 ひとり)."""
    from .readings import to_hiragana
    def adjacent(a, b):
        return a.begin + len(a.surface()) == b.begin

    out = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        surface = token.surface()
        m = NUMERAL.match(surface) if token.part_of_speech()[3] == '姓' else None
        if m and m.end() < len(surface) and surface[m.end():] in COUNTERS:  # 三軒, 百本 read as surnames
            found = reading(m.group(), surface[m.end():], '', text[:token.begin])
            if found:
                out.append((token.begin, token.begin + m.end(), token.begin + len(surface), *found))
        if not _is_numeral(token):
            i += 1
            continue
        j = i + 1
        while j < len(tokens) and _is_numeral(tokens[j]) and adjacent(tokens[j - 1], tokens[j]):
            j += 1
        # part of a number that isn't read here (ン十万: the 万 alone is not いちまん)
        unread = i and adjacent(tokens[i - 1], token) and tokens[i - 1].part_of_speech()[1] == '数詞'
        if j < len(tokens) and adjacent(tokens[j - 1], tokens[j]) and not unread:
            counter = tokens[j]
            end = counter.begin + len(counter.surface())
            # 一対一 (one on one) is いったいいち
            if not (counter.normalized_form() == '対' and NUMERAL.match(text[end:end + 1])):
                found = reading(text[token.begin:counter.begin], counter.normalized_form(),
                                to_hiragana(counter.reading_form()), text[:token.begin])
                if found:
                    out.append((token.begin, counter.begin, end, *found))
        i = j
    return out
