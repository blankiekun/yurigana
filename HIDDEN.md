# Hidden readings

Readings yurigana stopped showing as furigana (they stay in word lists), so they can be shown again once
something makes them sure. One row per form; forms and numbers only. A PR that shows one again moves its row
to "Shown again".

| form | reading no longer shown | right reading(s) in context | how hidden (code place) | evidence | from | way back |
|---|---|---|---|---|---|---|
| 入れる | いれる (was `only`) in a clause without を, unless imperative, volitional, causative, passive, before くれ/もらう/おく…, or after 手に/口に… | いれる; はいれる (入る's potential) | `readings.may_be_potential` → `Reader._reading` drops `only` | training-author ruby there: はいれる 34% (129/375); bare sample 19/60; ~22% of 入れる occurrences hidden | T242 | a cue for the potential (a place + negative, a person as subject) or for the object (a thing put in) |
| 弾ける | はじける (was `only`) everywhere but after an instrument | はじける; ひける (弾く's potential: ギターが弾けない) | extra-readings.tsv (弾ける ひける): never `only` (T151); the rule after an instrument is shown | conjugated 弾け read `only` はじける: 5/40 bare ひける; ruby ひける 136 occurrences / 17 authors | T241 | more cues for playing (上手く, まともに + an instrument further back) |
| 何故 | なにゆえ (was `model`) | なぜ, なにゆえ in literary speech (何故に) | `readings.MODEL_FIX`: given as なぜ, source `dictionary` | ruby where the model said なにゆえ: 20% (135/674) right; bare 15/15 なぜ | T250 | a frame for literary なにゆえ |
| 件 | くだり (was `model`) | けん (今回の件で); くだり (a passage), くだん | `readings.MODEL_FIX`: given as けん, source `dictionary` | ruby where the model said くだり: 8/15; bare 25/25 けん | T250 | a frame for くだり (その件を読む, 件を思い出す) |
| 等 | ら (was `model`) after anything but a pronoun or person word | など, とう (記号等, 小等部), ら after names | `readings.MODEL_FIX`: given as など, source `dictionary` | ruby there: ら 53%; bare: ~0.8 per book hidden, ~23% ら (names) | T250 | a name cue before 等; とう after kanji nouns |
| 入れ | いれ (was `only`) on its own before 」/。/と言う | はいれ (入る's imperative) | `Reader._reading` (`_HAIRE`): はいれ, source `dictionary` | bare 12/12 はいれ | T251 | はいれ listed for 入れ |
| 外 | ほか (was `rule`) after a noun + の | そと (村の外の人); ほか for abstract nouns (想定の外) | `_CONTEXT_RULES['外']`: the rule needs no noun + の before | 22 bare changes: 19 そと | T252 | a cue for abstract nouns (想定, 理解, 意志) |
| 癖 | くせ (was `only`) glued after a kanji/katakana noun or a verb's stem | ぐせ, へき (逃げ癖, 女装癖) | `Reader._reading`: `only` dropped, source `dictionary` | 17 in 176 books, most ぐせ or へき | T254 | ぐせ/へき from the first part |

## Shown again

| form | reading | shown again by | from |
|---|---|---|---|
