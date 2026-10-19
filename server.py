"""
Phase 4: FastAPI server handling registration, login, and security headers over HTTPS.
"""
import os
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

import db
from policy import PolicyEngine
from hashing import hash_password, verify_password, dummy_verify

app = FastAPI()

# Load model and initialize services once at startup
MODEL_PATH = os.environ.get("MODEL_PATH", "model.pkl")
BLOCKLIST_PATH = os.environ.get("BLOCKLIST_PATH", "data/processed/blocklist_top100k.txt")
DB_PATH = os.environ.get("DB_PATH", "auth.db")

engine = PolicyEngine(MODEL_PATH, BLOCKLIST_PATH if os.path.exists(BLOCKLIST_PATH) else None)
conn = db.connect(DB_PATH)


class AuthRequest(BaseModel):
    username: str = Field(..., max_length=32)
    password: str = Field(..., max_length=128)


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
    return "ok"


@app.post("/register", status_code=201)
def register(req: AuthRequest):
    if not db.valid_username(req.username):
        raise HTTPException(status_code=400, detail=["Invalid username format."])
    
    decision = engine.check(req.password, username=req.username)
    if not decision.accepted:
        raise HTTPException(status_code=400, detail=decision.feedback)
    
    hashed = hash_password(req.password)
    try:
        db.create_user(conn, req.username, hashed)
    except db.UserExists:
        raise HTTPException(status_code=400, detail=["Username already taken."])
    
    return {"message": "User registered successfully."}


@app.post("/login")
def login(req: AuthRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    user = db.get_user(conn, req.username)
    
    if user is None:
        # Prevent username enumeration via timing attacks
        dummy_verify(req.password)
        db.log_event(conn, req.username, ip, success=False)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if verify_password(user["password_hash"], req.password):
        db.reset_failed(conn, req.username)
        db.log_event(conn, req.username, ip, success=True)
        return {"message": "Login successful"}
    else:
        db.record_failed(conn, req.username)
        db.log_event(conn, req.username, ip, success=False)
        raise HTTPException(status_code=401, detail="Invalid username or password")


if __name__ == "__main__":
    insecure = os.environ.get("INSECURE_HTTP") == "1"
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