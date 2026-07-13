import hashlib
import secrets

from database.crud import create_app_user, get_user_by_email, get_user_by_id, mark_linkedin_connected
from database.db import get_db


def _hash_password(password: str) -> str:
    """One-way hash — plain passwords are never stored."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
    except ValueError:
        return False
    for iterations in (600_000, 100_000):
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
        if secrets.compare_digest(digest.hex(), expected):
            return True
    return False


def _user_payload(user) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name or user.email.split("@")[0],
        "linkedin_connected": bool(user.linkedin_connected),
    }


def signup(email: str, password: str, name: str | None = None) -> tuple[bool, str]:
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return False, "Enter a valid email address."
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters."

    with get_db() as db:
        if get_user_by_email(db, email):
            return False, "An account with this email already exists."
        create_app_user(db, email, _hash_password(password), name=name or None)
    return True, "Account created. You can log in now."


def login(email: str, password: str) -> tuple[bool, str, dict | None]:
    email = (email or "").strip().lower()
    with get_db() as db:
        user = get_user_by_email(db, email)
        if not user or not _verify_password(password, user.password_hash):
            return False, "Invalid email or password.", None
        return True, "Welcome back!", _user_payload(user)


def refresh_user(user_id: int) -> dict | None:
    with get_db() as db:
        user = get_user_by_id(db, user_id)
        return _user_payload(user) if user else None


def set_linkedin_connected(user_id: int) -> None:
    with get_db() as db:
        mark_linkedin_connected(db, user_id)


def set_linkedin_disconnected(user_id: int) -> None:
    with get_db() as db:
        from database.crud import mark_linkedin_disconnected as db_mark_disconnected
        db_mark_disconnected(db, user_id)
