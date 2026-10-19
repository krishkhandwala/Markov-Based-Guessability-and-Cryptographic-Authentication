"""
Enhanced FastAPI server handling registration, login, guessability scoring,
audit logs, and security headers with full CORS support for the interactive dashboard.
"""
import os
import time
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

import db
from policy import PolicyEngine
from hashing import hash_password, verify_password, dummy_verify

app = FastAPI(
    title="Markov-Based Guessability & Cryptographic Authentication API",
    description="Probabilistic password hardness assessment and Argon2id security",
    version="2.0.0"
)

# Enable CORS for local dev frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model and initialize services once at startup
MODEL_PATH = os.environ.get("MODEL_PATH", "model.pkl")
BLOCKLIST_PATH = os.environ.get("BLOCKLIST_PATH", "data/processed/blocklist_top100k.txt")
DB_PATH = os.environ.get("DB_PATH", "auth.db")

engine = PolicyEngine(MODEL_PATH, BLOCKLIST_PATH if os.path.exists(BLOCKLIST_PATH) else None)
conn = db.connect(DB_PATH)


class AuthRequest(BaseModel):
    username: str = Field(..., max_length=32)
    password: str = Field(..., max_length=128)


class ScoreRequest(BaseModel):
    password: str = Field(..., max_length=128)
    username: str = Field(default="", max_length=32)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
def health():
    return {
        "status": "online",
        "model_loaded": engine.model is not None,
        "blocklist_size": len(engine.blocklist),
        "timestamp": time.time()
    }


@app.post("/score")
def score_password(req: ScoreRequest):
    """
    Evaluates password in real-time without persisting credentials.
    Returns Markov log-probabilities, guess rank estimates, Shannon entropy,
    structural pattern detections, and policy admission decisions.
    """
    decision = engine.check(req.password, username=req.username if req.username else None)
    eval_res = decision.result
    
    # Calculate n-gram transition breakdown if model is available
    transitions = []
    if engine.model is not None and req.password:
        try:
            m = engine.model
            pad = "\x02" * (m.order - 1)
            s = pad + req.password + "\x03"
            h = m.order - 1
            for i in range(h, len(s)):
                ch = s[i]
                ctx = s[i - h:i] if h else ""
                prob = m._prob(ch, ctx)
                log10_p = float(np.log10(prob)) if prob > 0 else -15.0
                display_char = "<END>" if ch == "\x03" else ch
                display_ctx = ctx.replace("\x02", "^")
                transitions.append({
                    "char": display_char,
                    "context": display_ctx,
                    "prob": float(prob),
                    "log10_prob": round(log10_p, 3)
                })
        except Exception:
            pass

    return {
        "password_length": len(req.password),
        "is_acceptable": decision.accepted,
        "tier": eval_res.tier,
        "estimated_guesses": eval_res.estimated_guesses,
        "log10_prob": eval_res.log10_prob,
        "shannon_entropy_bits": eval_res.shannon_entropy_bits,
        "in_blocklist": eval_res.in_blocklist,
        "violations": eval_res.violations,
        "feedback": decision.feedback,
        "transitions": transitions[:32]
    }


@app.post("/register", status_code=201)
def register(req: AuthRequest):
    if not db.valid_username(req.username):
        raise HTTPException(status_code=400, detail=["Invalid username format (3-32 alphanumeric characters)."])
    
    decision = engine.check(req.password, username=req.username)
    if not decision.accepted:
        raise HTTPException(status_code=400, detail=decision.feedback)
    
    start_hash = time.perf_counter()
    hashed = hash_password(req.password)
    hashing_time_ms = round((time.perf_counter() - start_hash) * 1000, 2)
    
    try:
        db.create_user(conn, req.username, hashed)
    except db.UserExists:
        raise HTTPException(status_code=400, detail=["Username already taken."])
    
    return {
        "message": "User registered successfully.",
        "username": req.username,
        "tier": decision.result.tier,
        "estimated_guesses": decision.result.estimated_guesses,
        "hash_preview": hashed[:35] + "...",
        "hashing_time_ms": hashing_time_ms
    }


@app.post("/login")
def login(req: AuthRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    user = db.get_user(conn, req.username)
    
    if user is None:
        # Prevent username enumeration via timing attacks
        t0 = time.perf_counter()
        dummy_verify(req.password)
        auth_duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        db.log_event(conn, req.username, ip, success=False)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    t0 = time.perf_counter()
    valid = verify_password(user["password_hash"], req.password)
    auth_duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    if valid:
        db.reset_failed(conn, req.username)
        db.log_event(conn, req.username, ip, success=True)
        return {
            "message": "Login successful",
            "username": req.username,
            "auth_duration_ms": auth_duration_ms,
            "created_at": user["created_at"],
            "hash_algorithm": "Argon2id (RFC 9106)"
        }
    else:
        db.record_failed(conn, req.username)
        db.log_event(conn, req.username, ip, success=False)
        raise HTTPException(status_code=401, detail="Invalid username or password")


@app.get("/telemetry")
def telemetry():
    """Returns database telemetry, user counts, and recent security logs."""
    try:
        users = conn.execute("SELECT id, username, created_at, failed_attempts, substr(password_hash, 1, 35) as hash_preview FROM users ORDER BY id DESC LIMIT 15").fetchall()
        events = conn.execute("SELECT id, username, ip, success, ts FROM login_events ORDER BY id DESC LIMIT 20").fetchall()
        
        user_list = [dict(u) for u in users]
        event_list = [dict(e) for e in events]
        
        return {
            "total_users": len(user_list),
            "recent_users": user_list,
            "recent_events": event_list,
            "blocklist_count": len(engine.blocklist),
            "model_status": "Loaded (Order 4, Witten-Bell Smoothing)" if engine.model else "Unloaded"
        }
    except Exception as e:
        return {"error": str(e), "total_users": 0, "recent_users": [], "recent_events": []}


if __name__ == "__main__":
    insecure = os.environ.get("INSECURE_HTTP", "1") == "1"
    if insecure:
        uvicorn.run(app, host="127.0.0.1", port=8080)
    else:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8443,
            ssl_keyfile="key.pem",
            ssl_certfile="cert.pem"
        )