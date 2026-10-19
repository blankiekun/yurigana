"""Readings from a rank-based Yomitan frequency dictionary (e.g. Jiten's list,
jiten.moe/frequency-dictionaries): the `known` set of (form, reading) pairs."""
import json
import math
import zipfile

# Jiten's list is one 55 MB bank; anything far bigger is likely a deflate bomb.
MAX_MEMBER_BYTES = 128 * 1024 * 1024


def _read(archive: zipfile.ZipFile, name: str) -> bytes:
    if archive.getinfo(name).file_size > MAX_MEMBER_BYTES:
        raise ValueError(f'{name} is too large')
    return archive.read(name)


def entries(path: str):
    """(term, reading or None, rank) from a rank-based Yomitan frequency dictionary."""
    with zipfile.ZipFile(path) as archive:
        index = json.loads(_read(archive, 'index.json'))
        if index.get('frequencyMode') != 'rank-based':
            raise ValueError(f"{path}: not a rank-based frequency dictionary")
        for name in archive.namelist():
            if not name.startswith('term_meta_bank'):
                continue
            for term, kind, data in json.loads(_read(archive, name)):
                # data: a number, {value, displayValue}, or {reading, frequency: number | {value}}
                frequency = data.get('frequency', data) if isinstance(data, dict) else data
                value = frequency.get('value') if isinstance(frequency, dict) else frequency
                if kind == 'freq' and isinstance(value, (int, float)) and value > 0:
                    yield term, data.get('reading') if isinstance(data, dict) else None, value



def reading_ranks(path: str) -> dict:
    """(term, reading) -> best (lowest) rank; its keys are the `known` readings."""
    ranks = {}
    for term, reading, value in entries(path):
        if reading:
            ranks[term, reading] = min(value, ranks.get((term, reading), value))
    return ranks


def preferred(ranks: dict, order=()) -> tuple:
    """(the reading `ranks` {reading: rank} ranks first, or None; the best rank of the others).
    A list like Jiten's ranks words, not readings: every reading of one JMdict entry gets the
    entry's rank (言う いう = ゆう, 言葉 ことば = けとば). Readings tied at the best rank are one
    group, decided by `order` (JMdict's readings of the form, its first kana reading first),
    else undecided (None); the others' rank is the best one outside the group."""
    if not ranks:  # rows mined with an older list
        return None, math.inf
    top = min(ranks.values())
    tied = [r for r, rank in ranks.items() if rank == top]
    best = tied[0] if len(tied) == 1 else next((r for r in order if r in tied), None)
    return best, min((rank for rank in ranks.values() if rank != top), default=math.inf)
