# Hidden readings

Readings yurigana stopped showing as furigana (they stay in word lists), so they can be shown again once
something makes them sure. One row per form; forms and numbers only. A PR that shows one again moves its row
to "Shown again".

| form | reading no longer shown | right reading(s) in context | how hidden (code place) | evidence | from | way back |
|---|---|---|---|---|---|---|
| 開く | the model's reading (was `model`) where no rule fires | あく, ひらく | `readings.MODEL_UNSHOWN`: the model's reading kept, source `dictionary` | ruby where the model gives it 66% right; shown share of ruby occurrences 81 → 39%; plain DEV, the seven forms together: 7 of 13 wrong | T150 (#75) | rules per form (their readings are shown) |
| 空く | the model's reading (was `model`) where no rule fires | あく, すく | `readings.MODEL_UNSHOWN`: the model's reading kept, source `dictionary` | shown share 85 → 6%; plain DEV, the seven forms together: 7 of 13 wrong | T150 (#75) | rules per form (their readings are shown) |
| 止める | the model's reading (was `model`) where no rule fires | とめる, やめる | `readings.MODEL_UNSHOWN`: the model's reading kept, source `dictionary` | shown share 71 → 21%; plain DEV, the seven forms together: 7 of 13 wrong | T150 (#75) | rules per form (their readings are shown) |
| 注ぐ | the model's reading (was `model`) where no rule fires | そそぐ, つぐ | `readings.MODEL_UNSHOWN`: the model's reading kept, source `dictionary` | ruby 69% right; shown share 87 → 0%; plain DEV, the seven forms together: 7 of 13 wrong | T150 (#75) | rules per form (their readings are shown) |
| 堪える | the model's reading (was `model`) where no rule fires | こらえる, たえる, こたえる | `readings.MODEL_UNSHOWN`: the model's reading kept, source `dictionary` | ruby 58% right; plain DEV, the seven forms together: 7 of 13 wrong | T150 (#75) | rules per form (their readings are shown) |
| 弾く | the model's reading (was `model`) where no rule fires | ひく, はじく | `readings.MODEL_UNSHOWN`: the model's reading kept, source `dictionary` | ruby 32% right; plain DEV, the seven forms together: 7 of 13 wrong | T150 (#75) | rules per form (their readings are shown) |
| 辛い | the model's reading (was `model`) where no rule fires | つらい, からい | `readings.MODEL_UNSHOWN`: the model's reading kept, source `dictionary` | ruby 66% right; plain DEV, the seven forms together: 7 of 13 wrong | T150 (#75) | rules per form (their readings are shown) |
| 川 | かわ (was `only`) | かわ, がわ (river names split off: 多摩川) | `extra-readings.tsv`: never `only` (T151) | ruby がわ 156 occ/71 authors; bare 6/30 wrong | T230 (#84) | a rule for がわ after a river's name |
| 刀 | かたな (was `only`) | かたな, とう (曲刀, 一刀流) | `extra-readings.tsv`: never `only` (T151) | ruby 164/50; bare 6/30 | T230 (#84) | a rule for the reading the list lacks |
| 粉 | こな (was `only`) | こな, こ | `extra-readings.tsv`: never `only` (T151) | ruby 120/84; bare 2/30 | T230 (#84) | a rule for the reading the list lacks |
| 行き | いき (was `only`) | いき, ゆき (destinations) | `extra-readings.tsv`: never `only` (T151) | ruby 11/7; both standard | T230 (#84) | a rule for the reading the list lacks |
| 手数 | てすう (was `only`) | てすう, てかず (fight moves) | `extra-readings.tsv`: never `only` (T151) | ruby 58/32; bare 18/30 | T230 (#84) | a rule for the reading the list lacks |
| 言 | げん (was `only`) | げん, こと (二言三言) | `extra-readings.tsv`: never `only` (T151) | ruby 69/34; bare 7/30 | T230 (#84) | a rule for the reading the list lacks |
| 鬼 | おに (was `only`) | おに, き (復讐鬼) | `extra-readings.tsv`: never `only` (T151) | ruby 166/76; bare 6/30 | T230 (#84) | a rule for the reading the list lacks |
| 乳 | ちち (was `only`) | ちち, ち | `extra-readings.tsv`: never `only` (T151) | ruby 47/16; bare 5/30 | T230 (#84) | a rule for the reading the list lacks |
| 宝物 | たからもの (was `only`) | たからもの, ほうもつ (宝物庫) | `extra-readings.tsv`: never `only` (T151) | ruby 88/53; bare 6/30 | T230 (#84) | a rule for the reading the list lacks |
| 尽く | ことごとく (was `only`) | ことごとく, つく/ずく (至れり尽くせり) | `extra-readings.tsv`: never `only` (T151) | ruby 51/34; bare 3/6; sanity xfail | T230 (#84) | a rule for the reading the list lacks |
| 碑 | いしぶみ (was `only`) | いしぶみ, ひ | `extra-readings.tsv`: never `only` (T151) | ruby 49/22; bare 5/6; sanity xfail | T230 (#84) | a rule for the reading the list lacks |
| 崖下 | がいか (was `only`) | がけした | `extra-readings.tsv`: never `only` (T151) | ruby 144/86; bare 6/6; sanity xfail | T230 (#84) | a rule for the reading the list lacks |
| 世帯 | せたい (was `only`) | せたい, しょたい (世帯を持つ) | `extra-readings.tsv`: never `only` (T151) | ruby 11/5; bare 3/12 | T230 (#84) | a rule for the reading the list lacks |
| 井 | い (was `only`) | い, せい | `extra-readings.tsv`: never `only` (T151) | ruby 3/3; bare 4/6 | T230 (#84) | a rule for the reading the list lacks |
| 鋒 | きっさき (was `only`) | きっさき, ほこ | `extra-readings.tsv`: never `only` (T151) | ruby 19/15; bare 3/4 | T230 (#84) | a rule for the reading the list lacks |
| 倦む | あぐむ (was `only`) | うむ, あぐむ | `extra-readings.tsv`: never `only` (T151) | ruby 340/196; bare 3/4; sanity xfail | T230 (#84) | a rule for the reading the list lacks |
| 箕 | み (was `only`) | み, き | `extra-readings.tsv`: never `only` (T151) | ruby 3/3; bare 3/4 | T230 (#84) | a rule for the reading the list lacks |
| 雪洞 | ぼんぼり (was `only`) | ぼんぼり, せつどう | `extra-readings.tsv`: never `only` (T151) | ruby 8/6; bare 1/3 | T230 (#84) | a rule for the reading the list lacks |
| 蒼竜 | そうりょう (was `only`) | そうりゅう, そうりょう | `extra-readings.tsv`: never `only` (T151) | ruby 6-8 each; the list has りょう only | T230 (#84) | a rule for the reading the list lacks |
| 蒼龍 | そうりょう (was `only`) | そうりゅう, そうりょう | `extra-readings.tsv`: never `only` (T151) | ruby 6-8 each; the list has りょう only | T230 (#84) | a rule for the reading the list lacks |
| 蛟竜 | こうりょう (was `only`) | こうりゅう, こうりょう | `extra-readings.tsv`: never `only` (T151) | ruby 6-8 each; the list has りょう only | T230 (#84) | a rule for the reading the list lacks |
| 蛟龍 | こうりょう (was `only`) | こうりゅう, こうりょう | `extra-readings.tsv`: never `only` (T151) | ruby 6-8 each; the list has りょう only | T230 (#84) | a rule for the reading the list lacks |
| 殿 | でん (was `dictionary`, not shown) | どの after a name or title (村長殿); でん after a number (一殿) | `readings.HAND_DEFAULTS`: the default's reading, source `default` | labels 8 fixed; ruby where it fires 956/17, 97% | T221 (#87) | a check that the default holds in context (ruby/bare precision ≥ 90%) to make it a shown rule |
| 数百 | すーひゃく (was `dictionary`, not shown) | すうひゃく | `readings.HAND_DEFAULTS`: the default's reading, source `default` | labels 12 fixed; bare 105 /208 books | T221 (#87) | a check that the default holds in context (ruby/bare precision ≥ 90%) to make it a shown rule |
| 軽々 | けいけい (was `dictionary`, not shown) | かるがる | `readings.HAND_DEFAULTS`: the default's reading, source `default` | labels 6 fixed; bare 41 /208 books | T221 (#87) | a check that the default holds in context (ruby/bare precision ≥ 90%) to make it a shown rule |
| 高名 | こうみょう (was `dictionary`, not shown) | こうめい | `readings.HAND_DEFAULTS`: the default's reading, source `default` | labels 6 fixed; bare 29 /208 books | T221 (#87) | a check that the default holds in context (ruby/bare precision ≥ 90%) to make it a shown rule |
| 敵同士 | かたきどうし (was `only` with the JMdict-only Reader) | てきどうし | `readings.HAND_DEFAULTS`: the default's reading, source `default` | labels 6 fixed; bare 15 /208 books; extra-readings.tsv てきどうし | T221 (#87) | a check that the default holds in context (ruby/bare precision ≥ 90%) to make it a shown rule |
| 樽 | そん (was `dictionary`, not shown) | たる on its own | `readings.HAND_DEFAULTS`: the default's reading, source `default` | labels 3 fixed; bare 17 /208 books | T221 (#87) | a check that the default holds in context (ruby/bare precision ≥ 90%) to make it a shown rule |
| 宴 | えん (was `dictionary`, not shown) | うたげ on its own | `readings.HAND_DEFAULTS`: the default's reading, source `default` | labels 5 fixed; bare 89 /208 books | T221 (#87) | a check that the default holds in context (ruby/bare precision ≥ 90%) to make it a shown rule |
| 身体中 | しんたいじゅう (was `only`) | からだじゅう | `readings.HAND_DEFAULTS`: the default's reading, source `default` | bare 35 /208 books; extra-readings.tsv からだじゅう | T221 (#87) | a check that the default holds in context (ruby/bare precision ≥ 90%) to make it a shown rule |
| 入れる | いれる (was `only`) in a clause without を, unless imperative, volitional, causative, passive, before くれ/もらう/おく…, or after 手に/口に… | いれる; はいれる (入る's potential) | `readings.may_be_potential` → `Reader._reading` drops `only` | training-author ruby there: はいれる 34% (129/375); bare sample 19/60; ~22% of 入れる occurrences hidden | T242 | a cue for the potential (a place + negative, a person as subject) or for the object (a thing put in) |
| 弾ける | はじける (was `only`) everywhere but after an instrument | はじける; ひける (弾く's potential: ギターが弾けない) | extra-readings.tsv (弾ける ひける): never `only` (T151); the rule after an instrument is shown | conjugated 弾け read `only` はじける: 5/40 bare ひける; ruby ひける 136 occurrences / 17 authors | T241 | more cues for playing (上手く, まともに + an instrument further back) |
| 何故 | なにゆえ (was `model`) | なぜ, なにゆえ in literary speech (何故に) | `readings.MODEL_FIX`: given as なぜ, source `dictionary` | ruby where the model said なにゆえ: 20% (135/674) right; bare 15/15 なぜ | T250 | a frame for literary なにゆえ |
| 件 | くだり (was `model`) | けん (今回の件で); くだり (a passage), くだん | `readings.MODEL_FIX`: given as けん, source `dictionary` | ruby where the model said くだり: 8/15; bare 25/25 けん | T250 | a frame for くだり (その件を読む, 件を思い出す) |
| 等 | ら (was `model`) after anything but a pronoun or person word | など, とう (記号等, 小等部), ら after names | `readings.MODEL_FIX`: given as など, source `dictionary` | ruby there: ら 53%; bare: ~0.8 per book hidden, ~23% ら (names) | T250 | a name cue before 等; とう after kanji nouns |
| 入れ | いれ (was `only`) on its own before 」/。/と言う | はいれ (入る's imperative) | `Reader._reading` (`_HAIRE`): はいれ, source `dictionary` | bare 12/12 はいれ | T251 | はいれ listed for 入れ |
| 外 | ほか (was `rule`) after a noun + の | そと (村の外の人); ほか for abstract nouns (想定の外) | `_CONTEXT_RULES['外']`: the rule needs no noun + の before | 22 bare changes: 19 そと | T252 | a cue for abstract nouns (想定, 理解, 意志) |
| 癖 | くせ (was `only`) glued after a kanji/katakana noun or a verb's stem | ぐせ, へき (逃げ癖, 女装癖) | `Reader._reading`: `only` dropped, source `dictionary` | 17 in 176 books, most ぐせ or へき | T254 | ぐせ/へき from the first part |
| 平伏す | ひれふす (was `only`) as 平伏し (平伏した, 平伏して) | へいふく (平伏 + する), ひれふす | `readings.SPLIT_TOKENS`: 平伏 へいふく, source `dictionary` | ruby over 平伏し: へいふく 109, ひれふ 53 (half the training-author post-war books); ~0.1 per book hidden | T272 | a cue for ひれふす |
| 主に | おもに (was `only`) right after の | ぬし (声の主に), あるじ (屋敷の主に) | `readings.SPLIT_TOKENS`: kept おもに, source `dictionary` | ruby there: あるじ 30, ぬし 13, おも 0; bare ~0.04 per book | T273 | split 主 + に and read 主 as after の (`_CONTEXT_RULES['主']`) |
| 地竜 | じりゅう (was `only`) | ちりゅう | `extra-readings.tsv` + `HAND_DEFAULTS`: ちりゅう, source `default` | ruby ちりゅう 41 in 10 books, じりゅう 0; bare ~0.24 per book, in fantasy series | T277 | ちりゅう listed in the frequency list |
| 方 | かた (was `rule`) after a katakana word + の and だった/だって | ほう (…したのはルークの方だった), かた | `_CONTEXT_RULES['方']`: the katakana rule needs です/でし | 365 bare changes (~0.05 per book), 15 of 15 sampled ほう | T276 | – |
| 風 | ふう (was `rule`) in ない風を unless 装う/演じる/して/見せる/意識 follows | かぜ (見えない風を感じる), ふう | `_CONTEXT_RULES['風']` | 12 bare changes, 11 かぜ (1 a name) | T276 | – |
| 熱 | ねつ (was `only`, wrong there) before すぎ/そう/emphatic いっ | あつ (熱い's stem: 熱すぎる) | `Reader._adjectives`: the token becomes 熱い, which the list reads two ways (あつい, あっつい): `dictionary` | bare 300 training-author books: 11 occurrences, all あつ | T281 | `only` for an adjective whose listed readings share the stem's reading |
| 酷 | こく (was `only`, wrong there) before すぎ/emphatic いっ and before a small ェ | ひど (酷すぎる), ひで (酷ェ) | `Reader._adjectives`: 酷い (listed with ひでぇ…) or Sudachi's 酷え: `dictionary` | bare: 6 + 1, all right after | T281 | list readings for the slang form; `only` as for 熱 |
| 速 | そく (was `only`, wrong there) before すぎ and a small ェ | はや (速すぎ), はえ (速ぇ) | `Reader._adjectives`: 速い (listed はえー…) or 速え: `dictionary` | bare: 3, all right after | T281 | as for 酷 |
| 強 | きょう (was `only`, wrong there) before a small ェ/ぇ | つえ (強ェ) | `Reader._adjectives`: Sudachi's 強え, which the list lacks: `dictionary` | bare: 4, all right after; ruby 23 of 24 つえ (one つぇ) | T281 | list readings for the slang form |
| 弱 | じゃく (was `only`, wrong there) before a small ェ/ぇ | よえ (弱ぇ) | `Reader._adjectives`: Sudachi's 弱え: `dictionary` | bare: 3, all right after; ruby 9 of 9 | T281 | list readings for the slang form |
| 臭 | しゅう (was `only`, wrong there) before a small ェ/ぇ | くせ (面倒臭ぇ) | `Reader._adjectives`: Sudachi's 臭え: `dictionary` | bare: 2, all right after; ruby 8 of 8 | T281 | list readings for the slang form |
| 宿す | しゅくする (was `only` as Sudachi's 宿する, wrong) | やどす (瞳に宿し) | `WRONG_LEMMA` 宿する → 宿す, whose listed しゅくす is a hand default to やどす: `default` | bare: 7, all やどす | T280 | `only` for 宿す (the list's しゅくす is rare and old) |
| 何時頃, 何時ごろ | いつごろ (was `only`) | いつごろ or なんじごろ (時刻は何時頃: なんじごろ) | `extra-readings.tsv` なんじごろ: not `only`, Sudachi's いつごろ, `dictionary` | bare: 25 in 300 training-author books, about half なんじごろ by hand; ruby いつごろ 2, なんどきごろ 1 | T292 | a なんじごろ rule after 今/午前/午後/夜/時刻は, いつごろ where the text asks for a date |
| 何 | なに (was `rule`, wrong there) before 玉, 作, 針, か国 | なん (何作目, 何か国語) | `readings._CONTEXT_RULES['何']`: the なに rule doesn't fire, Sudachi's なん, `dictionary` | bare: 1 in 300 books; ruby lines 11, all なん by hand | T291 | なん as a shown rule before counters |
| 行く方, 行く行く | ゆくかた, ゆくゆく (was `only`, wrong there) before a particle or !/、 | いく + ほう, いく + いく | `readings.NOT_JOINED`: read as their tokens, 行く Sudachi's いく, `dictionary` | bare: 9 in 300 books, all いく by hand; ruby 行=い 1 of 1 | T290 | 行く いく as a rule before 方が/行く |
| 辛い | つらい (was `rule`) with a taste or food word within 12 characters | からい mostly (甘くて辛くて, それに辛い！); つらい in 食べられない日も辛かった | `readings._CONTEXT_RULES['辛い']`, `_TASTE`: the model's reading kept, `dictionary` (`MODEL_UNSHOWN`) | bare: 13 changes in 300 books, ~4 wrong つらい no longer shown, ~3 right つらい hidden; ruby where つらい fires 97 → 98% | T294 | からい cues for 辛さ/辛そう of food |

## Shown again

| form | reading | shown again by | from |
|---|---|---|---|
