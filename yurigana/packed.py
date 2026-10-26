"""A Reader's tables in one file read through mmap (Reader.save, Reader.load): processes that load the same
file share its pages, and nothing is parsed at start.

Layout: MAGIC, a 4-byte header length, a JSON header {name: [entries offset, entries end, slots offset,
slot count, entry count]} and per table its entries (`key \\0 value \\0`, UTF-8, in the dict's order, so iteration keeps
it) and an open-addressing hash table of uint32 entry offsets (crc32 of the key, linear probing, 0 = empty)."""
import json
import mmap
import os
import struct
import zlib
from array import array
from collections.abc import Mapping, Set

MAGIC = b'YGPK1\n'


def write(path: str, tables: dict, meta=None) -> None:
    """tables: {name: {str: str}}; keys and values must not contain NUL."""
    blobs, header, offset = [], {}, 0
    for name, table in tables.items():
        entries, offsets = bytearray(), []
        for key, value in table.items():
            offsets.append((key.encode(), len(entries)))
            entries += key.encode() + b'\0' + value.encode() + b'\0'
        slots = array('I', bytes(4 * max(1, 2 * len(offsets))))
        header[name] = [offset, offset + len(entries), 0, len(slots), len(offsets)]
        for key, at in offsets:
            i = zlib.crc32(key) % len(slots)
            while slots[i]:
                i = (i + 1) % len(slots)
            slots[i] = at + 1  # 0 marks an empty slot
        blobs.append((name, bytes(entries), slots))
        offset += len(entries) + 3 & ~3
        header[name][2] = offset
        offset += 4 * len(slots)
    head = json.dumps({'tables': header, 'meta': meta or {}}).encode()
    base = len(MAGIC) + 4 + len(head) + 3 & ~3
    # a new file, renamed over the old: processes that mapped the old one keep reading it (no SIGBUS)
    with open(path + '.tmp', 'wb') as f:
        f.write(MAGIC + struct.pack('<I', len(head)) + head)
        f.write(b'\0' * (base - f.tell()))
        for _, entries, slots in blobs:
            f.write(entries + b'\0' * (-len(entries) % 4))
            f.write(slots.tobytes())
    os.replace(path + '.tmp', path)


class Packed:
    """An open packed file: table(name) gives a read-only {str: str} Mapping; meta is the header's dict."""

    def __init__(self, path: str):
        with open(path, 'rb') as f:
            self._mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        if self._mm[:len(MAGIC)] != MAGIC:
            raise ValueError(f'{path}: not a packed yurigana file')
        size, = struct.unpack_from('<I', self._mm, len(MAGIC))
        start = len(MAGIC) + 4
        header = json.loads(self._mm[start:start + size])
        self.meta = header['meta']
        self._base = start + size + 3 & ~3
        self._tables = header['tables']

    def table(self, name: str) -> 'PackedMap':
        return PackedMap(self._mm, self._base, *self._tables[name])


class PackedMap(Mapping):
    def __init__(self, mm, base, start, end, slots, count, size):
        self._mm, self._start, self._end, self._len = mm, base + start, base + end, size
        self._slots = memoryview(mm)[base + slots:base + slots + 4 * count].cast('I')
        self._memo = {}  # key -> value or None: a book asks the same few thousand keys over and over

    def _find(self, key: str):
        """The offset of the key's value, or -1."""
        k = key.encode() + b'\0'
        mm, slots, n = self._mm, self._slots, len(self._slots)
        i = zlib.crc32(k[:-1]) % n
        while at := slots[i]:
            at += self._start - 1
            if mm[at:at + len(k)] == k:
                return at + len(k)
            i = (i + 1) % n
        return -1

    def _value(self, key: str):
        try:
            return self._memo[key]
        except KeyError:
            if len(self._memo) > 100_000:  # a long-lived worker reads many books: keep it to a few MB
                self._memo.clear()
            at = self._find(key)
            value = self._memo[key] = None if at < 0 else self._mm[at:self._mm.find(b'\0', at)].decode()
            return value

    def get(self, key, default=None):
        try:  # the memo first: most lookups are repeats
            value = self._memo[key]
        except (KeyError, TypeError):
            value = self._value(key) if isinstance(key, str) else None
        return default if value is None else value

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __contains__(self, key):
        try:
            return self._memo[key] is not None
        except (KeyError, TypeError):
            return isinstance(key, str) and self._value(key) is not None

    def items(self):
        mm, at = self._mm, self._start
        while at < self._end:
            mid = mm.find(b'\0', at)
            end = mm.find(b'\0', mid + 1)
            yield mm[at:mid].decode(), mm[mid + 1:end].decode()
            at = end + 1

    def __iter__(self):
        return (key for key, _ in self.items())

    def __len__(self):
        return self._len


class Decoded(Mapping):
    """A PackedMap whose values go through `decode` (readings: str.split)."""

    def __init__(self, table: PackedMap, decode):
        self.table, self.decode = table, decode

    def __getitem__(self, key):
        return self.decode(self.table[key])

    def get(self, key, default=None):
        value = self.table.get(key)
        return default if value is None else self.decode(value)

    def __contains__(self, key):
        return key in self.table

    def items(self):
        return ((k, self.decode(v)) for k, v in self.table.items())

    def __iter__(self):
        return iter(self.table)

    def __len__(self):
        return len(self.table)


def _key(pair):
    """`form \\t reading`, or None (in no table) for a pair with a None or other non-str part."""
    try:
        return '\t'.join(pair)
    except TypeError:  # a None or other non-str part
        return None


class PairMap(Mapping):
    """{(form, reading): decode(value)} over a table keyed `form \\t reading` (ranks: int)."""

    def __init__(self, table: PackedMap, decode=int):
        self.table, self.decode = table, decode

    def __getitem__(self, pair):
        return self.decode(self.table[_key(pair)])

    def get(self, pair, default=None):
        value = self.table.get(_key(pair))
        return default if value is None else self.decode(value)

    def __contains__(self, pair):
        return _key(pair) in self.table

    def __iter__(self):
        return (tuple(key.split('\t')) for key in self.table)

    def __len__(self):
        return len(self.table)


class PairSet(Set):
    """{(form, reading)} over a table keyed `form \\t reading`."""

    def __init__(self, table: PackedMap):
        self.table = table

    def __contains__(self, pair):
        return _key(pair) in self.table

    def __iter__(self):
        return (tuple(key.split('\t')) for key in self.table)

    def __len__(self):
        return len(self.table)
