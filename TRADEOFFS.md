# Trade-offs

Every change to how yurigana reads breaks a few items to fix more. This file records each trade-off that
was accepted, what it costs, and the way out, so it can be resolved later instead of forgotten.

Each PR that changes readings adds its trade-offs here (or marks one resolved) in the same PR. Costs are
items broken on the evaluation sets (`python -m yurigana.evaluate --compare`), word list %: B1/B2 are
Tatoeba's halves (MeCab+IPAdic gold, noisy), NDL is the NDL huriganacorpus-aozora held-out authors (human
ruby). Forms and numbers only.

## Open

| id | trade-off | from | cost | why accepted | way out |
|---|---|---|---|---|---|
| T1 | 何 defaults to なに/なん by the next word; なんか read なにか, and 何 before counters not in `COUNTERS` (割, 種類, 単位, 話, 袋) read wrong | #1 | 32 broken on half b | 439 fixed on half b | add those counters (隻 came in #18); なんか/なにか is often the transcriber's choice |
| T2 | Conjugated words take Sudachi's surface reading when it fits the list, so Sudachi's wrong surface readings come through (開い ひらい, 辛く つらく, 上っ のぼっ) instead of no reading | #4 | ~1% of new readings on Tatoeba, ~6% on NDL; certainty stays None | 5,353 had no reading and got the right one | context rules per form (辛い: #5); certainty hygiene keeps them out of shown furigana |
| T3 | Compounds are read as one word only when the reading list has them; phrases with particles/auxiliaries or ending in kana are never joined | #9 | Jiten-list noise (行く方 ゆくかた, 時女 ときめ, 弘氏 ひろし) | joining phrases gave NDL 3,249 fixed / 2,406 broken | a cleaner list (JMdict pairs, #2) |
| T4 | 他 defaults to ほか (its た rule is period-justified, see below) | #10 | NDL 17, half a 3 (older text's た: 他の章) | NDL's ruby is ほか ~80% (149/189) | a た cue for formal/older text (他国, 他の + abstract nouns) |
| T5 | 下 もと only after listed nouns | #10 | NDL 6 (社会の下で, 感化の下で) | 28 fixed on NDL | widen the noun list or a POS cue (abstract noun + の下で) |
| T6 | 白髪 defaults to しらが | #10 | NDL 2 (白髪の老紳士 はくはつ) | 3 fixed on NDL, 4/4 half a | literary/older-text cue |
| T8 | 日本 defaults to にほん (owner-approved) | #11 | にっぽん names (日本銀行, 大日本帝国) | にほん is the common reading | names/compounds keep にっぽん (default-guard agent) |
| T9 | 一歩 reads いっぽ | #15 | NDL 1 (author's ひとあし) | 一歩 いっぽ is standard | none needed (author choice) |
| T10 | 額 has no rule: がく/ひたい left to Sudachi | #15 | NDL 16, B1 1, bank 1 not fixed | a rule form switches off its model where no rule fires: NDL +16/-7 | after #5 (model where no rule fires) |
| T11 | 下手 しもて only with stage/river cues | #15 | ずっと下手 (worse vs stage-left) | no safe cue | none (genuinely ambiguous) |
| T12 | 方 かた person cues are Tatoeba-style (担当の方, 立派な方です) | #16 | rarely fire in fiction | no breaks on NDL | cues from literary text; 方 after an attributive verb (できる方は) needs meaning |
| T13 | 後 のち/うしろ and 中 うち have no rule | #16 | NDL ~10-20 | 後に → のち broke 56 on B1 | context model; most NDL cases are author ruby choices |
| T14 | Defaults fire on a token Sudachi split off a compound or name | #17 | NDL 9 (仏華, 腹立声, 神札箱, 管内視鏡) | 70 fixed on the held-out NDL half | a split-token guard (default-guard agent) |
| T15 | 銀杏 いちょう, 大文字 おおもじ defaults | #17 | ぎんなん, だいもんじ uses read wrong | data 9/0 and 7/0 | context cues (食べる/焼く → ぎんなん; 送り火/京都 → だいもんじ) |
| T17 | Left out of #17: 分別 ふんべつ (breaks ゴミの分別 ぶんべつ), 鬼 おに (name 善鬼), 表 おもて (71%), 側 そば, 気味 ぎみ, 階 | #17 | their misreads stay | each failed the bar | context rules (分別 after ゴミ/ごみ → ぶんべつ; 気味 after a noun/stem → ぎみ) and the split-token guard |
| T18 | A number + counter in one token is read as a counter even for any 人名 (a character called 三間) | #18 | names like 三軒 みのき read as counters | was already so for surnames; fixes 一回, 一列 | name evidence from the book (ruby) wins |
| T19 | Two consecutive kanji digits are "two or three" (二三日 にさんにち) | #18 | era years (昭和二三年) | rare | skip after an era name (昭和 平成 明治 大正 令和) |
| T20 | 一間 is read いっけん (length) | #18 | ひとま (one room) | no cue yet | context (部屋, 座敷 → ひとま) |
| T21 | A counter span Word overlaps its own tokens (三本 over 三 + 本) | #3 | word lists must skip it (chimimouryou's v7) | readings files can use it | none (consumer rule) |
| T23 | 分 as a tenth (ぶ) only with cues: pairs (五分五分), after 割/寸/両, before 咲き/目/通り | #15 | literary tenths without a cue (八分は…二分だけ) read as minutes | minutes are far more common | a cue from the sentence (another N分 nearby, no time words) |
| T22 | A bare 十分 with no minutes cue reads じゅうぶん, whether or not Sudachi splits it | #22 | 十分待った, 十分休んだ meaning ten minutes read じゅうぶん | "enough" is far more common (B1 29, B2 19, NDL 48 vs ~3 minutes) | more minute cues (counters.TEN_MINUTES_BEFORE/AFTER); 十分間に合う at a line start is split 十 + 分間 by Sudachi and still reads ふんかん |
| T24 | A split compound's second part is voiced when the list's compounds voice that tail ≥ 4 in 5 (小屋 ごや, 細工 ざいく) | #21 | NDL pairs that don't voice (袴羽織), a name + noun (先生布団); B1 8, NDL report 1 | B1 +26, NDL report +39 (display) | per-pair evidence; non-noun tails (好き, 深い) not handled yet |
| T25 | A Sudachi reading one voicing away from a 3+ character word's only listed reading takes the listed one | #21 | 投票所 じょ (list しょ; both in use) | 睡眠不足 ぶそく and similar | none (both standard) |
| T26 | 一 + one token joins when the list's only (or 3x higher ranked) reading starts with ひと/いっ (一思い, 一票, 一重 ひとえ) | #24 | 一箱 ひとはこ (いっぱこ also standard), 一茎 ひとくき (NDL いっけい), 一周忌 いっしゅうき; needs Jiten's ranks (off with a plain reading set) | B1 +53/-3, NDL full +163/-2 | per-form cues; a 和語/漢語 signal (UniDic word origin) for unlisted 一冬, 一膝, 一部屋 |
| T27 | 一日 defaults to いちにち; ついたち only after 月 / 月の | #24 | ついたち without a month cue (一日に給料が出る); 正月の一日 may misfire | ~40 errors fixed on B1 + NDL tuning half | more date cues (毎月, 朔日 context, 日付 words) |
| T28 | 一時 has no rule (いちじ / いっとき / ひととき) | #24 | NDL fiction いっとき 6 | no reliable cue; いちじ 16 | context model |
| T29 | 開く, 止める, 空く have no rule (あく/ひらく, やめる/とめる, すく/あく) | #28 | their misreads stay (B1 開く ~20, 止める ~12) | a rule form switches off its model where no rule fires: 開く B1 +13/-15, 止める B1 +7/-8, NDL +3/-5 | #5 (model where no rule fires), then cues (お腹が空く, 〜のを止める, 店が開いてますか) |
| T30 | 金 defaults to かね when no きん cue fires | #28 | metal 金 without a cue (金は高い, 金の花瓶, 金の粥) and kanji compounds Sudachi splits (奉還金, 封金, 無給金, 金紅色): B1 1, NDL tune 2, NDL report 7 | B1 +13, B2 +18, NDL +12/+7 for 金 | the split-token guard (T14, #26); more metal cues (色, 花瓶, 箔 nearby) |
| T31 | 外 is a rule form (ほか: 外の人, より外, 待つ外ない), so its model no longer answers | #28 | 目的の外は (NDL tune 1) | NDL tune +6/-1, report +3/-0 | #5 |
| T32 | 何 なに before やら/やって, に使う/について/にする, ごっこ, げない | #28 | 雪かきやら何やら (B1 1), 第二外国語は何にする (B2 1, IPAdic gold) | B1 +18, NDL +5, B2 +8 for 何 | a list cue (Xやら何やら → なん) |
| T33 | A conjugated word whose form the list lacks takes Sudachi's surface reading (泳げ およげる, 思ひ おもふ) instead of none | #23 | ~10% of these are wrong (往っ: Sudachi's lemma 往る → さる); never shown (source dictionary), but a consumer that uses dictionary readings gets them | B1 +241, B2 +225, NDL +1,955, 0 broken | per-form checks of Sudachi's lemma (往る), JMdict pairs for the form |
| T34 | default-readings.tsv: NDL (pre-war) nominates, modern text decides; only 身体 からだ, 時 とき, 実 み, 下 した pass. Left out though NDL's ruby supports them: 都 みやこ, 露 つゆ, 側 そば, 表 おもて, 咽喉 のど, 空地 あきち, 跫音 あしおと, 画 え and ~25 more (Tatoeba has too few or mixed cases) | #25 | NDL report: those ~40 fixed/net per form stay unfixed (e.g. 露 52, 都 39, 表 39, 側 36 on the test authors); 実 じつ in older text (NDL 2 broken) | post-war target: their support is mainly pre-war text; modern 側/表 right only 6/11, 5/7 | modern evidence per pair (library ruby/silver, a post-war gold set) to admit more; 側/表 need context (川の側 そば vs 敵の側 がわ) |
| T35 | 都 alone defaults to みやこ (fiction's capital); と only with Tokyo-government cues (都の職員, 都が発表); 露 alone defaults to つゆ, ろ next to a kanji (露大統領) | #34 | news text's bare 都 (Tokyo) without a cue reads みやこ | Sudachi's と/ろ was wrong for every story use; 0 broken on any set | more government cues from news text if a modern news set appears |

### Period-justified

Rules and defaults whose support is mainly period or classical text (NDL's Genji and 吉川英治) but that
change nothing on the modern sets (B1, B2, library ruby/silver; round-5e data audit). Kept because they
are harmless there; new ones need majority support from post-war text (README, contributing).

| rule or default | from | fires on |
|---|---|---|
| 君 ぎみ after a family or rank word | #28 | 尼君, 姫君, 母君 (Heian titles) |
| 尼 あま before 君/寺/僧/さん/御前/姿/になる | #28 | 尼君, 尼寺 |
| 音 ね after an instrument, an insect, ぐうの | #10 | 琴の音, 虫の音 |
| 中宮 ちゅうぐう (Sudachi's ちゅうぐうの) | #28 | the empress's title |
| 仏 ほとけ (Sudachi's ふつ) | #17 | 仏 alone; modern text mostly writes 仏 in compounds |
| 他 た in set phrases and as a prefix | #10 | 他の追随を許さない, 他に類を見ない, 他国 |

## Resolved

| id | trade-off | from | resolved by |
|---|---|---|---|
| R1 | Stripping る from 来る gave く over 来た/来ない/来い | `evaluate` | #15 (`surface_reading` with `after`) |
| R3 | 十分 read じゅっぷん where Sudachi split it even when it means "enough" (十分には, 将来十分見込み); じゅうぶん where Sudachi kept one token even with a minutes cue (十分足らず, あと十分) | #3 | #22: one cue set for both |
| R2 | 三軒 surname path had no effect (the dictionary Word won over the counter span) | #3 | #18 |
| R5 | 香 defaulted to か (Sudachi: こう); ruby かおり/におい was wrong either way | #17 | dropped in this PR: its support was period text (79% of its NDL items old-era, half Genji; 2 right / 5 wrong on pre-war) and, on Tatoeba, classical poems (梅が香, 色をも香をも); modern text's bare 香 is かおり or incense こう |
| R4 | 金 had no default (money 金 かね misread: B1 13, NDL 27, half a 38) | #10 | #28 (きん cues: 銀/鉄/金属 nearby, 金のくさり/モール, 金の値段; then the かね default; see T30) |
