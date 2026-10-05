import base64, hashlib, hmac, os
from datetime import datetime, timezone

SECRET = os.getenv("AUTH_SECRET", "rentmatch-ai-local-secret-change-me").encode()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return base64.urlsafe_b64encode(salt + digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(encoded.encode())
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def make_token(user_id: int) -> str:
    timestamp = int(datetime.now(timezone.utc).timestamp())
    payload = f"{user_id}:{timestamp}"
    sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()


def read_token(token: str) -> int:
    raw = base64.urlsafe_b64decode(token.encode()).decode()
    user_id, timestamp, sig = raw.rsplit(":", 2)
    payload = f"{user_id}:{timestamp}"
    expected = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Invalid token")
    return int(user_id)
