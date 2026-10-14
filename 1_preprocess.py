"""
Phase 1: clean rockyou.txt and create train/val/test splits.

Usage:
    python preprocess.py --input rockyou.txt --outdir data/processed
    python preprocess.py --input rockyou.txt --outdir data/proto --limit 1000000   # quick prototype
"""
import argparse
import os
import zlib
from collections import Counter

MIN_LEN, MAX_LEN = 4, 32


def is_clean(pw: str) -> bool:
    """Keep only printable ASCII (0x20-0x7E) within the length range."""
    return MIN_LEN <= len(pw) <= MAX_LEN and all(32 <= ord(c) <= 126 for c in pw)


def bucket(pw: str, seed: int) -> int:
    """Deterministic 0-99 bucket per unique password (same password -> same split)."""
    return zlib.crc32(f"{seed}:{pw}".encode("utf-8")) % 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="data/processed")
    ap.add_argument("--limit", type=int, default=0, help="read only first N lines (0 = all)")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    counts, total, kept = Counter(), 0, 0
    with open(a.input, "rb") as f:
        for i, raw in enumerate(f):
            if a.limit and i >= a.limit:
                break
            total += 1
            pw = raw.rstrip(b"\r\n").decode("latin-1")   # RockYou has mixed encodings
            if is_clean(pw):
                counts[pw] += 1
                kept += 1

    # Split UNIQUE passwords 80/10/10 so test passwords never appear in training.
    splits = {"train": [], "val": [], "test": []}
    for pw, c in counts.items():
        b = bucket(pw, a.seed)
        splits["train" if b < 80 else "val" if b < 90 else "test"].append((pw, c))

    for name, rows in splits.items():
        rows.sort(key=lambda x: -x[1])
        with open(os.path.join(a.outdir, f"{name}_counts.tsv"), "w", encoding="ascii") as f:
            for pw, c in rows:
                f.write(f"{pw}\t{c}\n")
        with open(os.path.join(a.outdir, f"{name}.txt"), "w", encoding="ascii") as f:
            f.writelines(pw + "\n" for pw, _ in rows)

    # Top-100k most common passwords -> blocklist
    with open(os.path.join(a.outdir, "blocklist_top100k.txt"), "w", encoding="ascii") as f:
        f.writelines(pw + "\n" for pw, _ in counts.most_common(100_000))

    print(f"lines read      : {total:,}")
    print(f"kept after clean: {kept:,} ({100*kept/max(total,1):.1f}%)")
    print(f"unique          : {len(counts):,}")
    for name, rows in splits.items():
        print(f"{name:<5} unique={len(rows):,}  total occurrences={sum(c for _, c in rows):,}")
    print("top 10:", [pw for pw, _ in counts.most_common(10)])


if __name__ == "__main__":
    main()