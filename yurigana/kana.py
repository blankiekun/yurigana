"""Kana and kanji helpers shared by every module (no imports from the package, so no cycles)."""
import itertools
import re

HAS_KANJI = re.compile(r'[㐀-䶿一-鿿豈-﫿]')
HIRAGANA_WORD = re.compile(r'^[ぁ-ゖ]+$')
KANA_READING = re.compile(r'^[ぁ-ゖー]+$')  # loanwords keep ー: ラーメン屋 らーめんや


KANJI = re.compile('[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\U00020000-\U0003134f]')  # is_kanji's characters


def is_kanji(char: str) -> bool:
    code = ord(char)
    return (0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0xF900 <= code <= 0xFAFF
            or 0x20000 <= code <= 0x3134F)


_HIRAGANA = {c: c - 0x60 for c in range(ord('ァ'), ord('ヶ') + 1)}


def to_hiragana(text: str) -> str:
    return text.translate(_HIRAGANA)


_VOWEL = {**dict.fromkeys('あかさたなはまやらわがざだばぱぁゃゎ', 'あ'), **dict.fromkeys('いきしちにひみりぎじぢびぴぃ', 'い'),
          **dict.fromkeys('うくすつぬふむゆるぐずづぶぷぅゅ', 'う'), **dict.fromkeys('えけせてねへめれげぜでべぺぇ', 'い'),
          **dict.fromkeys('おこそとのほもよろごぞどぼぽぉょ', 'う')}


def long_vowels(reading: str) -> str:
    """ー as the kana it stands for after a kana: o-row う, e-row い (こんぺいとー: こんぺいとう)."""
    return re.sub('(?<=(.))ー', lambda m: _VOWEL.get(m.group(1), 'ー'), reading)


def spelling(reading: str) -> str:
    """One spelling of a reading's sounds: ー spelled out, づ ず and ぢ じ alike (みかづき, みかずき)."""
    return long_vowels(reading).replace('づ', 'ず').replace('ぢ', 'じ')


VOICED = {'か': 'が', 'き': 'ぎ', 'く': 'ぐ', 'け': 'げ', 'こ': 'ご', 'さ': 'ざ', 'し': 'じ', 'す': 'ず',
          'せ': 'ぜ', 'そ': 'ぞ', 'た': 'だ', 'ち': 'ぢ', 'つ': 'づ', 'て': 'で', 'と': 'ど', 'は': 'ばぱ',
          'ひ': 'びぴ', 'ふ': 'ぶぷ', 'へ': 'べぺ', 'ほ': 'ぼぽ'}
UNVOICED = str.maketrans({v: k for k, vs in VOICED.items() for v in vs})
_VOICED_OBSTRUENT = re.compile('[がぎぐげござじずぜぞだぢづでどばびぶべぼ]')


def rendaku(reading: str) -> str | None:
    """The reading voiced at its start (たな → だな), or None: it can't voice, or Lyman's law
    (a voiced obstruent later in it, かぜ) keeps it from voicing."""
    voiced = VOICED.get(reading[:1], '')[:1]
    return voiced and not _VOICED_OBSTRUENT.search(reading[1:]) and voiced + reading[1:] or None


_SMALL = str.maketrans('つやゆよ', 'っゃゅょ')
_YOUON_AFTER = set('きぎしじちぢにひびぴみり')


def small_kana(reading: str):
    """Older books set ruby in large kana (いつしよ for いっしょ): `reading` with some of its つ
    (not first) and its や/ゆ/よ after an i-row kana made small. Small ぁぃぅぇぉ aren't tried:
    no hiragana reading of a kanji word uses them."""
    spots = [i for i, c in enumerate(reading)
             if i and (c == 'つ' or (c in 'やゆよ' and reading[i - 1] in _YOUON_AFTER))][:6]
    for k in range(1, len(spots) + 1):
        for chosen in itertools.combinations(spots, k):
            yield ''.join(c.translate(_SMALL) if i in chosen else c for i, c in enumerate(reading))


_LARGE = str.maketrans('ぁぃぅぇぉゃゅょ', 'あいうえおやゆよ')
_E_ROW = dict(zip('あかさたなはまらわがざだばぱおこそとのほもろごぞどぼぽ', 'えけせてねへめれえげぜでべぺえけせてねへめれげぜでべぺ'))
_I_ROW = dict(zip('うくすつぬふむるぐずぶぷ', 'いきしちにひみりぎじびぴ'))
# misspellings by one kana for another (ぜいいん, いきよい, しやわせ, とゆう, たあいない, おもひで); not い/え or う/え
# (意固地 えこじ, 成しうる) nor よ/い (仲の良い いい)
_LONG = {'お': 'う', 'え': 'い'}
_SWAPS = ({'ん', 'い'}, {'お', 'よ'}, {'あ', 'や'}, {'い', 'ゆ'}, {'わ', 'あ'}, {'ひ', 'い'})


def _sounds(reading: str) -> str:
    """A reading's sounds without emphasis: spelling(), small kana large, っ dropped, long お/え as う/い
    (ほおって ほうって, おねえ おねい)."""
    text = spelling(reading).translate(_LARGE).replace('っ', '')
    return re.sub('(?<=([^あいうえお]))[おえ]', lambda m: _LONG[m.group(0)] if _VOWEL.get(m.group(1)) == _LONG[m.group(0)]
                  else m.group(0), text)


def colloquial(reading: str, standard: str) -> bool:
    """Whether `reading` is a casual, emphatic or misspelt way to write `standard` (Jiten's list ranks
    such readings with the word: 長い なっがい, 当たり前 あたりめえ, 気付く きずく, 雰囲気 ふいんき, 全員 ぜいいん):
    the same sounds (_sounds), a final ai/ae/oi as ee or ui as ii (なげえ, さみい), one ん or long-vowel う
    added or dropped (おんなじ, しろと), two kana swapped, or one soft kana for another (_SWAPS), the last
    three in readings of 3+ kana. Not a reading of another sound (鳥 ちょう, 河 が)."""
    a, b = _sounds(reading), _sounds(standard)
    if a == b:
        return True
    if len(standard) > 1 and (standard[-1] in 'いえ' and standard[-2] in _E_ROW and a == b[:-2] + _E_ROW[standard[-2]] + 'い'
                              or standard[-1] == 'い' and standard[-2] in _I_ROW and a == b[:-2] + _I_ROW[standard[-2]] + 'い'):
        return True
    long, short = (a, b) if len(a) > len(b) else (b, a)
    if len(short) < 3:
        return False
    if len(long) == len(short) + 1:
        return any(long[:i] + long[i + 1:] == short and (long[i] == 'ん' or long[i] == 'う' and _VOWEL.get(long[i - 1]) == 'う')
                   for i in range(1, len(long)))
    diff = [i for i in range(len(a)) if len(a) == len(b) and a[i] != b[i]]
    return (len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]
            or len(diff) == 1 and {a[diff[0]], b[diff[0]]} in _SWAPS)
