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
| T4 | 他 defaults to ほか | #10 | NDL 17, half a 3 (older text's た: 他の章) | NDL's ruby is ほか ~80% (149/189) | a た cue for formal/older text (他国, 他の + abstract nouns) |
| T5 | 下 もと only after `cues.ABSTRACT`/`SUPERIOR` nouns (hand list plus WordNet's abstract and group nouns, PR B) | #10 | NDL ~6 (日の下, 夕月の下, 曇り空の下 もと in older text) | 28 fixed on NDL (#10), 4 more NDL + 1 library ruby with WordNet | a sky/celestial class lost (NDL tune +3/-5: 空の下 is した as often); needs period-text evidence, not a class |
| T6 | 白髪 defaults to しらが | #10 | NDL 2 (白髪の老紳士 はくはつ) | 3 fixed on NDL, 4/4 half a | literary/older-text cue |
| T8 | 日本 defaults to にほん (owner-approved) | #11 | にっぽん names (日本銀行, 大日本帝国) | にほん is the common reading | names/compounds keep にっぽん (default-guard agent) |
| T9 | 一歩 reads いっぽ | #15 | NDL 1 (author's ひとあし) | 一歩 いっぽ is standard | none needed (author choice) |
| T10 | 額 has no rule: がく/ひたい left to Sudachi | #15 | NDL 16, B1 1, bank 1 not fixed | a rule form switches off its model where no rule fires: NDL +16/-7 | after #5 (model where no rule fires) |
| T11 | 下手 しもて only with stage/river cues | #15 | ずっと下手 (worse vs stage-left) | no safe cue | none (genuinely ambiguous) |
| T12 | 方 かた person cues are Tatoeba-style (担当の方, 立派な方です) | #16 | rarely fire in fiction | no breaks on NDL | cues from literary text; 方 after an attributive verb (できる方は) needs meaning |
| T13 | 後 のち/うしろ and 中 うち have no rule | #16 | NDL ~10-20 | 後に → のち broke 56 on B1 | context model; most NDL cases are author ruby choices |
| T14 | Defaults fire on a token Sudachi split off a compound or name | #17 | NDL 9 (香台, 仏華, 腹立声, 神札箱, 管内視鏡) | 70 fixed on the held-out NDL half | a split-token guard (default-guard agent) |
| T15 | 銀杏 いちょう, 大文字 おおもじ defaults | #17 | ぎんなん, だいもんじ uses read wrong | data 9/0 and 7/0 | context cues (食べる/焼く → ぎんなん; 送り火/京都 → だいもんじ) |
| T16 | 香 defaults to か | #17 | ruby かおり/におい (already wrong before) | こう was wrong there too | literary cue for かおり |
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

## Resolved

| id | trade-off | from | resolved by |
|---|---|---|---|
| R1 | Stripping る from 来る gave く over 来た/来ない/来い | `evaluate` | #15 (`surface_reading` with `after`) |
| R3 | 十分 read じゅっぷん where Sudachi split it even when it means "enough" (十分には, 将来十分見込み); じゅうぶん where Sudachi kept one token even with a minutes cue (十分足らず, あと十分) | #3 | #22: one cue set for both |
| R2 | 三軒 surname path had no effect (the dictionary Word won over the counter span) | #3 | #18 |
| R4 | 金 had no default (money 金 かね misread: B1 13, NDL 27, half a 38) | #10 | #28 (きん cues: 銀/鉄/金属 nearby, 金のくさり/モール, 金の値段; then the かね default; see T30) |
