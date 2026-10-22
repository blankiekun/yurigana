"""A book's era from its text: 'prewar' (written before 1946, also in modern kana as Aozora Bunko gives it),
'period' (post-war historical fiction) or 'modern'. Reader.read(era='prewar') then reads with the
pre-war readings of prewar-readings.tsv.

prewar: a linear score over era-grams.tsv, character 1-2-grams (mostly post-war vocabulary such as 状況, 確認,
情報 that pre-war books lack). period: words of samurai fiction (殿, 藩, 奉行, 拙者, 〜左衛門) at least 30.6 per
10,000 characters (the 98th percentile of post-war books). Books under 10,000 characters are 'modern'."""
import math
import os
import re
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
MIN_CHARACTERS = 10000
_PERIOD = re.compile('殿|侍|藩|奉行|浪人|拙者|御座|城下|武士|家老|旗本|与力|同心|大名|太刀|足軽|主君|町人|岡っ引|ござ[るりい]|'
                     '上意|江戸|御家|刀|槍|寺|姫|若党|下郎|身共|それがし|某|左衛門|右衛門|兵衛|之助|之介|主水|やい|おのれ')
PERIOD_THRESHOLD = 30.6


def _grams(path=os.path.join(_HERE, 'era-grams.tsv')):
    grams, threshold = {}, 0.0
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.startswith('# threshold'):
                threshold = float(line.split('\t')[1])
            elif not line.startswith('#'):
                gram, weight, centre = line.rstrip('\n').split('\t')
                grams[gram] = (float(weight), float(centre))
    return grams, threshold


GRAMS, THRESHOLD = _grams()


def prewar_score(text: str) -> float:
    """Above THRESHOLD: pre-war."""
    per = len(text) / 10000
    counts = Counter(text[i:i + n] for n in (1, 2) for i in range(len(text) - n + 1))
    return sum(w * (math.log1p(counts[g] / per) - c) for g, (w, c) in GRAMS.items()) / len(GRAMS)


def book_era(text: str) -> str:
    """'prewar', 'period' or 'modern' for a whole book's text (a long sample does too)."""
    if len(text) < MIN_CHARACTERS:
        return 'modern'
    if prewar_score(text) > THRESHOLD:
        return 'prewar'
    if len(_PERIOD.findall(text)) / (len(text) / 10000) >= PERIOD_THRESHOLD:
        return 'period'
    return 'modern'


def _prewar_readings(path=os.path.join(_HERE, 'prewar-readings.tsv')) -> dict:
    with open(path, encoding='utf-8') as f:
        rows = [line.rstrip('\n').split('\t') for line in f if not line.startswith('#')]
    return {(form, reading or None): prewar for form, reading, prewar, *_ in rows}


PREWAR_READINGS = _prewar_readings()
