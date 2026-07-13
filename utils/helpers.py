import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


def generate_post_id(content: str, author: str) -> str:
    raw = f"{author}:{content[:500]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def parse_linkedin_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    raw = date_str.strip()
    date_str = raw.lower()
    now = datetime.utcnow()

    if "just now" in date_str:
        return now
    if "yesterday" in date_str:
        return now - timedelta(days=1)

    # Relative: 5m, 2h, 1d, 3w, 2mo, 1y
    rel = re.match(
        r"^(\d+)\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|"
        r"h|hr|hrs|hour|hours|d|day|days|w|wk|week|weeks|"
        r"mo|mos|month|months|y|yr|yrs|year|years)$",
        date_str,
    )
    if rel:
        n = int(rel.group(1))
        unit = rel.group(2)
        if unit.startswith("s"):
            return now - timedelta(seconds=n)
        if unit.startswith("m") and not unit.startswith("mo"):
            return now - timedelta(minutes=n)
        if unit.startswith("h"):
            return now - timedelta(hours=n)
        if unit.startswith("d"):
            return now - timedelta(days=n)
        if unit.startswith("w"):
            return now - timedelta(weeks=n)
        if unit.startswith("mo"):
            return now - timedelta(days=n * 30)
        if unit.startswith("y"):
            return now - timedelta(days=n * 365)

    # Absolute: Jun 23, 2025 or March 15
    for fmt in ("%b %d, %Y", "%b %d %Y", "%B %d, %Y", "%B %d %Y", "%b %d", "%B %d"):
        try:
            parsed = datetime.strptime(raw, fmt)
            if parsed.year == 1900:
                parsed = parsed.replace(year=now.year)
            return parsed
        except ValueError:
            continue

    return None


def format_posted_time(posted_at: Optional[datetime], posted_label: Optional[str] = None) -> str:
    """Human-readable posted time for the dashboard."""
    if posted_at:
        delta = datetime.utcnow() - posted_at
        if not posted_label:
            if delta.days > 0:
                posted_label = f"{delta.days}d"
            elif delta.seconds >= 3600:
                posted_label = f"{delta.seconds // 3600}h"
            elif delta.seconds >= 60:
                posted_label = f"{delta.seconds // 60}m"
            else:
                posted_label = "just now"
        formatted = posted_at.strftime("%b %d, %Y · %H:%M UTC")
        if posted_label == "just now":
            return f"just now ({formatted})"
        return f"{posted_label} ago ({formatted})"
    if posted_label:
        return posted_label
    return "Time unknown"


def safe_json_loads(text: str, default: Any = None) -> Any:
    try:
        cleaned = re.sub(r"```json\s*", "", text)
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return default


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def truncate_text(text: str, max_length: int = 500) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
