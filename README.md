# Markov-Based Guessability and Cryptographic Authentication

A password strength evaluation and authentication system combining character-level Markov models for guessability estimation with Argon2id cryptographic storage.

## Architecture

1. **Preprocessing (`1_preprocess.py`)**: Filters raw password datasets (printable ASCII, lengths 4-32), performs deterministic train/validation/test splits (80/10/10), and extracts frequent-password blocklists.
2. **Guessability Engine (`2_markov_model.py`)**: Character n-gram Markov chain with Witten-Bell smoothing and Monte Carlo estimation (Dell'Amico & Filippone, 2015) to calculate log-probabilities and expected guess numbers.
3. **Policy Engine (`3_policy.py`)**: Evaluates passwords against empirical guess-number tiers and blocklists to enforce registration policies.
4. **Cryptographic Storage (`4_crypto.py`)**: Password hashing using Argon2id with per-user salts, resistant to GPU and ASIC brute-force attacks.
5. **API Layer (`5_api.py`)**: REST interface for real-time guessability scoring, registration, and authentication.

## Project Status

| Component | Module | Status | Description |
|---|---|---|---|
| Phase 1: Preprocessing | `1_preprocess.py` | Completed | RockYou cleaning, 80/10/10 split, count tables, top-100k blocklist |
| Phase 2: Markov Model | `2_markov_model.py` | Completed | n-gram training, Witten-Bell smoothing, Monte Carlo guess estimation |
| Phase 3: Policy Engine | `3_policy.py` | Next Goal | Tier threshold calibration, blocklist filtering, strength classification |
| Phase 4: Cryptographic Auth | `4_crypto.py` | Next Goal | Argon2id hashing, salt management, token issuance |
| Phase 5: Web API | `5_api.py` | Pending | FastAPI endpoints for password scoring, registration, and login |
| Phase 6: Benchmarking | `6_benchmark.py` | Pending | Attack simulation and comparison against static entropy metrics |

## Installation

### Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

### Dataset

Download the RockYou dataset and place `rockyou.txt` in the repository root:
- [rockyou.txt download](https://drive.google.com/file/d/1VgXq3kuSSI57LXAlqdLuY3BytbrONmO5/view?usp=sharing)

## Usage

### 1. Data Preprocessing

Generate prototype splits (first 1,000,000 entries):
```bash
python 1_preprocess.py --input rockyou.txt --outdir data/proto --limit 1000000
```

Generate full dataset splits:
```bash
python 1_preprocess.py --input rockyou.txt --outdir data/processed
```

Output files in target directory:
- `train_counts.tsv`, `val_counts.tsv`, `test_counts.tsv`
- `train.txt`, `val.txt`, `test.txt`
- `blocklist_top100k.txt`

### 2. Markov Guessability Model

Compare perplexity across n-gram orders on the validation set:
```bash
python 2_markov_model.py compare --train data/proto/train_counts.tsv --val data/proto/val_counts.tsv --orders 2 3 4 5
```

Train model and compute Monte Carlo estimation:
```bash
python 2_markov_model.py train --train data/proto/train_counts.tsv \
                               --val data/proto/val_counts.tsv \
                               --order 4 \
                               --samples 200000 \
                               --out model.pkl
```

Score passwords using the trained model:
```bash
python 2_markov_model.py score model.pkl password P@ssw0rd "xK9#mQ2$vL"
```

## Next Objectives

1. **Threshold Calibration (`3_policy.py`)**:
   - Evaluate guess-number distribution on validation data to calibrate tier boundaries (`REJECT`, `WEAK`, `ACCEPT`, `STRONG`).
   - Integrate `blocklist_top100k.txt` filtering.
2. **Argon2id Authentication (`4_crypto.py`)**:
   - Implement password hashing using `argon2-cffi` (RFC 9106 parameter profile).
   - Add verification routine and secure session token generation via `cryptography`.
3. **API Implementation (`5_api.py`)**:
   - Implement endpoints:
     - `POST /score`: Password evaluation returning log probability and guess estimate.
     - `POST /register`: Policy check and Argon2id hash storage.
     - `POST /login`: Authentication against stored hash.