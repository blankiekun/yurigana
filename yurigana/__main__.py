"""python -m yurigana [--known LIST] [TEXT ...]: prints each TEXT (or each line of stdin) with
furigana, 漢字[かんじ]."""
import argparse
import sys

from . import furigana

parser = argparse.ArgumentParser(prog='yurigana', description=__doc__.split('\n')[0])
parser.add_argument('--known', help="a reading list, as Reader(known=...): e.g. Jiten's frequency list zip")
parser.add_argument('text', nargs='*', help='text to read (default: stdin, line by line)')
args = parser.parse_args()
for line in args.text or (line.rstrip('\n') for line in sys.stdin):
    print(furigana(line, args.known))
