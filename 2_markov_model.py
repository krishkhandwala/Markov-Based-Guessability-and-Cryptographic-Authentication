"""
Phase 2: Markov (n-gram) password guessability model.

- Character n-gram model with Witten-Bell interpolated smoothing
- Monte Carlo guess-number estimation (Dell'Amico & Filippone, 2015)
- Tier labels from estimated guess number

Usage:
    python markov_model.py compare --train data/proto/train_counts.tsv --val data/proto/val_counts.tsv
    python markov_model.py train   --train data/proto/train_counts.tsv --val data/proto/val_counts.tsv \
                                   --order 4 --samples 200000 --out model.pkl
    python markov_model.py score   model.pkl password P@ssw0rd 'xK9#mQ2$vL'
"""
import argparse
import pickle
import numpy as np

START, END = "\x02", "\x03"                      # not printable, so never in a password
ALPHABET = [chr(i) for i in range(32, 127)] + [END]
IDX = {c: i for i, c in enumerate(ALPHABET)}
V = len(ALPHABET)                                # 95 printable + end symbol = 96
MAXLEN = 32

# (upper bound on estimated guesses, label). Starting values: calibrate on your data (Phase 2.5).
TIERS = [(1e6, "REJECT"), (1e8, "WEAK"), (1e12, "ACCEPT"), (float("inf"), "STRONG")]


def label_for(guess_number: float) -> str:
    for bound, name in TIERS:
        if guess_number < bound:
            return name


class MarkovModel:
    def __init__(self, order: int = 4):
        self.order = order                        # context length = order - 1
        self.counts = [dict() for _ in range(order)]   # counts[k][context of len k][char] -> count
        self.tot = [dict() for _ in range(order)]
        self.types = [dict() for _ in range(order)]
        self.est_neg_lp = None                    # estimator arrays (set by build_estimator)
        self.est_cum = None

    # ---------- training ----------
    def train(self, pairs):
        """pairs: iterable of (password, count)."""
        pad = START * (self.order - 1)
        for pw, c in pairs:
            s = pad + pw + END
            for i in range(self.order - 1, len(s)):
                ch = s[i]
                for k in range(self.order):
                    d = self.counts[k].setdefault(s[i - k:i], {})
                    d[ch] = d.get(ch, 0) + c
        for k in range(self.order):
            for ctx, d in self.counts[k].items():
                self.tot[k][ctx] = sum(d.values())
                self.types[k][ctx] = len(d)

    # ---------- probabilities (Witten-Bell interpolation) ----------
    def _prob(self, ch, hist):
        p = 1.0 / V
        for k in range(self.order):
            ctx = hist[len(hist) - k:]
            d = self.counts[k].get(ctx)
            if d is None:
                continue
            t, n1 = self.tot[k][ctx], self.types[k][ctx]
            p = (d.get(ch, 0) + n1 * p) / (t + n1)
        return p

    def _dist(self, hist):
        p = np.full(V, 1.0 / V)
        for k in range(self.order):
            ctx = hist[len(hist) - k:]
            d = self.counts[k].get(ctx)
            if d is None:
                continue
            vec = np.zeros(V)
            for ch, c in d.items():
                vec[IDX[ch]] = c
            t, n1 = self.tot[k][ctx], self.types[k][ctx]
            p = (vec + n1 * p) / (t + n1)
        return p

    def log10_prob(self, pw: str) -> float:
        s = START * (self.order - 1) + pw + END
        h = self.order - 1
        return sum(np.log10(self._prob(s[i], s[i - h:i] if h else ""))
                   for i in range(h, len(s)))

    # ---------- Monte Carlo guess-number estimator ----------
    def build_estimator(self, n_samples=200_000, seed=1):
        rng = np.random.default_rng(seed)
        cache, lps = {}, np.empty(n_samples)
        for n in range(n_samples):
            hist, lp = START * (self.order - 1), 0.0
            for _ in range(MAXLEN + 1):
                if hist not in cache:
                    v = self._dist(hist)
                    cache[hist] = (np.cumsum(v), np.log10(v))
                cum, logv = cache[hist]
                j = min(int(np.searchsorted(cum, rng.random())), V - 1)
                lp += logv[j]
                if ALPHABET[j] == END:
                    break
                hist = (hist + ALPHABET[j])[1:]
            lps[n] = lp
        lps.sort()
        lps = lps[::-1]                                   # highest probability first
        w = 1.0 / (n_samples * 10.0 ** lps)               # each sample "stands for" 1/(N p) guesses
        self.est_neg_lp = -lps                            # ascending
        self.est_cum = np.cumsum(w)

    def guess_number(self, lp: float) -> float:
        """Estimated rank: sum over samples with higher probability of 1/(N p_i)."""
        count = int(np.searchsorted(self.est_neg_lp, -lp, side="left"))
        return 1.0 if count == 0 else float(self.est_cum[count - 1]) + 1.0

    # ---------- public API (the contract for the other teams) ----------
    def score(self, pw: str) -> dict:
        lp = self.log10_prob(pw)
        g = self.guess_number(lp)
        return {"log10_prob": lp, "est_guess_number": g, "label": label_for(g)}

    # ---------- evaluation ----------
    def perplexity(self, pairs) -> float:
        total_lp, total_sym = 0.0, 0
        for pw, c in pairs:
            total_lp += c * self.log10_prob(pw)
            total_sym += c * (len(pw) + 1)
        return 10.0 ** (-total_lp / total_sym)


class _Unpickler(pickle.Unpickler):
    """model.pkl created by running this file as a script refers to __main__.MarkovModel;
    map it back so the model can be loaded from other modules (policy.py, the server...)."""
    def find_class(self, module, name):
        if name == "MarkovModel":
            return MarkovModel
        return super().find_class(module, name)


def load_model(path):
    with open(path, "rb") as f:
        return _Unpickler(f).load()


def load_counts(path, limit=0):
    out = []
    with open(path, encoding="ascii") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            pw, c = line.rstrip("\n").rsplit("\t", 1)
            out.append((pw, int(c)))
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("train", "compare"):
        p = sub.add_parser(name)
        p.add_argument("--train", required=True)
        p.add_argument("--val", required=True)
        p.add_argument("--val-limit", type=int, default=50_000)
        if name == "train":
            p.add_argument("--order", type=int, default=4)
            p.add_argument("--samples", type=int, default=200_000)
            p.add_argument("--out", default="model.pkl")
        else:
            p.add_argument("--orders", type=int, nargs="+", default=[2, 3, 4, 5])
    s = sub.add_parser("score")
    s.add_argument("model")
    s.add_argument("passwords", nargs="+")
    a = ap.parse_args()

    if a.cmd == "score":
        m = load_model(a.model)
        for pw in a.passwords:
            r = m.score(pw)
            print(f"{pw!r:<28} log10p={r['log10_prob']:8.2f}  guesses~{r['est_guess_number']:.2e}  {r['label']}")
        return

    train, val = load_counts(a.train), load_counts(a.val, a.val_limit)
    if a.cmd == "compare":
        for k in a.orders:
            m = MarkovModel(k)
            m.train(train)
            print(f"order {k}: validation perplexity = {m.perplexity(val):.2f}")
        return
    m = MarkovModel(a.order)
    m.train(train)
    print(f"validation perplexity = {m.perplexity(val):.2f}")
    m.build_estimator(a.samples)
    with open(a.out, "wb") as f:
        pickle.dump(m, f)
    print("saved", a.out)


if __name__ == "__main__":
    main()