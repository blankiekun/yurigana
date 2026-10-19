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
    # 他 is ほか in plain text (DEFAULT_READINGS); た in その他, set phrases and as a prefix (他言語).
    '他': [('た', r'その$', r'の(?:追随|追従|干渉|介入|模範)|を(?:圧倒|寄せ付け|凌|しの)|に(?:類|例|比類)を(?:見|み)|[一-鿿]')],
    # 種 is たね (DEFAULT_READINGS) except as "kind": この種の, 数種, 百種.
    '種': [('しゅ', r'(?:この|その|あの|どの|ある|各|同|異|別|[数何一二三四五六七八九十百千0-9０-９])$', None)],
    # 下: もと under an abstract noun (指導の下に); した in "Xの下で" (Sudachi's もと there is nearly always wrong).
    '下': [('もと', r'(?:指導|監督|支配|管理|統治|指揮|命令|条件|体制|制度|方針|影響|庇護|保護|名|法|旗|約束|前提|協力|仮定'
              r'|環境|状況|状態|気候|先生|師|師匠|上司|親|両親|父母|主君)の$', None),
          ('した', r'の$', r'で', 'and')],
    # 音: ね for instruments and insects (琴の音, 虫の音) and ぐうの音; Sudachi's おと otherwise.
    '音': [('ね', r'(?:琴|箏|筝|(?<![霧汽警])笛|虫|琵琶|三味線|尺八|胡弓|弦|絃|ぐう|グウ)の$', None)],
    # 風: ふう for manner (こんな風に, 知らない風で), かぜ for the wind.
    '風': [('かぜ', None, r'の吹き回し'),
           ('ふう', r'(?:[こそあど]んな|(?:[こそど]う|ああ)(?:いう|いった|言う|云う|言った|云った)'
              r'|と(?:いう|いった|言う|云う|言った|云った)|ような|ふうな)$', None),
           ('ふう', r'ない$', r'[にでをも]', 'and'),
           ('かぜ', None, r'に(?:そよ|揺|ゆれ|なび|吹|舞|乱|あお|煽|任|散|飛|はため|翻|ひるがえ|鳴|運ば|乗)'
              r'|が(?:吹|強|弱|やみ|止|冷|涼|出|そよ)|を(?:受け|切|感じ|起こ)|の(?:音|便り)')],
    # 中 after a stretch of time or a place, "all through" (一日中, 世界中): じゅう; Sudachi says ちゅう,
    # right after activities (授業中), 午前, 今週/今月 (こんしゅうちゅう) and 数日 (within days).
    '中': [('じゅう', r'(?:(?<![十両数])[一１1]日|今日|明日|一晩|一夜|今夜|一年|今年|(?<![今来])年|[春夏秋冬]|一生'
             r'|世界|日本|国|町|街|村|家|部屋|学校|会社|体|身体|からだ|そこら|そこいら|辺り|あたり|近所|ホテル|クラス|島|屋敷|城)$', None)],
    # 方: かた for a person (あの方, 素敵な方です, 学生の方は, 方がいらっしゃる); ほう in comparisons (やる方がいい).
    # Sudachi's reading otherwise: ほう after の or a verb (北の方, 来た方), かた after a stem (話し方).
    '方': [('かた', r'あの$', r'(?!が(?:いい|良|よ|まし|好|楽|早|上|得|便利|大き|小さ|多|少))', 'and'),
           ('かた', r'(?:素敵|すてき|立派|りっぱ|有名|親切|優秀|上品|気さく|偉い|えらい|素晴らしい|すばらしい|優しい|やさしい)な?$',
            r'(?:です|でし|だ|なの|なん|で、|でいらっしゃ)', 'and'),
           ('かた', r'どんな$', r'(?:です|でし|だ|なの|なん)', 'and'),
           ('かた', r'(?:担当|係り?|窓口|受付|学生|女性|男性|年配|年寄り|高齢|専門|通訳|教徒|出身|経験|初心|家族|患者|客'
            r'|[おご](?:希望|利用|来場|越し|持ち|住まい|参加|申し込み|申込み))の$', r'(?![がへに])', 'and'),
           ('かた', r'[ァ-ヺー]{2,}の$', r'(?:です|でし|だっ)', 'and'),  # ドイツの方ですか
           ('かた', None, r'[がはをにも]?(?:いらっしゃ|お越し|おいで|お見え|ご存[知じ]|亡くなられ)'),
           ('ほう', None, r'が(?:いい|良|よ[いかくけろ]|まし|無難|得策|安全|楽|早)')],
    # 間: ま in いつの間に, 束の間, 一瞬の間; あいだ in この間 (the other day; Sudachi says かん).
    '間': [('ま', r'(?:いつ|何時|束|一瞬|咄嗟|瞬く|またたく|あっという|あっと言う|アッという)の?$', None),
           ('あいだ', r'この$', None)],
    # 後 before a number is あと (後五分で); Sudachi says ご. Not after その/この or a kanji (その後, 五年後, 購入後２日).
    '後': [('あと', r'(?<!その)(?<!この)(?<![一-鿿々0-9０-９])$', r'[0-9０-９一二三四五六七八九十百千数幾]', 'and')],
    '今日': [('こんにち', None, r'の(?:社会|日本|世界|経済|時代|状況|情勢|問題|課題|文明|科学|技術|教育|政治)'
              r'|に(?:至|いた)る|では|において')],
    # Sudachi says あす; books mostly say あした, except in formal phrases.
    '明日': [('あした', None, r'(?!の(?:日本|社会|世界|未来|地球|国)|を担|にも)')],
    '上手': [('かみて', r'舞台の?$', None), ('うわて', r'枚$', r'に出(?:る|た|て|ら|ま)')],
    # 下手 しもて: the stage's or a river's lower side; へた takes no へ (下手へ退く).
    '下手': [('しもて', r'(?:舞台|川|河)の?(?:ずっと|少し|やや|すぐ)?$', r'へ|から(?:登場|出|入|現)|向き|寄り'),
             ('したて', None, r'に出(?:る|た|て|ら|ま|れ)')],
    # 一足 いっそく: a pair of footwear; ひとあし (a step) otherwise.
    '一足': [('いっそく', r'(?:靴|くつ|クツ|靴下|草鞋|わらじ|下駄|足袋|スニーカー|ブーツ|サンダル|スリッパ|草履)[をがはも]?$',
              r'の(?:靴|くつ|クツ|靴下|草鞋|わらじ|下駄|足袋|スニーカー|ブーツ|サンダル|スリッパ|草履)')],
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
             r'|(?![年冊日番時匹台杯分周段箱点画便号名回人度月週歳個枚本階倍頭泊足軒件通語十百千万億兆曜秒])[一-鿿]')],
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
    # 気に入る, 水入らず: いる; Sudachi says はいる.
    '入る': [('いる', r'気に$', None), ('いる', r'水$', r'ず', 'and')],
    # 人 right after a katakana word (カナダ人); after a place name, see context_reading.
    '人': [('じん', r'[ァ-ヺー]$', None)],
    '一行': [('いちぎょう', r'(?:最初の|最後の|文章の|冒頭の|手紙の|ほんの|たった)$', r'目|ずつ|ごと|だけ|空け|の(?:文|文章|詩)')],
}
# Sudachi readings that are almost always wrong in plain modern text: (form, Sudachi's reading):
# the reading given instead, when no ruby, rule or model gives one. Chosen on Tatoeba's half a
# (fixes 10+ occurrences, right 90%+ of the times it changes one; see README). 他, 種 and 白髪
# were added later on the same half: 24/27, 8/9 and 4/4 of their changes right. 日本 にっぽん → にほん
# misses that bar on Tatoeba (its MeCab gold says にっぽん 18% of the time) but books' own ruby
# almost never does (under 2% on NDL's held-out authors: +46/-1 there, +8/-3 on Tatoeba's half a).
DEFAULT_READINGS = {('私', 'わたくし'): 'わたし', ('言う', 'ゆう'): 'いう', ('富士山', 'ふじやま'): 'ふじさん',
                    ('鶏肉', 'けいにく'): 'とりにく', ('今日', 'こんにち'): 'きょう', ('明後日', 'みょうごにち'): 'あさって',
                    ('他', 'た'): 'ほか', ('種', 'しゅ'): 'たね', ('白髪', 'はくはつ'): 'しらが',
                    ('日本', 'にっぽん'): 'にほん',
                    # Rendaku of ち is spelled ぢ (現代仮名遣い); Sudachi writes じ.
                    ('鼻血', 'はなじ'): 'はなぢ', ('間近', 'まじか'): 'まぢか', ('手近', 'てじか'): 'てぢか',
                    ('近々', 'ちかじか'): 'ちかぢか'}

_CONTEXT_RULES = {form: [(reading, before and re.compile(before), after and re.compile(after), bool(both))
                         for reading, before, after, *both in rules] for form, rules in _CONTEXT_RULES.items()}
_CONTEXT = 12  # characters looked at on each side


def context_reading(text: str, begin: int, surface: str, form: str, known, previous_pos=None) -> str | None:
    """The reading _CONTEXT_RULES give a word whose head token `surface` starts at `begin` in
    `text`, if `known` lists it for the form (as in ruby_reading). previous_pos: the part of
    speech of the token ending where the word starts, if any (人 after a place name is じん)."""
    if form == '人' and previous_pos and tuple(previous_pos[1:3]) == ('固有名詞', '地名') and (form, 'じん') in known:
        return 'じん'
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
