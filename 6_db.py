"""
Phase 3: database layer (SQLite). Only hashes are stored, never plaintext passwords.
All queries are parameterised (no string formatting) to prevent SQL injection.
"""
import re
import sqlite3
import time

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,          -- full Argon2id string (contains salt + parameters)
    created_at      REAL NOT NULL,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS login_events (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    ip       TEXT,
    success  INTEGER NOT NULL,
    ts       REAL NOT NULL
);
"""


class UserExists(Exception):
    pass


def connect(path="auth.db"):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def valid_username(u: str) -> bool:
    return bool(USERNAME_RE.match(u))


def create_user(conn, username, password_hash):
    try:
        with conn:
            conn.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                         (username.lower(), password_hash, time.time()))
    except sqlite3.IntegrityError:
        raise UserExists(username)


def get_user(conn, username):
    return conn.execute("SELECT * FROM users WHERE username = ?", (username.lower(),)).fetchone()


def update_hash(conn, username, new_hash):
    with conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username.lower()))


def record_failed(conn, username):
    with conn:
        conn.execute("UPDATE users SET failed_attempts = failed_attempts + 1 WHERE username = ?",
                     (username.lower(),))


def reset_failed(conn, username):
    with conn:
        conn.execute("UPDATE users SET failed_attempts = 0, locked_until = 0 WHERE username = ?",
                     (username.lower(),))


def log_event(conn, username, ip, success):
    with conn:
        conn.execute("INSERT INTO login_events (username, ip, success, ts) VALUES (?, ?, ?, ?)",
                     (username.lower(), ip, int(success), time.time()))