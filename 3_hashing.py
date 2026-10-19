"""
Phase 3: Argon2id password hashing (+ optional pepper).

    python hashing.py --benchmark       # find parameters that take ~250-500 ms on YOUR machine
"""
import base64
import hashlib
import hmac
import os
import time

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerifyMismatchError

# Starting parameters (OWASP-style minimum is m=19 MiB, t=2, p=1). Tune with --benchmark.
TIME_COST = 3
MEMORY_COST_KIB = 64 * 1024      # 64 MiB
PARALLELISM = 1

_ph = PasswordHasher(time_cost=TIME_COST, memory_cost=MEMORY_COST_KIB,
                     parallelism=PARALLELISM, hash_len=32, salt_len=16, type=Type.ID)


def _pepper(password: str) -> str:
    """Optional pepper: HMAC-SHA256 with a server-side secret kept OUTSIDE the database.
    Enabled by setting the PASSWORD_PEPPER environment variable."""
    key = os.environ.get("PASSWORD_PEPPER")
    if not key:
        return password
    mac = hmac.new(key.encode(), password.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(mac).decode()


def hash_password(password: str) -> str:
    """Returns an encoded string: $argon2id$v=19$m=...,t=...,p=...$<salt>$<hash>.
    A fresh random 16-byte salt (OS CSPRNG) is generated for every call and stored inside the string."""
    return _ph.hash(_pepper(password))


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        return _ph.verify(stored_hash, _pepper(password))   # constant-time comparison inside
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    """True if parameters have been strengthened since this hash was made (re-hash at next login)."""
    return _ph.check_needs_rehash(stored_hash)


_DUMMY = _ph.hash("dummy-password-for-timing")

def dummy_verify(password: str) -> None:
    """Call for unknown usernames so response time doesn't reveal whether the account exists."""
    verify_password(_DUMMY, password)


def benchmark():
    print(f"{'t':>2} {'m (MiB)':>8} {'p':>2}  avg ms/hash")
    for t, m_mib, p in [(1, 19, 1), (2, 19, 1), (1, 46, 1), (3, 64, 1), (3, 64, 4), (4, 128, 1)]:
        ph = PasswordHasher(time_cost=t, memory_cost=m_mib * 1024, parallelism=p, type=Type.ID)
        t0 = time.perf_counter()
        for _ in range(5):
            ph.hash("benchmark-password")
        print(f"{t:>2} {m_mib:>8} {p:>2}  {(time.perf_counter() - t0) / 5 * 1000:8.0f}")


if __name__ == "__main__":
    import sys
    if "--benchmark" in sys.argv:
        benchmark()
    else:
        h = hash_password("correct horse")
        print(h)
        print("verify ok   :", verify_password(h, "correct horse"))
        print("verify wrong:", verify_password(h, "wrong"))
        print("two hashes of same password differ (unique salt):", hash_password("x") != hash_password("x"))