# How yurigana reads a word

The steps, in order, and the rules behind them. Trade-offs of each rule are in [TRADEOFFS.md](../TRADEOFFS.md).

## The order of readings

With a reading list, 2-4 adjacent tokens whose joined form the list gives one reading
become one `Word` with that reading (`source='only'`): 三|日|月 みかづき, 身の上|話
みのうえばなし, 一|石|二鳥 いっせきにちょう, 昼|時 ひるどき. Spans with particles or ending in
kana are left out (Jiten's list has phrases such as 彼の かの), as are a number with its
counter (一|枚), spans right after a number (１|日|中), dates (四|月|一日 isn't わたぬき) and spans
with ruby. 一 + one token is joined only for a ひと…/いっ… reading, the sound change the split
misses (一|思い ひとおもい, 一|票 いっぴょう; the list's いち… there is mostly names, 一章 かずあき),
also when the list ranks that reading 3+ times above its others (一|重 ひとえ, `source='default'`).
A joined form JMdict doesn't have with that reading (mostly names and list noise: 三|日|後
みひりあ, 利根|川 さねがわ) is still joined, as `source='dictionary'`. Forms of 3+ characters
the list doesn't give one reading are joined too: one the list lacks with JMdict's only reading
(羅甸|語 らてんご, 水|餃子 すいぎょうざ, `source='only'`), and one whose top-ranked reading the
list ranks 3+ times above its others, its top rank shared only by spellings of that reading
(力|尽く ちからずく, 須弥|山 しゅみせん, 三|日|月 みかづき = みかずき; `source='default'`). Not
over a verb or adjective token (入り|方 isn't いりがた), not over a number but for such a ranked
form of 3+ tokens (二十|年 isn't JMdict's はたとせ), and not when Sudachi's tokens already read
the span a way the list gives. Two-kanji forms aren't joined this way: in book ruby they were
mostly other words or names (家|中 いえじゅう, 日|南 ひなみ). A list like Jiten's ranks
words, not readings, so the readings of one word share a rank (言う いう = ゆう, 頭 あたま =
かしら); wherever the rank picks a reading, readings tied at the top are decided by JMdict's
order (its first kana reading), else not at all (`yomitan.preferred`).
Splits of words Sudachi doesn't keep whole get DEFAULT_READINGS (below) on their joined
readings: 一昨|日 いっさくひ → おととい, 一|日中 いちにっちゅう → いちにちじゅう. A lone 一 before
the kana rest of a native word is ひ/ひと/いっ (一ト月, 一と息, 一しずく, 一たい), and ひと before
a verb's stem (一睨み). Otherwise each token is read on its own; the first step that gives a
reading wins:

1. **The book's ruby** (`ruby_reading`): ruby over the token, as one span or kanji by kanji
   (人《ひと》気《け》 gives ひとけ); ruby over the kanji stem of an inflected word, with the
   lemma's okurigana added (行《い》った is 行く read いく); ruby set in large kana, as older
   books do (いつしよ gives いっしょ).
2. **A context rule** (`context_reading`): about 65 forms whose reading depends on the
   words around them (人気, 今日, 明日, 上手, 市場, 金, 方, 間, 何, 今, 外, 気に入る いる, 尼君 ぎみ, カナダ人 じん,
   表に出る おもて, 館の主 あるじ, 赤ん坊を抱く だく, ローズ家 け, 佐藤家 け (after Sudachi's surname tag), 侯爵家 け,
   すぐ側 そば, この後 あと, この前 まえ, その場に留まる とどまる, 感情を露にする あらわ, 鍋の素 もと, 間に割って入る あいだ,
   上手に じょうず, 上手と下手 かみて/しもて, あのお方 かた, 教えてくださった方 かた, 、後に知る のち, しかる後 のち,
   表世界 おもて, 主の命令 あるじ, 陛下の下へ もと, 上の階 かい, いい画だ え, 目を擦る こする,
   攻撃を弾く はじく, 紐を解く ほどく, 涙を堪える こらえる, 被害を被る こうむる, ため息を吐く つく, 辛くなる つらい …), in
   `readings._CONTEXT_RULES`.
   人気がない is にんき as often as ひとけ, so it is ひとけ only with a cue (人気がない場所,
   周囲に人気がない); この店は人気がない stays にんき. 何 is なに before a counter kanji that
   starts a verb when the verb's okurigana follow (何着てる, 何話してる, 何間違えてる, 何歩いてる),
   なん before the counter itself (何着か, 何話まで, 何歩くらい) and in Xやら何やら. 銀杏 is ぎんなん
   with food cues (銀杏を焼く, 茶碗蒸しの銀杏, 銀杏の実), 大文字 だいもんじ for Kyoto's bonfire
   (京都の大文字, 大文字焼き, 大文字の送り火), 分別 ぶんべつ for sorting waste (ゴミの分別, 分別して出す);
   otherwise their defaults below (いちょう, おおもじ, ふんべつ).
3. **The reading model** (`ReadingModel`): a small naive Bayes classifier per form, over
   the two tokens on each side, their pairs and the content words within six tokens of the
   line. It answers only when its best reading's posterior is at least 0.7. A form that has
   rules gets a model only where it read better than Sudachi on the held-out occurrences no
   rule fires on (it is trained on those too); the table lists such forms (`ruleForms`), and
   an entry for a rule form that isn't listed is ignored.
4. **Sudachi's reading** of the token, for an unconjugated word. For a conjugated one
   (行っ, 言わ, 早く), with a reading list: the one listed reading of its form that conjugates
   to Sudachi's reading of the surface (行っ read いっ is 行く いく, not ゆく; 来 read き or こ
   is くる), when exactly one does (`readings.conjugated_reading`, `source='dictionary'`).
   When the list has no reading for the form at all (potential 泳げる, ら抜き 来れる, 文語 思ふ,
   悲し) or there is no list: Sudachi's reading of the stem plus the form's okurigana
   (`readings.unlisted_reading`, `source='dictionary'`, certainty None).
   A few of Sudachi's readings that are almost always wrong in modern text are replaced
   (`readings.DEFAULT_READINGS`, `source='default'`): 私 わたくし → わたし, 言う ゆう → いう,
   富士山 ふじやま → ふじさん, 鶏肉, 今日 こんにち, 明後日. They were chosen on Tatoeba's half a:
   each fixes 10+ occurrences there and is right 90%+ of the times it changes a reading.
   日本 にっぽん → にほん is the exception: Tatoeba's machine gold keeps にっぽん often enough
   to miss that bar, but the human ruby of the NDL test set almost never uses it.
   鼻血, 間近, 手近 and 近々 get ぢ, the spelling of their rendaku (Sudachi writes じ).
   A second batch (箱 ばこ → はこ, 深い ぶかい, 腹 ふく, 沿い そい, 仏 ふつ, 米 べい,
   鏡 きょう and 27 more) uses a lower bar on half a and B1 together: 2+ net fixes, 90%+
   right, and no more breaks than fixes on NDL's held-out authors. 一日 as one token
   (Sudachi's ついたち) is いちにち except after 月 or 月初め (来月の一日, 月初めの一日, a context rule); 一塊
   いっかい → ひとかたまり; 分別 ぶんべつ → ふんべつ (good sense; sorting waste is a rule, above).
   擦る する → こする and 素 もと → す were nominated by Opus's readings of post-war library
   sentences (where Opus reads a word otherwise than Sudachi in 3+ sentences by 3+ authors and 80%+
   of the time the same way) and checked on Tatoeba B1 (2 changes, both right); TRADEOFFS T45.
   A few more come from `yurigana/default-readings.tsv`, built by `tools/default_readings.py`:
   human readings of public-domain fiction (NDL's huriganacorpus-aozora, training authors only)
   nominate pairs that Sudachi's dictionary lacks or ranks low, and modern text (Tatoeba's half
   a and B1) must carry each one alone at the same 90% bar: 身体 しんたい → からだ, 時 じ → とき,
   実 じつ → み, 下 もと → した. Readings only older text uses (都 みやこ, 側 そば, 表 おもて) stay
   out. The table is not used for a one-kanji affix next to kanji or digits or after katakana
   (今学期, 3位, ダウンロード時); the hand-picked ones above win over it.
   Where Sudachi's reading of a word of 3+ characters is one voicing away from the one the
   list gives it, the list's is taken (睡眠不足 ふそく → ぶそく, `source='only'`).
   金 きん → かね: alone, 金 is money unless a rule finds the metal (銀 or 鉄 nearby, 金のくさり,
   金の値段). Four of Sudachi's dictionary entries carry a particle or extra kana in their
   reading and are cut back to the word: 中宮 ちゅうぐうの, 河原 かわらの, 甲斐 かいの, 土堤 どてい.
   下手 しもて → へた (the stage's side is a rule: 舞台の下手, 上手と下手). 鬼 き → おに, but not glued to a kanji like the table's (善鬼 ぜんき). 日本 is にほん in
   Sudachi's longer tokens too (日本一, 日本の伝統, 北日本), unless the reading list gives the
   form only with にっぽん (日本銀行, 日本男児). 気味 is ぎみ right after a noun or a verb's 連用形
   (風邪気味, 太り気味, a context rule).

Then, for every reading but ruby, its voicing follows its place (rendaku, `_voicing`), with
a reading list. Sudachi splits many compounds (プレハブ|小屋, 縮緬|細工) and gives the second
part's plain reading, and gives some words its voiced reading even alone (この箱 ばこ, 一番深い
ぶかい). A noun right after a compound's first part (a noun ending in kanji or katakana; not
a number or counter, an adverbial noun or a prefix: 今|風呂, お|菓子) is voiced when the list's
one-reading compounds ending in it read it voiced at least 4 times in 5, and 5 times
(小屋: 犬小屋 いぬごや, 山小屋 …; 細工; not 川 or 方, whose compounds are mixed); otherwise
it keeps its reading. Anywhere else, a reading Sudachi voiced is unvoiced when the list gives
only the plain one (箱 はこ). Lyman's law holds (a reading with a voiced obstruent, かぜ, never
voices) and names keep their readings. A voiced reading (小屋 ごや) is not itself in the
list: fold voicing to look it up there.

## Numbers and counters

Sudachi gives a number and its counter as separate tokens with fixed readings (三/さん +
本/ぽん), so `read` also gives one `Word` per number + counter span with the reading of the
whole, `source='counter'` and certainty None: `Word(start, end, '三本', 'さんぼん', 'counter', None)`.
It comes just before the tokens' own Words, which stay: the counter's Word gets the
counter's plain reading (本 ほん) for word lists, with `source='counter'` too (never `only`:
the plain reading is not how it reads there). Ruby over any part of the span wins: no
span Word then. Words Sudachi keeps whole (一人, 二十歳, 十分 じゅうぶん, 何本, 一日 ついたち
after a month) are its own, except names (三軒 みのき, 一列 かずなみ) and words it reads without
the sound change (一回 いちかい), which get the span's reading; 三十分 (三 + 十分) and 二十人 are
read as numbers. A number alone gets the same readings (六百 ろっぴゃく, 三千
さんぜん; Sudachi reads them digit by digit), as `source='counter'`; a written 一千 is いっせん
(一千万 いっせんまん).

The readings follow standard counter grammar (`yurigana/counters.py`, as in Wiktionary's
[Japanese counters appendix](https://en.wiktionary.org/wiki/Appendix:Japanese_counters)):
numbers in kanji (三十五, 一九九九), digits (35, ３５) and 何, 幾, 何十/百/千/万, with

| | readings |
|---|---|
| gemination of 1, 6, 8, 10, 100 before k and h, of 1, 8, 10 before s and t (h becomes p) | 一本 いっぽん, 六回 ろっかい, 八杯 はっぱい, 十冊 じゅっさつ, 百個 ひゃっこ, 一対 いっつい |
| voicing after 3, 何, 千, 万 | 三本 さんぼん, 何匹 なんびき, 三階 さんがい, 三軒 さんげん, 三足 さんぞく, 何分 なんぷん |
| h counters | 本 匹 杯 発 泊 版 編 分 歩 (minutes; 四分 よんぷん; 分 read ぶん, as in 三分の一, stays ぶん unless の goes on with a word: 徒歩１０分の距離 ふん, but 十分の じゅうぶん) |
| 分 as a tenth | ぶ in pairs (五分五分, 七分三分, 五分と五分), after 割/寸/両 (三割五分) and before 咲き/目/通り (三分咲き) |
| k counters | 個 回 階 軒 件 曲 巻 箇所 か月 (ヶ月, カ月, 箇月) 貫 脚 間 (けん; 三間 さんげん, not 二間 ふたま; 一間 ひとま next to a room or lodging word: 六畳一間, 一間の部屋, 一間を借りる) |
| s, t counters | 冊 歳/才 足 週 週間 銭 周 隻 艘 寸 尺 升 (三寸 さんずん, 三尺 さんじゃく, 三升 さんじょう); 対 点 頭 通 着 町 丁 |
| ひと, ふた for 1, 2 | 晩 粒 坪 (一晩 ひとばん, 二粒 ふたつぶ; 三晩 さんばん) |
| 羽 | わ, ば after 3/何/千, っぱ after 6, 8, 10, 100 |
| no sound change | 枚 台 度 番 倍 秒 名 円 年 年間 時 時間 人 列 畳 分目 (八分目 はちぶんめ) 話 (episodes: 第三話 さんわ) |
| 4, 7, 9 | よん, なな, きゅう; 時, 時間 よ, しち, く; 人 よ, しち; 円, 年, 畳 よ; 月 し, しち, く |
| days (日, 日間) | ついたち after 月, else いちにち; ふつか … とおか, じゅうよっか, はつか, にじゅうよっか, 十七日 じゅうしちにち |
| others | 一人 ひとり, 二人 ふたり, 二十歳 はたち, 月 がつ only as a month name (1-12, 何); two consecutive digits are "two or three" (二三日 にさんにち, 三四日 さんよっか, 四五人 しごにん), but a year after an era name (昭和二三年 にじゅうさんねん; 明治 大正 昭和 平成 令和 元禄) |

Where usage varies one reading is given: 8 geminates (はっぽん, not はちほん), 10 is じゅっ
(not じっ), 七人 しちにん. 一対一 (one on one) is left alone, and numbers with a point or
a comma are skipped.

`tests/test_counters.py` holds the acceptance grid: 1-10, 100, 1000 and 何, in kanji and
in digits, with 29 counters, written by hand from the grammar.

Tatoeba is not a fair test here: its readings come from MeCab + IPAdic and were mostly left
as they were, so they read the parts on their own (一匹 いち + ひき, ２杯 はい). On half b
(Jiten's list, the benchmark's span aligner, じっ = じゅっ), the 2,530 occurrences a counter
span covers go from 89.1% to 90.2% micro and 71.0% to 81.4% macro (all 72,838: 87.3% →
87.4% micro, 81.5% → 82.0% macro): 62 fixed, 32 worse, and all 32 are transcriptions
that keep the parts' own readings (三階 かい, 一本 いち) or split 二十歳 (はたち doesn't).

## The flavour rule

Books use ruby for flavour as well as for readings: マジ over 本気, スキル over 異能, そら
over 宇宙. Such ruby is never a reading:

- katakana ruby;
- ruby containing kanji;
- gikun or any reading the list doesn't give for the form (with no list: a reading not
  spelled by the kanji's own readings);
- ruby over part of a compound (魚《うお》市場).

## Names across a book

Books give a name's reading with ruby once, on its first appearance; later it stands bare and
Sudachi guesses (大谷 おおや for おおたに, invented names). `reader.read(text, hints, carry={})`
carries the book's ruby over a name to its later bare occurrences, as source `book`: pass `{}`
for a whole book in one text, or the same dict to each of a book's texts in order. A name is a
固有名詞 token or a form the list doesn't know (not a number); its hiragana ruby is taken even
when the list lacks the reading (nanori, invented readings: 信雄 のぶかつ), except pronouns
(鈴木《あいつ》); ruby over a two-token full name is split where Sudachi's reading of one part
fits (姫野芽衣《ひめのめい》: ひめの + めい). Common words are never carried (hiragana ruby once
isn't assumed for a heteronym's later bare occurrences), and a form stops being carried after
ruby over it that isn't taken (flavour, katakana) or that gives a second reading. Without
`carry`, nothing changes.

## Certainty

`source` and `certainty`:

| source | certainty |
|---|---|
| `ruby`, `book`, `rule`, `only` | 1.0 |
| `model` | the model's posterior for its reading (0.7 or more) |
| `default`, `counter` | None |
| `dictionary` | for a form the model has a table entry for: the share of that reading in the entry's prior; else None |

Whatever the source (but `ruby`), a reading the list doesn't give for the form (Sudachi's
reading of a word the list lacks, or reads otherwise) has certainty 0, and a reading that
isn't hiragana or ー (Sudachi's reading of a word it doesn't know is the word's own kanji, 於)
is None. Loanword readings keep ー (ラーメン屋 らーめんや): fine in a word list, never shown
(the list's reading of such a word is katakana, so it is never `only`). To show furigana
only where they are likely right, show `ruby`, `rule`, `model` and `only`.

Certainty is not calibrated. A ruby reading is the book's own, a rule reading what the rule
says; the model's posterior is a naive Bayes posterior, which is overconfident, and the only
calibration behind it is the 0.7 threshold, chosen because 0.5 changed hand-checked plain
sentences Sudachi had right. The dictionary value is a base rate, not a judgement of the
sentence. Use it to sort or flag, not as a probability.

## Cue words

The word lists the rules look for are shared, named classes in `yurigana/cues.py`: `PLACE`
(made of `REALM`, `SETTLEMENT`, `BUILDING`, `ROOM`, `GROUNDS`, `STREET`, `VICINITY`), `TIME_SPAN`,
`NIGHT`, `BODY`, `PERSON`, `ROLE`, `SUPERIOR`, `ABSTRACT`, `INSTRUMENT`, `INSECT`, `FOOTWEAR`,
`DURATION_BEFORE`, `DURATION_AFTER` (十分 as minutes, `counters.TEN_MINUTES_*`), `KIN_TITLE` (君 ぎみ), `TERM` (今 こん),
`PEOPLE`, `THINGS` (外の… ほか), `IRU_STEM` (…入る いる), `METAL` and `JEWELRY` (金 きん), `FEW` and `EDGE`
(ほんの/最初の: 十分 as minutes, 一行 いちぎょう), `SOCIETY`, `ISSUE` and `ACTIVITY` (今日 こんにち, 明日, 目下 もっか),
`PRAISE` and `CUSTOMER_ACT` (方 かた), `OCCUPATION` (気質 かたぎ), `COUNTER` (何 なん), `DISH` (辛い からい),
`PRODUCE` (市場 いちば), `VESSEL` (縁 ふち), `OPEN_HOURS` (開く あく),
`TRAFFIC` (空く すく), `HALTED` (止める とめる), `HUGGED` (抱く だく), `SERVANT` (主 あるじ), `PLAYED` (弾く ひく),
`TIED` (解く ほどく), `SUFFERED` (被る こうむる).
A class is a frozenset of plain words; `cues.words(...)` turns classes (and single words) into a
regex alternation for a rule:

```python
'音': [('ね', '(?:' + words(INSTRUMENT, INSECT, 'ぐう') + r'|(?<![霧汽警])笛)の$', None)],
'中': [('じゅう', words(TIME_SPAN, REALM, BUILDING - {'館', '駅'}) + '$', None)],
```

A rule takes the classes that fit it and leaves out, with `-`, the members that read wrong
there (駅中 is えきなか). Words that need a regex guard (笛 but not 汽笛) stay in the rule.
To add a word, put it in its class, not in one rule: every rule using the class gets it, so
grep the class name and evaluate (`--compare`) before and after.
