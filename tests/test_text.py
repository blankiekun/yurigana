"""Tests for yurigana.text: plain text and ruby hints."""
import os
import tempfile
import unittest
import zipfile

from yurigana.text import aozora_text, book_text

OPF = '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<manifest>
  <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
  <item id="c1" href="text/p-001.xhtml" media-type="application/xhtml+xml"/>
  <item id="col" href="text/colophon.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine><itemref idref="nav"/><itemref idref="c1"/><itemref idref="col"/></spine>
</package>'''


def epub(chapter: str):
    path = os.path.join(tempfile.mkdtemp(), 'book.epub')
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('META-INF/container.xml', '<container><rootfiles><rootfile full-path="OEBPS/content.opf"/>'
                                                   '</rootfiles></container>')
        archive.writestr('OEBPS/content.opf', OPF)
        archive.writestr('OEBPS/nav.xhtml', '<html><body><p>目次</p></body></html>')
        archive.writestr('OEBPS/text/p-001.xhtml', f'<html><body>{chapter}</body></html>')
        archive.writestr('OEBPS/text/colophon.xhtml', '<html><body><p>発行所　株式会社</p></body></html>')
    return path


class BookTextTest(unittest.TestCase):
    def test_skips_contents_and_colophon_and_counts_ruby(self):
        ruby = {}
        text = book_text(epub('<p><ruby>本気<rt>マジ</rt></ruby>で<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp>'
                              '</ruby>を読む。</p>'), 'EPUB', ruby)
        self.assertEqual(text, '本気で漢字を読む。')
        self.assertEqual(ruby, {'ruby': 2, 'kanji': 4, 'katakana': 1})

    def test_aozora_ruby_in_txt(self):
        path = os.path.join(tempfile.mkdtemp(), 'book.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('吾輩《わがはい》は｜猫《ねこ》である。\n')
        ruby = {}
        self.assertEqual(book_text(path, 'TXT', ruby), '吾輩は猫である。')
        self.assertEqual(ruby, {'ruby': 2, 'kanji': 3})


class RubyHintTest(unittest.TestCase):
    def hinted(self, text, hints):
        return [(text[start:end], reading) for start, end, reading in hints]

    def test_epub_hints_are_offsets_in_the_plain_text(self):
        hints = []
        text = book_text(epub('<p>夜の<ruby class="r">公園<rt class="x">こうえん</rt></ruby>は'
                              '<ruby><rb>人気</rb><rp>(</rp><rt>ひと<span>け</span></rt><rp>)</rp></ruby>がない。</p>'
                              '<p><ruby>本気<rt>マジ</rt></ruby>だ</p>'), 'EPUB', {}, hints)
        self.assertEqual(text, '夜の公園は人気がない。\n本気だ')
        self.assertEqual(self.hinted(text, hints), [('公園', 'こうえん'), ('人気', 'ひとけ'), ('本気', 'マジ')])

    def test_odd_markup_gives_no_hints_and_the_same_text(self):
        hints = []
        text = book_text(epub('<p><ruby> 人気<rt>ひとけ</rt></ruby>がない</p>'), 'EPUB', None, hints)
        self.assertEqual((text, hints), ('人気がない', []))

    def test_aozora_hints(self):
        hints = []
        text = aozora_text('　吾輩《わがはい》は\n｜猫《ねこ》である。\n', None, hints)
        self.assertEqual(text, '吾輩は\n猫である。')
        self.assertEqual(self.hinted(text, hints), [('吾輩', 'わがはい'), ('猫', 'ねこ')])


if __name__ == '__main__':
    unittest.main()
