"""Builds yurigana/jmdict-pairs.json.gz: the (written form, reading) pairs of JMdict's entries,
the reading list Reader() uses when it is given none. From JMdict (EDRDG, CC BY-SA 4.0,
http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz).

Only forms with kanji. A reading goes with the forms its re_restr names (all of them without
one, none with re_nokanji). Irregular, out-dated, rare and search-only kana (ik/ok/rk/sk) are
left out. Kanji forms tagged rare (rK) etc. stay: 居る is rK, yet a book that writes it means
いる (dropping it left only おる). Readings are hiragana (katakana converted, as Sudachi's are),
so タバコ over 煙草 is たばこ.

  python -I tools/jmdict_pairs.py JMdict_e.gz

Output: {"jmdict": "<the date JMdict was created>", "pairs": {form: "reading reading"}}.
"""
import gzip
import io
import json
import os
import re
import sys
from xml.etree import ElementTree

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yurigana', 'jmdict-pairs.json.gz')
LEFT_OUT = {'ik', 'ok', 'rk', 'sk'}
HAS_KANJI = re.compile(r'[㐀-䶿一-鿿豈-﫿\U00020000-\U0003134F]')


def hiragana(text):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in text)


def pairs(xml: bytes) -> dict:
    """form -> readings, in JMdict's order."""
    # Keep the tags' entity names (&rk;) rather than their expanded text.
    xml = re.sub(rb'<re_inf>&(\w+);', rb'<re_inf>\1', xml)
    found = {}
    for _, entry in ElementTree.iterparse(io.BytesIO(xml)):
        if entry.tag != 'entry':
            continue
        forms = [k.findtext('keb') for k in entry.iter('k_ele')]
        for r in entry.iter('r_ele'):
            if LEFT_OUT & {i.text for i in r.iter('re_inf')} or r.find('re_nokanji') is not None:
                continue
            restr = {x.text for x in r.iter('re_restr')}
            reading = hiragana(r.findtext('reb'))
            for form in forms:
                if HAS_KANJI.search(form) and (not restr or form in restr):
                    readings = found.setdefault(form, [])
                    if reading not in readings:
                        readings.append(reading)
        entry.clear()
    return found


def main(path):
    xml = gzip.open(path).read()
    created = re.search(rb'<!-- JMdict created: ([\d-]+) -->', xml)
    found = pairs(xml)
    data = {'jmdict': created.group(1).decode() if created else None,
            'pairs': {form: ' '.join(r) for form, r in sorted(found.items())}}
    with gzip.GzipFile(OUT, 'wb', compresslevel=9, mtime=0) as f:
        f.write(json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode())
    print(len(found), 'forms,', sum(map(len, found.values())), 'pairs, JMdict', data['jmdict'],
          os.path.getsize(OUT), 'bytes')


if __name__ == '__main__':
    main(sys.argv[1])
