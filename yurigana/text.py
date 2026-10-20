"""Plain text of books (EPUB, HTMLZ, Aozora-style TXT) with their ruby kept as reading
hints: (start, end, reading) offsets in the plain text, for ruby_reading.
"""
import html
import posixpath
import re
import zipfile
from xml.etree import ElementTree

from .kana import is_kanji

KATAKANA_READING = re.compile(r'^[ァ-ヺー・]+$')

_BLOCK_END = re.compile(r'</(?:p|div|h[1-6]|li|blockquote|tr|dd|dt)\s*>|<br\s*/?>', re.I)
_RT = re.compile(r'<rt[\s>].*?</rt>|<rp[\s>].*?</rp>', re.S | re.I)
_SKIP = re.compile(r'<(head|script|style)[\s>].*?</\1>', re.S | re.I)
_TAG = re.compile(r'<[^>]+>')


_RUBY = re.compile(r'<ruby[\s>](.*?)</ruby>', re.S | re.I)
_RT_TEXT = re.compile(r'<rt[\s>](.*?)</rt>', re.S | re.I)
# Aozora-style ruby in TXT: ｜base《reading》, or a run of kanji followed by 《reading》.
_AOZORA_RUBY = re.compile(r'(?:｜([^《｜\n]+)|([㐀-䶿一-鿿豈-﫿々〆ヶ]+))《([^》]*)》')
# Spine documents that aren't the story: tables of contents, colophons (奥付), store notices, ads.
_FRONT_MATTER = re.compile(r'^(?:toc|nav|navdoc|contents|colophon|okuduke|okuzuke|caution|copyright'
                           r'|ad|ads|advert|advertisement)[-_]?\d*$', re.I)


def _count_ruby(ruby: dict, base: str, reading: str):
    """Furigana statistics: kanji under ruby, and readings in katakana (マジ over 本気)."""
    kanji = sum(1 for c in base if is_kanji(c))
    if not kanji:
        return
    ruby['ruby'] = ruby.get('ruby', 0) + 1
    ruby['kanji'] = ruby.get('kanji', 0) + kanji
    if KATAKANA_READING.match(reading.strip()):
        ruby['katakana'] = ruby.get('katakana', 0) + 1


# Ruby kept as reading hints: the base between U+FFF9 and U+FFFA, the reading up to U+FFFB
# (Unicode's interlinear annotation characters), taken out again by _take_hints.
_HINT = re.compile('\ufff9([^\ufff9-\ufffb]*)\ufffa([^\ufff9-\ufffb]*)\ufffb')
_HINT_MARKS = dict.fromkeys(range(0xFFF9, 0xFFFC))
_RUBY_ELEMENT = re.compile(r'<ruby\b[^>]*>(.*?)</ruby>', re.S | re.I)
_RT_ELEMENT = re.compile(r'<rt\b[^>]*>(.*?)</rt>', re.S | re.I)


def _mark_ruby(base: str, reading: str) -> str:
    return '\ufff9' + base + '\ufffa' + re.sub(r'[\s《》｜]', '', reading) + '\ufffb'


def _take_hints(marked: str, plain: str, hints: list, offset: int = 0):
    """Adds (start, end, reading) of each ruby marked in `marked` to `hints`, offsets in `plain`
    plus `offset`; nothing when `marked` without its marks isn't `plain` (odd markup), so
    hints never change the text."""
    pieces, found, at, length = [], [], 0, 0
    for match in _HINT.finditer(marked):
        before = marked[at:match.start()].translate(_HINT_MARKS)
        base = match.group(1)
        length += len(before)
        found.append((offset + length, offset + length + len(base), match.group(2)))
        length += len(base)
        pieces += [before, base]
        at = match.end()
    pieces.append(marked[at:].translate(_HINT_MARKS))
    if ''.join(pieces) == plain:
        hints.extend(found)


def _lines(text: str) -> str:
    return '\n'.join(line.strip() for line in text.splitlines() if line.strip())


def _markup_to_text(markup: str, ruby: dict | None = None, hints: list | None = None) -> str:
    markup = _SKIP.sub('', markup)
    if ruby is not None:
        for match in _RUBY.finditer(markup):
            inner = match.group(1)
            reading = ''.join(_TAG.sub('', r) for r in _RT_TEXT.findall(inner))
            _count_ruby(ruby, html.unescape(_TAG.sub('', _RT.sub('', inner))), html.unescape(reading))
    text = _lines(html.unescape(_TAG.sub('', _BLOCK_END.sub('\n', _RT.sub('', markup)))))
    if hints is not None:
        marked = _RUBY_ELEMENT.sub(lambda m: _mark_ruby(
            _RT.sub('', m.group(1)), ''.join(_TAG.sub('', r) for r in _RT_ELEMENT.findall(m.group(1)))), markup)
        _take_hints(_markup_to_text(marked), text, hints)
    return text


def _epub_documents(archive: zipfile.ZipFile):
    container = ElementTree.fromstring(archive.read('META-INF/container.xml'))
    rootfile = next(el for el in container.iter() if el.tag.endswith('rootfile')).get('full-path')
    opf = ElementTree.fromstring(archive.read(rootfile))
    base = posixpath.dirname(rootfile)
    manifest = {el.get('id'): el.get('href') for el in opf.iter()
                if el.tag.endswith('}item') and 'html' in (el.get('media-type') or '')}
    skip = {el.get('id') for el in opf.iter() if el.tag.endswith('}item') and 'nav' in (el.get('properties') or '')}
    skip_hrefs = {(el.get('href') or '').split('#')[0] for el in opf.iter()
                  if el.tag.endswith('}reference') and el.get('type') in ('toc', 'copyright-page', 'colophon')}
    spine = [el for el in opf.iter() if el.tag.endswith('}itemref') and el.get('idref') in manifest]
    story = [el for el in spine if el.get('linear') != 'no' and el.get('idref') not in skip
             and manifest[el.get('idref')] not in skip_hrefs
             and not _FRONT_MATTER.match(posixpath.splitext(posixpath.basename(manifest[el.get('idref')]))[0])]
    for el in story or spine:
        yield posixpath.normpath(posixpath.join(base, manifest[el.get('idref')]))


def aozora_text(text: str, ruby: dict | None = None, hints: list | None = None) -> str:
    """Text with Aozora-style ruby (漢字《かんじ》 and ｜ markers) taken out."""
    if ruby is not None:
        for match in _AOZORA_RUBY.finditer(text):
            _count_ruby(ruby, match.group(1) or match.group(2), match.group(3))
    plain = _lines(re.sub(r'《[^》]*》|｜', '', text))
    if hints is not None:
        marked = _AOZORA_RUBY.sub(lambda m: _mark_ruby(m.group(1) or m.group(2), m.group(3)), text)
        _take_hints(_lines(re.sub(r'《[^》]*》|｜', '', marked)), plain, hints)
    return plain


def book_text(path: str, fmt: str, ruby: dict | None = None, hints: list | None = None) -> str:
    """Plain text of a book, one paragraph per line, without furigana (counted into `ruby`
    if given; with `hints`, ruby positions are added to it, see _take_hints), tables of
    contents, colophons or ads."""
    if fmt == 'TXT':
        raw = open(path, 'rb').read()
        for encoding in ('utf-8-sig', 'shift_jis', 'cp932', 'euc_jp', 'utf-16'):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = raw.decode('utf-8', 'replace')
        return aozora_text(text, ruby, hints)

    with zipfile.ZipFile(path) as archive:
        if fmt == 'HTMLZ':
            names = sorted(n for n in archive.namelist() if n.lower().endswith(('.html', '.xhtml', '.htm')))
        else:
            names = list(_epub_documents(archive))
        parts, offset = [], 0
        for name in names:
            try:
                part_hints = [] if hints is not None else None
                part = _markup_to_text(archive.read(name).decode('utf-8', 'replace'), ruby, part_hints)
            except KeyError:
                continue
            if part:
                if part_hints:
                    hints.extend((start + offset, end + offset, reading) for start, end, reading in part_hints)
                parts.append(part)
                offset += len(part) + 1
    return '\n'.join(parts)

