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

from .cues import DURATION_AFTER, DURATION_BEFORE, words

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
# class: k s t h gemination (h becomes p), w 羽, y ひと/ふた for 1 and 2 (一晩 ひとばん), n none
_479 = ('よん', 'なな', 'きゅう')
_YO = ('よ', 'なな', 'きゅう')
_HOURS = ('よ', 'しち', 'く')
COUNTERS = {
    '本': ('ほん', 'h', 'ぼん', _479), '匹': ('ひき', 'h', 'びき', _479), '杯': ('はい', 'h', 'ばい', _479),
    '発': ('はつ', 'h', 'ぱつ', _479), '泊': ('はく', 'h', 'ぱく', _479), '版': ('はん', 'h', 'ぱん', _479),
    '編': ('へん', 'h', 'ぺん', _479), '分': ('ふん', 'h', 'ぷん', _479), '歩': ('ほ', 'h', 'ぽ', _479),
    '個': ('こ', 'k', None, _479), '回': ('かい', 'k', None, _479), '階': ('かい', 'k', 'がい', _479),
    '軒': ('けん', 'k', 'げん', _479), '件': ('けん', 'k', None, _479), '曲': ('きょく', 'k', None, _479),
    '巻': ('かん', 'k', None, _479), '箇月': ('かげつ', 'k', None, _479), '箇所': ('かしょ', 'k', None, _479),
    '冊': ('さつ', 's', None, _479), '歳': ('さい', 's', None, _479), '足': ('そく', 's', 'ぞく', _479),
    '週': ('しゅう', 's', None, _479), '週間': ('しゅうかん', 's', None, _479),
    '対': ('つい', 't', None, _479), '点': ('てん', 't', None, _479), '頭': ('とう', 't', None, _479),
    '通': ('つう', 't', None, _479),
    '着': ('ちゃく', 't', None, _479),
    '羽': ('わ', 'w', 'ば', _479),
    '枚': ('まい', 'n', None, _479), '台': ('だい', 'n', None, _479), '度': ('ど', 'n', None, _479),
    '番': ('ばん', 'n', None, _479), '倍': ('ばい', 'n', None, _479), '秒': ('びょう', 'n', None, _479),
    '名': ('めい', 'n', None, _479), '円': ('えん', 'n', None, _YO), '年': ('ねん', 'n', None, _YO),
    '年間': ('ねんかん', 'n', None, _YO), '時': ('じ', 'n', None, _HOURS), '時間': ('じかん', 'n', None, _HOURS),
    '人': ('にん', 'n', None, ('よ', 'しち', 'きゅう')),
    # older measures and less common counters
    '銭': ('せん', 's', None, _479), '周': ('しゅう', 's', None, _479), '隻': ('せき', 's', None, _479),
    '艘': ('そう', 's', None, _479), '寸': ('すん', 's', 'ずん', _479), '尺': ('しゃく', 's', 'じゃく', _479),
    '升': ('しょう', 's', 'じょう', _479), '貫': ('かん', 'k', 'がん', _479), '脚': ('きゃく', 'k', None, _479),
    '間': ('けん', 'k', 'げん', _479), '町': ('ちょう', 't', None, _479), '丁': ('ちょう', 't', None, _479),
    '列': ('れつ', 'n', None, _479), '畳': ('じょう', 'n', None, _YO), '分目': ('ぶんめ', 'n', None, ('よん', 'しち', 'く')),
    '話': ('わ', 'n', None, _479),  # episodes (第三話, 何話)
    '晩': ('ばん', 'y', None, _479), '粒': ('つぶ', 'y', None, _479), '坪': ('つぼ', 'y', None, _479),
}
# counters whose kanji has other readings after a number (二間 ふたま, 三町 まち): only when Sudachi reads them so
_ONLY_AS = {'間': 'けん', '町': 'ちょう', '畳': 'じょう'}
# 二三日, 四五人: two consecutive digits are "two or three", each read
_PAIR = re.compile('[一二三四五六七八][二三四五六七八九]')
# right after an era name the digits are a year (昭和二三年 is 23), not "two or three"
_ERA = re.compile('(?:明治|大正|昭和|平成|令和|元禄)$')
_PAIR_FIRST = {'一': 'いち', '二': 'に', '三': 'さん', '四': 'し', '五': 'ご', '六': 'ろく', '七': 'しち', '八': 'はち'}
_GEMINATE = {'k': {1, 6, 8, 10, 100}, 'h': {1, 6, 8, 10, 100}, 's': {1, 8, 10}, 't': {1, 8, 10},
             'w': {6, 8, 10, 100}}
_VOICED_AFTER = {3, '何', 1000, 10 ** 4}
# 一間 is ひとま (one room) next to a room or lodging word (六畳一間, 一間の部屋, 一間を借りる), else いっけん
_HITOMA_BEFORE = re.compile('(?:畳|部屋|座敷|和室|宿|旅館|下宿|アパート|屋敷|家|二階)の?$')
_HITOMA_AFTER = re.compile('の(?:部屋|座敷|和室)|に(?:住|暮|通|案内|泊|寝)|を(?:借|間借|与|あてが)|きり')
_P = str.maketrans('はひふへほわ', 'ぱぴぷぺぽぱ')
_DAYS = {2: 'ふつ', 3: 'みっ', 4: 'よっ', 5: 'いつ', 6: 'むい', 7: 'なの', 8: 'よう', 9: 'ここの', 10: 'とお', 20: 'はつ'}
_MONTH = ('し', 'しち', 'く')
# native つ counts (四つ よっつ; Sudachi reads 四 よん, 六 むい, 八 よう) and their compound forms (四つ切り よつぎり,
# 四つ辻 よつつじ), the same for 1, 2, 5, 7 and 9
_TSU = {1: 'ひと', 2: 'ふた', 3: 'みっ', 4: 'よっ', 5: 'いつ', 6: 'むっ', 7: 'なな', 8: 'やっ', 9: 'ここの'}
_TSU_COMPOUND = {3: 'み', 4: 'よ', 6: 'む', 8: 'や'}
# a one-kanji noun after Xつ makes a compound (四つ辻, 八つ腕; and 裂く: 八つ裂き), except these, which go on
# counting (三つ上, 四つ目, 二つ分, 三つ先, 三つ四つ); longer nouns are counted (三つ指摘, ６つ部屋がある)
_TSU_GOES_ON = '上下目分程位共毎余先前後隣横縦奥右左年頃数〇一二三四五六七八九十百千'
# 分 as a tenth (ぶ): in pairs (五分五分, 七分三分, 五分と五分), after 割/寸/両 (三割五分, 一寸五分) and before
# 咲き/目/通り (三分咲き, 八分目)
_BU_BEFORE = re.compile(r'(?:[割寸両]|[〇一二三四五六七八九十0-9０-９]分と?)$')
_BU_AFTER = re.compile(r'と?[〇一二三四五六七八九十0-9０-９]+分|[咲目]|通り|どおり')
# 十分 on its own (no number before it) is じゅうぶん, "enough", unless a cue says minutes (三時十分,
# あと十分, 十分後, 十分ほど); readings._CONTEXT_RULES uses them too, where Sudachi keeps 十分 one token.
# Also a stretch of time going by (十分もしないうちに, 十分が過ぎ, 十分だけ待って, 十分休憩), a trip's length
# (歩いて十分, 車で十分) and a time next to it (二時間十分, 五分か十分か).
TEN_MINUTES_BEFORE = ('(?:' + words(DURATION_BEFORE) + r'|[0-9０-９〇零一二三四五六七八九十何]時|時間と?'
                      r'|(?:歩いて|徒歩|車で|バスで|電車で|自転車で|タクシーで|待つこと|歩くこと|走ること|かれこれ|開始)'
                      r'|[0-9０-９〇一二三四五六七八九十]分(?:か|や|と)、?)$')
TEN_MINUTES_AFTER = ('(?:' + words(DURATION_AFTER) + r'|前(?!後|進)|まえ|間(?!に合|にあ|違|ちが)|あまり(?!に|の)'
                     r'|[0-9０-９〇一二三四五六七八九]+秒|で(?:着|終|戻|帰|出|始|済|行|来)'
                     r'|も(?:しな|せず|な[いく]|経|た[たっつ]|かか|掛|すれ|すると|続|走|歩|待|早|遅|過)'
                     r'|[はが](?:経|過|た[たっつ]|かか|掛)|だけ(?!ど|れど)|ちょっと|頃|ごろ|休憩|の(?:間|休憩|遅|距離|道)'
                     r'|か(?:[二三四五]十|そこら)|から[二三四五]?十|以上は?(?:かか|掛|歩|走|経|待)|も横)')
_TEN_MINUTES = (re.compile(TEN_MINUTES_BEFORE), re.compile(TEN_MINUTES_AFTER))


# 一時 ひととき: a pleasant while (至福の一時, 夢のような一時, 先輩との一時), as a noun before a particle or the
# sentence's end; books' ruby 46 of 47 (the other いっとき). Times of day are left out (夜の一時, 午後の一時: clocks).
_HITOTOKI_BEFORE = re.compile(r'(?:(?:至福|優雅|寛ぎ|くつろぎ|憩い|癒し|癒やし|安らぎ|団欒|楽しい|穏やか|和やか|平和|幸せ|幸福|静か'
                              r'|有意義|有益|優しい|贅沢|素敵|大切|貴重|甘い)な?の?|(?:よう|様|みたい)な|(?:放課後|昼休み|食後|日暮れ前|休日|週末)の|との)$')
_HITOTOKI_AFTER = re.compile(r'(?:を|が|は|も|。|、|だ|で[しすあ]|…|」|』|$)')


def is_year(number: str, before: str) -> bool:
    """Whether two consecutive kanji digits are an era's year (昭和二三年: 23), not "two or three"."""
    return bool(_PAIR.fullmatch(number) and _ERA.search(before))


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


def _elements(value: int, one_thousand: bool = False):
    """[(kana, kind)]: the spoken parts of a number; kind is 1-9 for a final digit, else the unit.
    one_thousand: 千 is written 一千, read いっせん (一千万 いっせんまん)."""
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
                out.append(('いっせん' if d == 1 and one_thousand else _THOUSANDS.get(d) or _KANA[d] + 'せん', 1000))
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


def number_reading(value: int, one_thousand: bool = False) -> str:
    """A number's reading: 六百 ろっぴゃく, 三千 さんぜん (一千 いっせん with one_thousand)."""
    # shortcut: one_thousand applies to every 千 of the number (三千一千 doesn't occur)
    return ''.join(kana for kana, _ in _elements(value, one_thousand))


def reading(number: str, counter: str, sudachi: str = '', before: str = '', after: str = '',
            compound: bool = False):
    """(number's reading, counter's reading) for `number` followed by the counter token
    (`counter`: its normalized form, `sudachi`: Sudachi's reading of it in hiragana), or
    (reading of the whole, None) when it can't be split (一人 ひとり, 二十日 はつか), or None.
    `before`: the text before the number (月 there makes 一日 ついたち), `after`: the text after
    the counter (五分五分: 分 ぶ), `compound`: a noun follows that makes a compound with it (四つ辻)."""
    if counter in ('つ', 'つ切り', 'つ折り'):
        value = number_value(number)
        if value not in _TSU:
            return None
        kana = _TSU_COMPOUND.get(value, _TSU[value]) if compound or counter != 'つ' else _TSU[value]
        return kana, sudachi or 'つ'
    if _PAIR.fullmatch(number) and _DIGIT[number[1]] == _DIGIT[number[0]] + 1 and not is_year(number, before):
        if counter in ('日', '日間'):  # 二三日 にさんにち, 三四日 さんよっか
            return _PAIR_FIRST[number[0]] + ('よっ' if number[1] == '四' else _KANA[_DIGIT[number[1]]]), \
                ('か' if number[1] == '四' else 'にち') + counter[1:].replace('間', 'かん')
        found = reading(number[1], counter, sudachi, '', after)
        return found and found[1] and (_PAIR_FIRST[number[0]] + found[0], found[1])
    if number in _QUESTION:
        kana, kind = _QUESTION[number]
        value = None
    else:
        value = number_value(number)
        if value is None:
            return None
        elements = _elements(value, '一千' in number)
        kana, kind = ''.join(k for k, _ in elements), elements[-1][1]
    final = _KANA.get(kind) if isinstance(kind, int) and kind < 10 else None
    if counter == '時' and number == '一' and _HITOTOKI_BEFORE.search(before) and _HITOTOKI_AFTER.match(after):
        return 'ひととき', None  # 至福の一時, 優雅な一時を過ごす (not 夜の一時を回る: a clock time)
    if counter == '日' and number == '一' and re.match(r'の長(?![さいくけかめ所男女子期官])', after):
        return 'いち', 'じつ'  # 一日の長 (a slight edge): いちじつ
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
    if counter == '分' and (_BU_BEFORE.search(before) or _BU_AFTER.match(after)):
        if kind in (4, 7, 9):
            kana = kana[:-len(final)] + ('よん', 'しち', 'く')[(4, 7, 9).index(kind)]
        return kana, 'ぶ'
    if counter == '分' and number == '十' and not NUMERAL.search(before[-1:]) \
            and not (_TEN_MINUTES[0].search(before) or _TEN_MINUTES[1].match(after)):
        return 'じゅう', 'ぶん'  # 十分 "enough", where Sudachi split it (十分には)
    # a fraction (三分の一), unless の goes on with something else (徒歩１０分のところ: ふん; 十分の理解 never gets here)
    if counter == '分' and sudachi == 'ぶん' and (after[:1] != 'の' or NUMERAL.match(after[1:2])):
        return kana, 'ぶん'
    if counter == '人' and value in (1, 2):
        return ('ひとり', 'ふたり')[value - 1], None
    if counter == '歳' and value == 20:
        return 'はたち', None
    if counter not in COUNTERS or sudachi and _ONLY_AS.get(counter, sudachi) != sudachi:
        return None
    if counter == '升' and after[:1] == '目':  # 二升目: the second square (升目 ますめ)
        return None
    plain, cls, voiced, four79 = COUNTERS[counter]
    if counter == '間' and value == 1 and (_HITOMA_BEFORE.search(before) or _HITOMA_AFTER.match(after)):
        return 'ひと', 'ま'
    if cls == 'y' and value in (1, 2):
        return ('ひと', 'ふた')[value - 1], plain
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


def _fused(token, number: str, counter: str) -> bool:
    """Whether a token that is a number and a counter (一回, 三軒) is read as one here: names
    (三軒 みのき, 一列 かずなみ) and words Sudachi reads without the sound change (一回 いちかい)."""
    from .readings import to_hiragana
    pos = token.part_of_speech()
    value = number_value(number)
    return pos[2] == '人名' or pos[1] == '普通名詞' and value is not None and \
        to_hiragana(token.reading_form()) == number_reading(value) + COUNTERS[counter][0]


def spans(text: str, tokens: list):
    """(start, number end, end, number's reading, counter's reading) for each number + counter in
    `tokens` (Sudachi tokens of `text`); the number's reading is the whole span's and the counter's
    None when the reading doesn't split (一人 ひとり)."""
    from .readings import is_kanji, to_hiragana
    def adjacent(a, b):
        return a.begin + len(a.surface()) == b.begin

    out = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        surface = token.surface()
        m = NUMERAL.match(surface)
        if m and m.end() < len(surface) and surface[m.end():] in COUNTERS and _fused(token, m.group(), surface[m.end():]):
            found = reading(m.group(), surface[m.end():], '', text[:token.begin],
                            text[token.begin + len(surface):token.begin + len(surface) + 4])
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
            tens = re.fullmatch('(十)(分|人)', counter.surface())
            if tens:  # 三 + 十分 (じゅうぶん), 二 + 十人: the number goes on
                found = reading(text[token.begin:counter.begin + 1], tens[2], 'ふん' if tens[2] == '分' else '',
                                text[:token.begin], text[end:end + 4])
                if found:
                    out.append((token.begin, counter.begin + 1, end, *found))
                i = j + 1
                continue
            # 一対一 (one on one) is いったいいち
            if not (counter.normalized_form() == '対' and NUMERAL.match(text[end:end + 1])):
                following = tokens[j + 1] if j + 1 < len(tokens) and adjacent(counter, tokens[j + 1]) else None
                word = following.surface() if following else ''
                compound = word[:1] == '裂' or len(word) == 1 and is_kanji(word) and word not in _TSU_GOES_ON \
                    and following.part_of_speech()[0] == '名詞'
                found = reading(text[token.begin:counter.begin], counter.normalized_form(),
                                to_hiragana(counter.reading_form()), text[:token.begin], text[end:end + 4], compound)
                if found:
                    out.append((token.begin, counter.begin, end, *found))
        i = j
    return out
