"""The per-word reading tables: context rules (CONTEXT_RULES), defaults that replace Sudachi's reading
(HAND_DEFAULTS, default-readings.tsv), which of them are shown, model fixes, token splits and joins.
readings.py and reader.py apply them; TRADEOFFS.md records what each one costs."""
import os
import re

from .counters import TEN_MINUTES_AFTER as _TEN_MINUTES_AFTER, TEN_MINUTES_BEFORE as _TEN_MINUTES_BEFORE
from .cues import (ABSTRACT, ACTIVITY, BODY, BUILDING, COUNTER, CUSTOMER_ACT, DISH, SPICE, DRAWN, EDGE, FEW, FOOTWEAR, GROUNDS,
                   HALTED, HUGGED, INSECT, INSTRUMENT, IRU_STEM, ISSUE, JEWELRY, KIN_TITLE, METAL, NIGHT, OCCUPATION,
                   OPEN_HOURS, PEOPLE, PERSON, PLAYED, PLURAL_PERSON, PRAISE, PRODUCE, REALM, ROLE, ROOM, SERVANT, SETTLEMENT, SOCIETY,
                   STREET, SUFFERED, HONOUR, SUPERIOR, TERM, THINGS, TIED, TRAIT, TIME_SPAN, TRAFFIC, VESSEL, VICINITY, words)


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
# What follows 一文 when it is money (一文も, 一文の得, 一文無し, 一文でも二文でも).
_NOT_MONEY = r'(?!も|の(?:得|徳|値|ねうち|価値|銭|金|収入|負担|路用|足し|儲|役|価)|にもな[らっりる]|だに|無|な[しい]|欠|でも|銭|[二三四五六七八九十百千]文|ずつ|づつ)'
# Verb stems before 入る read いる (眺め入る, 恐れ入る, 聞き入る); Sudachi says はいる.
_IRU_STEM = '(?:' + words(IRU_STEM) + r'|[一-鿿](?<!少)[きぎしちびみりめれけせえね])'
# Metals and the like near 金 make it the metal, きん (金は銀より重い); 銀行 is money.
_METAL = '(?:' + words(METAL) + r'|銀(?!行))'
# A counter kanji that starts a verb after 何, followed by its okurigana (何着てる, 何話してる, 何間違えてる,
# 何歩いてる): 何 is なに; the counter (何着か, 何話しか, 何歩くらい) stays なん.
_VERB_AFTER_NANI = (r'(?:着[てたなられるろよせまさ]|話(?:し(?!か(?!け))|[さすせそ])|間(?:違|ちが|に合|にあ|抜)'
                    r'|曲(?:げ|が[らりるれろっ])|[歩巻](?:い[てたち]|き|く(?!らい|ぐらい)|け|こ)|発(?:し(?!か)|す|せ))')
# Not a comparison after 方 (来た方がいい: ほう).
_NOT_BETTER = (r'(?!が(?:いい|良|よ[いかくけろ]|まし|好|楽|早|上|得|便利|大き|小さ|多|少|ずっと|はるか|むしろ|まだ|断然|よほど|余程|よっぽど)'
               r'|より|と(?:比|くら))')
# A person before 下 もと (陛下の下へ, 俺の下に来い, ルークの下に): titles, pronouns, a katakana name.
_PERSON_OF = (r'(?:様|さま|さん|君|くん|殿|陛下|先生|師匠|主|王|父|母|俺|僕|私|わたし|儂|わし|自分|彼|彼女|あなた|貴方|貴女|お前|[ァ-ヺー]{2,}'
              r'|人|者|医者|女性|男性|二人|三人|仲間)'
              r'(?:たち|達)?の$')
_NOT_EYES = (r'(?!の?(?:眼|瞳|怪物|化け物|化物|妖怪|小僧|入道)|が(?:怪しく|ギョロ|ぎょろ|ぎろ|ギロ|光|輝|開|見開)'
             r'|を(?:ギョロ|ぎょろ|ぎろ|ギロ|見開|動か|細め|開|光))')
ALWAYS = '(?:)'  # an after-pattern that always matches: the form's one reading in bare text, shown
# Rain and snow right before a verb (雨が, 雪はしんしんと, 大雨も): 降る ふる; 霜が降りる and 光が降りる are おりる.
# Not after other kanji (白雪, 深雪: names that get off at a station).
_PRECIPITATION = (r'(?:(?<![一-鿿])|(?<=[大小豪霧氷初粉吹春秋冬夜長俄驟時性]))(?<![白深小]雪)(?:雨|雪|霰|雹|霙|みぞれ|あられ)'
                  r'(?:が|は|も|の)?(?:まだ|なお|今も|どのくらい|たくさん|沢山|激しく|強く|静かに|少し|ずっと|朝から|よく|一日中|一晩中'
                  r'|[一二三四五六七八九十数何]+(?:日|時間|週間|ヶ?月|か月)(?:間)?(?:も)?)?'
                  r'(?:[ぁ-んァ-ヴー]{2,6}と)?$')
# 降り続く雨, 降りしきる雪, 降り始めの雨: 降る ふる before rain or snow (T293).
_PRECIPITATION_AFTER = r'(?:続|つづ|始め|はじめ|しき|頻|ゆ|つけ|注|そそ)[ぁ-ん]{0,3}?(?:雨|雪|霰|雹|霙|みぞれ|あられ)'
# Surrender (軍門に降る, 傘下に降った): 降る くだる, also where Sudachi took the verb for 降りる (T260).
_SURRENDER = r'(?:軍門|傘下|麾下|配下|旗下|幕下)に$'
# A taste or food near 辛い (T294); 味 but not in 意味, 興味, 趣味, 気味, 正味, 地味, 味わう.
_TASTE = words(DISH - {'味'}, SPICE) + r'|(?<![意興趣気正地])味(?!わ)|からし(?![てた])'
# Tools held by a handle, え (柄 after them is not a sword's つか).
_HANDLED = (r'(?:ハンマー|槌|鎚|杖|スパナ|鉈|棒|モップ|ほうき|ホウキ|箒|鍬|鋤|斧|槍|鎌|傘|パラソル|包丁|スコップ|シャベル|刷毛|筆|ブラシ|旗|'
            r'柄杓|ひしゃく|おたま|ポール|トンファー|ステッキ|メイス|バット|熊手|鞭|ムチ|ハルバード|薙刀|なぎなた|戟|矛|鉾|ピッケル|'
            r'つるはし|ツルハシ|フライパン|鍋|錫杖|ハンドル|レバー|団扇|うちわ|扇|ポンプ|鋸|のこぎり)')
CONTEXT_RULES = {
    # 都: Tokyo's government (都の職員, 都が発表した), not the capital of a story (都 みやこ, HAND_DEFAULTS).
    '都': [('と', None, r'の?(?:職員|施設|予算|条例|担当|調査|方針|幹部|議会|知事|当局|教育委員会|福祉|保健|水道|交通局|税|事業|補助|管理|所有)'
            r'|が(?:発表|公表|決め|要請|実施|定め|設置|管理)')],
    # 画 え (a picture, a shot: いい画だ, 画になる, 画を描く) after a particle or an inflected word; Sudachi says が.
    # Not glued (肖像画, デザイン画: Sudachi's が) or as a credit (画・…, 画：…).
    '画': [('え', r'(?:[のないたるうをがはもにで]|一葉の)$', r'(?:[をがはもにでのとだ](?![・：:])|みたい|よう|です|。|」)', 'and')],
    '人気': [('にんき', None, r'の(?:な|無)(?:い|かった)(?:奴|やつ|者|人|キャラ|作品|商品|子(?!供|ども)|アイドル|作家|店)'),
             ('ひとけ', None, r'の(?:な[いくかけ]|無[いくかけ])|[がのはも]?(?:少な|絶え|途絶え)|も(?:な[いくかけ]|無)'),
             ('ひとけ', None, r'[がは](?:な|無)(?:い|く|かった)?(?:' + words(STREET, ROOM - {'室'}, '場所', '所', 'ところ', '道', '時', 'とき')
              + r'|のを確|ことを確|、?(?:静|しん|ひっそり))'),
             ('ひとけ', _HITOKE_PLACE, r'[がは](?:まったく|全く|ほとんど|全然|一切)?(?:な[いくかけ]|無[いくかけ])', 'and')],
    # 他 is ほか in plain text (DEFAULT_READINGS); た in その他, set phrases and as a prefix (他言語).
    '他': [('た', r'その$', r'の(?:追随|追従|干渉|介入|模範)|を(?:圧倒|寄せ付け|凌|しの)|に(?:類|例|比類)を(?:見|み)|[一-鿿]')],
    # 僕 is ぼく (TOP_READINGS) except as a servant: 神の僕, 忠実なる僕, 僕ども (T445).
    '僕': [('しもべ', r'(?:(?:神|主|主君|主人|ご主人様|あるじ|王|魔王|女王|悪魔|女神|陛下|殿下)の|忠実なる?|哀れな|卑しき)$', r'(?:ども|共)')],
    # 種 is たね (DEFAULT_READINGS) except as "kind": この種の, 数種, 百種.
    '種': [('しゅ', r'(?:この|その|あの|どの|ある|各|同|異|別|[数何一二三四五六七八九十百千0-9０-９])$', None)],
    # 期 is ご only in この期に及んで (Sudachi: き); a table learnt it from に and read 戦国期に ご.
    '期': [('ご', r'この$', r'に(?:及|およ)', 'and')],
    # 素振り is そぶり (a table entry); すぶり, a practice swing, with a bat or sword or as a drill (素振り百回, 素振りする).
    '素振り': [('そぶり', r'(?:[うくぐすつぬぶむるたい]|[^のをにでと]な)'
                         r'(?<!軽く)(?<!暫く)(?<!しばらく)(?<!大きく)(?<!強く)(?<!鋭く)(?<!早く)(?<!速く)(?<!よく)$', None),  # a manner, after a verb or adjective (考える素振り)
              ('すぶり', r'(?:木刀|竹刀|バット|ラケット|ゴルフクラブ)[^。」！？]*$', None),
              ('すぶり', None, r'を?[0-9０-９一二三四五六七八九十百千]+[回本]|の(?:稽古|練習)|(?:し(?!か)|する|すれ|させ)')],
    # 下: もと under an abstract noun (指導の下に); した in "Xの下で" (Sudachi's もと there is nearly always wrong).
    '下': [('もと', words(ABSTRACT, SUPERIOR) + 'の$', None),
          # A person + の下へ/に and a verb of going or serving (陛下の下へ向かう, 俺の下に来い): もと.
          ('もと', _PERSON_OF, r'[へに][はもの]?と?(?:戻|帰|来|き[たて]|く[るれ]|向か|駆け|馳せ|走|届|行|い[っくかきこ]|赴|参|集|身を寄せ|仕え|嫁|弟子入|預け|送|連れ|やって|訪|通|引き取'
           r'|近づ|近寄|案内|つ[いく]|い[るろ]のが)'
           r'|で(?:働|修行|学|仕え|育)', 'and'),
          # Under a titled person or a superior (フェルト様の下で, 上司の下で): もと, whatever follows (T270).
          ('もと', r'(?<!お日)(?<!お陽)(?<!お月)(?<!お天道)(?<!お星)(?:様|さま|さん|殿|陛下|殿下|閣下|先生|師匠|上司|社長|部長|課長|団長|隊長|親方|教授|監督)'
           r'(?:たち|達)?の$', r'で', 'and'),
          ('した', r'の$', r'で', 'and')],
    # 音: ね for instruments and insects (琴の音, 虫の音) and ぐうの音; Sudachi's おと otherwise.
    '音': [('ね', '(?:' + words(INSTRUMENT, INSECT, 'ぐう', 'グウ') + r'|(?<![霧汽警])笛)の$', None)],
    # 風: ふう for manner (こんな風に, 知らない風で), かぜ for the wind.
    '風': [('かぜ', None, r'の吹き回し'),
           ('ふう', r'(?:[こそあど]んな|(?:[こそど]う|ああ)(?:いう|いった|言う|云う|言った|云った)'
              r'|と(?:いう|いった|言う|云う|言った|云った)|ような|ふうな)$', None),
           # 知らない風を装う, 気にしてない風をして: ふう; not 見えない風を感じる (かぜ, T276).
           ('ふう', r'ない$', r'(?:[にでも]|を(?:装|よそお|演じ|し[てた]|する|見せ|意識))', 'and'),
           ('かぜ', None, r'に(?:そよ|揺|ゆれ|なび|吹|舞|乱|あお|煽|任|散|飛|はため|翻|ひるがえ|鳴|運ば|乗)'
              r'|が(?:吹|強|弱|やみ|止|冷|涼|出|そよ)|を(?:受け|切|感じ|起こ)|の(?:音|便り)')],
    # 中 after a stretch of time or a place, "all through" (一日中, 世界中): じゅう; Sudachi says ちゅう,
    # right after activities (授業中), 午前, 今週/今月 (こんしゅうちゅう) and 数日 (within days).
    # 十分: Sudachi's じゅうぶん where it keeps one token; minutes with a cue (counters.TEN_MINUTES_*).
    '十分': [('じゅっぷん', _TEN_MINUTES_BEFORE, _TEN_MINUTES_AFTER)],
    # Lone single-kanji nouns Sudachi reads with the on'yomi where the text means the kun word (札 ふだ, 角 つの).
    # 札 is ふだ on its own (HAND_DEFAULTS); さつ for money: 千円札 (glued), 財布の札, 札を刷る, 札束.
    '札': [('さつ', r'(?:にせ|ニセ|偽|贋)$|(?:財布|札入れ|金庫|万|千|お金|紙幣|給料|現金|小銭|レジ|中身の)[^。」]{0,10}$', None),
           ('さつ', None, r'[をがもで]?(?:刷|印刷|両替|崩|束|払|数え|勘定)|の束|と(?:硬貨|小銭)|だけ(?:を|が)?(?:抜|掏|す[っりら]|取|盗)')],
    'お札': [('おさつ', r'(?:財布|万|千|円|お金|紙幣|現金|給料|小銭|レジ|両替)[^。」]{0,8}$', None),
             ('おふだ', r'(?:神社|寺|祠|神棚|鴨居|お守り|護符|魔除け|厄除け|火の用心|お祓い|祈祷|呪い|封印|様)[^。」]{0,6}$', None),
             ('おふだ', None, r'[をがはも]?(?:貼|は[らりるれっ]|授|祀|納め|剥が|はが)'),
             ('おさつ', None, r'[をがもで]?(?:刷|印刷|両替|崩|束|払|数え)')],
    # 社 やしろ: a shrine (小さな社, 社の境内); しゃ (a company, Sudachi's) otherwise.
    '社': [('やしろ', r'(?:小さな|小さい|古い|古びた|朽ちた|寂れた|神の|稲荷の|鎮守の|村の|山の|森の|丘の|島の|祀る|まつる|祀った|'
                     r'祀られた|祀られている|神様の|神さまの|土地神の|お)$', None),
           ('やしろ', None, r'の(?:境内|鳥居|裏手|祭神|社殿|御神体|ご神体|神主|石段)|に(?:参|祀|詣|まつ)')],
    # 角 つの on an animal or a monster (角が生えた, 鬼の角); かど (a corner) otherwise.
    '角': [('つの', r'(?:(?:鬼|牛|山羊|ヤギ|羊|ヒツジ|鹿|シカ|竜|龍|ドラゴン|獣|魔獣|悪魔|一角獣|ユニコーン|サイ|犀|カブトムシ|水牛)の'
                   r'|一本の|二本の|一対の|頭の|額の|頭に|額に|額から|頭から|捩れた|ねじれた)$', r'(?!を曲が|を折れ|を左|を右)', 'and'),
           ('つの', r'(?:牙|尻尾|しっぽ|翼|蹄|ひづめ|鬣|たてがみ|鱗)[とや]$',
            r'[がを]?(?:生え|生や|はえ|はや|一本|二本)|の生え|が(?:伸び|折れ)|を伸ば|[とや](?:牙|尻尾|しっぽ|翼|蹄|ひづめ|鬣)')],
    # 柄: a sword's つか, a tool's or spear's え; がら (a pattern, one's nature) otherwise.
    '柄': [('つか', r'(?:剣|刀|太刀|短剣|短刀|小刀|脇差|大剣|長剣|聖剣|魔剣|刀剣|小太刀|サーベル|レイピア|木刀|竹刀)の$', None),
           ('え', r'(?:斧|槍|鎌|箒|ほうき|ホウキ|ハンマー|鎚|槌|モップ|柄杓|傘|包丁|スコップ|シャベル|鍬|鋤|モーニングスター|'
                 r'ハルバード|メイス|フライパン|鍋)の$', None),
           # gripped, not a tool's (柄を握る, 柄に手をかける: ruby つか 652 of 712) (T373)
           ('つか', r'^(?!.*' + _HANDLED + ')', r'を(?:握|掴|摑|つか|にぎ)|に(?:手を|指を|添え|手が)|から手', 'and')],
    # 面 つら in どの面下げて, 面を貸せ, 間抜けな面をして; おもて in 面を上げる, 面に出す (T373).
    '面': [('つら', r'(?<![ぁ-ゖ])どの$', r'を?(?:下げ|さげ)', 'and'), ('つら', r'(?:みたいな|みてえな|ような|そうな|げな)$', r'を[しす]', 'and'),
           ('つら', None, r'を?貸[しせさ]'), ('おもて', None, r'を(?:上げ|あげ|挙げ|伏せ|ふせ)|に(?:出|表|あらわ|現)')],
    # 値 ね: a price (値が張る, 値がつく, 値をつり上げる); Sudachi's あたい otherwise (T373).
    '値': [('ね', r'(?<![一-鿿])$', r'[がはも]?(?:張|は[るらりっれ])|[がも]?(?:つく|つい|付[くいけ])|を(?:つけ|付け|つり|吊り)|[がは](?:上が|下が|あが|さが|吊|つり)', 'and')],  # not 補正値が上がる
    # 弦 つる of a bow (弓の弦, 弦に矢を番える); げん (an instrument's) otherwise (T373).
    '弦': [('つる', r'(?:弓|ボウ|弩)', r'に(?:番|つが|矢)')],
    '業': [('わざ', r'(?:至難の|なせる|成せる|為せる|神の)$', None)],  # 至難の業
    '艶': [('つや', None, r'(?:っぽ|の|が|を|も|は|と|、|。|消|出し|々)')],  # not 艶やか あで
    # 直に: じか with touching, seeing or meeting (直に触れる); じき (soon) is left to Sudachi.
    '直': [('じか', None, r'に(?:触|さわ|見|会|あ[いうえっ]|話|聞|確か|感じ|伝|手渡|渡|接|肌|座|置|書|乗|当|受|届|響|叩|打|握|掴|'
                         r'つか|口|吸|飲|嗅|浴|入|顔)')],
    '要': [('かなめ', r'[^必重主]の$', r'(?![がも](?:あ|な))(?:だ|で|と|に|を|が|は|。|、|」|な)', 'and')],  # 防衛の要; not 検討の要がある
    '真': [('ま', None, r'に受け')],  # 真に受ける
    '紅': [('べに', None, r'を(?:引|ひ|差|さ|つけ|付け|塗|ぬ)|[がも](?:落ち|取れ|とれ|にじ|滲)')],  # 紅を引く
    '香': [('か', r'(?:梅|花|菊|蘭|桜|薔薇|百合|柚子|檜|若葉|春|茶|墨)の$', None)],  # 梅の香
    # 綿 is わた on its own (HAND_DEFAULTS); めん for the fabric (綿のシャツ, 綿とポリエステル).
    '綿': [('めん', r'(?:麻|絹)[やとか]$', r'(?:シャツ|パンツ|ズボン|ネル|モス|製|[0-9０-９]|の(?:シャツ|ズボン|パンツ|布|生地|服|靴下|'
                                         r'ロープ|ビロード|下着|手袋|マスク|ワンピース|ブラウス|スカート)|[とや](?:麻|ポリ|絹|化繊|合成|ナイロン)|か麻)')],
    '氏': [('うじ', None, r'より育ち')],
    '際': [('きわ', r'(?:崖|壁|窓|水|波|額|生え|淵|縁|谷)の$', None)],  # 崖の際
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
           ('かた', r'[ァ-ヺー]{2,}の$', r'(?:です|でし)', 'and'),  # ドイツの方ですか; not …したのはルークの方だった (ほう)
           ('かた', None, r'[がはをにも]?(?:いらっしゃ|お越し|おいで|お見え|ご存[知じ]|亡くなられ)'),
           ('かた', None, r'(?:たち|達)'),  # 騎士の方たち: people (T373)
           ('ほう', None, r'が(?:いい|良|よ[いかくけろ]|まし|無難|得策|安全|楽|早)'),
           # Plural after a person (あなた方, 先輩方, お嬢様方); not 母/父 (お母さん方の祖母: かた), nor an address (山田さん方で).
           ('がた', words(PLURAL_PERSON) + r'(?<![母父]さん)(?<![母父]さま)(?<![母父]様)(?<!お偉い)$',
            r'(?!で[、，]|に(?:住|下宿|寄宿|同居))', 'and'),
           ('かた', r'(?<!お)' + words(TRAIT) + r'な?$', _NOT_BETTER, 'and'),  # 勇敢な方の下に, 高貴な方のところへ
           ('かた', r'(?:様|さま|さん|君|くん|殿|陛下|先生|あなた|貴方|貴女|聖母|女神|神様|お前)(?:の(?:ような|様な)|みたいな)$',
            _NOT_BETTER, 'and'),  # 司祭様のような方, あなたのような方
           ('かた', r'(?:どのような|どういう|どういった)$', r'(?:です|でし|なの|なん|だ)', 'and'),
           ('かた', r'亡くな(?:っ|られ)た$', _NOT_BETTER, 'and'),
           # A person: お方, お三方, 紛う方なき; この方 + copula or topic; after an honorific verb (教えてくださった方).
           ('かた', r'(?:お[一二三四五六七八九十]?|紛う|まごう)$', None),
           ('かた', r'(?:この|こちらの|そちらの)$', r'(?:です|でし|でいらっしゃ|は)', 'and'),  # その方は: also そのほう (you)
           ('かた', r'(?:くださ|下さ|なさ|いらし|おっしゃ|お越しにな|ご覧にな)(?:っ?た|る)$', _NOT_BETTER, 'and')],
    # 間: ま in いつの間に, 束の間, 一瞬の間; あいだ in この間 (the other day; Sudachi says かん).
    # 間 ま also for a pause (間が空く, 間を置いて, する間もなく), not after の (その間も, AとBの間が空く: あいだ).
    '間': [('ま', r'(?:いつ|何時|束|一瞬|咄嗟|瞬く|またたく|あっという|あっと言う|アッという|呼吸|呼吸分|一拍|謁見|玉座)の?$', None),
           ('あいだ', r'この$', None),
           ('ま', r'(?<!の)$', r'が(?:空|あ[いくきけ]|開|でき|持た|悪|抜け)|も(?:な[くい]|無[くい]|与え|あた|惜し)'
            r'|を(?:置|お[いかきく])', 'and'),
           # Between people, not after の (玉座の間に入る is a room): 慌てて間に入る, 間に割って入る.
           ('あいだ', r'(?<!の)$', r'に(?:割|入|はい|挟)', 'and')],
    # 後 before a number is あと (後五分で); Sudachi says ご. Not after その/この or a kanji (その後, 五年後, 購入後２日).
    # この後, あの後: あと (Sudachi: ご); その後 keeps そのご (both standard).
    '後': [('あと', r'(?<!その)(?<!この)(?<![一-鿿々0-9０-９])$', r'[0-9０-９一二三四五六七八九十百千数幾]', 'and'),
           ('あと', r'(?:この|あの)$', None),
           # のち: "later" at the start of a clause (、後に彼は…), 後の世/時代, しかる後, それから後.
           ('のち', r'(?:^|[、。「『（　])$', r'に(?!(?:は|も|続|残|引|ひ|し|す|な|回|まわ|従|つ|来|戻|退|下が|さが|控|置|お'
            r'|い[るたてま]|居|生き|被|かぶ|油断|立|迫|[^、。]{0,4}?(?:足音|跫音|気配)))', 'and'),  # 後にいる者 (behind): あと/うしろ
           ('のち', r'(?<![一-鿿々])$', r'の(?:世(?!話|界|代)|時代|世代|歴史)', 'and'),  # not 羽柴後の時代 (ご)
           ('のち', r'(?:しかる|然る|而る|それから|あれから|これから)$', None)],
    # 表 おもて: the outside or the front (表に出る, 表に出さない, コインの表, 表の顔); ひょう (a table) otherwise.
    '表': [('おもて', r'(?:裏[とものか]|コインの|硬貨の)$',
            r'に(?:は|も)?(?:出|で[たてるな]|立|現)|へ(?:出|と)|を出歩|で(?:遊|待|絡)|[とか]裏|が(?:出|ない)|だって|立って|沙汰|向き'
            r'|の(?:顔|世界|社会|舞台|仕事|理由|看板|門|通り|玄関)'),
           # 表 starting a phrase (after punctuation or a particle other than の: not 順位表, 組み合わせ表, 四列の表) is
           # おもて in fiction (表世界, 表で待つ, 表に返す) unless it is a table: 表を作る, 表にまとめる, 表のように, 表や図, 表1.
           ('おもて', r'(?:^|[、。「『（　！？!?…―─」]|[をがはもにでへとや])$',
            r'(?!を(?:作|つく|書|か[いきく]|描|見[てる]|参照|まとめ|埋め|確認|用い|使|示|完成|配|貼|横|縦)|が(?:書|か[いかきく]|描)|、|など|に(?:まとめ|示|記入|書|整理|し[てた]|す[るれ]|あ[るりっ])'
            r'|の(?:よう|とお|通り|項目|数|読|中|上|下|左|右|内容|見方|作|縦|横|行|列|欄|形)|や|と(?:グラフ|図)|[0-9０-９１-９]|中|内|参照|計算|示|は(?:次|以下))', 'and')],
    # 主: あるじ for the master of a house or of servants (館の主, 我が主, 奴隷と主); Sudachi's ぬし otherwise
    # (声の主, 部屋の主). 主として is left alone: books' ruby there is mostly あるじ (主として認める), not しゅ.
    '主': [('おも', r'は$', r'として(?![のはも、])(?![^。、]{0,8}?(?:認|迎|仰|崇め|崇拝|あがめ|慕|敬|仕え|つか|戴|いただ|選|定め|契約|呼|従|君臨|相応|ふさわ|受け入))',
           'and'),  # mainly (…は主として扱う), not a master (主として認める, 主としての務め)
          # The main part: おも (治癒呪文が主で, 会議が主だから), しゅ against 従 (どちらが主でどちらが従).
          ('しゅ', r'(?<!我ら)(?<!われら)(?<![我わ汝])が$', r'で[^。]{0,12}従', 'and'),
          ('おも', r'(?<!我ら)(?<!われら)(?<![我わ汝])が$', r'(?:で(?![はあす])|だ(?:から|し|けど|が|な)|であろう)', 'and'),
          ('しゅ', None, r'[はが](?:仰せ|言われ)'),  # the Lord (主は仰せられた)
          # The master, standing alone (亡き主, 主は言った); after の Sudachi's ぬし stays (声の主, 森の主).
          ('あるじ', r'(?:^|[「『（　、。！？…―─])$', r'(?:[はがをへ、。」！？…]|なき|無き|だ|です|である)', 'and'),
          ('あるじ', r'(?:亡き|なき)$', None),
          ('あるじ', r'(?<![一-鿿々ァ-ヺー])$', r'として[^。、]{0,8}?(?:認|迎|仰|崇め|崇拝|あがめ|慕|敬|仕え|つか|戴|いただ|選|定め|契約|呼|従|君臨|相応|ふさわ|受け入)|としての', 'and'),
          ('あるじ', '(?:' + words(BUILDING - {'学校', '会社', '駅', 'ホテル'}, SERVANT,
                                    '邸', '邸宅', '道場', '店', '宿', '一家') + '[のと]|我が|わが|最愛の)$', None),
          # A master one serves: 主の命令, 主に仕える, 主を守る (not after の: 声の主の顔). 主様 is also ぬしさま.
          ('あるじ', r'(?<![一-鿿々のが])$', r'の(?:命|元|もと|ため|為|傍|側|身|意|仰せ|好み|期待|役|顔|帰り)|に(?:仕え|忠誠|従)|を(?:守|失|裏切|迎え)', 'and')],
    # 抱く だく: holding someone or something in the arms (赤ん坊を抱く, 抱きたい); Sudachi's いだく for feelings
    # (疑問を抱く) and, as books' ruby often has it, 腕に抱く and the passive (懐に抱かれる).
    '抱く': [('だく', r'(?<![一-鿿])' + words(HUGGED, PEOPLE, BODY) + r'を(?:[ぁ-ゑァ-ヶー]{2,6}と?|[一-鿿][ぁ-ゑ]{1,3})?$', None),
            ('だく', r'(?<!を)$', r'た[いくかけ]', 'and'), ('だく', None, r'て(?:寝|眠)')],
    # 家 け after a katakana name (ローズ家, フジバヤシ家) or a noble title (侯爵家, 大公家, 新王家); Sudachi says か.
    # After a proper noun (佐藤家, 高橋家) it is a POS rule in context_reading.
    '家': [('け', r'[ァ-ヺー・]{2,}(?<!ボロ)$|(?:爵|大公|辺境伯|伯|王|皇帝|騎士|公方|管領|関白|貴族|領主)$', None),
          # A family Sudachi doesn't know as a surname (黒石家の長男, 東雲家の両親): its members and house.
          ('け', r'(?<![国御])[一-鿿々]$', r'の(?:人間|者|人々|令嬢|息子|娘|子|長男|次男|三男|長女|次女|三女|末娘|末っ子|末弟|嫡男|嫡子|当主|跡取り|姫'
           r'|両親|祖父|祖母|父|母|兄|姉|弟|妹|家族|一員|血|使用人|メイド|執事|屋敷|邸|門|敷居|紋章|キッチン|台所|食卓)', 'and')],
    # 側 そば: beside (すぐ側, 彼の側にいる, 駅の側で); がわ (a side) otherwise (向こう側, 民の側につく).
    '側': [('そば', r'すぐ$', None),
           ('そば', r'を$', r'に(?:置|おい|お[かきくけ])', 'and'),  # 護衛を側に置く
           ('そば', r'[のがはも]$', r'に(?:いる|い[てたらまれよ]|居|あ[るっ]|置|寄|座|控|仕え|付き添|はべ|侍|来|行)|で(?!は)|まで', 'and')],
    # 階 かい after 上の/下の/同じ/この (上の階へ): Sudachi's きざはし is the steps of a palace or shrine.
    '階': [('かい', r'(?:[上下]の|同じ|[こそあど]の|別の|各|次の|隣の|真[上下]の)$', None)],
    # 棟 とう as a building's suffix Sudachi split off a kanji noun (研究棟, 理学部棟, 部室棟); Sudachi says むね.
    # Not after a number (一棟 ひとむね: the counter's) or a lone kanji (別棟).
    '棟': [('とう', r'(?:(?![〇一二三四五六七八九十百千万何数幾両])[㐀-䶿一-鿿々]){2}$', None)],
    # 傍 alone (not 傍ら) is そば before a particle: 彼の傍にいる, 窓の傍で; Sudachi says かたわら.
    '傍': [('そば', None, r'(?:に|で|まで|から|へ|を)')],
    # 留まる とどまる after に (その場に留まる, だけに留まる), but 目に留まる, 枝に留まる: とまる.
    '留まる': [('とどまる', r'(?<![目眼耳枝肩木々線])に$', None)],
    # 擦る こする: eyes rubbed (目を擦る), ごしごし, a cheek rubbed against (頬を擦りつける). Sudachi's する stays for
    # compounds it splits (擦り切れる, 擦りむく, 擦りガラス) and マッチ; さする (stroking a back or an arm) has no cue.
    '擦る': [('こする', '(?:(?<![一-鿿])(?:目|眼|瞼|まぶた|目元|目尻|目蓋|鼻|鼻の下|まなこ|両目|片目)を'
                       r'(?:手|指|袖|拳|手の甲|両手|右手|左手|片手|指先)?で?(?:ごしごし|ゴシゴシ|こしこし|しきりに|何度も|軽く|強く)?'
                       r'|(?:ごしごし|ゴシゴシ|こしこし)と?)$', None),
            ('こする', r'(?:頬|頰|顔)を$', r'(?:つけ|付け)', 'and'),
            ('さする', r'(?:お腹|おなか|お中)を(?:優しく|そっと|ゆっくりと?)?$', None)],
    # 弾く ひく for an instrument (ピアノを弾く); はじく for what bounces off or is flicked (攻撃を弾く, 指で弾く,
    # 弾かれたように) when no instrument is near. Otherwise the model.
    '弾く': [('ひく', r'(?<![一-鿿])' + words(PLAYED) + r'(?:を|で|も|は)$', None),
            ('はじく', r'^(?!.*' + words(PLAYED) + r').*(?:(?<!何)を|で|によって|(?<!ため)(?<!よう)に)$', None),
            ('はじく', r'^(?!.*' + words(PLAYED) + ')', r'れ(?!ば)', 'and')],
    # 弾ける ひける (can play, 弾く's potential) after an instrument (ギターが弾けない, ピアノなんて弾けない); はじける,
    # the list's reading, elsewhere, not shown: an extra reading (T241).
    '弾ける': [('ひける', r'(?<![一-鿿])' + words(PLAYED) + r'(?:が|を|も|は|なんて|でも|しか|だけ)?$', None)],
    # 降る ふる after rain or snow, also where Sudachi took the verb for 降りる (雨は降り続けた, WRONG_LEMMA, T240).
    '降る': [('ふる', _PRECIPITATION, _PRECIPITATION_AFTER), ('くだる', _SURRENDER, None)],
    # 解く ほどく for what is tied or wound (紐を解く, 髪を解く, 腕を解く); Sudachi's とく otherwise (謎を解く).
    '解く': [('ほどく', r'(?<![一-鿿])' + words(TIED) + r'(?:の(?:結び目|紐))?を$', None)],
    # 堪える こらえる for holding something back (涙を堪える, 笑うのを堪え, 堪えきれない); たえる (痛みに堪える) is the model's.
    '堪える': [('こらえる', r'を(?:ぐっと|必死に|必死で|なんとか|何とか|じっと|懸命に|どうにか)?$', None),
             ('こらえる', None, r'きれ')],
    '描く': [('かく', r'(?<![一-鿿])' + words(DRAWN) + r'(?:を|に|も)$', None),
            ('かく', None, r'(?:[いか]れ)?(?:た|ている|てある|ていた)' + words(DRAWN) + '(?!画)')],  # 描いた絵, 描かれた漫画
    # 吐く つく for a sigh, a lie or abuse (ため息を吐く, 嘘を吐く, 悪態を吐く); Sudachi's はく otherwise (息を吐く: both).
    '吐く': [('つく', r'(?:ため息|溜め息|溜息|嘘|ウソ|悪態)を$', None)],
    # 被る こうむる for harm or favour received (被害を被る, 恩恵を被る); Sudachi's かぶる otherwise (帽子を被る).
    # Also ごめん被る and 被った被害 (T371); Sudachi's こうむる for a bare 被る is a hand default to かぶる (HAND_DEFAULTS).
    '被る': [('こうむる', words(SUFFERED) + '[をはも]$', None), ('こうむる', r'(?:ごめん|御免)を?$', r'た?(?:被害|損害|損失|打撃)')],
    # 開ける ひらける: a view or a way opens (視界が開けた, 道が開ける, 開けた場所に出た); あける otherwise (T372).
    '開ける': [('ひらける', r'(?:視界|視野|眺望|展望|景色|眺め|前途|未来|道|運|運命|活路|人生|世界|森|林|空|天|目の前)[がは]'
                         r'(?:[ぁ-ゑ]{2,5}と?|[一-鿿][ぁ-ゑ]{1,3}|一気に|急に|一挙に|一面に|大きく)?$', r'(?!られ|させ)', 'and'),  # not 抜け道が開けられる
             ('ひらける', r'^[^を]*$', r'た(?:場所|空間|草原|草地|高台|荒野|平原|平地|空き?地|台地|通り|一角)', 'and')],
    # 脅かす おどかす: startling someone for fun (脅かさないで, ちょっと脅かしてやろう); おびやかす (threaten) otherwise (T372).
    '脅かす': [('おどかす', r'(?:ちょっと|冗談で|軽く)$', r'(?:ないで|なよ|すぎ|過ぎ|てやろ|てやる|やがっ|役|ちゃ)')],
    # 汚す けがす: honour or purity (家名を汚す); 汚れなき けがれ. よごす, よごれ otherwise (T372).
    '汚す': [('けがす', r'(?<![一-鿿])' + words(HONOUR) + r'[をもは]$', None)],
    '汚れ': [('けがれ', None, r'な[きく]')],
    # 来るべき is きたる before a noun (来るべき時); くる as a predicate (来るべきではなかった).
    '来る': [('くる', None, r'べき(?:では|じゃ|でな|だった|だろ|でしょ|です|だ[。、よなね！？」])')],
    '今日': [('こんにち', None, 'の' + words(REALM - {'国'}, SOCIETY - {'未来', '地球'}, ISSUE - {'急務', '懸案'})
              + r'|に(?:至|いた)る|では|において')],
    # Sudachi says あす; books mostly say あした, except in formal phrases.
    '明日': [('あした', None, r'(?!の' + words(REALM, SOCIETY - {'経済', '時代', '文明', '科学', '技術', '教育', '政治'}) + '|を担|にも)')],
    # 上手 かみて/下手 しもて: the stage's sides, also when the other side is named next to it (上手と下手);
    # Sudachi's しもて elsewhere is へた (HAND_DEFAULTS). 上手 is じょうず as an adjective (上手に, 上手だ, 上手。):
    # Sudachi sometimes says かみて there; 上手の, 上手を, 上手から keep its reading (stage, shogi うわて).
    '上手': [('かみて', r'(?:舞台|演壇|山|川|河)の?$|下手(?:と|から|へ)$|下手[がに].{1,10}、$', r'側|の?(?:袖|そで)|から(?:出|登場|現|入|来|やって)|(?:と|から|へ|、)下手|[がに].{1,10}、下手[がに]'),
             ('うわて', r'枚$|落ちの$', r'に出(?:る|た|て|ら|ま)|を(?:行|い)[かきくけっこ]'),
             ('じょうず', r'(?<!遥かに)(?<!はるかに)(?<!数段)(?<!一段)$',
              r'(?:に(?![出来入回立座向寄])|な(?![いく])|だ|です|でした|じゃ|ね|よ(?!り)|ー|っ|そう|すぎ|過ぎ|。|」|！|!|…|の手から)', 'and'),
             # A skill's suffix Sudachi split off (からかい上手, 射撃上手, 日本語上手).
             ('じょうず', r'(?:(?<!段)[一-鿿ァ-ヺー]|[いきしちひみりえけせてねべめれぎじび])$', None)],
    # 下手 しもて: the stage's or a river's lower side; へた takes no へ (下手へ退く).
    '下手': [('しもて', r'(?:舞台|演壇|川|河)の?(?:ずっと|少し|やや|すぐ)?$|上手(?:と|から|へ|、)$|上手[がに].{1,10}、$',
              r'へ|から(?:登場|出|入|現)|向き|寄り|側|(?:と|から|へ)上手|[がに].{1,10}、上手[がに]'),
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
    # なん before だ/です/で/の/と/て and counters (何年, 何冊, 何か国, 何作目: T291): Sudachi's; なに before か, する, verbs and ？.
    '何': [('なん', r'やら$', r'やら', 'and'),  # 雪かきやら何やら
          ('なに', r'何から$', None),  # 何から何まで
          ('なに', None, r'(?![かカヶケヵ箇]国|[玉針]|作(?![っらりるれろ]))(?:[をがもかし]|より|す|それ|これ|あれ|[？?！!、」]'
             r'|や(?:ら|かや|[っりるれろ])|' + _VERB_AFTER_NANI + r'|に(?:使|つい|つけ|する|し[たよま])|ごっこ|げな'
             r'|(?!' + words(COUNTER) + r')[一-鿿])')],
    '色紙': [('しきし', r'(?:サイン|寄せ書きの?)$', r'に(?:サイン|寄せ書き|書)|を(?:飾|贈)'),
             ('いろがみ', r'折り?$', r'.{0,6}?(?:折[っらりる]|鶴|切り抜)')],
    '寒気': [('かんき', r'(?:強い|上空の|大陸からの|冬型の|北からの)$', r'団|が(?:南下|流れ込|入)|の(?:影響|流れ込|南下)'),
             ('さむけ', None, r'が(?:し|す|走|襲)|を(?:覚え|感じ)')],
    '心中': [('しんじゅう', r'(?:無理|一家|親子)$', r'を(?:図|遂げ|はか)|する|した|して|しよう|未遂|事件|物'),
             ('しんちゅう', None, r'を(?:察|お察|推し量|思|吐露|明か|語)|穏やか|は(?:穏やか|複雑)|お察し')],
    '大家': [('たいか', r'(?:画|学|界|道|楽|壇|芸)の$', r'として'), ('おおや', None, r'さん')],
    # 分別: ぶんべつ for sorting waste (ゴミの分別, 分別して出す); ふんべつ (good sense, HAND_DEFAULTS) otherwise.
    '分別': [('ぶんべつ', r'(?:ゴミ|ごみ|資源|缶|瓶|びん|ペットボトル|プラスチック|プラ|生ゴミ|生ごみ|廃棄物)[のをはも]?$',
             r'(?:する|して|し[たまなろよ]|され|でき|収集|回収|処理|方法|ルール|作業|基準|ごみ|ゴミ)'),
            ('ふんべつ', r'(?:大人|年相応|思慮)(?:としての|の)$', r'が(?:な|つ|あ)|の(?:な|あ)|盛り|くさ|臭|を(?:わきまえ|失)')],
    '人事': [('ひとごと', None, r'(?:では|じゃ)な|とは思え|のよう|みたい|ながら')],
    '気質': [('かたぎ', words(OCCUPATION, '昔', '江戸っ子') + '$', None)],
    '末期': [('まつご', None, r'の(?:水|言葉|際|願い|一言|息)')],
    '床': [('とこ', r'(?:病の|お)$', r'に(?:就|伏|臥|入|はい)|から(?:起|出|離)|の(?:間|中)|を(?:上げ|敷|延べ|離|とっ|取)'),
           # 床につく, but not something put on the floor (頭を床につける, 手を床について): ゆか.
           ('とこ', r'(?<!を)$', r'につ(?!け[てたるらま])', 'and')],
    '辛い': [('からい', words(DISH - {'味付け', 'ソース'}, '口') + r'(?:は|が|も|の)?(?:ほど|より|くらい|ぐらい)?'
              r'(?:少し|とても|すごく|かなり|ちょっと)?$', words(DISH - {'スープ', '唐辛子', 'わさび', 'キムチ', '味'}, '食べ物', '食物', 'ソーセージ', '鍋')),
             # つらい unless food or a taste is near (辛い食べ物, 甘くて辛い, 舌が痺れるほど辛い: T294) or it ends a verb stem
             # (見辛い づらい) or a kanji word; 辛くも (からくも) and 辛いもの go to the model.
             ('つらい', r'^(?!.*(?:' + _TASTE + r')).*(?<![一-鿿ァ-ヺりきみちびぎべめれけせえねい])(?<![一-鿿]し)$',
              r'(?!も|物|の好き|方が|の(?:が|は|も)?(?:好き|苦手|得意|大好き|嫌い|ダメ|駄目)|けど(?:美味|おいし|うま|旨)'
              r'|すぎ|過ぎ|[？?]|ない(?:もの|物|の)|.*?(?:料理|' + _TASTE + '))', 'and')],
    '縁': [('ふち', words(VESSEL, '眼鏡', 'メガネ', 'めがね', '池', '崖', '井戸', 'ベッド', '帽子', '机', '窓') + 'の$',
            r'に(?:腰|座|手を|立)|を(?:なぞ|指で)')],
    '一寸': [('いっすん', None, r'先|法師|の虫|刻み')],
    # 分 alone as the odds (分が悪い, 分の悪い勝負, 私に分がある): ぶ.
    '分': [('ぶ', None, r'(?:が|の)(?:悪|わる)'), ('ぶ', r'[^のがはも]に$', r'が(?:あ|な[いく])', 'and')],
    # 十 alone as an age or a native count (十も年下, 十を過ぎたばかりの少女, 九つか十の子供): とお.
    '十': [('とお', r'(?:[一二三四五六七八九]つか|(?:歳|年齢)[もは])$', r'(?![一-鿿々ァ-ヺ0-9０-９…‥・])', 'and'),
           ('とお', None, r'(?:も(?:年|歳)[上下]|も(?:違|ちが)|かそこら|にも(?:手が届|満た)|(?:を|と少し)過ぎ'
                          r'|に(?:なる|なった)(?:か|子|娘|息子|頃|とき|時))')],
    # Xつ目 is the ordinal (三つ目の角 みっつめ) unless eyes are meant (三つ目が光る, 三つ目の怪物, 三つ目小僧: みつめ).
    **{form: [(reading, None, _NOT_EYES)] for form, reading in (('三つ目', 'みっつめ'), ('四つ目', 'よっつめ'))},
    '金': [('きん', r'(?:純|十八|(?:[白黒赤青緑紫茶]|銀)(?:と|地に))$', 'の' + words(JEWELRY, '延べ棒', '装飾', '粉', '糸', '髪', '仮面', '像', '鎖', 'ボタン', '刺繍',
                                                                 '刺繡', '瞳', '眼', '巻き毛', '縁', '斧', '矢', '砂', '漆', '簪', 'かんざし', '酒盃', '杯', '盃',
                                                                 '紋', '模様', '線', '横線', '羽', '装甲', '鎧', 'ポット', '皿', '卵', '聖堂', '鈴', '扇', '竪琴',
                                                                 '壺', 'まり', '毬', '林檎', 'リンゴ', '鯱', 'シャチホコ', '爪楊枝', '杖', '針', '光', '輝き')
            + r'|の目(?!当|的|処|安|に余)|色|メダル|貨|銀|と銀|箔|髪|属|の?(?:くさり|モール)|のよう|の(?:値段|価格|相場)|を(?:塗|ぬ|着せ|きせ|かぶせ|掘|採)'
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
    # Not after a noun + の: 里の外の人, 窓の外のこと are outside (そと).
    '外': [('ほか', r'(?:より|その)$', None), ('ほか', r'(?<!の)$', r'の' + _HOKA_OF + r'(?![間界])|なら[なぬずん]', 'and'),
           ('ほか', r'[うくぐすつぶむるたぬ]$', r'[はにも]?(?:な[いくかし]|無|あり|ある|ござ|仕方|手|道)', 'and')],
    # 人 right after a katakana word (カナダ人); after a place name, see context_reading.
    '人': [('じん', r'[ァ-ヺー]$', None)],
    # この前, その前, あの前: まえ (the other day, before that); Sudachi says ぜん before a noun (この前ホテルで).
    '前': [('まえ', r'(?:この|その|あの)$', None)],
    # 露 あらわ: laid bare (感情を露にする, 首が露になる); つゆ (dew, 露ほども, 露知らず) otherwise (HAND_DEFAULTS).
    '露': [('あらわ', None, r'に(?:し|す|さ|せ|な)|な(?![らりるれろ])'), ('つゆ', None, r'(?:知|し)ら')],
    # 素 もと: what something is made from (鍋の素, スープの素, 魂を素にする); す (素の自分, 素で) otherwise (HAND_DEFAULTS).
    # 日本 is にほん (HAND_DEFAULTS; a rule here also keeps the public table's にっぽん guesses out); にっぽん in cheers.
    '日本': [('にっぽん', r'(?:がんばれ|頑張れ|ガンバレ|フレーフレー)[、！!　]*$', r'[、！!　]*(?:チャチャチャ|ちゃちゃちゃ)')],
    # 転生 てんせい, 輪廻転生 keeps the Buddhist てんしょう; 御方 おかた (Sudachi: みかた).
    # Rules, not HAND_DEFAULTS, so the reading is shown (source rule).
    '転生': [('てんせい', r'(?<!輪廻)$', None)],
    '御方': [('おかた', r'$', None)],
    # 半身 はんみ: the body turned sideways (半身になる, 半身に構える); はんしん (half the body) otherwise.
    '半身': [('はんみ', r'(?<!の)$', r'に(?:な[っるりれろら]|構え|かまえ)|の(?:体勢|姿勢|構え)|で構え', 'and')],
    # 理 ことわり: the law of something (世の理, 自然の理); り otherwise (理にかなう, 理がある).
    '理': [('ことわり', r'(?<!分の)(?<!一面の)の$', r'(?!に(?:かな|適|叶|合|反|背|そむ)|合|がある)', 'and')],
    # 白髪 はくはつ for a young character's white hair (白髪の少女); しらが otherwise (HAND_DEFAULTS).
    '白髪': [('はくはつ', None, r'の(?:美?少女|美?少年|幼女|美?青年|美女|娘|女の子|男の子)')],
    '素': [('もと', r'(?:鍋|ナベ|スープ|カレー|かれー|シチュー|おにぎり|ふりかけ|料理|だし|出汁|味|混乱|元気)の$', None),
          # Not a person's 素 (彼女の素の顔, 雪平の素だ) or a prefix (素ッ首, 素筵).
          ('もと', r'(?<!彼)(?<!彼女)(?<!俺)(?<!私)(?<!僕)(?<!あたし)(?<!わたし)(?<!自分)(?<!ちゃん)(?<!さん)(?<!君)(?<!くん)(?<!様)(?<!前)の$',
           r'(?![のっだでなッ一-鿿々？]|が(?:出|見)|を(?:見|知|出|引|さら|表))', 'and'),
          ('もと', r'(?<![がはも])$', r'と(?:な[るりっ]|し|す)', 'and'), ('もと', r'を$', r'に(?:し|す)', 'and')],
    # 一日 as one token is Sudachi's ついたち (DEFAULT_READINGS: いちにち), the first of a month after 月 (来月の一日).
    '一日': [('ついたち', r'月(?:初め)?の?$', None), ('いちじつ', None, r'の長(?![さいくけかめ所男女子期官])')],
    # 銀杏 ぎんなん: the nut, eaten or picked (銀杏を焼く, 茶碗蒸しの銀杏); the tree いちょう (HAND_DEFAULTS).
    '銀杏': [('ぎんなん', r'(?:茶碗蒸し|焼き|炒り|煎り)(?:の|に|と|には)?$',
             r'の実|を(?:拾|焼|炒|煎|食|剥|む[いきく])|.{0,8}?(?:食べ|焼い|焼く|炒|煎|茶碗蒸し|美味|おいし)')],
    # 大文字 だいもんじ: Kyoto's bonfire (大文字の送り火, 大文字焼き); capital letters おおもじ (HAND_DEFAULTS).
    '大文字': [('だいもんじ', r'(?:京都|五山|送り火)の?$', r'焼|山|の?送り火|五山')],
    # These four also keep their model where no rule fires (the table's ruleForms).
    # 開く: ひらく after を (会を開く, 手紙を開いた); あく for opening hours (店は開いてますか) and lids.
    '開く': [('ひらく', r'を$', None),
            ('あく', words(OPEN_HOURS, '日', '曜日', 'まで') + r'[はがも]?$', None),
            ('あく', None, r'て(?:ますか|ます？|る？|ますよ)'),
            ('あく', r'(?:蓋|ふた|フタ)[がはも]?$', r'(?!れ)', 'and'),
            ('あく', r'(?<!落とし)穴[がはもの]?$', None)],
    # 止める: とめる for machines and flows (エンジンを止める); やめる for doing something (食べるのを止める, お止めください).
    '止める': [('とめる', words(HALTED) + 'を$', None),
             ('とめる', None, r'に(?:入|はい)'),  # 止めに入る: stepping in to stop a fight
             ('やめる', r'(?<!へ)(?:の|こと)を?$', r'(?!られ)', 'and'),
             ('やめる', r'お$', r'(?:ください|下さい|になって|なさい)', 'and')],
    # 空く: すく for roads and trains (道が空いている); お腹が空く is left to the model (it reads it already).
    '空く': [('すく', '(?:' + words(STREET, TRAFFIC) + r'|(?<!海)道)[がはも]?$', None), ('あく', r'穴[がはもの]?$', None),
           ('あく', None, r'[たて][^。、]{0,6}?穴')],  # 空いた穴, 空いている小さな穴
    # 額: がく for a frame (額に入れて飾る); ひたい for the forehead (額に汗, 額を拭う).
    '額': [('がく', None, r'に.{0,10}?(?:収め|納め|入れ|飾[っらりるれ])|縁|ぶち'),
           ('ひたい', None, r'[がは](?:熱|汗|広|狭)|に(?:汗|手|皺|しわ|傷|当て|かか|垂)|から汗|の(?:汗|傷|皺|しわ)'
            r'|を(?:拭|ぬぐ|押さえ|寄せ|集め)')],
    '一行': [('いちぎょう', words(EDGE, FEW - {'わずか', '僅か', 'ものの'}, '文章の', '冒頭の', '手紙の') + '$', r'目|ずつ|ごと|だけ|空け|の(?:文|文章|詩)')],
    # Read wrong in bare post-war text (Opus labels of 40 bare occurrences each from training authors, T200).
    # One reading there, shown: Sudachi's すうた, ふひょう, しゃらく, あらの, おにがみ.
    # 艶やか and 正しく elsewhere, and 呆ける, are HAND_DEFAULTS: not shown, since bare text also reads them
    # あでやか, まさしく, ぼける with no frame to tell (4, 6 and 2 of 40).
    '艶やか': [('あでやか', None, r'な?(?:着物|和服|振袖|衣装|微笑|笑み|舞|姿|装い)')],
    '正しく': [('まさしく', None, r'(?:それ|その通り|これ|あれ|奇跡|天才|神)')],
    '数多': [('あまた', None, ALWAYS)], '歩兵': [('ほへい', None, ALWAYS)], '洒落': [('しゃれ', None, ALWAYS)],
    '荒野': [('こうや', None, ALWAYS)], '鬼神': [('きしん', None, ALWAYS)],
    # A frame decides: にも拘らず, 止めを刺す, 気色の悪い, 細々とした, 大人気ない, 灰燼に帰す, 初心な.
    '拘る': [('かかわる', r'(?<!こと)に(?:も|さえ)?$', r'(?:わ?ら)?ず', 'and'), ('こだわる', None, ALWAYS)],
    '止め': [('とどめ', None, r'[をは](?:刺|射|さ[しすさせ])|の一撃|とばかり')],
    '気色': [('きしょく', None, r'[がの]?(?:悪|わる|ワル|[ッっ]悪)')],
    '細々': [('こまごま', None, r'と?した')],
    '大人気': [('おとなげ', None, r'(?:な|無)[いくかけさ]')],
    '帰す': [('きす', r'(?:灰燼|水泡|烏有|無|失敗|徒労|手中)[』」]?[にと]$', None)],
    '初心': [('うぶ', r'(?<!の)$', r'(?:な(?!い)|だ|で(?!は)|じゃ|すぎ|過ぎ|そう|っぽ|同)', 'and')],
    '如何': [('いかん', None, r'せん|とも|に(?:かかわ|拘|関わ|よ[っらりるれ])'),
           ('いかが', r'(?:ては|れば)$', r'(?!ほど|に)', 'and'), ('いかが', None, r'(?:です|でしょ|でした|でござ|なさ|いたし|致し|か[なね？?])')],
    # Glaring misreads in bare post-war text (Opus labels of sampled bare occurrences, T221).
    '仇': [('かたき', r'(?:親|父|母|兄|姉|弟|妹|主君|主|仲間|友|家族|師匠|師|妻|夫|娘|息子)の$', None),
           ('かたき', None, r'を(?:取|と[っらりるれろ]|討|う[たちつてっ]|打)|討ち')],
    '擦れる': [('かすれる', r'声[がはも]$', None), ('かすれる', None, r'た(?:声|音|囁|小声|悲鳴|吐息)')],
    '盛り': [('さかり', r'(?:かわいい|可愛い|やりたい|遊びたい|食べたい|育ち|働き|伸び|花の|今が)$', None)],
    '類': [('たぐい', r'(?:の|そんな|こんな|あんな|その|この|あの|どの)$', r'(?!を見|稀|まれ|い稀|い希|がな)', 'and')],
    '痛': [('いた', None, r'[っッ…‥]|たた|てて')],
    # 一文 as one token is a sentence, いちぶん, unless money is meant (一文も出さない, 一文の得にもならない); 一|文: MODEL_FIX.
    '一文': [('いちぶん', r'(?<!銭)$', _NOT_MONEY, 'and')],
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
                 # Bare post-war text, not shown: a minority reads them as Sudachi does (T200).
                 ('呆ける', 'ぼける'): 'ほうける', ('艶やか', 'あでやか'): 'つややか', ('正しく', 'まさしく'): 'ただしく',
                 # Sudachi reads a bare 被る こうむる by its neighbours (帽子を被る ok, 罪を被る not): かぶる unless a cue
                 # reads こうむる (CONTEXT_RULES; books' ruby where Sudachi says こうむる: かぶる 192, こうむる 22) (T371).
                 ('被る', 'こうむる'): 'かぶる',
                 # A word Sudachi has as a name only (T170, T261)
                 ('未来人', 'みきと'): 'みらいじん',
                 # Fantasy's ground dragon: books' ruby ちりゅう (T277), Sudachi and the list じりゅう.
                 ('地竜', 'じりゅう'): 'ちりゅう',
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
                 ('札', 'さつ'): 'ふだ', ('民', 'みん'): 'たみ', ('綿', 'めん'): 'わた', ('痕', 'こん'): 'あと',
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
                 ('数百', 'すーひゃく'): 'すうひゃく',
                 # 鬼 alone is おに; glued (善鬼 ぜんき, 餓鬼) it keeps Sudachi's き (GLUED_CHECKED).
                 ('鬼', 'き'): 'おに',
                 # Nominated by Opus's readings of post-war library sentences (Sudachi's reading where Opus
                 # gives another one, 3+ authors, 80%+ one reading), checked on Tatoeba B1 (TRADEOFFS T45).
                 ('擦る', 'する'): 'こする', ('素', 'もと'): 'す',
                 # A reading extra-readings.tsv adds: books' ruby is いれずみ 187 times in 2,500 books, しせい once.
                 ('刺青', 'しせい'): 'いれずみ',
                 # 分別 alone is good sense; sorting waste is a context rule (ゴミの分別 ぶんべつ).
                 ('分別', 'ぶんべつ'): 'ふんべつ',
                 # The stage's side is a context rule (舞台の下手, 上手と下手); Sudachi's しもて elsewhere is
                 # 下手をすれば, 下手に動く (TRADEOFFS T61).
                 ('下手', 'しもて'): 'へた',
                 # Left out of default-readings.tsv for want of Tatoeba cases (T34); training-author library ruby:
                 # 咽喉 のど 448 of 449, 空地 あきち 40 of 43.
                 ('咽喉', 'いんこう'): 'のど', ('空地', 'くうち'): 'あきち',
                 # Post-war bare text (TRADEOFFS T103): 妃 alone きさき
                 # (glued it keeps ひ: 王妃, 第四妃), 素 alone す (素に戻る; glued そ: 元素).
                 ('妃', 'ひ'): 'きさき', ('素', 'そ'): 'す',
                 # Glaring in bare post-war text, not shown (Opus labels of sampled bare occurrences, T221):
                 # 殿 after a name or title (村長殿; not after a number, DEFAULT_KEEP), 樽 and 宴 on their own (glued they keep Sudachi's).
                 ('軽々', 'けいけい'): 'かるがる',
                 ('高名', 'こうみょう'): 'こうめい', ('敵同士', 'かたきどうし'): 'てきどうし', ('殿', 'でん'): 'どの',
                 ('樽', 'そん'): 'たる', ('宴', 'えん'): 'うたげ', ('身体中', 'しんたいじゅう'): 'からだじゅう',
                 # Sudachi's ひける (can play) of 弾ける is mostly はじける in bare post-war text (24 of 30, 泡が弾ける);
                 # ひける after an instrument is a context rule (T241).
                 ('弾ける', 'ひける'): 'はじける',
                 # 宿す is やどす in modern text (瞳に宿した); しゅくす is Sudachi's reading of 宿する (WRONG_LEMMA, T280).
                 ('宿す', 'しゅくす'): 'やどす'
}

# Phrases Reader._idioms shows (each kanji token's slice, as a rule): training-author ruby agrees with the slices
# 97%+ of 10+ times (tools/shown_idioms.py, T435)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shown-idioms.tsv'), encoding='utf-8') as _f:
    SHOWN_IDIOMS = frozenset(line.split('\t')[0] for line in _f if line.strip() and not line.startswith('#'))

# Defaults shown as furigana (source 'rule'): right 97%+ where they fire in training-author post-war books' ruby
# (n >= 20) or, for rarer forms, in every sampled bare occurrence checked by hand (T320). A one-character one only on its
# own: not glued (glued), nor before katakana (他クラス た).
SHOWN_DEFAULTS = frozenset({
    ('他', 'ほか'), ('身体', 'からだ'), ('明後日', 'あさって'), ('一昨日', 'おととい'), ('隙', 'すき'), ('胡坐', 'あぐら'),
    ('鶏肉', 'とりにく'), ('箱', 'はこ'), ('民', 'たみ'), ('咽喉', 'のど'), ('間近', 'まぢか'),
    ('手近', 'てぢか'), ('卑怯者', 'ひきょうもの'), ('三日月', 'みかづき'), ('痕', 'あと'), ('正気', 'しょうき'),
    ('鼻血', 'はなぢ'), ('敵同士', 'てきどうし'), ('数百', 'すうひゃく'), ('綿', 'わた'), ('昼飯', 'ひるめし'),
    ('啄木鳥', 'きつつき'), ('喘息', 'ぜんそく'), ('高名', 'こうめい'), ('宿す', 'やどす'),
    # Bare text, not ruby, is the evidence for these (authors ruby わたくし, ゆう where they mean it): 39/39, 40/40 (T430)
    ('私', 'わたし'), ('言う', 'いう')})


def _table_defaults(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default-readings.tsv')) -> dict:
    """default-readings.tsv: the readings human ruby gives instead of Sudachi's, mined from NDL's
    Aozora corpus and checked on Tatoeba by tools/default_readings.py (身体 しんたい → からだ), for
    words not glued to others (see glued)."""
    with open(path, encoding='utf-8') as f:
        rows = [line.rstrip('\n').split('\t') for line in f if not line.startswith('#')]
    return {(form, sudachi): reading for form, sudachi, reading, *_ in rows}


DEFAULT_READINGS = {**_table_defaults(), **HAND_DEFAULTS}

# Rule forms whose model readings are wrong too often to show as furigana (training-author library ruby: 開く 66%,
# 注ぐ 69%, 弾く 32%, 堪える 58%, 辛い 66% right; plain DEV: 7 of 13 wrong): the model's reading is kept with
# source 'dictionary' (TRADEOFFS T150). Their rules' readings are still shown.
MODEL_UNSHOWN = frozenset({'開く', '空く', '止める', '注ぐ', '堪える', '弾く', '辛い'})
# Words whose top listed reading (Jiten) is shown like dominant-readings.tsv's, through Reader._dominant's guards:
# the next reading is 100+ times rarer and no item read otherwise on B1, B2, dev-silver, silver-modern or postwar NDL (T444).
# Not 他 た, 訳 やく, 夜 よ, 元, 今: as lopsided in the list, wrong in context. Not shown after a noun, prefix or verb
# stem (Reader._dominant): お得 とく, 発達し得る うる, 白身魚 ざかな.
TOP_READINGS = {'僕': 'ぼく', '魚': 'さかな', '体': 'からだ', '妹': 'いもうと', '役': 'やく', '得る': 'える',
                # the list's other readings only respell the word (きずく, ちかずく, はっやい, しやわせ, おまい)
                '気づく': 'きづく', '近づく': 'ちかづく', '早い': 'はやい', '幸せ': 'しあわせ', 'お前': 'おまえ'}
# Model readings that are wrong most of the time, or in a frame (training-author library ruby where the model gives
# them: 何時 なんじ 9%, 何故 なにゆえ 20%, 件 くだり 53%, 等 ら 53% right; bare text agrees but for 何時).
# Not context rules: a rule form loses its model. (form, the model's reading) -> [(text before, text after, the reading given, shown)]: the first entry
# whose patterns (None: any) match the text around the word applies; none: the model's reading (T250).
PRONOUNS_RA = {'あいつ', 'こいつ', 'そいつ', 'アイツ', 'コイツ', 'ソイツ', '貴様', 'きさま', '俺', 'おれ', 'オレ', 'お前', 'おまえ', 'オマエ',
               'お主', 'てめえ', 'てめぇ', 'てめー', 'テメエ', 'テメー', '手前', '諸君', '僕', 'ぼく', 'ボク', '私', 'わたし', 'ワタシ', '我',
               'われ', 'ワレ', '彼', '彼奴', '其方', 'そなた', 'あんた', 'アンタ', 'あなた', '貴方', 'わし', 'ワシ', '儂', 'あたし', 'アタシ',
               'あっし', 'おいら', 'オイラ', '君', 'きみ', '自分', '貴兄', '貴下', '我々', '奴', 'やつ', 'ヤツ', 'それ', 'これ', 'あれ', '子供', '子ども', '小僧', '娘'}
_JITSU_VERB = r'(?:言|い[うえわっいお]|云|申|あげ|挙げ|上げ|もって|以て|見出|見いだ)'  # 実を言うと, 実を挙げる: じつ
_OWN_FAMILY = r'の(?:お?[父母]|親|両親|子|娘|息子|兄|姉|弟|妹|家族|祖父|祖母|孫|叔父|叔母|伯父|伯母|パパ|ママ)'
# 何時 before か, しか, だって, でも, になく, 、 or a verb (何時か必ず, 何時帰った; not 今何時か, 何時起き): いつ;
# the model's なんじ is right in bare text elsewhere (何時に起きる, 今何時だ, 何時ぐらい), though authors ruby 何時 mostly where it is いつ.
MODEL_FIX = {('何時', 'なんじ'): [(r'(?:今|いま)[、は]?$', None, 'なんじ', True),  # 今何時か分かる
                             (None, r'(?:か(?!な|しら|ら|い[。？?！!」]|ね)|しか|だって|でも|ぞや|の日|にな[くっ]|になれ|にも|以来|ぶり|、|(?:だった|じゃった)か'
                                    r'|(?!起き)[㐀-䶿一-鿿々](?<![頃間]))', 'いつ', True)],
             ('何故', 'なにゆえ'): [(None, None, 'なぜ', False)], ('件', 'くだり'): [(None, None, 'けん', False)],
             # 等 after a pronoun or a person (あいつ等, 貴様等, 子供等): ら; after other nouns など or とう.
             ('等', 'ら'): [(words(PRONOUNS_RA) + '$', None, 'ら', True), (None, None, 'など', False)],
             # 一|文: a sentence (その一文, 一文だけ), not money (一文も, 一文の得).
             ('文', 'もん'): [(r'(?<![〇一二三四五六七八九十百千万銭])一$', _NOT_MONEY, 'ぶん', True)],
             # 術 glued after a kanji or katakana noun is a technique (護衛術, 変身術, スピン術); not 他術 (他に術はない).
             ('術', 'すべ'): [(r'[ァ-ヺー㐀-䶿一-鿿々](?<!他)$', None, 'じゅつ', True)],
             # Xを地で行く (理想を地でいく): true to form, じ (T275).
             ('地', 'ち'): [(r'を$', r'で(?:い[くかきけこっ]|行(?![わなう])|ゆ[くかきけこ])', 'じ', True)],
             # 実の父, 実の娘: one's own family, じつ; み for fruit (実のなる木) (T275).
             # 実を齧る, 実をつける, 実がなる: fruit, み; 実を言うと, 実を申せば: じつ (T295).
             ('実', 'み'): [(None, _OWN_FAMILY, 'じつ', True), (None, 'を' + _JITSU_VERB, 'じつ', True)],
             ('実', 'まこと'): [(None, _OWN_FAMILY, 'じつ', True)],
             ('実', 'じつ'): [(r'名(?:を捨て[て、]?|より|と|か)$|を選ぶか$|[ァ-ヺー]$', None, 'じつ', True),  # 名より実を取る
                         (r'(?:この|あの)$', r'(?!に)', 'み', True), (None, r'を(?!' + _JITSU_VERB + r')|が(?!な[いくかけ]|あ|伴|上が)', 'み', True)]}
MODEL_FIX = {key: [(before and re.compile(before), after and re.compile(after), reading, shown)
                   for before, after, reading, shown in fixes] for key, fixes in MODEL_FIX.items()}

# Conjugated words take the default of the reading their surface conjugates from too (擦った すっ: 擦る こする,
# TRADEOFFS T2). Where a hand default doesn't hold, Sudachi's reading stays: (text before, text after) the word.
# Before the kana or katakana half of a compound Sudachi splits off (擦りきれる, 擦りおろす, 擦りガラス) and
# after a match (マッチを擦る: する, 燐寸 8 of 9 in books' ruby).
DEFAULT_KEEP = {'実': (re.compile(r'(?!)'), re.compile(_OWN_FAMILY)),  # 実の父: Sudachi's じつ, not み (T275)
                '殿': (re.compile(r'[一二三四五六七八九十〇]$'), re.compile(r'(?!)')),  # 一殿, 七殿: palace halls
                '擦る': (re.compile(r'(?:マッチ|燐寸|まっち|墨)を$'),
                       re.compile(r'(?:きれ|きら|ぬけ|ぬか|おろ|下ろ|へっ|へら|へり|へる|むけ|むい|こ[まみむめん]|込|ガラス|硝子|リンゴ|りんご)'))}


# Sudachi's lemma of a conjugated verb that the text around it shows is another word: {lemma: (word, before, after)},
# where the text right before matches `before` or the text right after starts with `after`.
# 雨は降り続けた, 雪も降ります, 軍門に降りなさい: 降る, not 降りる (T240, T260). Lemmas Sudachi takes where the
# modern word is another (T280): 宿する (瞳に宿した: 宿す, read やどす, HAND_DEFAULTS), 欲す (the list's ほりす;
# 欲した ほっした: 欲する), and 欲する before が (欲しがる: 欲しい).
_ALWAYS = re.compile('')
WRONG_LEMMA = {'降りる': ('降る', re.compile(f'(?:{_PRECIPITATION})|{_SURRENDER}'), re.compile(_PRECIPITATION_AFTER)),
               '宿する': ('宿す', _ALWAYS, None), '欲す': ('欲する', _ALWAYS, None),
               '欲する': ('欲しい', None, re.compile('が[らりるれろっ]'))}

# A token Sudachi reads as one word that is another here, Word per entry (surface: [(before, after the token, kanji
# span or None for the whole token, form, reading, shown)]). お話して, お話させて: 話 はなし + して (the し of
# お話しして left out); 我が主に, 主に仕える: 主 あるじ + に, not おもに; 解せない: げせない, not かいする (意味を解せない:
# かい); 平伏した: へいふく or ひれふす, not shown (T271-T274).
_AFTER_ARUJI = (r'(?:お?仕え|忠誠|忠義|従[わいうえっ]|逆ら|楯突|盾突|たてつ|歯向|刃向|はむか|牙を|拝謁|謁見|相応し|ふさわし|'
                r'捧げ|反抗|背[いくかけ])')
SPLIT_TOKENS = {'話し': [(r'お$', r'(?:て|た|ま[すせしっ]|ちゃ|と[いくけこ]|よう)', 1, '話', 'はなし', True)],
                '話さ': [(r'お$', r'(?:せ|れ)', 1, '話', 'はなし', True)],
                '主に': [(r'(?:我が|わが|我らが|われらが|我等が|己が|汝が|最愛の|亡き|なき)$', None, 1, '主', 'あるじ', True),
                         (r'(?<![一-鿿々ァ-ヺー])(?<!の)$', _AFTER_ARUJI, 1, '主', 'あるじ', True),
                         (r'の$', None, None, '主に', 'おもに', False)],  # 声の主に: ぬし or あるじ
                '解せ': [(r'(?<!を)$', r'(?:ない|なかっ|ぬ|ん|ず)', None, '解す', 'げす', True)],
                '平伏し': [(None, None, None, '平伏', 'へいふく', False)]}
# お供します, お供した, お供しよう: お + 供 とも + する, not 供する きょうする (書類を供する, 食事が供された); Sudachi joins
# お供 only before させ, できる, いたす (T370).
SPLIT_TOKENS.update({surface: [(r'(?<!御)お$', None, 1, '供', 'とも', True)]
                     for surface in ('供し', '供する', '供すれ', '供しよ', '供しよう', '供しよっ', '供しろ', '供せよ', '供さ', '供せ')})
SPLIT_TOKENS = {surface: [(before and re.compile(before), after and re.compile(after), *rest) for before, after, *rest in entries]
                for surface, entries in SPLIT_TOKENS.items()}

# 行っ that Sudachi takes for 行う (おこなっ) but is 行く (いっ), T432: going somewhere (に, へ, まで before it), with
# company or by a vehicle (二人で, 車で), eyes or understanding (目が行った, 納得が行った), coming back (行ってくる),
# back and forth (行ったり来たり), the better way or having been (行った方が, 行ったことがある), or along a path
# (先を行く, 道を行って). Not after を in the clause, but for a path or 行ったり: books' 行う is mostly 〜を行った,
# and also 〜が行った調査, 定期的に行っている.
IKU_MEANS = re.compile(r'(?:[一二三四五六七八九十何数大０-９0-9]人|ひとり|ふたり|みんな|皆|大勢|家族|友達|友人|旅行|車|バス|タクシー|'
                       r'電車|列車|徒歩|自転車|飛行機|船|新幹線)$')
IKU_AFTER = re.compile(r'て(?:く[るれ]|き|来|こ[いよ]|らっしゃ)|たり(?:来|き)|た(?:ほう|方)が|たところ|'
                       r'た(?:こと|事)(?:が|も)?(?:ある|あり|あっ|ない|なかっ|無)')
IKU_PATH = re.compile(r'(?:先|(?<![㐀-䶿一-鿿々])道|前|後ろ|最先端|先頭)を$')
IKU_IDIOM = re.compile(r'(?:目|視線|注意|納得|合点|得心|連絡|情報)が$')  # 目が行く, 納得が行く

# Joined forms the list reads one way that are a phrase of their tokens where the text after matches: 行く方が, 行く行く！
# (いく + ほう, いく + いく; not ゆくかた, ゆくゆく as in 行く方知れず, 行く行くは) (T290).
NOT_JOINED = {'行く方': re.compile(r'(?!知|し[れらりるろ])'), '行く行く': re.compile(r'(?!は)'),
              # JMdict's one reading of a phrase that books also read literally (library ruby under 90%, or the
              # literal reading common in bare text): Reader._idioms leaves them to the tokens' own readings
              **dict.fromkeys('頭を振る 頭を垂れる 頭をたれる 首を垂れる 気もない 夜が明ける 夜があける 後になる 口の端 あの娘 その様 この様 '
                              '堪えられない 朱に染まる 鈴を鳴らす 術ない 床につく 主として 主だった 主になる 主とする 身体の自由 '
                              '面目が立つ 止めになる 止めておく 目に留める 鐘の音 骨を埋める 奴さん 端ない お頭 阿呆らしい 拍手を打つ '
                              '汚れのない 夜の静寂 五葉の松 棺に納める 食わず嫌い 拳を打つ 時間の歪み 大人の玩具 汚れを知らない '
                              '何れにも 間にある 言葉が過ぎる その実 杯を重ねる 灯をつける もう先 天の下 男の娘'.split(), re.compile(''))}


# Hand defaults that, like the table's, hold only for the word on its own (露大統領 stays ろ).
GLUED_CHECKED = frozenset({('都', 'と'), ('露', 'ろ'), ('鬼', 'き'), ('種', 'しゅ'), ('妃', 'ひ'), ('素', 'そ'), ('札', 'さつ'), ('民', 'みん'), ('綿', 'めん'), ('痕', 'こん'), ('樽', 'そん'), ('宴', 'えん')})
# Glued by what comes before only: 上位種, オーク種 (しゅ), but 種選び, 種入り (たね).
GLUED_BEFORE = frozenset({('種', 'しゅ')})


CONTEXT_RULES = {form: [(reading, before and re.compile(before), after and re.compile(after), bool(both))
                         for reading, before, after, *both in rules] for form, rules in CONTEXT_RULES.items()}
