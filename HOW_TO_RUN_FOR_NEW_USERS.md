# GETTING STARTED GUIDE FOR NEW USERS
**Markov-Based Guessability & Cryptographic Authentication System**

Follow these instructions to set up, build, and run the complete system (Backend API + Interactive Frontend Dashboard) from scratch on any machine.

---

## 1. Prerequisites

Make sure the following tools are installed on your system:
- **Python**: Version 3.10 or higher ([Download Python](https://www.python.org/downloads/))
- **Node.js**: Version 18 or higher with `npm` ([Download Node.js](https://nodejs.org/))
- **Git**: Installed and available in your terminal

---

## 2. One-Time Setup (First Time Only)

Open your terminal (PowerShell, Command Prompt, or Bash) and navigate to the project directory:

```bash
cd "Markov-Based-Guessability-and-Cryptographic-Authentication"
```

### Step 2.1: Install Python Backend Dependencies
```bash
pip install -r requirements.txt
```

### Step 2.2: Ensure the Markov Model and Certificates Exist
If `model.pkl` or SSL certificates do not already exist, generate them:

1. **Generate HTTPS SSL Certificates**:
   ```bash
   python gen_cert.py
   ```
   *(This creates `cert.pem` and `key.pem`)*

2. **Generate / Train the Markov Model (if `model.pkl` is not present)**:
   ```bash
   # Preprocess sample dataset:
   python preprocess.py --input rockyou_sample.txt --outdir data/processed

   # Train Markov Model (Order 4) with Monte Carlo Estimator:
   python -c "
   import pickle, markov_model
   train_pairs = markov_model.load_counts('data/processed/train_counts.tsv')
   model = markov_model.MarkovModel(order=4)
   model.train(train_pairs)
   model.build_estimator(n_samples=50000, seed=42)
   with open('model.pkl', 'wb') as f:
       pickle.dump(model, f)
   print('Model trained and saved to model.pkl!')
   "
   ```

### Step 2.3: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 3. Running the Entire System (2-Step Process)

To run the application, open **two separate terminal windows**.

---

### Terminal 1: Start the Backend API Server

Navigate to the project root directory and start the server:

```powershell
# Navigate to project root:
cd "Markov-Based-Guessability-and-Cryptographic-Authentication"

# Start FastAPI server on port 8088:
python -c "import server, uvicorn; uvicorn.run(server.app, host='127.0.0.1', port=8088)"
```

- **Backend Status:** You should see:
  ```text
  INFO: Started server process
  INFO: Application startup complete.
  INFO: Uvicorn running on http://127.0.0.1:8088 (Press CTRL+C to quit)
  ```
- **Backend API URL:** `http://127.0.0.1:8088`
- **Swagger Interactive Docs:** `http://127.0.0.1:8088/docs`
- **Health Check:** `http://127.0.0.1:8088/health`

---

### Terminal 2: Start the Frontend Application

Open a second terminal window, navigate into the `frontend` folder, and start the development server:

```powershell
# Navigate into the frontend folder:
cd "Markov-Based-Guessability-and-Cryptographic-Authentication\frontend"

# Launch the Vite dev server:
npm run dev
```

- **Frontend Status:** You should see:
  ```text
  VITE v8.3.4 ready in 350 ms

  ➜  Local:   http://localhost:5174/
  ➜  Network: use --host to expose
  ```
- **Web Dashboard URL:** Open your browser and go to **`http://localhost:5174/`** (or `http://localhost:5173/`).

---

## 4. One-Click Command (PowerShell Only)

If you are using Windows PowerShell, you can launch both backend and frontend simultaneously with a single command:

```powershell
cd "Markov-Based-Guessability-and-Cryptographic-Authentication"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -c 'import server, uvicorn; uvicorn.run(server.app, host=\"127.0.0.1\", port=8088)'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
```

---

## 5. How to Test & Verify It's Working

1. **Open the Web Interface**: Go to `http://localhost:5174/`.
2. **Tab 1 (Markov Evaluator)**:
   - Type `password` $\rightarrow$ Observe the red **REJECT** badge, breached blocklist hit, and high-probability character transitions.
   - Click the preset button **`Diceware Passphrase`** $\rightarrow$ Observe the green **STRONG** badge ($6.38 \times 10^{31}$ guesses) and high Shannon entropy.
3. **Tab 2 (Argon2id Portal)**:
   - Click **`REGISTER WITH POLICY`**.
   - Enter username `newuser` and password `Secure#Passphrase2026!`.
   - Click Register $\rightarrow$ Confetti bursts and your memory-hard Argon2id hash is generated and stored in SQLite `auth.db`.
4. **Tab 3 (Security Audit & DB)**:
   - View real-time registered subscriber counts and the immutable security audit log.

---

## 6. Running Automated Backend Tests

To test the backend independently without a browser, open a terminal in the root directory and run:

```bash
python test_client.py
```

All 6 automated integration tests will execute and confirm:
- Server health (`200 OK`)
- Weak password rejection (`400 Bad Request`)
- Strong password registration (`201 Created`)
- Correct password login (`200 OK`)
- Incorrect password rejection (`401 Unauthorized`)
- Unknown user timing attack defense (`401 Unauthorized`)
