"""Builds yurigana/kanji-readings.json: on and kun readings (hiragana, okurigana dropped) of
常用 and 人名用 kanji (KANJIDIC2 grade 1-10), from KANJIDIC2 (EDRDG, CC BY-SA 4.0,
https://www.edrdg.org/kanjidic/kanjidic2.xml.gz).

  python tools/kanji_readings.py kanjidic2.xml.gz
"""
import gzip
import json
import os
import sys
from xml.etree import ElementTree

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yurigana', 'kanji-readings.json')


def hiragana(text):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in text)


readings = {}
for char in ElementTree.parse(gzip.open(sys.argv[1])).getroot().iter('character'):
    grade = char.findtext('misc/grade')
    if grade and int(grade) <= 10:
        found = []
        for r in char.iter('reading'):
            if r.get('r_type') in ('ja_on', 'ja_kun'):
                value = hiragana(r.text.split('.')[0].strip('-'))
                if value and value not in found:
                    found.append(value)
        if found:
            readings[char.findtext('literal')] = ' '.join(found)
json.dump(readings, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
print(len(readings), 'kanji with readings')
