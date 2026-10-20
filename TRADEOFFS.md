# Trade-offs

Every change to how yurigana reads breaks a few items to fix more. This file records each trade-off that
was accepted, what it costs, and the way out, so it can be resolved later instead of forgotten. Each PR
that changes readings adds its rows here (or resolves one) in the same PR; the evidence (items fixed and
broken per set, samples, library ruby counts) stays in that PR. Forms and numbers only.

## Open

Costs are for post-war text, the target (pre-war NDL is report-only): the estimated wrong words per
typical book of ~19,000 kanji words (a form's frequency in 300 post-war books times its error rate on a
hand-checked sample of bare occurrences). "dev" is the plain DEV set (2,996 sentences from post-war
training-author books, blind Opus readings; misses × 1.3 per book). **Accept**: too cheap to be worth a
rule. **Needs work**: the way out says what would fix it.

| id | trade-off | from | post-war cost | way out |
|---|---|---|---|---|
| T1 | 何 defaults to なに/なん by the next word (なに before それ/これ/あれ and in 何から何まで); なんか read なにか | #1, #72 | ~1 (dev: 0 of 112 after #72; 何重 なにじゅう). Needs work | なんか/なにか is often the transcriber's choice |
| T2 | Conjugated words take Sudachi's surface reading when it fits the list, Sudachi's lemma included (行ったり来たり 行う, 通ってる 通る); not `only` where two listed verbs share the っ-form (T152); hand defaults apply (擦った こする) | #4, #75 | shown ~0; word list ~10 lemma errors on dev (the rest are T154's choices). Needs work | the lemma from context (たり来, に通う) |
| T3 | Compounds are joined only when the list (or JMdict, T90) reads them one way; phrases with particles or ending in kana never are | #9 | small, unmeasured (身体中 しんたいじゅう for からだじゅう). Needs work | a cleaner list; JMdict priority tags (T91) |
| T5 | 下 もと only after listed nouns (`cues.ABSTRACT`, `SUPERIOR`) and a person (pronoun, name, さん, 人/者, 仲間) + の下へ/に/で + going, serving, staying or coming near (T82) | #10, #62, #76 | ~0.1 (彼の下で, 使節団の下に戻る). Needs work | more nouns from modern text; a POS cue (監視の下に) was tried in #46 and failed |
| T6 | 白髪 defaults to しらが | #10 | <0.1 (はくはつ in narration). Accept | a literary cue |
| T8 | 日本 defaults to にほん (owner-approved) | #11 | ~0.5, both standard. Accept | names keep にっぽん |
| T9 | 一歩 reads いっぽ | #15 | ~0. Accept | – |
| T11 | 下手 しもて only with stage/river cues (T61); へた elsewhere | #15 | ~0. Accept | – |
| T12 | 方 かた only by person cues (担当の方, お方, この方は, after an honorific verb, `cues.PERSON`; a person-only quality `cues.TRAIT`, 様のような, 亡くなった) | #16, #58, #72 | ~1.5 (dev: 受けた方は かた). Needs work | 方 after a plain attributive verb (受けた方は, 依頼された方) needs a context model |
| T13 | 後 うしろ and 中 うち have no rule; 後 のち only with clause cues (T55) | #16 | ~1. Needs work | a context model |
| T17 | Left out of #17: 鬼 おに, 気味 ぎみ | #17 | ~0.05 (おされ気味 きみ). Accept | 気味 after a passive stem |
| T18 | A number + counter token is read as a counter even in a name (三間) | #18 | ~0. Accept | the book's ruby wins |
| T21 | A counter span Word overlaps its own tokens (三本 over 三 + 本) | #3 | none (word lists skip it) | – |
| T23 | 分 ぶ (a tenth) only with cues: 五分五分, after 割/寸/両, before 咲き/目/通り; the odds (分が悪い, 私に分がある) since #76 | #15, #76 | ~0.1. Accept | another N分 nearby, no time words |
| T24 | A split compound's second part is voiced when the list's compounds voice that tail ≥ 4 in 5 (小屋 ごや) | #21 | unmeasured (B1 8 broken). Needs work | per-pair evidence; non-noun tails |
| T25 | A Sudachi reading one voicing from a 3+-character word's only listed reading takes the listed one (投票所 しょ) | #21 | 0. Accept | – (both standard) |
| T26 | 一 + one token joins when the list's top reading starts with ひと/いっ (一思い, 一重 ひとえ) | #24 | ~0. Accept | per-form cues; UniDic word origin for unlisted 一冬 |
| T28 | 一時 has no rule (いちじ / いっとき / ひととき) | #24 | ~0.3. Needs work | a context model |
| T30 | 金 defaults to かね when no きん cue fires (cues: metals, colours and things made of gold: 金の瞳/斧/縁取り, 白と金) | #28, #76 | ~0.1 (金の豆, 金 as an element). Needs work | more things made of gold |
| T31 | 外 is a rule form (ほか), so its model no longer answers | #28 | ~0. Accept | retrain 外 on what no rule reads |
| T33 | A conjugated word the list lacks takes Sudachi's surface reading (泳げ およげる) | #23 | none shown; rare in word lists. Accept | per-form lemma checks (往っ さる) |
| T34 | default-readings.tsv: pre-war NDL nominates, modern text decides (身体 からだ, 時 とき, 実 み, 下 した; 咽喉, 空地 by hand, T83) | #25 | ~0. Accept | modern evidence per pair to admit more |
| T35 | 都 alone is みやこ (と with Tokyo-government cues); 露 by context (T64) | #34 | ~0. Accept | government cues from news text |
| T37 | 辛い keeps its model where no rule fires (T75), not shown (T150) | #40, #75 | ~0.1 (辛い役目 からい), never shown. Accept | more つらい cues |
| T38 | With `carry`, a name's hiragana ruby is taken even when unlisted and carried to later bare occurrences | #44 | ~0. Accept | stop carrying at a second ruby; widen `_PRONOUNS` |
| T39 | 開く after を is ひらく; 止める after の/こと is やめる (とめる objects: `cues.HALTED`, #63; 止めに入る); 空く すく only for roads and trains (あく before 穴) | #41, #75 | ~3 in word lists (…のを止められない: ruby 5 やめる / 5 とめる), never shown (T150). Needs work | a "stop someone" cue; eyes and windows for 開く |
| T40 | Readings Jiten ranks the same are decided by JMdict's first reading, a few the wrong way (一束 いっそく, 一声 いっせい) | #43 | ~0. Accept | JMdict priority tags for ties |
| T41 | A joined compound JMdict lacks with the list's reading is `dictionary` (not shown) | #43 | none on word lists; right names lose shown furigana. Accept | `carry` (T38); JMnedict confirms only 4 of 10 (dev), 15 of 34 (library ruby): not a way out |
| T140 | A name (Sudachi's 固有名詞) JMdict lacks is `dictionary`, not `only`: the list's one reading is a guess (T42) | #73 | none wrong; ~100 right name furigana per book not shown (library ruby). Needs work | callers pass `carry` (chimimouryou's readings file doesn't yet) |
| T141 | Names JMdict has stay `only` (安芸 あき for a character named あげ) | #73 | ~1.4 shown wrong per book. Accept | – |
| T44 | The public table was trained on the NDL test authors' ruby and pruned on Tatoeba half b | #47 | none (evaluation leakage) | the shared-model rebuild |
| T45 | Hand defaults 擦る こする (conjugated forms too: T153), 素 す (from Opus's readings of post-war text) | #49 | ~0.3 (背中を擦った さする: T70), not shown. Needs work | a context rule for 素 もと (origin) |
| T47 | 抱く だく only after a held thing or person + を, or before たい with no を; いだく elsewhere | #50, #63 | ~0.7 in word lists, not shown (Sudachi's). Accept: no passive cue reaches 90% in books' ruby (Xに抱かれ だく 162 / いだく 75; 腕に 16/16) | – |
| T48 | By cue: 側 そば, 表 おもて (T81), 主 あるじ (T82), 間 ま, 家 け (T60), この後 あと, 留まる とどまる | #50 | ~0.3 before, mostly 部屋の主; 側 ~0.02 (Xの側である がわ: 2 in 300 post-war books, while 公園の側である is そば). Needs work | 主 cues |
| T49 | With no reading list, JMdict's pairs are the list | #51 | none with a list (chimimouryou always has one). Accept | – |
| T50 | 分別 alone is ふんべつ; ぶんべつ after ゴミ/資源… or before する/収集… | #55 | ~0. Accept | more sorting cues |
| T55 | 後 のち: 後に at a clause start, 後の時代/世, しかる後, これから後 | #58 | ~0. Accept | a context model (T13) |
| T56 | 方 かた after お, 紛う, この方は, or an honorific verb, unless a comparison follows | #58 | ~0.1. Accept | – |
| T60 | 家 け after a surname, a kanji 固有名詞 or a noble title (伊達家, 侯爵家) | #61 | unmeasured, small (多胡家包 いえ); fixes ~7.5 per book | a name list for 姓 + 家 (飯津家 いいづか) |
| T61 | 下手 is へた; しもて only with stage cues | #61 | small (下手に座っている with no cue) | a stage cue from the paragraph |
| T62 | 上手 じょうず by its adjective endings; かみて with stage cues | #61 | small (彼の方が上手。 うわて) | – |
| T63 | 前 まえ after この/その/あの | #61 | none seen | – |
| T64 | 露 あらわ before に + する/なる or な; つゆ before 知らず | #61 | none seen | – |
| T65 | 素 もと after food and 混乱/元気 + の; す otherwise (T45) | #61 | small (灰を素に) | more cues |
| T66 | 方 かた after ファン/一般/上司/責任者… + の | #61 | none seen | see T12 |
| T67 | 間 あいだ before に割って/に入る/に挟む, not after の | #61 | none seen | – |
| T70 | 擦る こする after 目/瞼/鼻を (+ 右手で…), ごしごし, 頬/顔を擦りつける, さする after お腹を; こする elsewhere (T45, conjugated too: T2), する after マッチ/燐寸を and in split compounds (擦りガラス) | #63, #75 | ~0.2 (背中を, 腕を さする: ruby 69%, 78%), not shown. Accept | – |
| T71 | 弾く ひく after an instrument, はじく after を/で/に or before a passive; 弾く, 堪える keep their models, not shown (T150) | #63, #75 | ~0.05 (instrument out of reach), never shown. Accept | a PLAYED word anywhere in the paragraph |
| T72 | 解く ほどく after a tied thing + を (`cues.TIED`) | #63 | ~0.25 (帯, 荷, both standard), not shown. Accept: in books' ruby 帯を ほどく 67%, 荷物を 70%, 包みを 83% | – |
| T73 | 堪える こらえる after を and before きれ; the model elsewhere, not shown (T150: ruby 58% right) | #63, #75 | ~0.15, never shown. Accept | – |
| T75 | 辛い つらい unless food follows, after a kanji or verb stem (見辛い づらい), or before も/すぎ/？ | #63 | ~0.1 | a food cue from the paragraph |
| T76 | 来る くる before べき as a predicate; きたる before a noun | #63 | ~0 | – |
| T77 | An okurigana variant (幼ない) gets Sudachi's reading of its normalized form, not the list's `only` | #63 | ~0 (pre-war forms go wrong) | check the normalized form is the same word |
| T78 | 開く, 空く あく after 穴, not 落とし穴 | #63 | ~0 | – |
| T79 | 吐く つく after ため息/嘘/悪態 + を; はく otherwise | #63 | ~0 | – |
| T80 | 家 け also after 貴族, 領主 | #62 | none seen | – |
| T81 | 表 at a phrase start is おもて unless a table cue follows (表を作る, 表1) | #62 | small (a table with no cue) | a genre signal for non-fiction |
| T82 | 下 もと after a person + の下へ/に + going or serving; 主 あるじ, 側 そば, 階 かい by cue | #62 | small (主のもとに しゅ) | 主様 (ぬし/あるじ both) |
| T83 | 画 え after a particle or inflected word, before a particle; hand defaults 咽喉 のど, 空地 あきち | #62 | small (空地 くうち) | – |
| T90 | With a list, 2-4 tokens join into a 3+-character form: JMdict's one reading of a form the list lacks (羅甸語 らてんご) or a form the list ranks one way 3× (三日月 みかづき) | #65 | ~0.01. Accept | JMdict priority tags |
| T91 | Left out of T90: two-character forms (家中), shared top ranks (曽祖父), ranked readings the kanji don't spell (真正面 まとも) | #65 | small (曽祖父 そそふ). Needs work | rank by JMdict priority or bare-text counts |
| T100 | 21 forms read by table entries learnt from generated sentences (素振り, 貴女, 素性, 前世, 瞬く, 罰…; docs/training.md) | #68 | none broken anywhere | sentences where suffix forms are own tokens (通り どおり) |
| T101 | 素振り すぶり only with a practice cue (木刀, 百回, の稽古); そぶり elsewhere | #68 | small (すぶり with no cue) | more cues |
| T102 | 期 ご only in この期に及んで | #68 | none seen | – |
| T103 | Left out of T100: 理, 強者, 半身, 元, 首, 開ける, and forms under 90% (御方, 転生, 妃…) | #68 | their misreads stay | fixed-phrase rules; more sentences |
| T122 | 十 alone stays じゅう unless an age or count cue (十も年下, 九つか十の, 歳も十に: とお, #76) | #67, #76 | ~0.01. Accept | |
| T130 | `extra-readings.tsv`: 25 hand-checked pairs Jiten's list lacks (良い いい, 描く かく, 刺青 いれずみ) join `known` after the form's own readings | #69 | ~0. Accept | pairs a combined list brings in leave the file |
| T131 | 描く かく after a picture (`cues.DRAWN`) + を/に/も or before one (描いた絵, ruby 35/37); えがく elsewhere, not shown (T151) | #69, #75 | ~2-3 in word lists (パステルで描く, 描かせていただく), never shown. Accept: drawings take either reading (T154); instruments are かく 7 / えがく 8 in ruby | – |
| T132 | 刺青 defaults to いれずみ | #69 | ~0 (titles: 『刺青』 しせい) | – |
| T133 | Pairs left out of `extra-readings.tsv`: お義母さん かあ, 解せない げせない, 放っておく ほうっ, gikun ruby | #69 | small, unmeasured. Needs work | a rule per item |
| T150 | `readings.MODEL_UNSHOWN`: the model's readings of 開く, 空く, 止める, 注ぐ, 堪える, 弾く, 辛い are kept with source `dictionary`, not shown | #75 | coverage: plain DEV 68.1 → 67.9%; books' ruby 空く 85 → 6%, 注ぐ 87 → 0%, 止める 71 → 21%, 開く 81 → 39% shown (their shown precision 69-89% → 93-98%). Accept | rules per form (rules' readings are shown) |
| T151 | A form with an `extra-readings.tsv` pair is never `only` (描く えがく, 経緯 けいい) | #75 | coverage: 描く shown only by T131's rule (25% of ruby occurrences). Accept | rules per form |
| T152 | A っ-form two listed verbs share (行っ 行う/行く, 通っ, 放っ, 弄っ) is not `only`, unless the other is 5 times rarer in the list | #75 | coverage: also 経っ (経る), 断っ (断つ), whose other verb has no such form; plain DEV 4 words. Accept | Sudachi's conjugation type for the other verb |
| T153 | Conjugated 擦る takes the こする default (T45) | #75 | ruby: right 197 → 1,840 of 2,538 changed (さする 背中を, 腕を; 擦りつける すり), not shown. Accept | – |
| T154 | Verbs with two standard readings keep Sudachi's or the model's choice, not shown: 良い よい/いい, 描く for drawings, ドアが開く, 行き交う ゆき/いき, 擦れる こすれる/すれる, 抱かれる, 瞑る, 注ぐ for drinks | – | ~25 on dev (word lists only). Accept: no cue reaches 90% in books' ruby (ドアが あく 44%, 酒を つぐ 70%, 茶を つぐ 70%) | – |
| T160 | 方 がた right after a person (あなた方, 先輩方, お嬢様方, `cues.PLURAL_PERSON`); not after 母/父さん (お母さん方, the mother's side) nor in an address (山田さん方で) | #72 | ~0: those two keep Sudachi's かた. Accept | – |
| T161 | Lone 札 民 綿 痕 default to ふだ たみ わた あと (`HAND_DEFAULTS`, `GLUED_CHECKED`); 札/お札 さつ near money (財布, 万, 紙幣, にせ札, 札だけ抜き取る), お札 おふだ near a shrine or a charm (神社, 祠, 貼る, 納める), 綿 めん for cloth (綿のシャツ, 麻や綿) | PR_LONE | ~1 (libruby held-out 札: 130 of 137 changes right; misses are money without a cue: 札を握ったまま). Needs work | money without a cue word needs a context model |
| T162 | Lone kun nouns by cue: 社 やしろ (小さな社, 社の境内), 角 つの (鬼の角, 角が生え), 柄 つか/え (剣の柄, 箒の柄), 業 わざ (至難の業, なせる業), 艶 つや, 直に じか (+ 触れる/見る/会う…), 要 かなめ (防衛の要), 真に受ける ま, 紅 べに (紅を引く), 香 か (梅の香), 氏より育ち うじ, 際 きわ (崖の際) | PR_LONE | ~0.5 (libruby held-out: 3,528 of 3,600 changes right, 角 128/128, 柄 1,396/1,464). Accept | 艶 えん in 艶に笑う, 香 こう after 香草 |

### Period-justified

Rules whose support is mainly period text but that change nothing on the modern sets; new ones need
majority support from post-war text.

| rule or default | from | fires on |
|---|---|---|
| 君 ぎみ after a family or rank word | #28 | 尼君, 姫君, 母君 |
| 尼 あま before 君/寺/僧/さん/御前/姿/になる | #28 | 尼君, 尼寺 |
| 音 ね after an instrument, an insect, ぐうの | #10 | 琴の音, 虫の音 |
| 中宮 ちゅうぐう | #28 | the empress's title |
| 仏 ほとけ (Sudachi's ふつ) | #17 | 仏 alone |
| 他 た in set phrases and as a prefix | #10 | 他の追随を許さない, 他国 |
| 他 ほか default (was T4) | #10 | its た misses are pre-war; post-war 0 of 40 |
| 可愛いく → 可愛 かわい (was T43) | #46 | breaks one pre-war spelling |
| 傍 そば before a particle (was T46) | #50 | its かたわら misses are pre-war; post-war 0 of 30 |

## Resolved

| id | trade-off | resolved by |
|---|---|---|
| R1 | 来る stripped to く over 来た/来ない | #15 (`surface_reading` with `after`) |
| R2 | 三軒 surname path had no effect | #18 |
| R3 | 十分 じゅっぷん/じゅうぶん decided by Sudachi's split | #22 (one cue set) |
| R4 | 金 had no default | #28 (きん cues, then かね; T30) |
| R5 | 香 defaulted to か (period support) | dropped in #37 |
| R6 | 額 had no rule (was T10) | #40, #41 |
| R7 | 開く, 止める, 空く lost their model to a rule (was T29) | #40, #41 |
| R8 | 昭和二三年 read にさんねん (was T19) | #55 (`counters.is_year`) |
| R9 | 銀杏 いちょう, 大文字 おおもじ defaults (was T15) | #55 (food and Kyoto cues) |
| R10 | 一間 always いっけん (was T20) | #55 (ひとま after room words) |
| R11 | 何 なに in Xやら何やら (was T32) | #55 |
| R12 | 何 before a counter that starts a verb; 着, 間, 話 not counters (was T36) | #55 (`readings._VERB_AFTER_NANI`) |
| R20 | A name JMdict lacks kept the list's reading as `only` (麻里 あさざと, 隆治 たかじ; was T42) | #73 (T140) |
| R21 | Jiten's noisy surname readings (佐藤 さとあ, 加藤 かとお; was part of T133) | measured in #73: Sudachi's reading wins when the list's differs, and agreeing noise is no longer shown (T140) |
| R25 | 被る こうむる after 汚名/損 (was T74) | #75 (汚名, 損 left out of `cues.SUFFERED`: ruby かぶる 32 of 42, 4 of 13; the rule is 99% right) |
| R35 | A bare 十分 with no minutes cue read じゅうぶん (十分もしないうちに, 歩いて十分, 二時間十分) (was T22) | #76 (`counters.TEN_MINUTES_*`: time going by, trips, times) |
| R36 | Xつ目 joined as eyes (三つ目の角 みつめ) (was T121) | #76 (ordinal みっつめ/よっつめ unless eyes: 三つ目が光る, 三つ目小僧) |
| R37 | 一日 いちにち where ついたち or いちじつ is meant (was T27) | #24, #55, #76 (一日の長 いちじつ; dates after a month: 0 left in 300 books) |
| R38 | Xつ (3, 4, 6, 8) read as a compound before a one-kanji noun (三つ門) (was T120) | #67 (1 miss in 300 post-war books: ~0) |
| R39 | Defaults fired on a token Sudachi split off a compound (委託金 かね, 上位種 たね) (was T14) | #76 (金 after a kanji noun or prefix: きん; 種 glued to what precedes keeps しゅ, `GLUED_BEFORE`; ~0.02 left: 米占領軍, 食卵) |
