"""Overlap tests over a read's ruby spans (`hint_at`: start -> (end, reading)) and number+counter spans
(`counted`: (start, number end, end, number, counter)) by binary search, instead of scanning all of them
for every token and candidate: on long books with much ruby that scan was a third of Reader.read."""
from bisect import bisect_left, bisect_right

# shortcut: keyed by identity and length: a span collection changed in place at the same length would
# keep a stale index; Reader.read builds both once per text and never changes them. Upgrade to an
# explicit index object passed along if that changes.
_cache = {}


def _index(spans):
    """Sorted starts, and the largest end of the spans up to each one."""
    hit = _cache.get(id(spans))
    if hit and hit[0] is spans and hit[1] == len(spans):
        return hit[2], hit[3]
    if isinstance(spans, dict):
        pairs = sorted((start, value[0]) for start, value in spans.items())
    else:
        pairs = sorted((span[0], span[2]) for span in spans)
    starts, max_end, m = [], [], -1
    for start, end in pairs:
        m = max(m, end)
        starts.append(start)
        max_end.append(m)
    if len(_cache) > 16:
        _cache.clear()
    _cache[id(spans)] = (spans, len(spans), starts, max_end)
    return starts, max_end


def overlaps(spans, begin, end):
    """Whether a span overlaps begin..end: any(s < end and e > begin)."""
    starts, max_end = _index(spans)
    k = bisect_left(starts, end)
    return k > 0 and max_end[k - 1] > begin


def covers(spans, begin, end):
    """Whether a span holds begin..end: any(s <= begin and end <= e)."""
    starts, max_end = _index(spans)
    k = bisect_right(starts, begin)
    return k > 0 and max_end[k - 1] >= end
