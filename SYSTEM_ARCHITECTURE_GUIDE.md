# SYSTEM ARCHITECTURE & CODEBASE COMPREHENSIVE GUIDE
**Markov-Based Guessability and Cryptographic Authentication System**
Repository: `Markov-Based-Guessability-and-Cryptographic-Authentication`

---

## 1. Executive Summary & Purpose of the System

Traditional password policies rely on arbitrary regex composition rules (e.g., at least 8 characters, 1 uppercase, 1 symbol, 1 digit). Empirical security research reveals that human users predictably circumvent these rules (e.g., capitalizing only the first letter and appending "1!" or current year at the end). As a result, static rules fail to thwart modern computational adversaries equipped with statistical dictionary crackers.

This system solves that problem by integrating:
1. **Probabilistic Language Modeling (Markov Chains)**: Character n-gram transitions calibrated with Witten-Bell smoothing to measure how predictable a password is based on real-world leaked passwords (RockYou dataset).
2. **Monte Carlo Guess Rank Estimation**: Directly estimates the number of brute-force/dictionary guesses an optimal attacker would need before reaching the password (Dell'Amico & Filippone, 2015).
3. **Multi-Vector Policy Engine**: Combines the Markov score with Shannon entropy calculations, breached credential blocklists, sequential character run detection, and username substring checks.
4. **Hardware-Resilient Cryptographic Hashing**: Employs **Argon2id (RFC 9106)** memory-hard password hashing (configured with 64 MiB RAM, 3 iterations, 1 parallelism, and 16-byte cryptographically secure per-user salts) with optional HMAC secret peppering.
5. **Side-Channel & Timing Attack Defense**: Constant-time dummy verification routines for non-existent users prevent account enumeration.
6. **Unified Secure API & Interactive Dashboard**: A production FastAPI server and a reactive React/Vite dashboard allowing real-time password analysis, n-gram inspection, secure registration, and audit telemetry.

---

## 2. Directory Structure & File Map

```text
Markov-Based-Guessability-and-Cryptographic-Authentication/
│
├── preprocess.py          # Phase 1: RockYou dataset cleaning & train/val/test splitting
├── markov_model.py        # Phase 2: n-gram Markov model, Witten-Bell smoothing & Monte Carlo ranker
├── policy.py              # Phase 3: Password policy engine, tier assignment & structural checks
├── calibrate.py           # Calibration script: Measures tier distribution against test datasets
├── hashing.py             # Phase 4 (Cryptographic): Argon2id hashing, timing dummy & benchmarking
├── 3_hashing.py           # Original phase-numbered copy of hashing module
├── db.py                  # Phase 4 (Storage): SQLite database layer with parameterised queries
├── 6_db.py                # Original phase-numbered copy of database module
├── gen_cert.py            # Certificate generator: Generates ECDSA P-256 self-signed SSL/TLS certs
├── server.py              # Phase 5: FastAPI REST server (HTTPS/HTTP), scoring, auth & telemetry
├── test_client.py         # Automated integration test suite validating endpoints & auth logic
├── requirements.txt       # Python environment dependencies
│
├── data/                  # Processed datasets (train_counts.tsv, blocklist_top100k.txt, etc.)
├── model.pkl              # Serialized trained MarkovModel instance with Monte Carlo CDF
├── auth.db                # SQLite database storing users and security audit logs
├── cert.pem / key.pem     # SSL certificate and private key for HTTPS
│
└── frontend/              # Interactive React + Vite Dashboard
    ├── index.html         # HTML entry with Syne & JetBrains Mono typography
    ├── vite.config.js     # Dev server configuration with proxy to backend port 8088
    ├── src/
    │   ├── main.jsx       # React application root DOM mount
    │   ├── App.jsx        # Complete interactive UI: live scoring, portal, telemetry, architecture
    │   └── index.css      # Design system: glassmorphic panels, cyber-gold accents, responsive layout
```

---

## 3. Deep Dive: Module-by-Module Code Understanding

### 3.1. `preprocess.py` (Phase 1: Dataset Preprocessing)
- **Role in System**: Cleans raw, noisy password dumps (such as `rockyou.txt`) and produces reproducible training, validation, and testing splits, alongside high-frequency blocklists.
- **Key Functions & Logic**:
  - `is_clean(pw)`: Filters passwords to ensure printable ASCII characters (`0x20` to `0x7E`) and length constraints (4 to 32 characters). Eliminates encoding corruptions.
  - `bucket(pw, seed)`: Uses CRC32 hashing (`zlib.crc32`) to deterministically partition passwords into 0–99 buckets.
  - **80/10/10 Unique Split**: Assigns unique passwords to `train` (<80), `val` (80–89), and `test` (≥90) partitions. This ensures that validation and test passwords never appear in the training dataset, preventing overfitting.
  - **Blocklist Generation**: Extracts the top 100,000 most frequent passwords to `blocklist_top100k.txt`.
- **System Impact**: Supplies the foundational ground-truth data required to train the Markov chain and calibrate policy thresholds.

---

### 3.2. `markov_model.py` (Phase 2: Guessability Model & Monte Carlo Estimator)
- **Role in System**: Core statistical intelligence engine. Calculates the likelihood that a human wrote a given string based on preceding character contexts.
- **Key Classes & Methods**:
  - `MarkovModel(order=4)`:
    - Maintains transition counts across context orders $k \in [0, \text{order}-1]$.
    - `train(pairs)`: Ingests `(password, count)` pairs and tracks character frequency following character context windows.
    - `_prob(ch, hist)`: Implements **Witten-Bell Interpolation Smoothing**. If a high-order context (e.g., 3 preceding characters) has not been observed, it gracefully backs off to order-2, order-1, and finally a uniform distribution ($1/V$ where $V=96$).
    - `log10_prob(pw)`: Computes the sum of log₁₀ probabilities for every character in the string, including start `\x02` and end `\x03` delimiters.
    - `build_estimator(n_samples=50_000, seed=1)`: Implements the **Dell'Amico & Filippone (2015)** Monte Carlo guess rank algorithm. Generates $N$ random passwords sampled directly from the model's probability distribution, sorts them by probability, and builds a cumulative weight array $w_i = \frac{1}{N \cdot 10^{\text{lp}_i}}$.
    - `guess_number(lp)`: For any input password with log-probability `lp`, performs binary search (`np.searchsorted`) over the sampled distribution to determine how many guesses an attacker would execute before attempting this password.
    - `score(pw)`: Public API returning `{log10_prob, est_guess_number, label}`.
  - `load_model(path)`: Custom unpickler that safely resolves serialized model objects across modules.
- **System Impact**: Replaces subjective password rules with an objective numerical metric: "How many attempts would an optimal attacker need to guess this?"

---

### 3.3. `policy.py` (Phase 3: Password Policy & Classification Engine)
- **Role in System**: Gatekeeper enforcing admission decisions before registration. Merges statistical predictions with structural safety checks.
- **Key Components**:
  - `TIER_BOUNDS`:
    - `< 10^6` guesses $\rightarrow$ **REJECT** (Trivially cracked in seconds)
    - `10^6` to `10^8` guesses $\rightarrow$ **WEAK** (Vulnerable to modest dictionary attacks)
    - `10^8` to `10^12` guesses $\rightarrow$ **ACCEPT** (Standard production security)
    - `> 10^12` guesses $\rightarrow$ **STRONG** (Highly resistant)
  - `PasswordPolicy` (aliased as `PolicyEngine`):
    - `load_blocklist(path)`: Loads breached passwords into an in-memory hash set for $O(1)$ lookups.
    - `load_markov_model(path)`: Integrates the trained `markov_model.py`.
    - `calculate_shannon_entropy(password)`: Calculates theoretical entropy based on character pool diversity (lowercase, uppercase, digits, symbols): $\text{Bits} = L \times \log_2(\text{Pool})$.
    - `_find_sequential_run(password)`: Algorithmic detection of sequential runs of length 4+ (e.g., `1234`, `abcd`, `dcba`).
    - `_detect_structural_patterns(password)`: Identifies repeated identical characters (`aaaa`) and consecutive sequences.
    - `evaluate(password)`: Validates length (8 to 64 chars), checks blocklist, calculates Markov score and Shannon entropy, and flags structural flaws.
    - `check(password, username)`: Backwards-compatible wrapper that also checks whether the password contains the username substring.
- **System Impact**: Guarantees that only structurally sound, guess-resistant credentials are permitted into the authentication pipeline.

---

### 3.4. `calibrate.py` (Policy Threshold Calibration)
- **Role in System**: Tooling to empirically measure policy behavior on real-world datasets.
- **Key Logic**:
  - Compares the Markov policy against a conventional regex policy (`rule_ok`: length ≥ 8, uppercase, lowercase, digit, symbol).
  - Demonstrates that a large percentage of passwords that satisfy standard complexity rules are nevertheless classified as `REJECT` or `WEAK` by the Markov model due to predictable human typing patterns.
- **System Impact**: Validates and tunes policy tier cutoffs against true statistical distributions.

---

### 3.5. `hashing.py` / `3_hashing.py` (Phase 4: Cryptographic Storage)
- **Role in System**: Implements password hashing and verification conforming to the **RFC 9106 Argon2id** standard.
- **Key Parameters & Functions**:
  - `TIME_COST = 3`: Number of iterative passes over memory.
  - `MEMORY_COST_KIB = 64 * 1024` (64 MiB): High memory allocation rendering GPU/ASIC parallel password cracking hardware cost-prohibitive.
  - `PARALLELISM = 1`: Thread utilization per hash computation.
  - `_pepper(password)`: Optional defense-in-depth layer using HMAC-SHA256 with a server-side secret key stored outside the database.
  - `hash_password(password)`: Generates an encoded string containing parameters, an OS-level CSPRNG 16-byte salt, and the Argon2id hash.
  - `verify_password(stored_hash, password)`: Verifies candidates using constant-time comparison inside Argon2 CFFI.
  - `dummy_verify(password)`: Runs a dummy verification against a pre-computed hash whenever an unknown username is requested. This ensures identical server execution time whether the user exists or not, defeating **timing side-channel attacks** for username enumeration.
  - `benchmark()`: Utility to measure hashing duration on host hardware.
- **System Impact**: Secures stored credentials such that even in the event of an SQL database dump, brute-force recovery is practically infeasible.

---

### 3.6. `db.py` / `6_db.py` (Database Layer)
- **Role in System**: Manages persistent storage with SQLite using strictly parameterised queries to prevent SQL injection vulnerabilities.
- **Database Schema**:
  - `users`:
    - `id` (INTEGER PRIMARY KEY)
    - `username` (TEXT UNIQUE)
    - `password_hash` (TEXT, stores full Argon2id encoded string)
    - `created_at` (REAL timestamp)
    - `failed_attempts` (INTEGER, for lockout tracking)
    - `locked_until` (REAL timestamp)
  - `login_events`:
    - `id` (INTEGER PRIMARY KEY)
    - `username` (TEXT)
    - `ip` (TEXT)
    - `success` (INTEGER: 1 for success, 0 for failure)
    - `ts` (REAL timestamp)
- **Key Functions**:
  - `valid_username(u)`: Validates format (`^[A-Za-z0-9_.-]{3,32}$`).
  - `create_user(conn, username, password_hash)`: Inserts new user or raises `UserExists`.
  - `get_user(conn, username)`: Retrieves user record.
  - `record_failed(conn, username)` / `reset_failed(conn, username)`: Tracks brute-force lockouts.
  - `log_event(conn, username, ip, success)`: Writes to immutable audit log.
- **System Impact**: Provides reliable, thread-safe, injection-immune data persistence and forensic auditing.

---

### 3.7. `gen_cert.py` (Cryptographic HTTPS Certificate Generation)
- **Role in System**: Automatically creates self-signed X.509 SSL/TLS certificates using the Python `cryptography` library.
- **Key Details**:
  - Uses ECDSA with the **SECP256R1** elliptic curve (P-256).
  - Configures Subject Alternative Names (SAN) for `localhost` and `127.0.0.1`.
  - Exports `cert.pem` and `key.pem`.
- **System Impact**: Enables encrypted transport over HTTPS to protect credentials in transit against eavesdropping and man-in-the-middle (MITM) attacks.

---

### 3.8. `server.py` (Phase 5: FastAPI REST Backend Service)
- **Role in System**: Central integration server exposing REST endpoints over HTTP/HTTPS, serving both backend tests and the web frontend.
- **Key Endpoints & Middleware**:
  - **Security Headers Middleware**: Injects `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Cache-Control: no-store`.
  - **CORS Middleware**: Allows seamless API access for frontend dev servers.
  - `GET /health`: Returns operational status, model state, and blocklist size.
  - `POST /score`: Real-time password evaluation without persisting data. Returns guess estimate, tier, Shannon entropy, blocklist hit, and character-by-character n-gram conditional probabilities.
  - `POST /register`: Validates password against `PolicyEngine`, hashes via `Argon2id`, records to SQLite `users` table, and returns performance telemetry (hashing duration in milliseconds).
  - `POST /login`: Authenticates user against stored hash, triggers constant-time `dummy_verify` if account does not exist, updates failed attempt counts, and writes to `login_events`.
  - `GET /telemetry`: Provides telemetry for the dashboard (registered user count, recent login audit events with timestamps, blocklist size, and model status).
- **System Impact**: Serves as the nervous system connecting the statistical models, cryptographic modules, database, and client interface.

---

### 3.9. `test_client.py` (End-to-End Verification Client)
- **Role in System**: Automated integration suite executing a complete test scenario against the running server.
- **Test Pipeline**:
  1. `GET /health` $\rightarrow$ verifies server is up.
  2. `POST /register` with weak password (`123`) $\rightarrow$ expects 400 Bad Request with policy feedback.
  3. `POST /register` with strong password (`CorrectHorseBatteryStaple99!`) $\rightarrow$ expects 201 Created.
  4. `POST /login` with correct credentials $\rightarrow$ expects 200 OK.
  5. `POST /login` with incorrect password $\rightarrow$ expects 401 Unauthorized.
  6. `POST /login` with non-existent user $\rightarrow$ expects identical 401 Unauthorized (timing attack validation).
- **System Impact**: Ensures regressions are caught immediately.

---

### 3.10. Frontend Architecture (`frontend/`)
- **Technology Stack**: React 18, Vite, Lucide Icons, Canvas Confetti.
- **Design Aesthetic**: Premium cyber-cryptographic glassmorphism with dark obsidian background (`#07090e`), gold accents (`#e2b253`), emerald pass badges (`#00f2a1`), crimson reject indicators (`#ff3366`), and high-readability typography (`Syne` and `JetBrains Mono`).
- **Files & Responsibilities**:
  - `frontend/vite.config.js`: Proxies all `/api/*` network calls directly to backend port `8088`.
  - `frontend/src/index.css`: Defines glassmorphic panel tokens, animations, custom scrollbars, and button styling.
  - `frontend/src/App.jsx`:
    - **Tab 1: Real-Time Markov Evaluator**: Debounced live evaluation input, quick archetype benchmark presets, character-by-character n-gram probability badges, Monte Carlo guess rank display, Shannon entropy gauge, and actionable recommendations.
    - **Tab 2: Argon2id Portal**: Interactive registration and login forms displaying real-time memory-hard derivation time and constant-time verification durations.
    - **Tab 3: Security Audit & DB**: Live SQLite audit table showing login attempts, host IPs, success/failure flags, and registered subscriber counts.
    - **Tab 4: Architecture & Methodology**: Educational guide breaking down character n-gram math and Argon2id memory-hardness principles.

---

## 4. End-to-End Data & Execution Flow

### Registration Flow:
```text
User enters Username & Password in Frontend
                   │
                   ▼
        POST /register to server.py
                   │
                   ▼
       Validates username format in db.py
                   │
                   ▼
       policy.py (PolicyEngine.check)
         ├── In-memory top-100k blocklist check
         ├── Structural check (repeats, sequential runs)
         ├── Username substring check
         ├── Shannon entropy calculation
         └── markov_model.py: log10_prob & Monte Carlo guess_number
                   │
           [If tier rejected] ──> Returns 400 with feedback
                   │
           [If accepted]
                   ▼
       hashing.py: hash_password(password)
         ├── Generates 16-byte random salt
         ├── Hashes via Argon2id (m=64MiB, t=3, p=1)
         └── Computes execution time
                   │
                   ▼
       db.py: create_user(conn, username, hash)
         └── Persists to SQLite 'users' table
                   │
                   ▼
       Frontend displays confirmation & hash preview
```

### Authentication Flow:
```text
User enters Username & Password
                   │
                   ▼
         POST /login to server.py
                   │
                   ▼
         db.py: get_user(conn, username)
         ├── User Not Found:
         │     ├── hashing.py: dummy_verify(password)  [Constant-time defense]
         │     ├── db.py: log_event(..., success=False)
         │     └── Returns 401 "Invalid username or password"
         │
         └── User Exists:
               ├── hashing.py: verify_password(hash, password)
               ├── If valid:
               │     ├── db.py: reset_failed(...)
               │     ├── db.py: log_event(..., success=True)
               │     └── Returns 200 OK with timing telemetry
               └── If invalid:
                     ├── db.py: record_failed(...)
                     ├── db.py: log_event(..., success=False)
                     └── Returns 401 "Invalid username or password"
```

---

## 5. Summary of System Strengths

1. **Empirical Defense**: Replaces flawed static password rules with data-driven Markov chain probabilities.
2. **State-of-the-Art Cryptography**: Employs RFC 9106 Argon2id to defeat dedicated hardware attack rigs.
3. **Defense-in-Depth**: Combines blocklists, Shannon entropy, sequential pattern detectors, and timing attack resistance.
4. **Developer & User Experience**: Offers real-time feedback with character-level visual diagnostics and an intuitive web interface.
