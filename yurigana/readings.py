"""Readings of kanji words in context: the book's ruby (ruby_reading) and hand rules for
forms whose reading depends on the words around them (context_reading).

`known` is the set of (written form, hiragana reading) pairs a reading must be one of,
e.g. the keys of a Yomitan frequency list's readings (yurigana.yomitan.reading_ranks).
Anything with `__contains__` works.
"""
import itertools
import os
import re

from .counters import TEN_MINUTES_AFTER as _TEN_MINUTES_AFTER, TEN_MINUTES_BEFORE as _TEN_MINUTES_BEFORE
from .cues import (ABSTRACT, ACTIVITY, BODY, BUILDING, COUNTER, CUSTOMER_ACT, DISH, EDGE, FEW, FOOTWEAR, GROUNDS,
                   HALTED, HUGGED, INSECT, INSTRUMENT, IRU_STEM, ISSUE, JEWELRY, KIN_TITLE, METAL, NIGHT, OCCUPATION,
                   OPEN_HOURS, PEOPLE, PERSON, PRAISE, PRODUCE, REALM, ROLE, ROOM, SERVANT, SETTLEMENT, SOCIETY,
                   STREET, SUPERIOR, TERM, THINGS, TIME_SPAN, TRAFFIC, VESSEL, VICINITY, words)

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
_HITOKE_PLACE = ('(?:' + words(VICINITY - {'近所', 'そこら', 'そこいら'}, GROUNDS, NIGHT, STREET - {'路地'}, SETTLEMENT - {'村', '島'},
                               BUILDING - {'家', '屋敷', '城', 'ホテル', '学校', '会社'}, ROOM - {'部屋'}, '他', 'ほか', '奥', 'しんと')
                 + r'|(?<![国海])[内外]|(?<!海)道|(?<![長短])所)(?:に|には|は|も|では|、)?$')
# 君 is ぎみ after a family or rank word (尼君, 姫君, 母君); Sudachi reads it くん there.
_GIMI_BEFORE = words(KIN_TITLE)
# Nouns 今 (接頭辞) is こん before (今学期); before anything else it is いま (今医者だ, 今席を外して).
_KON_NEXT = words(TERM)
# People and things 外 is ほか before (外の人, 外の乗客): "the other ...".
_HOKA_OF = words(PEOPLE, THINGS)
# Verb stems before 入る read いる (眺め入る, 恐れ入る, 聞き入る); Sudachi says はいる.
_IRU_STEM = '(?:' + words(IRU_STEM) + r'|[一-鿿](?<!少)[きぎしちびみりめれけせえね])'
# Metals and the like near 金 make it the metal, きん (金は銀より重い); 銀行 is money.
_METAL = '(?:' + words(METAL) + r'|銀(?!行))'
_CONTEXT_RULES = {
    # 都: Tokyo's government (都の職員, 都が発表した), not the capital of a story (都 みやこ, HAND_DEFAULTS).
    '都': [('と', None, r'の?(?:職員|施設|予算|条例|担当|調査|方針|幹部|議会|知事|当局|教育委員会|福祉|保健|水道|交通局|税|事業|補助|管理|所有)'
            r'|が(?:発表|公表|決め|要請|実施|定め|設置|管理)')],
    '人気': [('にんき', None, r'の(?:な|無)(?:い|かった)(?:奴|やつ|者|人|キャラ|作品|商品|子(?!供|ども)|アイドル|作家|店)'),
             ('ひとけ', None, r'の(?:な[いくかけ]|無[いくかけ])|[がのはも]?(?:少な|絶え|途絶え)|も(?:な[いくかけ]|無)'),
             ('ひとけ', None, r'[がは](?:な|無)(?:い|く|かった)?(?:' + words(STREET, ROOM - {'室'}, '場所', '所', 'ところ', '道', '時', 'とき')
              + r'|のを確|ことを確|、?(?:静|しん|ひっそり))'),
             ('ひとけ', _HITOKE_PLACE, r'[がは](?:まったく|全く|ほとんど|全然|一切)?(?:な[いくかけ]|無[いくかけ])', 'and')],
    # 他 is ほか in plain text (DEFAULT_READINGS); た in その他, set phrases and as a prefix (他言語).
    '他': [('た', r'その$', r'の(?:追随|追従|干渉|介入|模範)|を(?:圧倒|寄せ付け|凌|しの)|に(?:類|例|比類)を(?:見|み)|[一-鿿]')],
    # 種 is たね (DEFAULT_READINGS) except as "kind": この種の, 数種, 百種.
    '種': [('しゅ', r'(?:この|その|あの|どの|ある|各|同|異|別|[数何一二三四五六七八九十百千0-9０-９])$', None)],
    # 下: もと under an abstract noun (指導の下に); した in "Xの下で" (Sudachi's もと there is nearly always wrong).
    '下': [('もと', words(ABSTRACT, SUPERIOR) + 'の$', None),
          ('した', r'の$', r'で', 'and')],
    # 音: ね for instruments and insects (琴の音, 虫の音) and ぐうの音; Sudachi's おと otherwise.
    '音': [('ね', '(?:' + words(INSTRUMENT, INSECT, 'ぐう', 'グウ') + r'|(?<![霧汽警])笛)の$', None)],
    # 風: ふう for manner (こんな風に, 知らない風で), かぜ for the wind.
    '風': [('かぜ', None, r'の吹き回し'),
           ('ふう', r'(?:[こそあど]んな|(?:[こそど]う|ああ)(?:いう|いった|言う|云う|言った|云った)'
              r'|と(?:いう|いった|言う|云う|言った|云った)|ような|ふうな)$', None),
           ('ふう', r'ない$', r'[にでをも]', 'and'),
           ('かぜ', None, r'に(?:そよ|揺|ゆれ|なび|吹|舞|乱|あお|煽|任|散|飛|はため|翻|ひるがえ|鳴|運ば|乗)'
              r'|が(?:吹|強|弱|やみ|止|冷|涼|出|そよ)|を(?:受け|切|感じ|起こ)|の(?:音|便り)')],
    # 中 after a stretch of time or a place, "all through" (一日中, 世界中): じゅう; Sudachi says ちゅう,
    # right after activities (授業中), 午前, 今週/今月 (こんしゅうちゅう) and 数日 (within days).
    # 十分: Sudachi's じゅうぶん where it keeps one token; minutes with a cue (counters.TEN_MINUTES_*).
    '十分': [('じゅっぷん', _TEN_MINUTES_BEFORE, _TEN_MINUTES_AFTER)],
    '中': [('じゅう', '(?:' + words(TIME_SPAN, REALM, SETTLEMENT, BUILDING - {'館', '駅'}, BODY,
                                   VICINITY - {'周囲', '周り', '付近'}, ROOM - {'室', '廊下'}, 'クラス')
             + r'|(?<![十両数])[一１1]日|(?<![今来])年)$', None)],
    # 方: かた for a person (あの方, 素敵な方です, 学生の方は, 方がいらっしゃる); ほう in comparisons (やる方がいい).
    # Sudachi's reading otherwise: ほう after の or a verb (北の方, 来た方), かた after a stem (話し方).
    '方': [('かた', r'あの$', r'(?!が(?:いい|良|よ|まし|好|楽|早|上|得|便利|大き|小さ|多|少))', 'and'),
           ('かた', words(PRAISE) + r'な?$',
            r'(?:です|でし|だ|なの|なん|で、|でいらっしゃ)', 'and'),
           ('かた', r'どんな$', r'(?:です|でし|だ|なの|なん)', 'and'),
           ('かた', '(?:' + words(PERSON, ROLE)
            + r'|[おご]' + words(CUSTOMER_ACT) + r')の$', r'(?![がへに])', 'and'),
           ('かた', r'[ァ-ヺー]{2,}の$', r'(?:です|でし|だっ)', 'and'),  # ドイツの方ですか
           ('かた', None, r'[がはをにも]?(?:いらっしゃ|お越し|おいで|お見え|ご存[知じ]|亡くなられ)'),
           ('ほう', None, r'が(?:いい|良|よ[いかくけろ]|まし|無難|得策|安全|楽|早)')],
    # 間: ま in いつの間に, 束の間, 一瞬の間; あいだ in この間 (the other day; Sudachi says かん).
    # 間 ま also for a pause (間が空く, 間を置いて, する間もなく), not after の (その間も, AとBの間が空く: あいだ).
    '間': [('ま', r'(?:いつ|何時|束|一瞬|咄嗟|瞬く|またたく|あっという|あっと言う|アッという|呼吸|呼吸分|一拍|謁見|玉座)の?$', None),
           ('あいだ', r'この$', None),
           ('ま', r'(?<!の)$', r'が(?:空|あ[いくきけ]|開|でき|持た|悪|抜け)|も(?:な[くい]|無[くい]|与え|あた|惜し)'
            r'|を(?:置|お[いかきく])', 'and')],
    # 後 before a number is あと (後五分で); Sudachi says ご. Not after その/この or a kanji (その後, 五年後, 購入後２日).
    # この後, あの後: あと (Sudachi: ご); その後 keeps そのご (both standard).
    '後': [('あと', r'(?<!その)(?<!この)(?<![一-鿿々0-9０-９])$', r'[0-9０-９一二三四五六七八九十百千数幾]', 'and'),
           ('あと', r'(?:この|あの)$', None)],
    # 表 おもて: the outside or the front (表に出る, 表に出さない, コインの表, 表の顔); ひょう (a table) otherwise.
    '表': [('おもて', r'(?:裏[とものか]|コインの|硬貨の)$',
            r'に(?:は|も)?(?:出|で[たてるな]|立|現)|へ(?:出|と)|を出歩|で(?:遊|待|絡)|[とか]裏|が(?:出|ない)|だって|立って|沙汰|向き'
            r'|の(?:顔|世界|社会|舞台|仕事|理由|看板|門|通り|玄関)')],
    # 主: あるじ for the master of a house or of servants (館の主, 我が主, 奴隷と主); しゅ in 主として (mainly);
    # Sudachi's ぬし otherwise (声の主, 森の主).
    '主': [('しゅ', r'(?<!の)$', r'として', 'and'),
           ('あるじ', '(?:' + words(BUILDING - {'学校', '会社', '駅', 'ホテル'}, ROOM - {'室', '廊下'}, SERVANT,
                                    '邸', '邸宅', '道場', '店', '宿', '一家') + '[のと]|我が|わが|最愛の)$', None)],
    # 抱く だく: holding someone or something in the arms (赤ん坊を抱く, 腕に抱く, 抱かれる, 抱きたい);
    # Sudachi's いだく for feelings (疑問を抱く, 不満を抱かれる).
    '抱く': [('だく', r'(?:(?<![一-鿿])' + words(HUGGED, PEOPLE, BODY) + r'を|腕に|腕の中に)$', None),
            ('だく', r'(?<!を)$', r'れ|た[いくかけ]', 'and')],
    # 家 け after a katakana name (ローズ家, フジバヤシ家); Sudachi says か.
    '家': [('け', r'[ァ-ヺー・]{2,}$', None)],
    # 側 そば: beside (すぐ側, 彼の側にいる, 駅の側で); がわ (a side) otherwise (向こう側, 民の側につく).
    '側': [('そば', r'すぐ$', None),
           ('そば', r'[のがはも]$', r'に(?:いる|い[てたらまれよ]|居|あ[るっ]|置|寄|座|控|仕え|付き添|はべ|侍|来|行)|で(?!は)|まで', 'and')],
    # 傍 alone (not 傍ら) is そば before a particle: 彼の傍にいる, 窓の傍で; Sudachi says かたわら.
    '傍': [('そば', None, r'(?:に|で|まで|から|へ|を)')],
    # 留まる とどまる after に (その場に留まる, だけに留まる), but 目に留まる, 枝に留まる: とまる.
    '留まる': [('とどまる', r'(?<![目眼耳枝肩木々線])に$', None)],
    '今日': [('こんにち', None, 'の' + words(REALM - {'国'}, SOCIETY - {'未来', '地球'}, ISSUE - {'急務', '懸案'})
              + r'|に(?:至|いた)る|では|において')],
    # Sudachi says あす; books mostly say あした, except in formal phrases.
    '明日': [('あした', None, r'(?!の' + words(REALM, SOCIETY - {'経済', '時代', '文明', '科学', '技術', '教育', '政治'}) + '|を担|にも)')],
    '上手': [('かみて', r'舞台の?$', None), ('うわて', r'枚$', r'に出(?:る|た|て|ら|ま)')],
    # 下手 しもて: the stage's or a river's lower side; へた takes no へ (下手へ退く).
    '下手': [('しもて', r'(?:舞台|川|河)の?(?:ずっと|少し|やや|すぐ)?$', r'へ|から(?:登場|出|入|現)|向き|寄り'),
             ('したて', None, r'に出(?:る|た|て|ら|ま|れ)')],
    # 一足 いっそく: a pair of footwear; ひとあし (a step) otherwise.
    '一足': [('いっそく', words(FOOTWEAR) + '[をがはも]?$', 'の' + words(FOOTWEAR))],
    '市場': [('いちば', words(PRODUCE - {'野菜', '果物'}, '朝', '築地', '近所の', '朝早く') + '$',
             r'.{0,8}?(?:' + words(PRODUCE - {'青物'}, '八百屋', '買い物', '売り子') + r'|買[っうい])')],
    '生物': [('なまもの', None, r'を(?:食べ|食[うっ]|召し上が)|.{0,8}?(?:冷蔵|早めに|腐[らりるっ]|扱いに注意)')],
    '最中': [('もなか', r'(?:アイス|栗|餡)の$|(?:餡|あんこ).{0,8}入[っり].{0,2}$',
              r'を(?:食べ|頬張|かじ|買)|と(?:お茶|緑茶)')],
    '方々': [('ほうぼう', None, r'を?(?:探|捜|歩|回|駆け|走り|尋ね|旅)|から(?:集ま|聞こえ|寄せ)|に(?:散|手を)')],
    '目下': [('もっか', None, r'のところ|の' + words(ISSUE, '最大') + '|、|' + words(ACTIVITY)),
             ('めした', None, r'の(?:者|人)')],
    # なん before だ/です/で/の/と/て and counters (何年, 何冊): Sudachi's; なに before か, する, verbs and ？.
    '何': [('なに', None, r'[をがもかし]|より|す|[？?！!、」]'
             r'|や(?:ら|かや|[っりるれろ])|に(?:使|つい|つけ|する|し[たよま])|ごっこ|げな'
             r'|(?!' + words(COUNTER) + r')[一-鿿]')],
    '色紙': [('しきし', r'(?:サイン|寄せ書きの?)$', r'に(?:サイン|寄せ書き|書)|を(?:飾|贈)'),
             ('いろがみ', r'折り?$', r'.{0,6}?(?:折[っらりる]|鶴|切り抜)')],
    '寒気': [('かんき', r'(?:強い|上空の|大陸からの|冬型の|北からの)$', r'団|が(?:南下|流れ込|入)|の(?:影響|流れ込|南下)'),
             ('さむけ', None, r'が(?:し|す|走|襲)|を(?:覚え|感じ)')],
    '心中': [('しんじゅう', r'(?:無理|一家|親子)$', r'を(?:図|遂げ|はか)|する|した|して|しよう|未遂|事件|物'),
             ('しんちゅう', None, r'を(?:察|お察|推し量|思|吐露|明か|語)|穏やか|は(?:穏やか|複雑)|お察し')],
    '大家': [('たいか', r'(?:画|学|界|道|楽|壇|芸)の$', r'として'), ('おおや', None, r'さん')],
    '分別': [('ふんべつ', r'(?:大人|年相応|思慮)(?:としての|の)$', r'が(?:な|つ|あ)|の(?:な|あ)|盛り|くさ|臭|を(?:わきまえ|失)')],
    '人事': [('ひとごと', None, r'(?:では|じゃ)な|とは思え|のよう|みたい|ながら')],
    '気質': [('かたぎ', words(OCCUPATION, '昔', '江戸っ子') + '$', None)],
    '末期': [('まつご', None, r'の(?:水|言葉|際|願い|一言|息)')],
    '床': [('とこ', r'(?:病の|お)$', r'に(?:就|つ|伏|臥|入|はい)|から(?:起|出|離)|の(?:間|中)|を(?:上げ|敷|延べ|離|とっ|取)')],
    '辛い': [('からい', words(DISH - {'味付け', 'ソース'}, '口') + r'(?:は|が|も|の)?'
              r'(?:少し|とても|すごく|かなり|ちょっと)?$', words(DISH - {'スープ', '唐辛子', 'わさび', 'キムチ', '味'}))],
    '縁': [('ふち', words(VESSEL, '眼鏡', 'メガネ', 'めがね', '池', '崖', '井戸', 'ベッド', '帽子', '机', '窓') + 'の$',
            r'に(?:腰|座|手を|立)|を(?:なぞ|指で)')],
    '一寸': [('いっすん', None, r'先|法師|の虫|刻み')],
    '金': [('きん', r'(?:純|銀と|十八)$', 'の' + words(JEWELRY, '延べ棒', '装飾', '粉', '糸', '髪', '仮面', '像', '鎖', 'ボタン', '刺繍')
            + r'|色|メダル|貨|銀|と銀|箔|髪|属|の?(?:くさり|モール)|のよう|の(?:値段|価格|相場)|を(?:塗|ぬ|着せ|きせ|かぶせ|掘|採)'
            r'|に(?:等し|輝)|より(?:重|軽|高)|.{0,8}?' + _METAL),
           ('きん', _METAL + r'.{0,8}$', None),
           ('かね', None, r'を(?:貸|借|払|稼|返|出|使|積|ため|貯|盗|渡|持)|が(?:な[いく]|無|足り|か[かけ]|要|い[るり]|あ[るれっ])'
            r'|に(?:困|な[るら])|で(?:買|解決|雇)|持ち|目当て|づる|遣い|儲け')],
    '見物': [('みもの', None, r'だ(?:な|ね|ぞ|わ)?(?:[。！」]|$)|である|です')],
    # 気に入る, 水入らず, a verb stem + 入る (眺め入る), 郷に入っては: いる; Sudachi says はいる.
    '入る': [('いる', r'気に$', None), ('いる', r'水$', r'ず', 'and'), ('いる', _IRU_STEM + '$', None)],
    '君': [('ぎみ', _GIMI_BEFORE + '$', None)],
    '尼': [('あま', None, r'君|寺|僧|さん|御前|姿|に(?:な|し)')],
    '今': [('いま', None, r'(?!' + _KON_NEXT + ')')],
    # 外 ほか: "other" (外の人) and "nothing but" (待つ外ない); Sudachi's そと otherwise.
    '外': [('ほか', r'(?:より|その)$', None), ('ほか', None, r'の' + _HOKA_OF + r'(?![間界])|なら[なぬずん]'),
           ('ほか', r'[うくぐすつぶむるたぬ]$', r'[はにも]?(?:な[いくかし]|無|あり|ある|ござ|仕方|手|道)', 'and')],
    # 人 right after a katakana word (カナダ人); after a place name, see context_reading.
    '人': [('じん', r'[ァ-ヺー]$', None)],
    # 一日 as one token is Sudachi's ついたち (DEFAULT_READINGS: いちにち), the first of a month after 月 (来月の一日).
    '一日': [('ついたち', r'月の?$', None)],
    # These four also keep their model where no rule fires (the table's ruleForms).
    # 開く: ひらく after を (会を開く, 手紙を開いた); あく for opening hours (店は開いてますか) and lids.
    '開く': [('ひらく', r'を$', None),
            ('あく', words(OPEN_HOURS, '日', '曜日', 'まで') + r'[はがも]?$', None),
            ('あく', None, r'て(?:ますか|ます？|る？|ますよ)'),
            ('あく', r'(?:蓋|ふた|フタ)[がはも]?$', r'(?!れ)', 'and')],
    # 止める: とめる for machines and flows (エンジンを止める); やめる for doing something (食べるのを止める, お止めください).
    '止める': [('とめる', words(HALTED) + 'を$', None),
             ('やめる', r'(?<!へ)(?:の|こと)を?$', r'(?!られ)', 'and'),
             ('やめる', r'お$', r'(?:ください|下さい|になって|なさい)', 'and')],
    # 空く: すく for roads and trains (道が空いている); お腹が空く is left to the model (it reads it already).
    '空く': [('すく', '(?:' + words(STREET, TRAFFIC) + r'|(?<!海)道)[がはも]?$', None)],
    # 額: がく for a frame (額に入れて飾る); ひたい for the forehead (額に汗, 額を拭う).
    '額': [('がく', None, r'に.{0,10}?(?:収め|納め|入れ|飾[っらりるれ])|縁|ぶち'),
           ('ひたい', None, r'[がは](?:熱|汗|広|狭)|に(?:汗|手|皺|しわ|傷|当て|かか|垂)|から汗|の(?:汗|傷|皺|しわ)'
            r'|を(?:拭|ぬぐ|押さえ|寄せ|集め)')],
    '一行': [('いちぎょう', words(EDGE, FEW - {'わずか', '僅か', 'ものの'}, '文章の', '冒頭の', '手紙の') + '$', r'目|ずつ|ごと|だけ|空け|の(?:文|文章|詩)')],
}
# Sudachi readings that are almost always wrong in plain modern text: (form, Sudachi's reading):
# the reading given instead, when no ruby, rule or model gives one. Chosen on Tatoeba's half a
# (fixes 10+ occurrences, right 90%+ of the times it changes one; see docs/how-it-works.md). 他, 種 and 白髪
# were added later on the same half: 24/27, 8/9 and 4/4 of their changes right. 日本 にっぽん → にほん
# misses that bar on Tatoeba (its MeCab gold says にっぽん 18% of the time) but books' own ruby
# almost never does (under 2% on NDL's held-out authors: +46/-1 there, +8/-3 on Tatoeba's half a).
HAND_DEFAULTS = {('私', 'わたくし'): 'わたし', ('言う', 'ゆう'): 'いう', ('富士山', 'ふじやま'): 'ふじさん',
                 ('鶏肉', 'けいにく'): 'とりにく', ('今日', 'こんにち'): 'きょう', ('明後日', 'みょうごにち'): 'あさって',
                 ('他', 'た'): 'ほか', ('種', 'しゅ'): 'たね', ('白髪', 'はくはつ'): 'しらが',
                 ('日本', 'にっぽん'): 'にほん',
                 # Fiction's 都 みやこ and 露 つゆ (Sudachi: と, ろ); 都 as Tokyo's government is a context rule,
                 # and 露 next to a kanji (露大統領, Russia) keeps ろ (GLUED_CHECKED).
                 ('都', 'と'): 'みやこ', ('露', 'ろ'): 'つゆ', ('朝露', 'ちょうろ'): 'あさつゆ',
                 # Rendaku of ち is spelled ぢ (現代仮名遣い); Sudachi writes じ.
                 ('鼻血', 'はなじ'): 'はなぢ', ('間近', 'まじか'): 'まぢか', ('手近', 'てじか'): 'てぢか',
                 ('近々', 'ちかじか'): 'ちかぢか',
                 # Batch 2: (fixed - broken) >= 2 and 90%+ right on Tatoeba (half a + B1), not losing on
                 # NDL's held-out authors. 或いは is the one exception: Tatoeba never leaves it to Sudachi,
                 # and あるいわ only misspells あるいは (NDL +11/-0).
                 ('箱', 'ばこ'): 'はこ', ('米', 'べい'): 'こめ', ('深い', 'ぶかい'): 'ふかい',
                 ('腹', 'ふく'): 'はら', ('沿い', 'そい'): 'ぞい', ('大文字', 'だいもんじ'): 'おおもじ',
                 ('船便', 'せんびん'): 'ふなびん', ('仏', 'ふつ'): 'ほとけ', ('隙', 'ひま'): 'すき',
                 ('鏡', 'きょう'): 'かがみ', ('時々', 'じじ'): 'ときどき', ('喘息', 'ずだ'): 'ぜんそく',
                 ('不味い', 'まじい'): 'まずい', ('銀杏', 'ぎんなん'): 'いちょう',
                 ('塵', 'ごみ'): 'ちり', ('啄木鳥', 'けら'): 'きつつき',
                 ('生魚', 'せいぎょ'): 'なまざかな', ('入用', 'にゅうよう'): 'いりよう', ('薪', 'たきぎ'): 'まき',
                 ('手品師', 'でじなし'): 'てじなし', ('或は', 'あるいわ'): 'あるいは', ('或いは', 'あるいわ'): 'あるいは',
                 ('氷柱', 'ひょうちゅう'): 'つらら', ('正気', 'せいき'): 'しょうき', ('昼飯', 'ちゅうはん'): 'ひるめし',
                 ('卵', 'らん'): 'たまご', ('胡坐', 'こざ'): 'あぐら', ('緒', 'いとぐち'): 'お',
                 ('雪道', 'せつどう'): 'ゆきみち', ('卑怯者', 'ひきょうしゃ'): 'ひきょうもの',
                 ('無理強い', 'むりつよい'): 'むりじい', ('人手不足', 'ひとでふそく'): 'ひとでぶそく',
                 ('草冠', 'そうこう'): 'くさかんむり', ('大火事', 'だいかじ'): 'おおかじ',
                 # 一X read ひと…/いち… (#24). 一日 as one token: Sudachi's ついたち (月一日: a rule).
                 # 一昨日, 一日中: Sudachi splits them 一昨|日 (いっさく|ひ, |にち), 一|日中, joined in Reader._compound.
                 ('一日', 'ついたち'): 'いちにち', ('一昨日', 'いっさくひ'): 'おととい', ('一昨日', 'いっさくにち'): 'おととい',
                 ('一日中', 'いちにっちゅう'): 'いちにちじゅう',  # 一|日中 (Sudachi), not 一|日|中
                 ('一塊', 'いっかい'): 'ひとかたまり',
                 # 金 alone is money (かね) unless a rule finds the metal (TRADEOFFS T30).
                 ('金', 'きん'): 'かね',
                 # Sudachi dictionary bugs: a particle or extra kana in the reading (中宮 ちゅうぐうの).
                 ('中宮', 'ちゅうぐうの'): 'ちゅうぐう', ('河原', 'かわらの'): 'かわら', ('甲斐', 'かいの'): 'かい',
                 ('土堤', 'どてい'): 'どて',
                 # 鬼 alone is おに; glued (善鬼 ぜんき, 餓鬼) it keeps Sudachi's き (GLUED_CHECKED).
                 ('鬼', 'き'): 'おに',
                 # Nominated by Opus's readings of post-war library sentences (Sudachi's reading where Opus
                 # gives another one, 3+ authors, 80%+ one reading), checked on Tatoeba B1 (TRADEOFFS T45).
                 ('擦る', 'する'): 'こする', ('素', 'もと'): 'す'}


def _table_defaults(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default-readings.tsv')) -> dict:
    """default-readings.tsv: the readings human ruby gives instead of Sudachi's, mined from NDL's
    Aozora corpus and checked on Tatoeba by tools/default_readings.py (身体 しんたい → からだ), for
    words not glued to others (see glued)."""
    with open(path, encoding='utf-8') as f:
        rows = [line.rstrip('\n').split('\t') for line in f if not line.startswith('#')]
    return {(form, sudachi): reading for form, sudachi, reading, *_ in rows}


DEFAULT_READINGS = {**_table_defaults(), **HAND_DEFAULTS}


# Hand defaults that, like the table's, hold only for the word on its own (露大統領 stays ろ).
GLUED_CHECKED = frozenset({('都', 'と'), ('露', 'ろ'), ('鬼', 'き')})


def glued(text: str, begin: int, end: int) -> bool:
    """Whether a one-character word text[begin:end] is an affix Sudachi split off: a kanji or digit
    right before or after it, or a katakana word before it (郵便局側, 今学期, 3位, ダウンロード時),
    where default-readings.tsv's readings (側 そば, 今 いま, 位 くらい, 時 とき) don't hold."""
    before, after = text[max(begin - 1, 0):begin], text[end:end + 1]
    return end - begin == 1 and (any(is_kanji(c) or c.isdigit() for c in before + after) or bool(re.match('[ァ-ヺー]', before)))


_CONTEXT_RULES = {form: [(reading, before and re.compile(before), after and re.compile(after), bool(both))
                         for reading, before, after, *both in rules] for form, rules in _CONTEXT_RULES.items()}
_CONTEXT = 12  # characters looked at on each side


def context_reading(text: str, begin: int, surface: str, form: str, known, previous_pos=None) -> str | None:
    """The reading _CONTEXT_RULES give a word whose head token `surface` starts at `begin` in
    `text`, if `known` lists it for the form (as in ruby_reading). previous_pos: the part of
    speech of the token ending where the word starts, if any (人 after a place name is じん)."""
    if form == '人' and previous_pos and tuple(previous_pos[1:3]) == ('固有名詞', '地名') and (form, 'じん') in known:
        return 'じん'
    # 気味 is ぎみ as a suffix: right after a noun (風邪気味) or a verb's 連用形 (太り気味); Sudachi says きみ.
    if form == '気味' and previous_pos and (form, 'ぎみ') in known and (
            previous_pos[0] in ('名詞', '接尾辞') and previous_pos[2] != '副詞可能'
            or previous_pos[0] == '動詞' and ''.join(previous_pos[5:6]).startswith('連用形')):
        return 'ぎみ'
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
