from pathlib import Path

from config.settings import BASE_DIR


def linkedin_profile_dir(user_id: int) -> Path:
    return BASE_DIR / "storage" / "browser_profiles" / f"user_{user_id}"


def linkedin_session_file(user_id: int) -> Path:
    return BASE_DIR / "storage" / "sessions" / f"user_{user_id}_linkedin.json"
