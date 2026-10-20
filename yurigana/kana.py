"""Kana and kanji helpers shared by every module (no imports from the package, so no cycles)."""
import itertools
import re

HAS_KANJI = re.compile(r'[㐀-䶿一-鿿豈-﫿]')
HIRAGANA_WORD = re.compile(r'^[ぁ-ゖ]+$')
KANA_READING = re.compile(r'^[ぁ-ゖー]+$')  # loanwords keep ー: ラーメン屋 らーめんや


def is_kanji(char: str) -> bool:
    code = ord(char)
    return (0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0xF900 <= code <= 0xFAFF
            or 0x20000 <= code <= 0x3134F)


def to_hiragana(text: str) -> str:
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in text)


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
