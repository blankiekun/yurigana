"""Builds yurigana/cue-words.json.gz: word classes for yurigana.cues from the Japanese WordNet
(NICT / Francis Bond, https://github.com/bond-lab/wnja, wnjpn-ok.tab.gz) and Princeton WordNet 3.0
(https://wordnetcode.princeton.edu/3.0/WordNet-3.0.tar.gz, dict/data.noun and dict/lexnames). Both
licences ask for their notices on every copy, so the file carries them (`_notice`).

  python tools/cue_words.py wnjpn-ok.tab.gz WordNet-3.0/dict WordNet-3.0/LICENSE wnja-license.txt

ABSTRACT: Japanese nouns, kanji only and two or more of them, all of whose WordNet senses are acts,
thoughts, states, communication, attributes, relations, feelings, motives or groups (指導, 感化,
一笑, 社会): what one can be "under" (指導の下に, 社会の下で: 下 もと).
"""
import gzip
import json
import os
import re
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yurigana', 'cue-words.json.gz')
ABSTRACT = {'noun.act', 'noun.cognition', 'noun.state', 'noun.communication', 'noun.attribute', 'noun.relation',
            'noun.feeling', 'noun.motive', 'noun.group'}

wnjpn, wordnet, *licences = sys.argv[1:]
names = {int(n): name for n, name, _ in (line.split() for line in open(os.path.join(wordnet, 'lexnames')))}
lexname = {}
for line in open(os.path.join(wordnet, 'data.noun'), encoding='latin-1'):
    if not line.startswith('  '):
        offset, filenum = line.split()[:2]
        lexname[offset + '-n'] = names[int(filenum)]
senses = {}
for line in gzip.open(wnjpn, 'rt', encoding='utf-8'):
    synset, lemma, _ = line.rstrip('\n').split('\t')
    if synset in lexname:
        senses.setdefault(lemma, set()).add(lexname[synset])
classes = {'ABSTRACT': sorted(w for w, s in senses.items() if s <= ABSTRACT and re.fullmatch(r'[一-鿿々]{2,}', w))}
notice = '\n\n'.join(open(path, encoding='utf-8').read().strip() for path in licences)
data = json.dumps({'_notice': notice, **classes}, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
with open(OUT, 'wb') as f:
    f.write(gzip.compress(data, mtime=0))
print({k: len(v) for k, v in classes.items()})
