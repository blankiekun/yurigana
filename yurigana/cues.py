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
HALTED = frozenset({'車', 'エンジン', 'ガス', '水', '水道', '電気', '息', '血', '機械', 'タクシー', '足', '手'})

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
DURATION_BEFORE = frozenset({'あと', '後', '残り', '約', 'およそ', '最初の', '最後の', 'わずか', '僅か', 'ほんの', 'たった',
                             'ものの'})
DURATION_AFTER = frozenset({'後', 'おき', '置き', 'ごと', '毎', '以内', '足らず', 'たらず', '弱', 'ほど', '程', 'くらい', 'ぐらい',
                            'ばかり', '近く', 'ちかく', '余り', '経', 'たっ', 'たた', 'たつ', '遅れ', 'おくれ', 'かか', 'かけ', '掛'})

# People: those above someone (指導の下に, 師の下で: 下 もと), and people by role or kind (学生の方 かた).
SUPERIOR = frozenset({'先生', '師', '師匠', '上司', '親', '両親', '父母', '主君'})
PERSON = frozenset({'学生', '女性', '男性', '年寄り', '通訳', '家族', '患者', '客'})
# What a person is described by: 担当の方, 経験の方, 初心の方.
ROLE = frozenset({'担当', '係', '係り', '窓口', '受付', '年配', '高齢', '専門', '教徒', '出身', '経験', '初心'})

# Authority, conditions and circumstances one is under: 指導の下に, 条件の下で (下 もと).
ABSTRACT = frozenset({'指導', '監督', '支配', '管理', '統治', '指揮', '命令', '条件', '体制', '制度', '方針', '影響',
                      '庇護', '保護', '名', '法', '旗', '約束', '前提', '協力', '仮定', '環境', '状況', '状態', '気候'})

# Sound makers whose sound is ね (琴の音, 虫の音). 笛 needs a guard (汽笛, 霧笛, 警笛) and stays in rules.
INSTRUMENT = frozenset({'琴', '箏', '筝', '琵琶', '三味線', '尺八', '胡弓', '弦', '絃'})
INSECT = frozenset({'虫'})

FOOTWEAR = frozenset({'靴', 'くつ', 'クツ', '靴下', '草鞋', 'わらじ', '下駄', '足袋', 'スニーカー', 'ブーツ', 'サンダル',
                      'スリッパ', '草履'})


def words(*classes) -> str:
    """The classes' words (or single words) as a non-capturing regex alternation, longest first."""
    union = set().union(*({c} if isinstance(c, str) else c for c in classes))
    return '(?:' + '|'.join(re.escape(w) for w in sorted(union, key=lambda w: (-len(w), w))) + ')'
