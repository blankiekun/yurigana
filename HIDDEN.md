# Hidden readings

Readings yurigana stopped showing as furigana (they stay in word lists), so they can be shown again once
something makes them sure. One row per form; forms and numbers only. A PR that shows one again moves its row
to "Shown again".

| form | reading no longer shown | right reading(s) in context | how hidden (code place) | evidence | from | way back |
|---|---|---|---|---|---|---|
| 入れる | いれる (was `only`) in a clause without を, unless imperative, volitional, causative, passive, before くれ/もらう/おく…, or after 手に/口に… | いれる; はいれる (入る's potential) | `readings.may_be_potential` → `Reader._reading` drops `only` | training-author ruby there: はいれる 34% (129/375); bare sample 19/60; ~22% of 入れる occurrences hidden | T242 | a cue for the potential (a place + negative, a person as subject) or for the object (a thing put in) |
| 弾ける | はじける (was `only`) everywhere but after an instrument | はじける; ひける (弾く's potential: ギターが弾けない) | extra-readings.tsv (弾ける ひける): never `only` (T151); the rule after an instrument is shown | conjugated 弾け read `only` はじける: 5/40 bare ひける; ruby ひける 136 occurrences / 17 authors | T241 | more cues for playing (上手く, まともに + an instrument further back) |

## Shown again

| form | reading | shown again by | from |
|---|---|---|---|
