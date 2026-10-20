"""Named word classes the context rules (readings._CONTEXT_RULES) share as cues.

A class is a frozenset of plain words. A rule turns classes into a regex alternation with
`words` (words(INSTRUMENT, INSECT) + 'の$': after 琴の, 虫の), so one list feeds every rule
that needs, say, a place. Words that need a guard (笛 but not 汽笛) stay in the rule as regex.

Add a word to the class it belongs to, not to one rule: every rule using the class gets it, so
check the rules that use it (grep the class name) and evaluate before and after.
"""
import re

# Stretches of time: 一日中, 一年中, 今夜中 (中 じゅう). 一日 and 年 need guards (十一日, 今年) and stay in rules.
TIME_SPAN = frozenset({'今日', '明日', '一晩', '一夜', '今夜', '一年', '今年', '春', '夏', '秋', '冬', '一生'})
NIGHT = frozenset({'夜', '深夜'})

# Places, by kind; rules take the kinds that fit (世界中 じゅう but not 人気がない after 世界).
REALM = frozenset({'世界', '日本', '国'})
SETTLEMENT = frozenset({'町', '街', '村', '島'})
BUILDING = frozenset({'家', '屋敷', '城', 'ホテル', '学校', '会社', '館', '駅'})
ROOM = frozenset({'部屋', '室', '廊下'})
GROUNDS = frozenset({'庭', '園', '森', '林', '浜', '港', '広場', '駐車場', '墓場'})
STREET = frozenset({'通り', '路地'})  # 道 needs a guard (海道) and stays in rules
VICINITY = frozenset({'辺り', 'あたり', '周囲', '周り', '付近', '近所', 'そこら', 'そこいら'})
PLACE = REALM | SETTLEMENT | BUILDING | ROOM | GROUNDS | STREET | VICINITY

BODY = frozenset({'体', '身体', 'からだ'})

# Places with opening hours: 店が開いてますか, 図書館は開いてる (開く あく).
OPEN_HOURS = frozenset({'店', 'お店', '図書館', '銀行', '郵便局', '病院', '博物館', '美術館', 'デパート', 'スーパー', '駐車場'})
# Roads and transport that are empty or crowded: 道が空いている (空く すく). 道 needs a guard (海道) and stays in rules.
TRAFFIC = frozenset({'道路', '電車', 'バス'})
# Machines and flows one stops: エンジンを止める, 息を止める (止める とめる).
HALTED = frozenset({'車', 'エンジン', 'ガス', '水', '水道', '電気', '息', '血', '機械', 'タクシー', '足', '手', '動き', '動作', '時',
                    '時間', '呼吸', '箸', '歩み', '心臓', '鼓動', '出血', '流れ', '再生', '震え', '指'})
# Instruments one plays (ピアノを弾く: 弾く ひく); 弦 and 琴線 are plucked (はじく), so not INSTRUMENT.
PLAYED = frozenset({'ピアノ', 'ギター', 'バイオリン', 'ヴァイオリン', 'チェロ', '琴', '箏', '三味線', 'ハープ', 'リュート', 'オルガン',
                    '鍵盤', '曲', '楽器', 'ベース', 'キーボード', 'メロディ', '旋律', 'ソナタ', 'エレキ', '伴奏', 'ワルツ', 'ウクレレ',
                    '竪琴', '琵琶', 'マンドリン', 'フレーズ', 'クラシック', 'アコーディオン'})
# Things tied or wound that one undoes (紐を解く, 髪を解く: 解く ほどく); 帯, 荷, 包み are mixed in books' ruby.
TIED = frozenset({'紐', 'リボン', '髪', '結び目', '糸', 'ネクタイ', '三つ編み', '包帯', '腕', '手', '指', '縄', '鎖', '靴紐', '風呂敷'})
# Harm and favour one suffers or receives (被害を被る, 恩恵を被る: 被る こうむる).
SUFFERED = frozenset({'恩恵', '被害', '損害', '損失', 'ダメージ', '迷惑', '打撃', '影響', '不利益', '損', '罰', '天罰', '災難', '災い',
                      '嫌疑', '汚名', '痛手', '恩', '苦痛'})

# Family and rank words a name-like 君 follows as ぎみ (尼君, 姫君, 母君).
KIN_TITLE = frozenset({'尼', '姫', '婿', '姉', '妹', '兄', '弟', '若', '母', '父'})
# Terms and sessions 今 is こん before (今学期, 今年度, 今シーズン).
TERM = frozenset({'学期', '年度', '世紀', '大会', '会期', '国会', '場所', '季', '期', 'シーズン', '次', '般', '定例', '上半期',
                  '下半期'})
# Generic people and things, "the other ..." after 外の (外の人, 外の方法: 外 ほか).
PEOPLE = frozenset({'人', '者', '女', '男', '子', '児', '客', '乗客', 'お客', '連中', '奴', '子供', '子ども', '生徒', '兵', '仲間',
                    '家族', '兄弟', '姉妹', '誰'})
THINGS = frozenset({'もの', '物', '事', 'こと', '話', '仕事', '用事', '方法', '手段', '理由'})
# Kana stems and phrases before 入る read いる (ながめ入る, 郷に入っては); kanji + kana stems stay a regex in the rule.
IRU_STEM = frozenset({'ながめ', 'おそれ', 'いたみ', '郷に', '虎穴に'})
# Metals and the like near 金 make it the metal, きん. 銀 needs a guard (銀行) and stays in the rule.
METAL = frozenset({'鉄', '銅', '鉛', '錫', 'プラチナ', '白金', '金属', '宝石', 'ダイヤ'})

# Words around a length of time, before it (あと十分, 約十分) and after it (十分後, 十分ほど, 十分おき):
# they make 十分 minutes, not じゅうぶん. 前, 間 and あまり need guards (前後, 間に合う, あまりに) and stay in rules.
# Few and only (ほんの十分, たった一行), and the first or last one (最初の十分, 最後の一行).
FEW = frozenset({'わずか', '僅か', 'ほんの', 'たった', 'ものの'})
EDGE = frozenset({'最初の', '最後の'})
DURATION_BEFORE = frozenset({'あと', '後', '残り', '約', 'およそ'}) | FEW | EDGE
DURATION_AFTER = frozenset({'後', 'おき', '置き', 'ごと', '毎', '以内', '足らず', 'たらず', '弱', 'ほど', '程', 'くらい', 'ぐらい',
                            'ばかり', '近く', 'ちかく', '余り', '経', 'たっ', 'たた', 'たつ', '遅れ', 'おくれ', 'かか', 'かけ', '掛'})

# People: those above someone (指導の下に, 師の下で: 下 もと), and people by role or kind (学生の方 かた).
SUPERIOR = frozenset({'先生', '師', '師匠', '上司', '親', '両親', '父母', '主君'})
PERSON = frozenset({'学生', '女性', '男性', '年寄り', '通訳', '家族', '患者', '客', '助手', '連れ', '警察官', '警備員', '係員', '職員',
                    '店員', '医師', '看護師', '運転手', '王族', '貴族', '旅', '初対面', '近所', 'ファン', '一般', '上司',
                    '代表', '関係者', '責任者', '目上', '年上'})
# What a person is described by: 担当の方, 経験の方, 初心の方.
ROLE = frozenset({'担当', '係', '係り', '窓口', '受付', '年配', '高齢', '専門', '教徒', '出身', '経験', '初心'})

# Authority, conditions and circumstances one is under: 指導の下に, 条件の下で (下 もと).
ABSTRACT = frozenset({'指導', '監督', '支配', '管理', '統治', '指揮', '命令', '条件', '体制', '制度', '方針', '影響',
                      '庇護', '保護', '名', '法', '旗', '約束', '前提', '協力', '仮定', '環境', '状況', '状態', '気候'})

# Sound makers whose sound is ね (琴の音, 虫の音). 笛 needs a guard (汽笛, 霧笛, 警笛) and stays in rules.
INSTRUMENT = frozenset({'琴', '箏', '筝', '琵琶', '三味線', '尺八', '胡弓', '弦', '絃'})
INSECT = frozenset({'虫'})

# Society and the age: 今日の社会 (こんにち), 明日の日本 (あす); issues of the moment: 目下の課題 (もっか).
SOCIETY = frozenset({'社会', '経済', '時代', '文明', '科学', '技術', '教育', '政治', '未来', '地球'})
ISSUE = frozenset({'状況', '情勢', '問題', '課題', '急務', '懸案'})
# Work under way: 目下調査中, 目下検討 (もっか).
ACTIVITY = frozenset({'調査', '検討', '準備', '交渉', '捜査', '審議', '開発', '建設', '進行', '継続', '捜索', '修理', '工事'})

# Praise for a person: 素敵な方です, 立派な方 (方 かた).
PRAISE = frozenset({'素敵', 'すてき', '立派', 'りっぱ', '有名', '親切', '優秀', '上品', '気さく', '偉い', 'えらい', '素晴らしい',
                    'すばらしい', '優しい', 'やさしい'})
# What a customer or visitor does, after お/ご: ご利用の方, お越しの方 (方 かた).
CUSTOMER_ACT = frozenset({'希望', '利用', '来場', '越し', '持ち', '住まい', '参加', '申し込み', '申込み'})
# Trades and walks of life whose temperament 気質 is, かたぎ: 職人気質, 学生気質.
OCCUPATION = frozenset({'職人', '商人', '芸人', '役者', '書生', '学生'})

# Counters 何 is なん before (何年, 何冊, 何曜, 何単位): every one-kanji counter of counters.COUNTERS (tests check it).
# Those that start verbs (何着てる, 何話してる, 何間違えてる: なに) are guarded in readings._VERB_AFTER_NANI.
COUNTER = (frozenset('年冊日番時匹台杯分周段箱点画便号名回人度月週歳個枚本階倍頭泊足軒件通語十百千万億兆曜秒'
                     '発版編歩曲巻対羽円銭隻艘寸尺升貫脚町丁列畳晩粒坪袋組頁票着間話')
           | {'試合', '単位'})

# Food: spicy dishes (カレーが辛い: からい), fresh produce sold at a market (魚の市場: いちば).
DISH = frozenset({'カレー', '料理', 'スープ', 'ラーメン', '唐辛子', 'わさび', 'キムチ', '味', '味付け', 'ソース'})
PRODUCE = frozenset({'魚', '青物', '野菜', '果物'})
# Things with a rim (縁 ふち): カップの縁, 皿の縁.
VESSEL = frozenset({'カップ', 'グラス', 'コップ', '茶碗', '皿', '鍋', '器'})
# Jewellery and medals made of gold: 金の指輪 (金 きん).
JEWELRY = frozenset({'ネックレス', '指輪', '腕輪', '首飾り', '冠', 'メダル'})

# What one holds in the arms (赤ん坊を抱く, 肩を抱く: 抱く だく), with PEOPLE and BODY; feelings take いだく.
HUGGED = frozenset({'赤ん坊', '赤ちゃん', '赤子', '我が子', '娘', '息子', '孫', '猫', '子猫', '犬', '子犬', '人形', 'ぬいぐるみ',
                    '枕', 'クッション', '籠', '膝', '肩', '両肩', '腰', '私', '僕', '俺', 'あたし', '彼女', '彼', '妻', '夫',
                    '背中', '腕', '自分', 'お前', 'あなた', '少女', '少年', '母', '父', '妹', '姉', '弟', '兄', '恋人', '袋', '箱',
                    '卵'})
# Those who serve a master (奴隷と主, 従者の主: 主 あるじ).
SERVANT = frozenset({'奴隷', '従者', '家来', '家臣', '召使い', '召使', 'しもべ', '下僕', '使い魔', '眷属', '従僕', 'メイド',
                     '執事', '騎士'})

FOOTWEAR = frozenset({'靴', 'くつ', 'クツ', '靴下', '草鞋', 'わらじ', '下駄', '足袋', 'スニーカー', 'ブーツ', 'サンダル',
                      'スリッパ', '草履'})


def words(*classes) -> str:
    """The classes' words (or single words) as a non-capturing regex alternation, longest first."""
    union = set().union(*({c} if isinstance(c, str) else c for c in classes))
    return '(?:' + '|'.join(re.escape(w) for w in sorted(union, key=lambda w: (-len(w), w))) + ')'
