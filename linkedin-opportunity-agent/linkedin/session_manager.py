import json
from pathlib import Path

from playwright.async_api import BrowserContext, Page

from config.settings import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionManager:
    def __init__(self, session_path: str | None = None):
        settings = get_settings()
        self.session_path = Path(session_path or settings.linkedin_session_path)
        self.session_path.parent.mkdir(parents=True, exist_ok=True)

    def session_exists(self) -> bool:
        if not self.session_path.exists() or self.session_path.stat().st_size < 10:
            return False
        try:
            data = json.loads(self.session_path.read_text())
            if "storage" in data:
                cookies = data["storage"].get("cookies", [])
            else:
                cookies = data.get("cookies", [])
            return len(cookies) > 0
        except (json.JSONDecodeError, OSError):
            return False

    def get_storage_state(self) -> dict | None:
        if not self.session_exists():
            return None
        try:
            data = json.loads(self.session_path.read_text())
            if "storage" in data:
                return data["storage"]
            if "cookies" in data:
                return {"cookies": data["cookies"], "origins": []}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Invalid session file: %s", e)
        return None

    def clear_session(self):
        if self.session_path.exists():
            self.session_path.unlink()
            logger.info("Cleared stale LinkedIn session")

    async def save_session(self, context: BrowserContext):
        storage = await context.storage_state()
        data = {"storage": storage}
        self.session_path.write_text(json.dumps(data, indent=2))
        logger.info("LinkedIn session saved to %s", self.session_path)

    async def is_logged_in(self, page: Page) -> bool:
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        url = page.url
        logged_in = (
            ("feed" in url or "mynetwork" in url)
            and "login" not in url
            and "checkpoint" not in url
            and "authwall" not in url
        )
        if logged_in:
            logger.info("Session is valid (URL: %s)", url)
        else:
            logger.info("Session invalid or expired (URL: %s)", url)
        return logged_in
