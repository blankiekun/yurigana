"""Readings of kanji words in context: the book's ruby (ruby_reading) and hand rules for
forms whose reading depends on the words around them (context_reading).

`known` is the set of (written form, hiragana reading) pairs a reading must be one of,
e.g. the keys of a Yomitan frequency list's readings (yurigana.yomitan.reading_ranks).
Anything with `__contains__` works.
"""
import itertools
import re

HAS_KANJI = re.compile(r'[㐀-䶿一-鿿豈-﫿]')
_HIRAGANA_WORD = re.compile(r'^[ぁ-ゖ]+$')


def is_kanji(char: str) -> bool:
    code = ord(char)
    return (0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0xF900 <= code <= 0xFAFF
            or 0x20000 <= code <= 0x3134F)



def to_hiragana(text: str) -> str:
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in text)


def ruby_reading(hints: dict, begin: int, surface: str, form: str, known) -> str | None:
    """The book's ruby as the reading of a word whose head token starts at `begin`: ruby over that
    token (one span or adjacent per-kanji spans, 人《ひと》気《け》), or over its kanji stem when the
    rest is kana (行《い》った: the ruby plus the lemma's okurigana, いく), in hiragana, and a
    reading listed for the form (`known`), as written or with
    large kana made small (いつしよ, see _small_kana). Flavour ruby (マジ over 本気, そら over
    宇宙) is never a reading."""
    token_end, end, reading = begin + len(surface), begin, ''
    while end < token_end and end in hints and hints[end][0] > end:
        end, part = hints[end]
        reading += part
    if end == begin or end > token_end or not _HIRAGANA_WORD.match(reading):
        return None
    tail = ''
    if end < token_end:
        base = surface[:end - begin]
        if not form.startswith(base) or any(is_kanji(c) for c in surface[end - begin:] + form[len(base):]):
            return None  # ruby over part of a compound (魚《うお》市場), or a lemma spelled differently
        tail = form[len(base):]
    for candidate in (reading, *_small_kana(reading)):
        if (form, candidate + tail) in known:
            return candidate + tail
    return None


_SMALL = str.maketrans('つやゆよ', 'っゃゅょ')
_YOUON_AFTER = set('きぎしじちぢにひびぴみり')


def _small_kana(reading: str):
    """Older books set ruby in large kana (いつしよ for いっしょ): `reading` with some of its つ
    (not first) and its や/ゆ/よ after an i-row kana made small. Small ぁぃぅぇぉ aren't tried:
    no hiragana reading of a kanji word uses them."""
    spots = [i for i, c in enumerate(reading)
             if i and (c == 'つ' or (c in 'やゆよ' and reading[i - 1] in _YOUON_AFTER))][:6]
    for k in range(1, len(spots) + 1):
        for chosen in itertools.combinations(spots, k):
            yield ''.join(c.translate(_SMALL) if i in chosen else c for i, c in enumerate(reading))


# Context rules (form: [(reading, text before, text after[, 'and'])]): a rule
# fires when its `before` pattern ends where the word starts or its `after` pattern starts where the
# word's head token ends (with 'and': both), within the line. Checked against readings-test.tsv.
# 人気がない is にんき as often as ひとけ in plain text (この店は人気がない), so が/は + ない needs a cue.
_HITOKE_PLACE = (r'(?:辺り|あたり|周囲|周り|付近|他|ほか|(?<![国海])[内外]|奥|(?<!海)道|通り|街|町|庭|園|室|館|駅|森|林|浜|港|廊下|広場|駐車場|墓場|(?<![長短])所'
                 r'|夜|深夜|しんと)(?:に|には|は|も|では|、)?$')
_CONTEXT_RULES = {
    '人気': [('にんき', None, r'の(?:な|無)(?:い|かった)(?:奴|やつ|者|人|キャラ|作品|商品|子(?!供|ども)|アイドル|作家|店)'),
             ('ひとけ', None, r'の(?:な[いくかけ]|無[いくかけ])|[がのはも]?(?:少な|絶え|途絶え)|も(?:な[いくかけ]|無)'),
             ('ひとけ', None, r'[がは](?:な|無)(?:い|く|かった)?(?:場所|所|ところ|道|通り|廊下|路地|部屋|時|とき'
              r'|のを確|ことを確|、?(?:静|しん|ひっそり))'),
             ('ひとけ', _HITOKE_PLACE, r'[がは](?:まったく|全く|ほとんど|全然|一切)?(?:な[いくかけ]|無[いくかけ])', 'and')],
    '他': [('た', r'その$', None)],
    '今日': [('こんにち', None, r'の(?:社会|日本|世界|経済|時代|状況|情勢|問題|課題|文明|科学|技術|教育|政治)'
              r'|に(?:至|いた)る|では|において')],
    # Sudachi says あす; books mostly say あした, except in formal phrases.
    '明日': [('あした', None, r'(?!の(?:日本|社会|世界|未来|地球|国)|を担|にも)')],
    '上手': [('かみて', r'舞台の?$', None), ('うわて', r'枚$', r'に出(?:る|た|て|ら|ま)')],
    '下手': [('しもて', r'舞台の?$', None), ('したて', None, r'に出(?:る|た|て|ら|ま)')],
    '市場': [('いちば', r'(?:魚|青物|朝|築地|近所の|朝早く)$', r'.{0,8}?(?:魚|野菜|果物|八百屋|買い物|買[っうい]|売り子)')],
    '生物': [('なまもの', None, r'を(?:食べ|食[うっ]|召し上が)|.{0,8}?(?:冷蔵|早めに|腐[らりるっ]|扱いに注意)')],
    '最中': [('もなか', r'(?:アイス|栗|餡)の$|(?:餡|あんこ).{0,8}入[っり].{0,2}$',
              r'を(?:食べ|頬張|かじ|買)|と(?:お茶|緑茶)')],
    '方々': [('ほうぼう', None, r'を?(?:探|捜|歩|回|駆け|走り|尋ね|旅)|から(?:集ま|聞こえ|寄せ)|に(?:散|手を)')],
    '目下': [('もっか', None, r'のところ|の(?:急務|課題|問題|状況|情勢|最大|懸案)|、|調査|検討|準備|交渉|捜査|審議|開発'
              r'|建設|進行|継続|捜索|修理|工事'),
             ('めした', None, r'の(?:者|人)')],
    # なん before だ/です/で/の/と/て and counters (何年, 何冊): Sudachi's; なに before か, する, verbs and ？.
    '何': [('なに', None, r'[をがもかし]|より|す|[？?！!、」]'
             r'|(?![年冊日番時匹台杯分周段箱点画便号名回人度月週歳個枚本階倍頭泊足軒件通語])[一-鿿]')],
    '色紙': [('しきし', r'(?:サイン|寄せ書きの?)$', r'に(?:サイン|寄せ書き|書)|を(?:飾|贈)'),
             ('いろがみ', r'折り?$', r'.{0,6}?(?:折[っらりる]|鶴|切り抜)')],
    '寒気': [('かんき', r'(?:強い|上空の|大陸からの|冬型の|北からの)$', r'団|が(?:南下|流れ込|入)|の(?:影響|流れ込|南下)'),
             ('さむけ', None, r'が(?:し|す|走|襲)|を(?:覚え|感じ)')],
    '心中': [('しんじゅう', r'(?:無理|一家|親子)$', r'を(?:図|遂げ|はか)|する|した|して|しよう|未遂|事件|物'),
             ('しんちゅう', None, r'を(?:察|お察|推し量|思|吐露|明か|語)|穏やか|は(?:穏やか|複雑)|お察し')],
    '大家': [('たいか', r'(?:画|学|界|道|楽|壇|芸)の$', r'として'), ('おおや', None, r'さん')],
    '分別': [('ふんべつ', r'(?:大人|年相応|思慮)(?:としての|の)$', r'が(?:な|つ|あ)|の(?:な|あ)|盛り|くさ|臭|を(?:わきまえ|失)')],
    '人事': [('ひとごと', None, r'(?:では|じゃ)な|とは思え|のよう|みたい|ながら')],
    '気質': [('かたぎ', r'(?:職人|昔|江戸っ子|学生|商人|芸人|役者|書生)$', None)],
    '末期': [('まつご', None, r'の(?:水|言葉|際|願い|一言|息)')],
    '床': [('とこ', r'病の$', r'に(?:就|つ|伏|臥)|の間|を(?:上げ|敷|延べ)')],
    '辛い': [('からい', r'(?:カレー|料理|スープ|ラーメン|味|唐辛子|わさび|キムチ|口)(?:は|が|も|の)?'
              r'(?:少し|とても|すごく|かなり|ちょっと)?$', r'(?:料理|カレー|ラーメン|味付け|ソース)')],
    '縁': [('ふち', r'(?:眼鏡|メガネ|めがね|カップ|グラス|コップ|池|崖|井戸|ベッド|茶碗|帽子|皿|鍋|器|机|窓)の$',
            r'に(?:腰|座|手を|立)|を(?:なぞ|指で)')],
    '一寸': [('いっすん', None, r'先|法師|の虫|刻み')],
    '金': [('きん', r'(?:純|銀と|十八)$', r'の(?:ネックレス|指輪|延べ棒|メダル|装飾|粉|糸|髪|仮面|冠|像|鎖|腕輪|首飾り|ボタン|刺繍)'
            r'|色|メダル|貨|銀|と銀|箔|髪|属'),
           ('かね', None, r'を(?:貸|借|払|稼|返|出|使|積|ため|貯|盗|渡|持)|が(?:な[いく]|無|足り|か[かけ]|要|い[るり]|あ[るれっ])'
            r'|に(?:困|な[るら])|で(?:買|解決|雇)|持ち|目当て|づる|遣い|儲け')],
    '見物': [('みもの', None, r'だ(?:な|ね|ぞ|わ)?(?:[。！」]|$)|である|です')],
    '一行': [('いちぎょう', r'(?:最初の|最後の|文章の|冒頭の|手紙の|ほんの|たった)$', r'目|ずつ|ごと|だけ|空け|の(?:文|文章|詩)')],
}
# Sudachi readings that are almost always wrong in plain modern text: (form, Sudachi's reading):
# the reading given instead, when no ruby, rule or model gives one. Chosen on Tatoeba's half a
# (fixes 10+ occurrences, right 90%+ of the times it changes one; see README).
DEFAULT_READINGS = {('私', 'わたくし'): 'わたし', ('言う', 'ゆう'): 'いう', ('富士山', 'ふじやま'): 'ふじさん',
                    ('鶏肉', 'けいにく'): 'とりにく', ('今日', 'こんにち'): 'きょう', ('明後日', 'みょうごにち'): 'あさって'}

_CONTEXT_RULES = {form: [(reading, before and re.compile(before), after and re.compile(after), bool(both))
                         for reading, before, after, *both in rules] for form, rules in _CONTEXT_RULES.items()}
_CONTEXT = 12  # characters looked at on each side


def context_reading(text: str, begin: int, surface: str, form: str, known) -> str | None:
    """The reading _CONTEXT_RULES give a word whose head token `surface` starts at `begin` in
    `text`, if `known` lists it for the form (as in ruby_reading)."""
    rules = _CONTEXT_RULES.get(form)
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
