"""
Phase 3: Password Policy and Guessability Evaluation Engine.

Integrates Markov-based guessability scoring with breached-password blocklist
filtering, Shannon entropy estimation, and structural pattern detection.
Enforces NIST SP 800-63B aligned password admission rules.

Usage:
    python 3_policy.py evaluate "P@ssw0rd123" "xK9#mQ2$vL"
    python 3_policy.py evaluate --json "correcthorsebatterystaple"
    python 3_policy.py calibrate --val data/proto/val_counts.tsv --limit 25000
    python 3_policy.py audit --file passwords.txt
"""

import argparse
import importlib
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np


# Default tier cutoffs based on estimated number of guesses
TIER_BOUNDS = [
    (1e6, "REJECT"),
    (1e8, "WEAK"),
    (1e12, "ACCEPT"),
    (float("inf"), "STRONG"),
]

# Minimum sequential run length to flag (e.g. '1234', 'abcd')
_MIN_SEQUENTIAL_RUN = 4


@dataclass
class PolicyResult:
    password: str
    is_acceptable: bool
    tier: str
    estimated_guesses: float
    log10_prob: float
    shannon_entropy_bits: float
    in_blocklist: bool
    violations: List[str]
    feedback: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class PasswordPolicy:
    """Enforces password complexity, blocklist checks, and Markov guessability thresholds."""

    def __init__(
        self,
        model_path: Optional[str] = "model.pkl",
        blocklist_path: Optional[str] = None,
        min_length: int = 8,
        max_length: int = 64,
        min_acceptable_tier: str = "ACCEPT",
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.min_acceptable_tier = min_acceptable_tier
        self.blocklist: Set[str] = set()
        self.model = None

        # Load blocklist
        resolved_blocklist = blocklist_path or self._find_default_blocklist()
        if resolved_blocklist and os.path.exists(resolved_blocklist):
            self.load_blocklist(resolved_blocklist)

        # Load Markov model
        if model_path and os.path.exists(model_path):
            self.load_markov_model(model_path)

    def _find_default_blocklist(self) -> Optional[str]:
        candidates = [
            "data/processed/blocklist_top100k.txt",
            "data/proto/blocklist_top100k.txt",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def load_blocklist(self, path: str) -> None:
        """Load blocklist of known leaked passwords into an in-memory set."""
        with open(path, "r", encoding="ascii", errors="ignore") as f:
            self.blocklist = {line.strip().lower() for line in f if line.strip()}

    def load_markov_model(self, path: str) -> None:
        """Dynamically loads MarkovModel from markov_model.py or 2_markov_model.py."""
        try:
            try:
                markov_module = importlib.import_module("markov_model")
            except ImportError:
                markov_module = importlib.import_module("2_markov_model")
            self.model = markov_module.load_model(path)
        except Exception as e:
            raise RuntimeError(f"Failed to load Markov model from {path}: {e}")

    @staticmethod
    def calculate_shannon_entropy(password: str) -> float:
        """Calculates theoretical Shannon entropy in bits based on character pool."""
        if not password:
            return 0.0

        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)

        pool_size = 0
        if has_lower:
            pool_size += 26
        if has_upper:
            pool_size += 26
        if has_digit:
            pool_size += 10
        if has_symbol:
            pool_size += 32

        if pool_size == 0:
            return 0.0

        return round(len(password) * math.log2(pool_size), 2)

    @staticmethod
    def _find_sequential_run(password: str, min_length: int = _MIN_SEQUENTIAL_RUN) -> Optional[str]:
        """Returns the first ascending or descending ASCII run of `min_length` or more, or None."""
        pw = password.lower()
        if len(pw) < min_length:
            return None
        run_start = 0
        for i in range(1, len(pw)):
            delta = ord(pw[i]) - ord(pw[i - 1])
            prev_delta = ord(pw[i - 1]) - ord(pw[i - 2]) if i >= 2 else delta
            if delta != prev_delta or delta not in (1, -1):
                # Reset run if direction changed or not strictly sequential
                if i - run_start >= min_length:
                    return pw[run_start:i]
                run_start = i - 1 if delta in (1, -1) else i
        if len(pw) - run_start >= min_length:
            return pw[run_start:]
        return None

    def _detect_structural_patterns(self, password: str) -> Tuple[List[str], List[str]]:
        """Detect repeated characters and sequential ASCII runs."""
        violations = []
        feedback = []

        # Consecutive identical characters (e.g., 'aaaa', '1111')
        if re.search(r"(.)\1{2,}", password):
            feedback.append("Avoid sequences of 3 or more repeated characters.")

        # Algorithmically detect consecutive ascending/descending ASCII runs (e.g., '1234', 'dcba')
        run = self._find_sequential_run(password)
        if run:
            feedback.append(f"Avoid consecutive character sequences (detected: '{run}').")

        return violations, feedback

    def _assign_tier(self, guess_number: float) -> str:
        for bound, tier_name in TIER_BOUNDS:
            if guess_number < bound:
                return tier_name
        return "STRONG"

    def evaluate(self, password: str) -> PolicyResult:
        """Evaluates password against length, blocklist, structural patterns, and Markov model."""
        violations: List[str] = []
        feedback: List[str] = []

        # 1. Length validation
        pw_len = len(password)
        if pw_len < self.min_length:
            violations.append(f"Password must be at least {self.min_length} characters (got {pw_len}).")
        elif pw_len > self.max_length:
            violations.append(f"Password must not exceed {self.max_length} characters (got {pw_len}).")

        # 2. Blocklist lookup
        in_blocklist = password.lower() in self.blocklist
        if in_blocklist:
            violations.append("Password appears in breached credential blocklists.")

        # 3. Structural patterns
        _, pattern_feedback = self._detect_structural_patterns(password)
        feedback.extend(pattern_feedback)

        # 4. Markov Model scoring
        if self.model is not None:
            try:
                score = self.model.score(password)
                log10_prob = float(score["log10_prob"])
                est_guesses = float(score["est_guess_number"])
            except Exception:
                log10_prob = 0.0
                est_guesses = 1.0
        else:
            log10_prob = 0.0
            est_guesses = 0.0

        # If password is in blocklist, force estimated guesses to 1
        if in_blocklist:
            est_guesses = 1.0

        # Tier assignment
        tier = self._assign_tier(est_guesses)

        # Enforce minimum tier threshold
        if tier == "REJECT":
            violations.append("Estimated guessability is too high (rejected by Markov model).")
        elif tier == "WEAK":
            violations.append("Password falls below acceptable guess-resistance threshold (WEAK tier).")

        # Overall admission decision
        is_acceptable = (len(violations) == 0) and (tier in ["ACCEPT", "STRONG"])

        # Construct actionable feedback if weak
        if not is_acceptable and not feedback:
            if pw_len < 12:
                feedback.append("Increasing password length significantly improves guess resistance.")
            feedback.append("Use a passphrase or mix unrelated words to lower predictable n-gram patterns.")

        entropy = self.calculate_shannon_entropy(password)

        return PolicyResult(
            password=password,
            is_acceptable=is_acceptable,
            tier=tier,
            estimated_guesses=est_guesses,
            log10_prob=round(log10_prob, 2),
            shannon_entropy_bits=entropy,
            in_blocklist=in_blocklist,
            violations=violations,
            feedback=feedback,
        )

    def check(self, password: str, username: Optional[str] = None):
        """Compatibility wrapper returning an object with .accepted and .feedback."""
        res = self.evaluate(password)
        feedback = list(res.violations) + list(res.feedback)
        accepted = res.is_acceptable

        # Username substring check
        if username and len(username) >= 3 and username.lower() in password.lower():
            accepted = False
            feedback.insert(0, "Password must not contain the username.")

        class Decision:
            def __init__(self, accepted, feedback, result):
                self.accepted = accepted
                self.feedback = feedback
                self.result = result

        return Decision(accepted, feedback, res)


# Alias PasswordPolicy as PolicyEngine for backwards compatibility with server.py
PolicyEngine = PasswordPolicy


def calibrate_on_dataset(
    policy: PasswordPolicy,
    dataset_path: str,
    limit: int = 25000,
) -> None:
    """Evaluates tier distributions and guess statistics on validation/test datasets."""
    if not os.path.exists(dataset_path):
        print(f"Dataset path not found: {dataset_path}")
        sys.exit(1)

    print(f"Running policy calibration on {dataset_path} (limit={limit:,})...")

    tier_counts = {"REJECT": 0, "WEAK": 0, "ACCEPT": 0, "STRONG": 0}
    blocklist_hits = 0
    accepted_count = 0
    guess_numbers = []

    total = 0
    with open(dataset_path, "r", encoding="ascii", errors="ignore") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            pw = line.split("\t")[0]
            total += 1

            res = policy.evaluate(pw)
            tier_counts[res.tier] += 1
            if res.in_blocklist:
                blocklist_hits += 1
            if res.is_acceptable:
                accepted_count += 1
            guess_numbers.append(res.estimated_guesses)

    guess_arr = np.array(guess_numbers)
    percentiles = [5, 10, 25, 50, 75, 90, 95, 99]
    pct_values = np.percentile(guess_arr, percentiles)

    print("-" * 60)
    print(f"Calibration Sample Size: {total:,}")
    print(f"Blocklist Hits         : {blocklist_hits:,} ({100 * blocklist_hits / total:.2f}%)")
    print(f"Admitted by Policy     : {accepted_count:,} ({100 * accepted_count / total:.2f}%)")
    print(f"Rejected / Blocked     : {total - accepted_count:,} ({100 * (total - accepted_count) / total:.2f}%)")
    print("-" * 60)
    print("Tier Distribution:")
    for tier, count in tier_counts.items():
        pct = 100 * count / total
        print(f"  {tier:<8}: {count:>8,} ({pct:>5.2f}%)")
    print("-" * 60)
    print("Estimated Guess Percentiles:")
    for p, v in zip(percentiles, pct_values):
        print(f"  {p:>2}th percentile: {v:.2e} guesses")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description="Password Policy & Guessability Engine")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # Subcommand: evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate passwords against policy")
    eval_parser.add_argument("passwords", nargs="*", help="Passwords to evaluate")
    eval_parser.add_argument("--model", default="model.pkl", help="Path to trained Markov model")
    eval_parser.add_argument("--blocklist", default=None, help="Path to top-100k blocklist")
    eval_parser.add_argument("--min-len", type=int, default=8, help="Minimum password length")
    eval_parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    # Subcommand: calibrate
    cal_parser = subparsers.add_parser("calibrate", help="Calibrate tier thresholds on dataset")
    cal_parser.add_argument("--val", required=True, help="Path to validation counts TSV")
    cal_parser.add_argument("--model", default="model.pkl", help="Path to trained Markov model")
    cal_parser.add_argument("--blocklist", default=None, help="Path to blocklist")
    cal_parser.add_argument("--limit", type=int, default=25000, help="Number of rows to sample")

    # Subcommand: audit
    audit_parser = subparsers.add_parser("audit", help="Audit a file of passwords")
    audit_parser.add_argument("--file", required=True, help="Input password text file")
    audit_parser.add_argument("--model", default="model.pkl", help="Path to trained Markov model")
    audit_parser.add_argument("--blocklist", default=None, help="Path to blocklist")

    args = parser.parse_args()

    # Initialize policy engine
    policy = PasswordPolicy(
        model_path=args.model,
        blocklist_path=args.blocklist,
        min_length=getattr(args, "min_len", 8),
    )

    if args.cmd == "evaluate":
        passwords = args.passwords
        if not passwords:
            # Read from stdin if no positional args
            passwords = [line.strip() for line in sys.stdin if line.strip()]

        results = [policy.evaluate(pw) for pw in passwords]

        if args.json:
            print(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            for r in results:
                status = "PASS" if r.is_acceptable else "FAIL"
                print(f"[{status}] Password : {r.password}")
                print(f"       Tier     : {r.tier}")
                print(f"       Guesses  : {r.estimated_guesses:.2e} (log10p = {r.log10_prob})")
                print(f"       Entropy  : {r.shannon_entropy_bits} bits")
                print(f"       Blocklist: {'Yes' if r.in_blocklist else 'No'}")
                if r.violations:
                    print("       Violations:")
                    for v in r.violations:
                        print(f"         - {v}")
                if r.feedback:
                    print("       Feedback:")
                    for f in r.feedback:
                        print(f"         - {f}")
                print()

    elif args.cmd == "calibrate":
        calibrate_on_dataset(policy, args.val, args.limit)

    elif args.cmd == "audit":
        if not os.path.exists(args.file):
            print(f"Audit file not found: {args.file}")
            sys.exit(1)
        with open(args.file, "r", encoding="ascii", errors="ignore") as f:
            passwords = [line.strip() for line in f if line.strip()]
        total = len(passwords)
        passed = 0
        for pw in passwords:
            r = policy.evaluate(pw)
            if r.is_acceptable:
                passed += 1
        print(f"Audited {total:,} passwords: {passed:,} passed policy ({100 * passed / max(total, 1):.2f}%).")


if __name__ == "__main__":
    main()
