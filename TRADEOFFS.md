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
| T13 | 後 うしろ and 中 うち have no rule; 後 のち only with clause cues (T55) | #16 | ~0 post-war: in books' ruby, 後 うしろ (75) is 12 of 14 authors pre-war (吉川英治, 永井荷風, 森鴎外, 江戸川乱歩) and 中 うち (176) mostly so (夢野久作, 江戸川乱歩, 永井荷風; ~20 post-war, among members: 三人の中); post-war writers write 後ろ and うち. Accept | a context model |
| T17 | Left out of #17: 鬼 おに, 気味 ぎみ | #17 | ~0.05 (おされ気味 きみ). Accept | 気味 after a passive stem |
| T18 | A number + counter token is read as a counter even in a name (三間) | #18 | ~0. Accept | the book's ruby wins |
| T21 | A counter span Word overlaps its own tokens (三本 over 三 + 本) | #3 | none (word lists skip it) | – |
| T23 | 分 ぶ (a tenth) only with cues: 五分五分, after 割/寸/両, before 咲き/目/通り; the odds (分が悪い, 私に分がある) since #76 | #15, #76 | ~0.1. Accept | another N分 nearby, no time words |
| T24 | A split compound's second part is voiced when the list's compounds voice that tail ≥ 4 in 5 (小屋 ごや) | #21 | unmeasured (B1 8 broken). Needs work | per-pair evidence; non-noun tails |
| T25 | A Sudachi reading one voicing from a 3+-character word's only listed reading takes the listed one (投票所 しょ) | #21 | 0. Accept | – (both standard) |
| T26 | 一 + one token joins when the list's top reading starts with ひと/いっ (一思い, 一重 ひとえ) | #24 | ~0. Accept | per-form cues; UniDic word origin for unlisted 一冬 |
| T28 | 一時 いっとき has no rule (いちじ elsewhere); ひととき only after a pleasant word (至福の, 夢のような, 先輩との: #83, books' ruby 46 of 47), not after a time of day (夜の一時を回る is a clock) | #24, #83 | ~0.2: ruby いっとき 292 (一時の恥, 一時、言葉を失う), but bare 一時 is mostly いちじ (一時は, 一時停止). Needs work | a context model |
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
| T230 | A form whose JMdict reading the list lacks is `only` unless that reading is checked standard in training-author books (22 forms in `extra-readings.tsv`: 崖下 がけした, 碑 ひ, 手数 てかず, 刀 とう, 川 がわ); archaic or rare JMdict readings (理由 わけ, 背中 せな) leave `only` as is | this PR | coverage −0.04 on dev, shown precision held; the other 400 forms where `only` fires and ruby gives a JMdict reading were hand-checked on bare samples: 99%+ right, or both readings standard (口腔, 逝く). Accept | a rule for 川 がわ after a river's name |
| T152 | A っ-form two listed verbs share (行っ 行う/行く, 通っ, 放っ, 弄っ) is not `only`, unless the other is 5 times rarer in the list | #75 | coverage: also 経っ (経る), 断っ (断つ), whose other verb has no such form; plain DEV 4 words. Accept | Sudachi's conjugation type for the other verb |
| T153 | Conjugated 擦る takes the こする default (T45) | #75 | ruby: right 197 → 1,840 of 2,538 changed (さする 背中を, 腕を; 擦りつける すり), not shown. Accept | – |
| T154 | Verbs with two standard readings keep Sudachi's or the model's choice, not shown: 良い よい/いい, 描く for drawings, ドアが開く, 行き交う ゆき/いき, 擦れる こすれる/すれる, 抱かれる, 瞑る, 注ぐ for drinks | – | ~25 on dev (word lists only). Accept: no cue reaches 90% in books' ruby (ドアが あく 44%, 酒を つぐ 70%, 茶を つぐ 70%) | – |
| T160 | 方 がた right after a person (あなた方, 先輩方, お嬢様方, `cues.PLURAL_PERSON`); not after 母/父さん (お母さん方, the mother's side) nor in an address (山田さん方で) | #72 | ~0: those two keep Sudachi's かた. Accept | – |
| T161 | Lone 札 民 綿 痕 default to ふだ たみ わた あと (`HAND_DEFAULTS`, `GLUED_CHECKED`); 札/お札 さつ near money (財布, 万, 紙幣, にせ札, 札だけ抜き取る), お札 おふだ near a shrine or a charm (神社, 祠, 貼る, 納める), 綿 めん for cloth (綿のシャツ, 麻や綿) | #78 | ~1 (libruby held-out 札: 130 of 137 changes right; misses are money without a cue: 札を握ったまま). Needs work | money without a cue word needs a context model |
| T162 | Lone kun nouns by cue: 社 やしろ (小さな社, 社の境内), 角 つの (鬼の角, 角が生え), 柄 つか/え (剣の柄, 箒の柄), 業 わざ (至難の業, なせる業), 艶 つや, 直に じか (+ 触れる/見る/会う…), 要 かなめ (防衛の要), 真に受ける ま, 紅 べに (紅を引く), 香 か (梅の香), 氏より育ち うじ, 際 きわ (崖の際) | #78 | ~0.5 (libruby held-out: 3,528 of 3,600 changes right, 角 128/128, 柄 1,396/1,464). Accept | 艶 えん in 艶に笑う, 香 こう after 香草 |
| T164 | One-kanji nouns Sudachi takes as a suffix (雨 う, 家 か/や, 君 くん, 的 てき, 下 か, 店 てん, 街 がい, 車 しゃ, 石 せき) read as the noun after a function word, adverb, verb or time word (`readings.SPLIT_SUFFIX`) | #82 | bare audit of 100 post-war books: ~3 wrong of 106 changed (げぼく君 a nickname, 深夜店). Accept | – |
| T155 | A word whose Sudachi reading is neither listed nor JMdict's takes the list's top reading, not shown (七五三 ななごさん, 氷室 ひょうしつ, 獰猛 ねいもう); not for names, one-character forms, two numerals, a listed verb's potential (弾ける ひける), a listed する verb's godan form (徹す てっす), Kansai u-onbin (買うて こう), loanwords (麦酒 びーる), 秋桜 (Sudachi picks コスモス by context), nor when another listed form with one of its kanji reads Sudachi's way (無性 むしょう, 朝陽 あさひ) | #80 | ~0.1 (300-book sample: 上側 うわかわ, 黄緑色 おうりょくしょく, 手鎖, 鹿狩 しかがり); up to ~0.2 with both-way forms (大商人 おおあきんど, 双乳 もろち); 山居 さんきょ in ruby. Accept | a pair in extra-readings.tsv does not help (the list's top wins); a list of Sudachi's context-picked entries |
| T200 | Bare post-war text: 数多 あまた, 歩兵 ほへい, 洒落 しゃれ, 荒野 こうや, 鬼神 きしん shown (rules); frames (shown) decide 拘る, 止め, 気色, 細々, 大人気, 帰す, 初心, 如何, 艶やか あでやか, 正しく まさしく; 呆ける ほうける, 艶やか つややか, 正しく ただしく are HAND_DEFAULTS, not shown | #81 | Opus labels of 40 bare occurrences per form (gate.py): right 235 → 596 of 636, 12 broken (あでやか 4, まさしく 6, ぼける 2: no frame found, hence not shown); shown 351, 0 wrong. Library ruby favours まさしく (79 of 120) and あでやか (29%): authors ruby the rarer reading. Accept | 如何ほど いかほど (~0.01: 7 bare in 1,000 books; 如何に is listed now, いかに `only`, ~0 left); 退く ひく/どく left to Sudachi; 顔を埋める うずめる (Tatoeba B1 reads うめる) |
| T170 | A name token Sudachi gives an ordinary word is read as a word only for counts (数人 かずひと → すうにん, 数度, 数歩, 三百 みつお, 二十八 つちや: `_COUNT_NAME`); 未来人 みきと is a hand default (T261); 万代 もず, 土日月 (full dictionary) stay | #85 | ~0.7 fixed per book; the rest ~0 (万代: 1 bare in 1,000 books). Accept: widening it to every name token whose reading JMdict and the list lack changed ~5,000 words in 300 books, mostly real names (最上さん, 高木, 金子, 月火 つきひ) | |
| T171 | A joined form JMdict lacks keeps the list's reading (not shown) unless it spans a number the tokens can't spell (三日後 みひりあ → 三日|後) | #85 | 利根川 さねがわ, 竜人 きみひと left (~0.005, not shown: 利根川 5 bare in 1,000 books). Accept: the same check without the number dropped real names split into words (沙|倉 さくら, 晴|翔 はると: ~2,400 in 300 books) | |
| T172 | 1日/１日 is いちにち unless a month comes right before it (ついたち) | #85 | ~0.1 (1日 as the first of an unnamed month). Accept | |
| T220 | Loanwords spelt in kanji that Sudachi cuts in pieces (無問題 もーまんたい, 油条, 麻辣; `ateji.tsv`: JMdict forms read only in katakana, no mahjong terms, not 加油 快手 三板) are one word, certainty 0, never shown, not where ruby or a token edge cuts them | this PR | ~0.02 words per book (6 fires in 300 training-author books, all right; 5 wrongly shown pieces 油 あぶら, 麻 あさ gone); single-token ateji (香港, 珈琲) were already Sudachi's. Mahjong terms stay pieces in mahjong books. Accept | ruby-mined ateji: book ruby over all-kanji bases was creative (自分 イスカ) |
| T221 | Glaring bare-text misreads from Opus labels of 2,590 sampled bare occurrences: rules (shown) 仇 かたき (親の仇, 仇を討つ), 擦れる かすれる (擦れた声), 盛り さかり (かわいい盛り), 類 たぐい (装飾品の類), 痛 いた (痛っ), 床につく only without を (頭を床につける ゆか); `HAND_DEFAULTS` (not shown) 殿 どの (not after a number), 数百 すうひゃく, 軽々 かるがる, 高名 こうめい, 敵同士 てきどうし, 樽 たる, 宴 うたげ, 身体中 からだじゅう | this PR | ~3 words per book fixed (bare counts in 208 books), 0 broken on the labels; library ruby 92-100% where each rule fires (仇 93%: authors ruby あだ over 仇を討つ too; 殿 97%: palace halls 鳥羽殿). Accept | the rest of the labels: ROUTE in the PR (入れ はいれ: T242/T251, 何故 なにゆえ, 一文 もん, 件 くだり, 等 ら: T250, 外 ほか: T252, 玩具, エロ本, 縁 ふち, lone-kanji pieces) |
| T240 | Sudachi's 降りる right after rain or snow (雨は降り続けた, 雪がたくさん降ります, ひと雨降りそう) is 降る ふる (`WRONG_LEMMA`, a rule, shown); 霜/光が降りる stay おりる; not after other kanji (白雪, 深雪) | this PR | ~0.01 words per book fixed (40 bare in 4,800 training-author books, 37 sure right, 3 either: 雪が降りてくる); further adverbs (雪がますます降りながら) still read おりる `only`; 降る くだる (surrender) is T260. Accept | the lemma from context for other verbs (T2) |
| T241 | 弾ける ひける (弾く's potential) after an instrument (ギターが弾けない, ピアノなんて弾けない; rule, shown); elsewhere はじける, not shown (extra reading, T151); Sudachi's ひける is a hand default はじける | this PR | ruby where the rule fires 38/38, bare 30/30; word lists +0.15 per book (Sudachi's ひける was はじける 24 of 30 bare); ひける without a near instrument (まともに弾けなかった) stays はじける, unshown, ~0.05 per book. Accept | cues further back (ピアノは…満足に弾けない) |
| T242 | 入れる in a clause without を (部屋には入れない, 中に入れた) isn't `only`: it may be 入る's potential はいれる; still `only` after 手に/口に… and when imperative, volitional, causative, passive or before くれ/もらう/おく | this PR | ~4 words per book hidden, ~1.4 of them were wrong when shown (ruby there はいれる 34%, bare 19 of 60); word lists keep いれる (~1.4 wrong per book). Needs work | a cue for which verb: a place + negative or potential sense (はいれる), a thing put in (いれる) |
| T250 | `readings.MODEL_FIX`, model readings wrong in a frame or most of the time: 何時 なんじ is いつ before か/しか/だって/でも/になく/、/だったか or a verb (shown; not after 今, not 何時起き); 一\|文 もん is ぶん unless money (一文も, 一文の得; shown); 術 すべ is じゅつ glued after a kanji or katakana noun (護衛術; shown); 何故 なにゆえ → なぜ, 件 くだり → けん, 等 ら → など unless after a pronoun or a person word, not shown | this PR | bare, 176 training-author books: ~0.25 words per book fixed and shown (一文 0.16, 術 0.06), ~1.1 hidden (等 0.8, 何故 0.15, 件 0.14), ~0.2 of them right before (ら after names: マルクス等); library ruby, shown: 何時 58 → 82%, 何故 95 → 99%, 等 52 → 92%. Needs work | 等 ら after a name and とう after kanji nouns (記号等, 小等部); frames for literary 何故 なにゆえ and 件 くだり |
| T251 | 入れ, the noun Sudachi takes, on its own (not after a noun or お) before 」/。/と言う is 入る's imperative はいれ, not shown (the list reads 入れ いれ only) | this PR | ~0.07 words per book, 12 of 12 bare right. Accept | はいれ listed for 入れ would let it show |
| T252 | 外 ほか before の + people or things only when not after a noun + の (村の外の人, 窓の外のこと: Sudachi's そと, not shown) | this PR | ~0.02 per book hidden; abstract X の外 (想定の外, 理解の外: ほか) now そと, 3 of 22 changes. Accept | – |
| T253 | Rendaku after a class letter (Ａ組 ぐみ: a single letter counts as a compound's first part in `Reader._voicing`); not after a count of times or steps (一回\|部屋 へや, `_ACTION_COUNT`) | this PR | ~0.95 words per book fixed (165 of 165 bare changes right); 木組み細工 さいく, 双斧術 おの left (1 each in 208 books). Accept | – |
| T254 | 癖 glued after a kanji or katakana noun or a verb's stem (逃げ癖, 遅刻癖, 盗聴癖) is くせ, ぐせ or へき: `only` dropped, Sudachi's くせ not shown | this PR | ~0.1 words per book hidden (17 in 176 books, most ぐせ or へき). Needs work | ぐせ/へき from the first part (a kanji noun of a habit: へき) |
| T260 | 降る くだる (surrender) only right after 軍門/傘下/麾下/配下/旗下/幕下 + に (軍門に降った), also where Sudachi took the verb for 降りる (`_SURRENDER`, a rule, shown); 敵に降る, 陣営に降りなさい stay ふる/おりる | this PR | ~0.02 words per book fixed (12 bare in 1,000 training-author books, all surrender); library ruby 17 of 17 くだ. Accept | – |
| T261 | 未来人 is a hand default みらいじん over Sudachi's name みきと (not shown: `default`) | this PR | ~0.1 words per book fixed (162 bare in 1,000 books, 2 in 3 read みきと). Accept | – |
| T262 | A numeral compound Sudachi splits (十\|中\|八九, 三\|白眼, 四\|人組, 二\|人組, 四\|天王, 七\|賢人) is joined when the list reads it one way and JMdict has that reading (`Reader._numeral_idiom`, `only`, shown); not N文字 (counts of letters), 八歳児 (はっさいじ, not やつご) or 十二神将 (books ruby じゅうにしんしょう) | this PR | ~0.8 words per book fixed (313 in 384 books); 27 more both standard (二十一世紀 いっせいき, 六角形 ろっかっけい). Left: 一世一代 (two listed readings), 四十九日 (a counter span), 十中八九 without a list (JMdict gives three readings): ~0.05. Accept | – |
| T270 | 下 もと after a titled person or superior + の and で (フェルト様の下で, 上司の下で, 陛下の下で; not お日様/お陽様), shown | this PR | ~0.02 words per book fixed (121 changes in 7,213 training-author books, ~2 wrong: お陽様, a physical "under"); a bare name + の下で (Xの下でも) still した, ~0.01. Accept | a person cue for bare names |
| T271 | お話して, お話したい, お話させて (お + 話 + する without the okurigana し): 話 はなし, the し is する's (`readings.SPLIT_TOKENS`, shown); Sudachi's 話す はな showed おはなして | this PR | ~0.16 words per book fixed (1,179 changes, 25 of 25 sampled right, ruby 10 of 10). Accept | – |
| T272 | 平伏し (平伏した, 平伏して) is 平伏 へいふく in word lists, not shown; Sudachi's 平伏す ひれふす was `only` | this PR | ~0.12 words per book hidden (856 changes); ruby there へいふく 109, ひれふ 53, so ~1 in 3 is now wrong in word lists (was 2 in 3, shown). Needs work | a cue for ひれふす |
| T273 | 主に after 我が/わが/亡き… or before 仕える/忠誠/従う/逆らう/相応しい/捧げる…: 主 あるじ + に (shown), not the adverb おもに; after の not shown (ぬし or あるじ) | this PR | ~0.03 words per book fixed and shown, ~0.04 hidden; ruby where shown あるじ 43 of 60, the 13 しゅ all from one Bible translation (the Lord: 主に仕える); 主に + other verbs (主に命じられ) still おもに `only`. Accept | the Lord (しゅ) from a religious cue, as `_CONTEXT_RULES['主']` |
| T274 | 解せない/解せぬ/解せん/解せず: 解す げす (shown), not Sudachi's 解する かいする `only`; not after を (意味を解せない: かい) | this PR | ~0.12 words per book fixed (860 changes; ruby げ 356 of 358). Accept | – |
| T275 | Model readings in a frame (`MODEL_FIX`, shown): 地 じ in Xを地でいく/行く, 実 じつ before の + a family word (実の父, 実の娘), not み/まこと; there Sudachi's じつ is kept over the default み (`DEFAULT_KEEP`, not shown) | this PR | ~0.25 words per book fixed (265 地, 527 実 shown, 929 実 hidden; ruby 18 of 18). Accept | – |
| T276 | 方 かた after a katakana word + の only before です/でし (…したのはルークの方だった/だって: ほう); 風 ふう in ない風を only before 装う/演じる/して/見せる/意識 (見えない風を感じる: かぜ) | this PR | ~0.05 words per book fixed (365 方, 15 of 15 sampled ほう; 12 風), now Sudachi's, not shown. Accept | – |
| T277 | 地竜 is a hand default ちりゅう (not shown); the list's `only` じりゅう (JMdict: the earthworm) dropped (`extra-readings.tsv`) | this PR | ~0.24 words per book fixed on average, all in fantasy (1,742 in 134 books; ruby ちりゅう 41 in 10 books, じりゅう 0). Accept | ちりゅう in the list would let it show |
| T280 | Lemmas Sudachi takes where the modern word is another (`WRONG_LEMMA`): 宿する → 宿す (瞳に宿し, hand default しゅくす → やどす, not shown), 欲す → 欲する (the list's 欲す ほりす is noise: 欲した ほっした, `only`), 欲する before が → 欲しい (欲しがる, `only`) | this PR | ~0.07 words per book fixed (20 bare in 300 training-author books, all right by hand); other lemma mix-ups seen in a light novel (面し つら, 舞って/物語って as noun + って, 射殺さん いころ, 痛う いとう, 回らさ まわ) are ~0 in bare text or inseparable from the verb. Accept | the lemma from context for other verbs (T2) |
| T281 | A one-kanji noun or suffix that is an adjective's stem is that adjective (`Reader._adjectives`): before すぎ/過ぎ/そう/emphatic いっ (酷すぎる ひど, 熱すぎ あつ), and a kanji before a small ェ/ぇ that Sudachi reads as a slang adjective with え (強ェ つえぇ, 痛ぇ いてぇ, 酷ェ ひでぇ); the adjective's reading is mostly not shown (several listed readings, or none for the slang form) | this PR | ~0.2 words per book fixed (~60 bare in 300 books: 29 shown-wrong stems now right but hidden, 21 now shown right, ~35 slang forms; all right by hand); 甘ぇ (Sudachi's noun 甘え) and 熱ィ stay wrong. Accept | list readings for the slang forms, so they can be shown |
| T282 | Tails voiced after a compound's first part though the list's compounds are mixed (`_VOICED_TAILS`: 揃い 返し 通り 顔 切れ 机 帰り 皿 開き 処 走り 座り 疲れ 替わり 心 稽古: 美人揃い ぞろい, オウム返し がえし, 予定通り どおり, ドヤ顔 がお, 魔力切れ ぎれ, 執務机 づくえ); their unvoiced compounds have a verb's stem or a prefix first (繰り返し, お返し) | this PR | ~2.7 words per book fixed (~800 in 300 books, 131 of them shown); ~6% of changes wrong (a dropped particle: 次の日顔を, 基本顔), not shown for 通り/顔/切れ/心/処; library ruby where it fires 73 of 77 (training books; the rest flavour such as すとりーと, none with the old reading), 14 of 16 held-back. Accept | count only compounds whose first part is a noun in `_tail_counts` (tried: 64 forms flip, ruby 60% right: titles after names, 大将, 簀桁) |
| T283 | 兄/姉 right after the prefix お/御 and before 様/さま/ちゃま is にい/ねえ (お兄様 おにいさま, お姉さま おねえさま; a rule, shown); Sudachi's あに/あね before; 兄様 without お stays あに (にいさま and あにさま are both used), お兄上 stays おあにうえ | this PR | ~2.8 words per book fixed (845 bare in 300 training-author books, 41 books, all right); library ruby 11 of 11. Accept | 兄様/姉様 without お, 兄ィ/兄ぃ (にい), 妾 わらわ (first person; めかけ in 妾の子): report-only, not near 100% either way |
| T290 | 行く方 and 行く行く are not joined into the list's ゆくかた/ゆくゆく before a particle or !/、 (`readings.NOT_JOINED`): 行く + 方, 行く + 行く, mostly not shown (行く いく is Sudachi's); 行く行くは and 行く方知れず stay joined | this PR | ~0.03 words per book fixed (9 bare in 300 training-author books, all いくほう/いくいく by hand; ruby 行=い 1 of 1). Accept | – |
| T291 | 何 before 玉, 作 (not 作る), 針 and か国 is a count (何作目, 何か国語): Sudachi's なん, not shown, instead of the なに rule | this PR | ~0.003 words per book fixed (1 bare in 300 books; 11 in ruby lines, all right by hand). Accept | なん as a shown rule before counters |
| T292 | 何時頃/何時ごろ are not `only` いつごろ (`extra-readings.tsv` なんじごろ): Sudachi's いつごろ, not shown | this PR | ~0.08 words per book hidden (25 bare in 300 books; by hand about half なんじごろ: 時刻は/夜、/昨夜の何時頃); ruby いつごろ 2, なんどきごろ 1. Accept | a なんじごろ rule after 今/午前/午後/夜/時刻は |
| T293 | 降る after rain/snow also with よく, 一日中/一晩中 or a span of days (雨が三日間降り続けた), and before 続く/始め/しきる/ゆく + rain or snow (降りつづく雪, 降り始めの雨): `_PRECIPITATION`, `_PRECIPITATION_AFTER`, also for Sudachi's 降りる (T240) | this PR | ~0.01 words per book fixed (3 bare in 300 books; ruby 降=ふ 3 of 3, 6 of 6 by hand). Accept | the lemma from context for other verbs (T2) |
| T294 | 辛い's つらい rule doesn't fire with a taste or food word within 12 characters (`readings._TASTE`: `cues.DISH`, `cues.SPICE`, 味 but not 意味/地味/味わう); からい also after 料理ほど and before 食べ物/食物/ソーセージ/鍋 | this PR | ~0.03 words per book: ~4 of 13 bare changes in 300 books were shown つらい and wrong, now hidden, 2 now からい shown; ~3 right つらい now hidden (食べられない日も辛かった); ruby where つらい fires 97 → 98% (train), 97% (held). Accept | more からい cues (辛さ, 辛そう of food) |
| T295 | 実 じつ from the model is み before を (not 言う/申す/挙げる/もって/見出す) or が (not ない/ある), and after この/あの (not before に): 実を齧る, 実をつける, 実が欲しい (`MODEL_FIX`, shown); 実を言うと/実を申せば じつ where the model says み; じつ kept after 名より/名を捨てて/名と | this PR | ~0.09 words per book fixed (27 bare in 300 books, 26 right by hand); ruby 実=み 6 of 6; 3 changes in ruby lines are a person named 実 (みのる; じつ before, み now). Accept | – |
| T320 | Defaults right 97%+ where they fire in training-author post-war books' ruby (n ≥ 20) or, rarer, in every sampled bare occurrence checked by hand are shown, source `rule` (`readings.SHOWN_DEFAULTS`: 他 ほか, 身体 からだ, 箱 はこ, 数百 すうひゃく, 間近 まぢか, 明後日, 一昨日, 正気, 鼻血, 民, 高名, 宿す …, 25 forms); a one-character one only on its own (not glued or before katakana: 他クラス) | this PR | ~19 words per book newly shown (5,834 in 300 training-author books); ruby where they fire 99.6% (train), 99.5% (held-back authors), dev/B1 shown precision held, 1 B1 and 3 B2 shown items against Tatoeba's IPAdic gold (他の た, 一昨日 いっさくじつ, both standard). Accept | – |
| T321 | Number + counter spans are shown (`counter`, certainty 1.0) but for counters and spans books often read otherwise (`counters.shown`: N月, N分, old measures, 羽, 足, 頭, 一度/三度 ひとたび/みたび, 一時, 何時, 一日, 三晩, 四番, 十八番, 千歳, 110番, a bare 万/億/兆, the second number of a range ２、３日, numbers with 七 (しち/なな), 二十歳 はたち, 幾年, 三三九度, 十時/十話 (names)) and spans Sudachi tags as names | this PR | ~150 words per book newly shown (45,048 in 300 training-author books, +0.9 to +2.0 points of coverage); ruby where shown 98.8% (train, gloss ruby left out; misses are native readings 四年 よとせ, 三粒 みつぶ, 五歳 いつつ), 96.1% (held: 何軒 なんけん, 千年 ちとせ); B1 shown precision 99.57 → 99.58 (gold-fix alts for IPAdic per-token gold: 一匹 いち+ひき); a written １千万 is いっせんまん now (25 B1 fixed). Accept | numeral names from the book's ruby (`carry`); 110番 ひゃくとおばん, 万歳/万人 (read いちまん…) as their own words; 七 by context |

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
