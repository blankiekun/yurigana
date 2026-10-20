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

## Shown again

| form | reading | shown again by | from |
|---|---|---|---|
