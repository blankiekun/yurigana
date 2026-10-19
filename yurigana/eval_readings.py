"""How often yurigana gives a word the right reading in context, on hand-written sentences.

readings-test.tsv: book id or '-', sentence, form, character offset of the form in the
sentence, gold reading (hiragana; several allowed as a|b), source ('hand' = written and
checked by hand, 'hand-ruby' = the same with the book's ruby in Aozora markup, 人気《ひとけ》
or ｜人気《ひとけ》; offsets count without the markup). Prints accuracy per form and the
macro average (each form weighs the same).

With --dictionary (a rank-based Yomitan frequency list with readings, e.g. Jiten's), ruby,
the context rules and then the reading model (--model, default the public table) give the
reading (ruby_reading, context_reading, ReadingModel), and the result without ruby is
printed too; without it none applies.

  python -m yurigana.eval_readings [readings-test.tsv] [--dictionary frequency-dictionary.zip]
"""
import argparse
import csv
import os
from collections import defaultdict

from .reading_model import PUBLIC_TABLE

HERE = os.path.dirname(os.path.abspath(__file__))


def score(results, label):
    accuracy = [sum(ok for ok, *_ in rows) / len(rows) for rows in results.values()]
    if not accuracy:
        return
    total = [ok for rows in results.values() for ok, *_ in rows]
    print(f'{label}macro {sum(accuracy) / len(accuracy):.1%} over {len(accuracy)} forms, '
          f'micro {sum(total) / len(total):.1%} over {len(total)} sentences')


def main(path, dictionary=None, model_path=None):
    from .readings import _HIRAGANA_WORD, DEFAULT_READINGS, conjugated_reading, context_reading, ruby_reading, to_hiragana
    from .reading_model import ReadingModel
    from .text import aozora_text
    from .tokens import SudachiTokenizer
    from .yomitan import reading_ranks
    analyzer = SudachiTokenizer()
    tokenizer = analyzer.tokenizer
    known, model = (), None
    if dictionary:
        known = reading_ranks(dictionary)
        model = ReadingModel.load(model_path) if model_path and os.path.exists(model_path) else None
    readings = defaultdict(list)
    for form, reading in known:
        if _HIRAGANA_WORD.match(reading):
            readings[form].append(reading)
    results, without_ruby = defaultdict(list), defaultdict(list)
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
            hints = []
            sentence, form, offset = aozora_text(row['sentence'], None, hints), row['form'], int(row['offset'])
            if sentence[offset:offset + len(form)] != form:
                raise ValueError(f'{form} is not at {offset} in {sentence}')
            token = next(m for m in tokenizer.tokenize(sentence) if m.begin() <= offset < m.end())
            # Sudachi's reading: of whole, unconjugated words; a conjugated one's picks a listed reading.
            sudachi = to_hiragana(token.reading_form()) if token.surface() == token.dictionary_form() else (
                conjugated_reading(token.surface(), token.dictionary_form(), to_hiragana(token.reading_form()),
                                   readings.get(token.dictionary_form(), ())))
            default = dictionary and DEFAULT_READINGS.get((token.dictionary_form(), sudachi))
            sudachi = default if default and (token.dictionary_form(), default) in known else sudachi
            ruby = ruby_reading({s: (e, r) for s, e, r in hints}, token.begin(), token.surface(),
                                token.dictionary_form(), known)
            tokens = list(analyzer.tokens(sentence))
            index = next((i for i, t in enumerate(tokens) if t.begin == token.begin()), None)
            previous = tokens[index - 1] if index else None
            previous_pos = previous.part_of_speech() if previous and previous.begin + len(previous.surface()) == token.begin() else None
            rule = context_reading(sentence, token.begin(), token.surface(), token.dictionary_form(), known, previous_pos)
            if model and index is not None:
                rule = rule or model.reading(sentence, tokens, index, token.dictionary_form(), known)
            for reading, out in ((ruby or rule or sudachi, results), (rule or sudachi, without_ruby)):
                ok = token.surface() == form and reading in row['reading'].split('|')
                got = reading if token.surface() == form else f'{token.surface()}:{reading}'
                out[form].append((ok, got, row))
    print('form\tright\treading given (gold)')
    for form, rows in results.items():
        wrong = ', '.join(f"{got} ({row['reading']})" for ok, got, row in rows if not ok)
        print(f"{form}\t{sum(ok for ok, *_ in rows)}/{len(rows)}\t{wrong}")
    if dictionary:
        score(without_ruby, 'without ruby: ')
        ruby_rows = {form: [r for r in rows if r[2]['source'].endswith('-ruby')] for form, rows in results.items()}
        plain_rows = {form: [r for r in rows if r[2]['source'].endswith('-ruby')] for form, rows in without_ruby.items()}
        score({k: v for k, v in plain_rows.items() if v}, 'ruby rows without ruby: ')
        score({k: v for k, v in ruby_rows.items() if v}, 'ruby rows with ruby: ')
    score(results, 'with ruby: ' if dictionary else '')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', default=os.path.join(HERE, 'readings-test.tsv'))
    parser.add_argument('--dictionary', help="rank-based Yomitan frequency list with readings (e.g. Jiten's)")
    parser.add_argument('--model', default=PUBLIC_TABLE, help='reading model table; with --dictionary')
    args = parser.parse_args()
    main(args.path, args.dictionary, args.model)
