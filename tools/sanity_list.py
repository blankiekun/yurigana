"""Builds eval/sanity.tsv, the regression list tests/test_sanity.py checks (README, "The sanity
list"). Run once to make the list; after that the TSV is edited by hand (waivers, new rows), so
don't rerun it over a list with hand edits.

  python -I tools/sanity_list.py jpn_transcriptions.tsv.bz2 JMdict_e.gz [--rank jiten_freq_global.zip]

- frequent: forms of Tatoeba's half a (reviewed transcriptions, fetch_tatoeba.py's split) read
  one way 90%+ of MIN_COUNT+ times, the TOP most frequent by --rank (a Yomitan frequency list,
  used only to order the forms), else by their count in half a. Expected: JMdict's only reading
  with a priority tag (re_pri) for the form, else half a's majority. One half-a sentence each,
  not right after a number (Tatoeba's gold has no counter sound changes), with the word in its
  dictionary form where one has it (without a reading list, Reader gives conjugated words none).
- counter: number × counter, written by hand from standard grammar (COUNTERS), in a template
  sentence each; alts where usage varies.
- convention: words with two standard readings (CONVENTIONS), alts for the other.
- probe: numbers with counters in real half-a sentences (PROBES), readings by hand.

Rows the current Reader() gets wrong are marked xfail, with its reading in the note.
Tatoeba (CC BY 2.0 FR): https://downloads.tatoeba.org/exports/per_language/jpn/; JMdict (EDRDG,
CC BY-SA 4.0): http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz.
"""
import argparse
import bz2
import gzip
import io
import os
import re
import sys
from collections import Counter, defaultdict
from xml.etree import ElementTree

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)

from tests.test_sanity import COLUMNS, outcome  # noqa: E402
from yurigana import Reader, __version__, aozora_text, ruby_reading  # noqa: E402
from yurigana.fetch_tatoeba import half_of, to_aozora  # noqa: E402
from yurigana.kana import HAS_KANJI, to_hiragana  # noqa: E402
from yurigana.reader import _Any  # noqa: E402
from yurigana.tokens import SudachiTokenizer  # noqa: E402

OUT = os.path.join(ROOT, 'eval', 'sanity.tsv')
TOP, MIN_COUNT, MIN_SHARE = 500, 10, 0.9
NUMERAL = re.compile(r'[0-9０-９一二三四五六七八九十百千万何数幾]')

# number → its reading before a counter is the counter's business; per counter, the readings of
# 一 二 三 四 五 六 七 八 九 十 百 千 何 + counter ('' = not used), alternatives after '/'.
NUMBERS = '一二三四五六七八九十百千何'
COUNTERS = {
    '本': ('鉛筆を{}買った。', 'いっぽん にほん さんぼん よんほん ごほん ろっぽん ななほん はっぽん/はちほん きゅうほん '
          'じゅっぽん/じっぽん ひゃっぽん せんぼん なんぼん'),
    '匹': ('庭に猫が{}いる。', 'いっぴき にひき さんびき よんひき ごひき ろっぴき ななひき はっぴき/はちひき きゅうひき '
          'じゅっぴき/じっぴき ひゃっぴき せんびき なんびき'),
    '杯': ('コーヒーを{}飲んだ。', 'いっぱい にはい さんばい よんはい ごはい ろっぱい ななはい はっぱい/はちはい きゅうはい '
          'じゅっぱい/じっぱい ひゃっぱい せんばい なんばい'),
    '階': ('事務所はビルの{}にある。', 'いっかい にかい さんがい/さんかい よんかい ごかい ろっかい ななかい はっかい/はちかい '
          'きゅうかい じゅっかい/じっかい ひゃっかい せんかい/せんがい なんがい/なんかい'),
    '個': ('りんごを{}食べた。', 'いっこ にこ さんこ よんこ ごこ ろっこ ななこ はっこ/はちこ きゅうこ じゅっこ/じっこ '
          'ひゃっこ せんこ なんこ'),
    '回': ('その映画を{}見た。', 'いっかい にかい さんかい よんかい ごかい ろっかい ななかい はっかい/はちかい きゅうかい '
          'じゅっかい/じっかい ひゃっかい せんかい なんかい'),
    '冊': ('図書館で{}借りた。', 'いっさつ にさつ さんさつ よんさつ ごさつ ろくさつ ななさつ はっさつ/はちさつ きゅうさつ '
          'じゅっさつ/じっさつ ひゃくさつ/ひゃっさつ せんさつ なんさつ'),
    '歳': ('息子は{}になった。', 'いっさい にさい さんさい よんさい ごさい ろくさい ななさい/しちさい はっさい きゅうさい '
          'じゅっさい/じっさい ひゃくさい  なんさい'),
    '分': ('駅まで{}かかった。', 'いっぷん にふん さんぷん よんぷん ごふん ろっぷん ななふん/しちふん はっぷん/はちふん '
          'きゅうふん じゅっぷん/じっぷん ひゃっぷん せんぷん なんぷん'),
    '人': ('部屋に{}いた。', 'ひとり ふたり さんにん よにん ごにん ろくにん ななにん/しちにん はちにん きゅうにん/くにん '
          'じゅうにん ひゃくにん せんにん なんにん'),
    '日': ('来月の{}に会おう。', 'ついたち ふつか みっか よっか いつか むいか なのか/なぬか ようか ここのか とおか '
          '  なんにち'),
    '月': ('弟は{}に生まれた。', 'いちがつ にがつ さんがつ しがつ ごがつ ろくがつ しちがつ はちがつ くがつ じゅうがつ '
          '  なんがつ'),
    '時': ('毎朝{}に起きる。', 'いちじ にじ さんじ よじ ごじ ろくじ しちじ/ななじ はちじ くじ じゅうじ   なんじ'),
    '枚': ('紙を{}使った。', 'いちまい にまい さんまい よんまい ごまい ろくまい ななまい/しちまい はちまい きゅうまい '
          'じゅうまい ひゃくまい せんまい なんまい'),
    '台': ('駐車場に車が{}ある。', 'いちだい にだい さんだい よんだい ごだい ろくだい ななだい/しちだい はちだい きゅうだい '
          'じゅうだい ひゃくだい せんだい なんだい'),
    '足': ('靴を{}買った。', 'いっそく にそく さんぞく/さんそく よんそく ごそく ろくそく ななそく はっそく/はちそく '
          'きゅうそく じゅっそく/じっそく ひゃくそく せんぞく/せんそく なんぞく/なんそく'),
    '軒': ('通りに家が{}ある。', 'いっけん にけん さんげん/さんけん よんけん ごけん ろっけん ななけん はっけん/はちけん '
          'きゅうけん じゅっけん/じっけん ひゃっけん せんげん/せんけん なんげん/なんけん'),
    '着': ('シャツを{}買った。', 'いっちゃく にちゃく さんちゃく よんちゃく ごちゃく ろくちゃく ななちゃく '
          'はっちゃく/はちちゃく きゅうちゃく じゅっちゃく/じっちゃく ひゃくちゃく せんちゃく なんちゃく'),
    '点': ('テストで{}取った。', 'いってん にてん さんてん よんてん ごてん ろくてん ななてん はってん/はちてん '
          'きゅうてん じゅってん/じってん ひゃくてん せんてん なんてん'),
    '頭': ('牧場に牛が{}いる。', 'いっとう にとう さんとう よんとう ごとう ろくとう ななとう はっとう/はちとう '
          'きゅうとう じゅっとう/じっとう ひゃくとう せんとう なんとう'),
    '羽': ('空を鳥が{}飛んでいる。', 'いちわ にわ さんわ/さんば よんわ/よんば ごわ ろくわ/ろっぱ ななわ はちわ/はっぱ '
          'きゅうわ じゅうわ/じゅっぱ/じっぱ ひゃくわ/ひゃっぱ せんわ/せんば なんわ/なんば'),
    '週間': ('旅行は{}続いた。', 'いっしゅうかん にしゅうかん さんしゅうかん よんしゅうかん ごしゅうかん ろくしゅうかん '
            'ななしゅうかん はっしゅうかん/はちしゅうかん きゅうしゅうかん じゅっしゅうかん/じっしゅうかん '
            'ひゃくしゅうかん せんしゅうかん なんしゅうかん'),
    '年': ('東京に{}住んだ。', 'いちねん にねん さんねん よねん ごねん ろくねん ななねん/しちねん はちねん '
          'きゅうねん/くねん じゅうねん ひゃくねん せんねん なんねん'),
    '円': ('全部で{}だった。', 'いちえん にえん さんえん よえん ごえん ろくえん ななえん はちえん きゅうえん じゅうえん '
          'ひゃくえん せんえん なんえん'),
    '度': ('彼には{}言った。', 'いちど にど さんど よんど ごど ろくど ななど/しちど はちど きゅうど じゅうど ひゃくど '
          'せんど なんど'),
}
# Outside the grid: dates and durations that don't fit it.
EXTRA_COUNTERS = [
    ('来月の二十日に会おう。', '二十日', 'はつか', ''),
    ('来月の十四日に会おう。', '十四日', 'じゅうよっか', ''),
    ('仕事に一日かかった。', '一日', 'いちにち', ''),
    ('仕事に百日かかった。', '百日', 'ひゃくにち', ''),
    ('娘は二十歳になった。', '二十歳', 'はたち', 'にじゅっさい|にじっさい'),
    ('一つください。', '一つ', 'ひとつ', ''),
    ('二つください。', '二つ', 'ふたつ', ''),
    ('九つください。', '九つ', 'ここのつ', ''),
]

# (sentence, span, reading, alts): both readings are standard.
CONVENTIONS = [
    ('明日は雨が降るだろう。', '明日', 'あした', 'あす'),
    ('明日また来ます。', '明日', 'あした', 'あす'),
    ('今日はとても暑い。', '今日', 'きょう', ''),
    ('今日の日本では珍しくない。', '今日', 'こんにち', 'きょう'),
    ('日本に行きたい。', '日本', 'にほん', 'にっぽん'),
    ('日本の夏は暑い。', '日本', 'にほん', 'にっぽん'),
    ('昨日は忙しかった。', '昨日', 'きのう', 'さくじつ'),
    ('昨日、駅で彼に会った。', '昨日', 'きのう', 'さくじつ'),
    ('今年の冬は寒い。', '今年', 'ことし', 'こんねん'),
    ('今年は海外へ行くつもりだ。', '今年', 'ことし', 'こんねん'),
    ('一昨日、雨が降った。', '一昨日', 'おととい', 'おとつい|いっさくじつ'),
    ('一昨日の新聞を読んだ。', '一昨日', 'おととい', 'おとつい|いっさくじつ'),
    ('皆、元気です。', '皆', 'みんな', 'みな'),
    ('皆で歌を歌った。', '皆', 'みんな', 'みな'),
    ('家に帰りたい。', '家', 'いえ', 'うち'),
    ('彼の家は大きい。', '家', 'いえ', 'うち'),
    ('他に質問はありますか。', '他', 'ほか', 'た'),
    ('他の人に聞いてください。', '他', 'ほか', 'た'),
    ('私は学生です。', '私', 'わたし', 'わたくし'),
    ('私の名前は田中です。', '私', 'わたし', 'わたくし'),
]

# (Tatoeba id, span, reading, alts): counters in half a's own sentences (filled in by hand).
PROBES = [
    (2912714, '何人', 'なんにん', ''),
    (6705562, '三人', 'さんにん', ''),
    (430408, '一人', 'ひとり', ''),
    (123072, '二人', 'ふたり', ''),
    (2349192, '四人', 'よにん', ''),
    (2520543, '五人', 'ごにん', ''),
    (81671, '一冊', 'いっさつ', ''),
    (2062302, '三冊', 'さんさつ', ''),
    (109290, '十冊', 'じゅっさつ', 'じっさつ'),
    (91679, '何冊', 'なんさつ', ''),
    (124790, '五分', 'ごふん', ''),
    (169479, '三分', 'さんぷん', ''),
    (3162657, '何分', 'なんぷん', ''),
    (5021684, '一匹', 'いっぴき', ''),
    (1037828, '二匹', 'にひき', ''),
    (107712, '三匹', 'さんびき', ''),
    (187316, '何匹', 'なんびき', ''),
    (149134, '一台', 'いちだい', ''),
    (10984813, '三台', 'さんだい', ''),
    (2976139, '一回', 'いっかい', ''),
    (148147, '何回', 'なんかい', ''),
    (11027758, '千回', 'せんかい', ''),
    (148437, '一本', 'いっぽん', ''),
    (202876, '三本', 'さんぼん', ''),
    (232190, '何本', 'なんぼん', ''),
    (75827, '二本', 'にほん', ''),
    (11014036, '十本', 'じゅっぽん', 'じっぽん'),
    (10138169, '何杯', 'なんばい', ''),
    (4740, '一枚', 'いちまい', ''),
    (188631, '何枚', 'なんまい', ''),
    (935927, '十歳', 'じゅっさい', 'じっさい'),
    (1116409, '三歳', 'さんさい', ''),
    (5325, '何歳', 'なんさい', ''),
    (10979890, '四歳', 'よんさい', ''),
    (89482, '一足', 'いっそく', ''),
    (11502811, '何足', 'なんそく', 'なんぞく'),
    (163509, '五階', 'ごかい', ''),
    (1749320, '二階', 'にかい', ''),
    (10901816, '三階', 'さんがい', 'さんかい'),
    (11013892, '一階', 'いっかい', ''),
    (11065678, '何階', 'なんがい', 'なんかい'),
    (79611, '六頭', 'ろくとう', ''),
    (12146470, '何頭', 'なんとう', ''),
    (10682237, '二十歳', 'はたち', ''),
]


def half_a(path: str) -> list:
    """(id, Aozora-style text) of half a's reviewed transcriptions, as fetch_tatoeba.py keeps them."""
    sentences = []
    for line in bz2.open(path, 'rt', encoding='utf-8'):
        parts = line.rstrip('\n').split('\t')
        if len(parts) == 5 and parts[1] == 'jpn' and re.fullmatch(r'[\w.-]+', parts[3] or '-') and parts[3]:
            if half_of(int(parts[0])) == 'a':
                sentences.append((int(parts[0]), to_aozora(parts[4])))
    return sentences


def gold(sentences) -> tuple:
    """form → Counter of gold readings; form → [(id, plain text, surface, reading)] usable sentences."""
    tokenizer, known = SudachiTokenizer(), _Any()
    counts, candidates = defaultdict(Counter), defaultdict(list)
    for sid, marked in sentences:
        hints = []
        text = aozora_text(marked, None, hints).strip()
        hint_at = {start: (end, reading) for start, end, reading in hints}
        for token in tokenizer.tokens(text):
            surface, form = token.surface(), token.dictionary_form()
            if not HAS_KANJI.search(surface):
                continue
            reading = ruby_reading(hint_at, token.begin, surface, form, known)
            if not reading:
                continue
            counts[form][reading] += 1
            if text.count(surface) == 1 and not NUMERAL.match(text[token.begin - 1:token.begin] or ' '):
                candidates[form].append((sid, text, surface, reading))
    return counts, candidates


def priority_readings(path: str) -> dict:
    """form → JMdict's readings with a priority tag (re_pri) that go with it."""
    xml = re.sub(rb'<re_inf>&(\w+);', rb'<re_inf>\1', gzip.open(path).read())
    found = defaultdict(set)
    for _, entry in ElementTree.iterparse(io.BytesIO(xml)):
        if entry.tag != 'entry':
            continue
        forms = [k.findtext('keb') for k in entry.iter('k_ele')]
        for r in entry.iter('r_ele'):
            if r.find('re_pri') is None or r.find('re_nokanji') is not None:
                continue
            restr = {x.text for x in r.iter('re_restr')}
            reading = to_hiragana(r.findtext('reb'))
            for form in forms:
                if not restr or form in restr:
                    found[form].add(reading)
        entry.clear()
    return found


def frequent_rows(tatoeba: str, jmdict: str, rank_path: str | None) -> list:
    counts, candidates = gold(half_a(tatoeba))
    priority = priority_readings(jmdict)
    rank = {}
    if rank_path:
        from yurigana.yomitan import entries
        for term, _, value in entries(rank_path):
            rank[term] = min(value, rank.get(term, value))
    forms = [f for f, c in counts.items() if sum(c.values()) >= MIN_COUNT and c.most_common(1)[0][1] >= MIN_SHARE * sum(c.values())]
    forms.sort(key=lambda f: (rank.get(f, float('inf')), -sum(counts[f].values()), f))
    rows = []
    for form in forms:
        majority, n = counts[form].most_common(1)[0]
        only = priority.get(form, set())
        reading, by = (next(iter(only)), 'JMdict') if len(only) == 1 else (majority, 'majority')
        chosen = sorted((c for c in candidates[form] if c[3] == reading), key=lambda c: (c[2] != form, len(c[1]) < 8, len(c[1]), c[0]))
        if not chosen:
            continue
        sid, text, surface, _ = chosen[0]
        total = sum(counts[form].values())
        rows.append([text, surface, reading, '', 'frequent', '',
                     f'tatoeba {sid}; {by}; half a {majority} {n}/{total}'])
        if len(rows) == TOP:
            break
    return rows


def counter_rows() -> list:
    rows = []
    for counter, (template, readings) in COUNTERS.items():
        assert len(readings.split(' ')) == len(NUMBERS), counter
        for number, cell in zip(NUMBERS, readings.split(' ')):
            if cell:
                reading, *alts = cell.split('/')
                if number == '七' and reading.startswith('なな') and 'しち' + reading[2:] not in alts:
                    alts.append('しち' + reading[2:])  # しち is the older reading, still heard
                rows.append([template.format(number + counter), number + counter, reading, '|'.join(alts), 'counter', '', ''])
    rows += [[s, span, r, alts, 'counter', '', ''] for s, span, r, alts in EXTRA_COUNTERS]
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tatoeba', help="Tatoeba's jpn_transcriptions.tsv.bz2")
    parser.add_argument('jmdict', help='JMdict_e.gz')
    parser.add_argument('--rank', help='a rank-based Yomitan frequency list, to order the frequent forms')
    args = parser.parse_args()
    by_id = dict(half_a(args.tatoeba))
    rows = frequent_rows(args.tatoeba, args.jmdict, args.rank) + counter_rows()
    rows += [[s, span, r, alts, 'convention', '', ''] for s, span, r, alts in CONVENTIONS]
    for sid, span, reading, alts in PROBES:
        text = aozora_text(by_id[sid], None, []).strip()
        rows.append([text, span, reading, alts, 'probe', '', f'tatoeba {sid}'])
    reader = Reader()
    for row in rows:
        passes, got = outcome(reader, dict(zip(COLUMNS, row)))
        if not passes:
            row[5] = 'xfail'
            row[6] = '; '.join(filter(None, [row[6], f'{__version__} gives {got}']))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('# Regression list, see README "The sanity list". Tatoeba sentences CC BY 2.0 FR (see NOTICE).\n')
        f.write('\t'.join(COLUMNS) + '\n')
        f.writelines('\t'.join(row) + '\n' for row in rows)
    print(Counter((r[4], r[5] or 'pass') for r in rows))


if __name__ == '__main__':
    main()
