#!/bin/sh
# Scores the working tree and a base commit on every gold set and lists what changed:
#   tools/compare.sh SETS_DIR [BASE=origin/main]
# Reads SETS_DIR/*.jsonl (and SETS_DIR/freq.zip as --known when present), without intervals.
# The base's report is cached per commit and evaluate.py in SETS_DIR/.base-*.json; this tree's
# goes to SETS_DIR/.report.json, its misses to SETS_DIR/.misses.tsv. PYTHON picks the
# interpreter. Both are scored with this tree's evaluate.py.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd) py=${PYTHON:-python3}
sets=$(cd "$1" && pwd) base=$(git -C "$here" rev-parse "${2:-origin/main}")
known=; [ -f "$sets/freq.zip" ] && known="--known $sets/freq.zip"
cached=$sets/.base-$base-$(cksum < "$here/yurigana/evaluate.py" | cut -d" " -f1).json
if [ ! -f "$cached" ]; then
  tmp=$(mktemp -d)
  trap 'git -C "$here" worktree remove --force "$tmp/tree"; rm -rf "$tmp"' EXIT
  git -C "$here" worktree add -q --detach "$tmp/tree" "$base"
  cp "$here/yurigana/evaluate.py" "$tmp/tree/yurigana/"
  [ -f "$tmp/tree/yurigana/tatoeba-b2-ids.txt.gz" ] || cp "$here/yurigana/tatoeba-b2-ids.txt.gz" "$tmp/tree/yurigana/"
  (cd "$tmp/tree" && "$py" -m yurigana.evaluate "$sets"/*.jsonl $known --bootstrap 0 --out "$cached.tmp" >/dev/null)
  mv "$cached.tmp" "$cached"
fi
cd "$here" && "$py" -m yurigana.evaluate "$sets"/*.jsonl $known --bootstrap 0 --compare "$cached" \
  --out "$sets/.report.json" --misses "$sets/.misses.tsv"
