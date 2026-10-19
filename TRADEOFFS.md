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
| T1 | 何 defaults to なに/なん by the next word; なんか read なにか, and 何 before a counter missing from `cues.COUNTER` (話: 何話してる is なに) reads なに | #1 | 32 broken on half b | 439 fixed on half b | #36 took every `counters.COUNTERS` counter but 着/間 into `cues.COUNTER` (+ 単位 袋 組 頁 票 試合); 話 needs a verb guard; なんか/なにか is often the transcriber's choice |
| T2 | Conjugated words take Sudachi's surface reading when it fits the list, so Sudachi's wrong surface readings come through (開い ひらい, 辛く つらく, 上っ のぼっ) instead of no reading | #4 | ~1% of new readings on Tatoeba, ~6% on NDL; certainty stays None | 5,353 had no reading and got the right one | context rules per form (辛い: #5); certainty hygiene keeps them out of shown furigana |
| T3 | Compounds are read as one word only when the reading list has them; phrases with particles/auxiliaries or ending in kana are never joined | #9 | Jiten-list noise (行く方 ゆくかた, 時女 ときめ, 弘氏 ひろし); since #43 joins JMdict lacks are no longer shown (T41), but word lists still get them | joining phrases gave NDL 3,249 fixed / 2,406 broken | a cleaner list (JMdict pairs, #2) |
| T4 | 他 defaults to ほか (its た rule is period-justified, see below) | #10 | NDL 17, half a 3 (older text's た: 他の章) | NDL's ruby is ほか ~80% (149/189) | a た cue for formal/older text (他国, 他の + abstract nouns) |
| T5 | 下 もと only after listed nouns | #10 | NDL 6 (社会の下で, 感化の下で) | 28 fixed on NDL | widen the noun list with modern evidence. A POS cue (kanji サ変 noun + の下: 監視の下に) was tried in #46 and left out: B1, B2 and the bank have no 下 もと after の to support it, the modern miss it was meant for follows a 副詞可能 noun, and it reads 照明の下で もと |
| T6 | 白髪 defaults to しらが | #10 | NDL 2 (白髪の老紳士 はくはつ) | 3 fixed on NDL, 4/4 half a | literary/older-text cue |
| T8 | 日本 defaults to にほん (owner-approved) | #11 | にっぽん names (日本銀行, 大日本帝国) | にほん is the common reading | names/compounds keep にっぽん (default-guard agent) |
| T9 | 一歩 reads いっぽ | #15 | NDL 1 (author's ひとあし) | 一歩 いっぽ is standard | none needed (author choice) |
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
| T30 | 金 defaults to かね when no きん cue fires | #28 | metal 金 without a cue (金は高い, 金の花瓶, 金の粥) and kanji compounds Sudachi splits (奉還金, 封金, 無給金, 金紅色): B1 1, NDL tune 2, NDL report 7 | B1 +13, B2 +18, NDL +12/+7 for 金 | the split-token guard (T14, #26); more metal cues (色, 花瓶, 箔 nearby) |
| T31 | 外 is a rule form (ほか: 外の人, より外, 待つ外ない), so its model no longer answers | #28 | 目的の外は (NDL tune 1) | NDL tune +6/-1, report +3/-0 | retrain 外 on the occurrences no rule reads: its current entry, trained on all of them, reads B1 0/1 when allowed (#40) |
| T32 | 何 なに before やら/やって, に使う/について/にする, ごっこ, げない | #28 | 雪かきやら何やら (B1 1), 第二外国語は何にする (B2 1, IPAdic gold) | B1 +18, NDL +5, B2 +8 for 何 | a list cue (Xやら何やら → なん) |
| T33 | A conjugated word whose form the list lacks takes Sudachi's surface reading (泳げ およげる, 思ひ おもふ) instead of none | #23 | ~10% of these are wrong (往っ: Sudachi's lemma 往る → さる); never shown (source dictionary, certainty 0 since #33: not a listed reading), but a consumer that uses dictionary readings gets them | B1 +241, B2 +225, NDL +1,955, 0 broken | per-form checks of Sudachi's lemma (往る), JMdict pairs for the form |
| T34 | default-readings.tsv: NDL (pre-war) nominates, modern text decides; only 身体 からだ, 時 とき, 実 み, 下 した pass. Left out though NDL's ruby supports them: 都 みやこ, 露 つゆ, 側 そば, 表 おもて, 咽喉 のど, 空地 あきち, 跫音 あしおと, 画 え and ~25 more (Tatoeba has too few or mixed cases) | #25 | NDL report: those ~40 fixed/net per form stay unfixed (e.g. 露 52, 都 39, 表 39, 側 36 on the test authors); 実 じつ in older text (NDL 2 broken) | post-war target: their support is mainly pre-war text; modern 側/表 right only 6/11, 5/7 | modern evidence per pair (library ruby/silver, a post-war gold set) to admit more; 側/表 need context (川の側 そば vs 敵の側 がわ) |
| T35 | 都 alone defaults to みやこ (fiction's capital); と only with Tokyo-government cues (都の職員, 都が発表); 露 alone defaults to つゆ, ろ next to a kanji (露大統領) | #34 | news text's bare 都 (Tokyo) without a cue reads みやこ | Sudachi's と/ろ was wrong for every story use; 0 broken on any set | more government cues from news text if a modern news set appears |
| T36 | 何 before a counter that also starts a verb (歩 曲 巻 発: 何歩いてる, 何曲げてんの) reads なん; 着 and 間 are left out of `cues.COUNTER` for that reason (何着てる, 何間違えてる) | #36 | none on any set (B1, B2, bank, library ruby/silver, NDL) | B1 +1, B2 +3, NDL Meiji +1, 0 broken (何隻, 何脚, 何組, 何袋, 何単位) | a guard for a counter followed by verb okurigana, then 着/間/話 can join |
| T37 | 辛い keeps its model where no rule fires (からい from food context it learnt on Tatoeba) | #40 | NDL report: prewar fiction つらい read からい 3 (窮屈で辛い); modern library sets 0 | B1 +6/-1, B2 +5/-1 (からい food talk Sudachi read つらい) | more つらい cues (思い, 気持ち, 窮屈) or a fiction-trained 辛い entry |
| T38 | With `carry`, a name's (固有名詞 or unlisted form) hiragana ruby is taken even when unlisted, and carried to later bare occurrences of the form | #44 | flavour hiragana ruby over a name or unlisted form that isn't a listed pronoun (鈴木《おれさま》) is taken and carried; a later bare occurrence that is another person/place with the same kanji; NDL: 24 broken (all the gold's own inconsistency within a work), Aozora post-war 0 | NDL within-work 615 fixed, 1,093 ruby occurrences newly taken; Aozora post-war 33/0 | a second ruby reading stops carrying; widen `_PRONOUNS`; a kanji-spelling check for 固有名詞 the list knows cost ~170 fixes (nanori) |
| T39 | 開く after を reads ひらく; 止める after の/こと reads やめる; 空く has a すく rule only for roads and trains (お腹が空く stays with the model) | #41 | B2 1 (窓を開いたまま, IPAdic gold あ); NDL report: 眼を開いていよう あく 1, というのを止めてくれた とめる 1 (meiji) | B1 +19/-0, B2 +2/-1, NDL report +8/-1; library 0/0. お腹 → すく fixed nothing on B1 (the model already reads it) and broke 1 there on IPAdic gold, so it was left out | a cue for eyes and windows (眼/目/窓を開く: both readings), a "stop someone" cue (〜のを止めてくれた) |
| T40 | Readings Jiten ranks the same (it ranks a JMdict entry, so all its readings tie: 言う いう = ゆう) are decided by JMdict's first reading where a rank picks one (一X joins, reading_context's fallback); JMdict's order isn't frequency when neither reading is marked common, so 一X now joins 25 more forms, a few the wrong way: 一束 いっそく, 一塊 いっかい, 一声 いっせい (ひと… is usual) | #43 | B2 1 (一束) | B1 +1 (一滴), NDL meiji +3; 一人 一言 一組 一滴 get ひと…/いっ… | JMdict's priority tags (re_pri) for ties: decide only for a tied reading JMdict marks common (leaves 一束 undecided; 一声 いっせい is marked, so not that one); per-form cues |
| T41 | A joined compound (2-4 tokens) JMdict doesn't have with the list's reading is joined as before but `source='dictionary'` (not shown) | #43 | right names and places lose their furigana (浅間山, 新大阪 on Tatoeba): shown right B1 1, B2 3, bank 2, silver 1, NDL prewar 91, period 143 | wrong shown readings go (三日後 みひりあ, 利根川 さねがわ, 中古屋 なかごや, 森氏 もりうじ): shown wrong B1 −7, B2 −6, silver −1, NDL prewar −29, period −117; word list unchanged | `Reader.read(carry=)` (#44, the book's ruby on an earlier occurrence); JMnedict place names; not joining them at all fixed B1 +4, B2 +5/−1 but broke a temple name on the bank and NDL period +16/−27 |
| T42 | A single token's reading stays `only` when JMdict has no entry for the form at all (names Sudachi keeps whole: 室子 さやこ, 時女 ときめ) | #43 | Jiten's wrong name readings stay shown at 1.0 | names stay shown (owner decision, #33); JMdict has no names | `carry` (#44); JMnedict |
| T43 | A conjugated token whose lemma the list lacks but is a listed form plus kana (可愛いく: Sudachi's lemma 可愛いい) is read as that form, so its kanji take the kana (可愛 かわい) | #46 | NDL prewar 1 (ruby 可愛 かわ: an older spelling where the い is the ending) | library ruby +1; 0 broken on B1, B2, bank, silver, other NDL eras | none needed for post-war text |
| T44 | The committed public table predates the fetch fixes: it was trained on the 23 NDL test authors' Aozora ruby and pruned on all of Tatoeba half b, B2 included | #47 | NDL figures for those authors are leaky (NDL is report-only); B2 slightly optimistic | a rebuild with the fixes lost ~20 items per Tatoeba half against it (B1 9/29, B2 8/24), mostly build luck, and dropped 辛い's rule-form entry | the shared-model rebuild (queue item 6) is the first honest table |
| T48 | With no reading list, JMdict's (form, reading) pairs are the list: its one-reading forms are `only` (also joined over Sudachi's tokens), and rules and the model keep to its readings | #51 | B1 31, B2 33 broken (vs 88, 68 fixed); library modern 3 (vs 4 fixed). Mostly gold noise (数日 すうじつ, 大掃除 おおそうじ), but some real: JMdict phrases joined over the tokens (行く方 ゆくかた in 行く方がいい; お腹空く おなかがすく, whose が isn't in the surface: お腹空[なかがす]いた); 0.5 s and ~140 MB more at start | bank +9 fixed, 0 broken; shown precision 97.2 → 99.4 and coverage 3.5 → 67 % on B1; identical with a list | no compound over a verb or adjective token (tried: B1 +3, B2 +2 net, but it changes results with a list too); skip JMdict readings with kana the surface lacks |

### Period-justified

Rules and defaults whose support is mainly period or classical text (NDL's Genji and 吉川英治) but that
change nothing on the modern sets (B1, B2, library ruby/silver; round-5e data audit). Kept because they
are harmless there; new ones need majority support from post-war text (README, docs/evaluation.md).

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
| R6 | 額 had no rule: がく/ひたい left to Sudachi (was T10) | #15 | #40 + #41: a frame cue (額に入れて飾る) for がく, forehead cues (額に汗, 額を拭う) for ひたい, and the model still answers where neither fires: B1 +2 |
| R7 | 開く, 止める, 空く had no rule, because a rule switched off their model (was T29) | #28 | #40 (a rule form keeps its model where no rule fires, listed in the table's ruleForms) + #41 (the rules, see T39): B1 +19/-0; the same rules with the models off would be B1 +28/-43 |
