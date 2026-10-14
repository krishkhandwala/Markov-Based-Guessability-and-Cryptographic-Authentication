# Markov-Based Guessability and Cryptographic Authentication

## Setup and Installation 

### Step 1: Clone the Repository

1. Create a folder where you want to store the project.
2. Open a terminal in that folder.
3. Clone the repository:

```bash
git clone https://github.com/krishkhandwala/Markov-Based-Guessability-and-Cryptographic-Authentication.git
```

4. Navigate into the project directory:

```bash
cd Markov-Based-Guessability-and-Cryptographic-Authentication
```

### Step 2: Install Dependencies

Install the required Python packages by running:

```bash
pip install -r requirements.txt
```

### Step 3: Download the Dataset

Download the `rockyou.txt` dataset from the following link:

[Download rockyou.txt from Google Drive](https://drive.google.com/file/d/1VgXq3kuSSI57LXAlqdLuY3BytbrONmO5/view?usp=sharing)

Place the downloaded `rockyou.txt` file in the root directory of the project.

### Step 4: Preprocess the Dataset

Run the following commands from the project root directory.

**1. Generate the prototype dataset (limited to 1,000,000 entries):**

```bash
python 1_preprocess.py --input rockyou.txt --outdir data/proto --limit 1000000
```

**2. Generate the processed dataset using the full input file:**

```bash
python 1_preprocess.py --input rockyou.txt --outdir data/processed
```

After successful execution, the preprocessed data will be available in:

- `data/proto` — Prototype dataset generated using the first 1,000,000 entries, as handled by the preprocessing script.
- `data/processed` — Processed dataset generated from the full input file.

## Notes

- Ensure Python and pip are installed and accessible from your terminal.
- Make sure `rockyou.txt` is placed in the project root directory before running the preprocessing commands.
- The preprocessing process may take some time depending on your system specifications and dataset size.