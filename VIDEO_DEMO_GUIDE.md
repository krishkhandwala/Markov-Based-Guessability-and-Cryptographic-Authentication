# VIDEO DEMO SCRIPT & DEMONSTRATION GUIDE
**Markov-Based Guessability & Cryptographic Authentication System**
Repository: `Markov-Based-Guessability-and-Cryptographic-Authentication`

---

## 1. Quick Video Outline & Timeline (Total Duration: ~3 to 5 Minutes)

| Timestamp | Segment Title | What to Show on Screen | What to Say / Highlight |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:45** | **The Problem & Architecture** | Code editor or Title slide / Dashboard | "Traditional regex rules (1 symbol, 1 uppercase) don't stop password crackers. This project implements Markov character n-grams + Argon2id." |
| **0:45 - 2:00** | **Live Markov Evaluator Demo** | Tab 1 (`Markov Evaluator`) | Type weak, common, and strong passwords. Show live n-gram probabilities, guess numbers, and entropy updating in real-time. |
| **2:00 - 3:15** | **Argon2id Registration & Auth** | Tab 2 (`Argon2id Portal`) | Try registering a weak password (fails), then a strong password (succeeds with confetti + hash preview). Show memory-hard derivation time (~300-400ms). |
| **3:15 - 4:00** | **Audit Log & Telemetry** | Tab 3 (`Security Audit & DB`) | Show the live SQLite table recording login attempts, timestamps, and host IPs. Demonstrate timing attack protection. |
| **4:00 - 4:45** | **CLI Verification (Terminal)** | Terminal with `test_client.py` | Run the automated test script to prove backend API compliance and HTTPS certificate validity. |

---

## 2. Pre-Recording Preparation

### Step 1: Open Terminal 1 & Start the Backend Server
```powershell
cd "C:\Users\Krish Khandwala\.gemini\antigravity-ide\scratch\Markov-Based-Guessability-and-Cryptographic-Authentication"

python -c "import server, uvicorn; uvicorn.run(server.app, host='127.0.0.1', port=8088)"
```
*Expected output: `INFO: Uvicorn running on http://127.0.0.1:8088`*

### Step 2: Open Terminal 2 & Start the Frontend
```powershell
cd "C:\Users\Krish Khandwala\.gemini\antigravity-ide\scratch\Markov-Based-Guessability-and-Cryptographic-Authentication\frontend"

npm run dev
```
*Expected output: `Local: http://localhost:5174/`*

### Step 3: Open Your Browser
Navigate to **`http://localhost:5174/`**. Keep your browser zoomed to 100% or 110% so the text and badges look crisp on video.

---

## 3. Step-by-Step Video Walkthrough Script

### Act 1: The Core Innovation (0:00 – 0:45)
- **Action**: Show the web dashboard header with the badge `MARKOV ORDER 4 + ARGON2ID`.
- **Talking Points**:
  > *"Most websites enforce rules like 'must contain 8 characters, 1 uppercase, and 1 symbol'. But attackers know humans simply capitalize the first letter and put '!' or '1' at the end. This system replaces that with an empirical 4th-order Markov model trained on leaked passwords and a Monte Carlo guess rank estimator, paired with RFC 9106 Argon2id memory-hard storage."*

---

### Act 2: Real-Time Guessability Analyzer (0:45 – 2:00)
- **Action**: Click on Tab 1 (**Markov Evaluator**).
- **Test Examples to Type on Camera**:

#### Example 1: The Classic Breached Password
- **Input**:
  - Username: `alice`
  - Password: `password`
- **What happens on screen**:
  - Verdict changes to **`REJECT`** (Red indicator).
  - Guesses: **`1.00e+00 guesses`**.
  - Blocklist: **`Flagged (Hit in Top 10,001 breached list)`**.
  - N-gram breakdown: Badges turn red because the transition `p -> a -> s -> s -> w -> o -> r -> d` has an extremely high conditional probability in RockYou.
- **Talking Points**:
  > *"Notice how the system immediately flags this as REJECT. Even if an attacker didn't have the dictionary, the joint log probability is high, placing it in the 1st guess category."*

#### Example 2: The "Rule-Compliant" Deception
- **Input**:
  - Username: `alice`
  - Password: `Password123!`
- **What happens on screen**:
  - Shows that while Shannon entropy is higher, the Markov transitions for `123` and `word` are still highly predictable to attackers.
  - The model detects the consecutive run `123`.

#### Example 3: The Username Attack (Context Violation)
- **Input**:
  - Username: `alice`
  - Password: `MySuperAliceSecret99!`
- **What happens on screen**:
  - System rejects admission with actionable recommendation: **`"Password must not contain the username."`**
- **Talking Points**:
  > *"Even with high entropy, the policy checks context. If a user includes their username, it is instantly denied."*

#### Example 4: The Diceware / High-Entropy Passphrase (Pass)
- **Input**: Click the preset button **`Diceware Passphrase`** (`correct-horse-battery-staple-77`) or type:
  - Password: `CorrectHorseBatteryStaple99!`
- **What happens on screen**:
  - Verdict turns bright green: **`STRONG`** / **`REGISTRATION PERMITTED`**.
  - Guesses: **`6.38e+31 guesses`** (trillions of years to crack).
  - Shannon Entropy: **`183.53 bits`**.
  - Transition Badges: Turn green and gold, showing that unexpected transitions lower attacker predictability.

---

### Act 3: Cryptographic Registration & Authentication (2:00 – 3:15)
- **Action**: Switch to Tab 2 (**Argon2id Portal**).

#### Test Scenario A: Denied Registration
1. Toggle mode to **`REGISTER WITH POLICY`**.
2. Username: `testuser`
3. Password: `123`
4. Click **`Verify Policy & Register User`**.
5. **Result**: Red box appears with exact policy violations: *"Password must be at least 8 characters (got 3). Estimated guessability is too high."*

#### Test Scenario B: Successful Memory-Hard Registration
1. Username: `demo_user`
2. Password: `SecureKey#2026!Passphrase`
3. Click **`Verify Policy & Register User`**.
4. **Result**:
   - Confetti bursts on screen!
   - Shows confirmation message: *"User registered successfully."*
   - Displays **Stored Argon2id Hash** preview: `$argon2id$v=19$m=65536,t=3,p=1$...`
   - Displays **Execution Time**: ~300 to 450 ms (shows the deliberate memory-hard work to defeat GPUs).
- **Talking Points**:
  > *"Notice the ~350 millisecond hashing duration. That is intentional. Argon2id requires 64 Megabytes of RAM and 3 passes per hash, making ASIC/GPU parallel cracking racks completely ineffective."*

#### Test Scenario C: Login Verification
1. Toggle to **`SIGN IN`**.
2. Enter `demo_user` with correct password $\rightarrow$ Status: **`Login successful`** in constant time.
3. Try typing the wrong password $\rightarrow$ Status: **`Invalid username or password (401)`**.

---

### Act 4: Live Telemetry & Timing Attack Resistance (3:15 – 4:00)
- **Action**: Switch to Tab 3 (**Security Audit & DB**).
- **What to Show**:
  - The stats counters: `Registered Identities` (increases as you register users), `Markov Status: ORDER IV`, `Breach Blocklist: 10,001`.
  - The live SQLite table: Show how every login attempt (success or failed) is recorded with IP, username, outcome badge, and timestamp.
- **Talking Points**:
  > *"In our database layer, passwords are never stored in plaintext. Furthermore, notice our timing attack protection: if an unknown user tries to log in, the server runs a dummy Argon2id verification so the response duration never leaks whether an account exists or not."*

---

### Act 5: Terminal Automated Test Suite (4:00 – 4:45)
- **Action**: Bring up a terminal window next to the browser and run:
  ```powershell
  python test_client.py
  ```
- **What happens on screen**:
  - All tests execute in sequence:
    ```text
    Testing /health... Status: 200, Response: ok
    Testing registration with weak password... Status: 400
    Testing registration with strong password... Status: 201
    Testing correct login... Status: 200
    Testing login with wrong password... Status: 401
    Testing login with unknown user... Status: 401
    All tests passed successfully!
    ```
- **Closing Statement**:
  > *"All tests pass cleanly end-to-end, validating the mathematical model, policy gatekeeper, database layer, and Argon2id cryptographic core."*

---

## 4. Cheat Sheet: Copy-Paste Inputs for Your Recording

| Test Case | Username | Password String | Expected Result |
| :--- | :--- | :--- | :--- |
| **Weak / Breached** | `demo` | `password` | **REJECT** (< 10⁶ guesses, blocklist flagged) |
| **Sequential Run** | `demo` | `Alpha12345678!` | **Flags sequential character run** `12345678` |
| **Username Substring** | `demo_user` | `P@sswordDemo_user99` | **REJECT** ("Password must not contain username") |
| **Short Password** | `demo` | `Abc!1` | **REJECT** ("Must be at least 8 characters") |
| **Strong Passphrase** | `demo_user` | `CorrectHorseBatteryStaple99!` | **STRONG / ACCEPT** (10²¹+ guesses, 183 bits entropy) |
| **Cryptographic High-Entropy**| `demo_user` | `xK9#mQ2$vL90!wPq` | **STRONG / ACCEPT** (6.38e+31 guesses) |

---

## 5. Helpful Presentation Tips
1. **Show Both Windows**: If you have space, split your screen with the **Frontend on the left** and the **Backend Terminal on the right**. When you hit "Register", the terminal logs flash simultaneously, proving real-time connection.
2. **Preset Buttons**: Click the buttons under *"Quick Archetype Benchmarks"* on Tab 1 if you don't want to type long passwords manually while speaking.
3. **Audio Tip**: Mention the reference papers (*Dell'Amico & Filippone 2015* and *RFC 9106*) to highlight academic and industry standard credibility.
