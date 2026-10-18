import argparse
import random
import re
from collections import Counter

from markov_model import load_model, load_counts

TIERS = ["REJECT", "WEAK", "ACCEPT", "STRONG"]


def rule_ok(pw):
    return (
        len(pw) >= 8
        and re.search(r"[a-z]", pw)
        and re.search(r"[A-Z]", pw)
        and re.search(r"\d", pw)
        and re.search(r"[^A-Za-z0-9]", pw)
    )


def report(title, pws, model):
    labels = [model.score(p)["label"] for p in pws]
    c = Counter(labels)

    print(f"\n== {title} (n={len(pws)}) ==")

    for t in TIERS:
        print(f"  {t:<7} {100 * c[t] / len(pws):6.2f}%")

    ok = [(p, l) for p, l in zip(pws, labels) if rule_ok(p)]

    if ok:
        bad = sum(1 for _, l in ok if l in ("REJECT", "WEAK"))

        print(
            f"  passwords passing the rule-based policy: "
            f"{len(ok)} ({100 * len(ok) / len(pws):.1f}%)"
        )
        print(
            f"  ...of those, flagged REJECT/WEAK by Markov: "
            f"{bad} ({100 * bad / len(ok):.1f}%)"
        )

        ex = [p for p, l in ok if l in ("REJECT", "WEAK")][:8]
        print("  examples that pass the rules but are predictable:", ex)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)

    a = ap.parse_args()

    model = load_model(a.model)
    rows = load_counts(a.test)

    pws = [r[0] for r in rows]
    cnt = [r[1] for r in rows]

    rng = random.Random(a.seed)

    report(
        "Weighted by popularity (realistic users)",
        rng.choices(pws, weights=cnt, k=a.n),
        model,
    )

    report(
        "Uniform over distinct passwords",
        rng.sample(pws, min(a.n, len(pws))),
        model,
    )


if __name__ == "__main__":
    main()