from pathlib import Path

from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeout

from config.settings import get_settings
from linkedin.session_manager import SessionManager
from utils.helpers import ensure_dir
from utils.logger import setup_logger

logger = setup_logger(__name__)

LOGIN_URLS = [
    "https://www.linkedin.com/login",
    "https://www.linkedin.com/uas/login",
]

EMAIL_SELECTORS = [
    "#username",
    'input[name="session_key"]',
    'input[autocomplete="username"]',
    'input[id="session_key"]',
    'input[type="email"]',
    'input[aria-label*="Email"]',
    'input[aria-label*="email"]',
]

PASSWORD_SELECTORS = [
    "#password",
    'input[name="session_password"]',
    'input[autocomplete="current-password"]',
    'input[id="session_password"]',
    'input[type="password"]',
]

SUBMIT_SELECTORS = [
    'button[type="submit"]',
    'button[data-litms-control-urn="login-submit"]',
    ".btn__primary--large",
    'button:has-text("Sign in")',
    'button:has-text("Log in")',
]

COOKIE_DISMISS_SELECTORS = [
    'button:has-text("Accept")',
    'button:has-text("Accept all")',
    'button:has-text("Reject")',
    'button[action-type="ACCEPT"]',
    'button[action-type="DENY"]',
]


async def _save_debug_screenshot(page: Page, name: str):
    try:
        export_dir = ensure_dir(Path(get_settings().export_dir).parent / "debug")
        path = export_dir / f"{name}.png"
        await page.screenshot(path=str(path), full_page=True)
        logger.info("Debug screenshot saved: %s", path)
    except Exception as e:
        logger.debug("Could not save screenshot: %s", e)


async def _is_on_feed(page: Page) -> bool:
    url = page.url
    return (
        ("feed" in url or "mynetwork" in url)
        and "login" not in url
        and "checkpoint" not in url
        and "authwall" not in url
    )


async def _find_visible_locator(page: Page, selectors: list[str], timeout: int = 8000):
    # Check main page and any iframes
    frames = [page] + page.frames
    for frame in frames:
        for selector in selectors:
            try:
                locator = frame.locator(selector).first
                await locator.wait_for(state="visible", timeout=timeout)
                return locator
            except PlaywrightTimeout:
                continue
    return None


async def _dismiss_cookie_banner(page: Page):
    for selector in COOKIE_DISMISS_SELECTORS:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=1500):
                await btn.click()
                await page.wait_for_timeout(1000)
                logger.info("Dismissed cookie/consent banner")
                return
        except PlaywrightTimeout:
            continue


async def _fill_login_form(page: Page, email: str, password: str) -> bool:
    await _dismiss_cookie_banner(page)
    await page.wait_for_timeout(1500)

    email_input = await _find_visible_locator(page, EMAIL_SELECTORS, timeout=10000)
    if not email_input:
        return False

    await email_input.click()
    await email_input.fill(email)
    await page.wait_for_timeout(500)

    password_input = await _find_visible_locator(page, PASSWORD_SELECTORS, timeout=5000)
    if not password_input:
        next_btn = await _find_visible_locator(page, SUBMIT_SELECTORS, timeout=5000)
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(2500)
            password_input = await _find_visible_locator(page, PASSWORD_SELECTORS, timeout=10000)

    if not password_input:
        return False

    await password_input.click()
    await password_input.fill(password)
    await page.wait_for_timeout(500)

    submit_btn = await _find_visible_locator(page, SUBMIT_SELECTORS, timeout=5000)
    if submit_btn:
        await submit_btn.click()
    else:
        await page.keyboard.press("Enter")

    return True


async def _wait_for_manual_login(page: Page, timeout_seconds: int = 180) -> bool:
    logger.info(
        ">>> Log in to LinkedIn in the browser window (waiting up to %d seconds)...",
        timeout_seconds,
    )
    await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=60000)

    for i in range(timeout_seconds):
        await page.wait_for_timeout(1000)
        if await _is_on_feed(page):
            logger.info("Login successful!")
            return True
        if i % 15 == 0 and i > 0:
            logger.info("Still waiting... (complete login or any security challenge in the browser)")

    logger.error("Login timed out. Run: python app.py --login")
    return False


async def login_to_linkedin(
    page: Page,
    context: BrowserContext | None = None,
    session_path: str | None = None,
    headless: bool | None = None,
    email: str | None = None,
    password: str | None = None,
) -> bool:
    settings = get_settings()
    session_manager = SessionManager(session_path=session_path)
    is_headless = settings.linkedin_headless if headless is None else headless

    login_email = email or settings.linkedin_email
    login_password = password or settings.linkedin_password

    # 1. Check if persistent browser profile is already logged in
    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(2000)
    if await _is_on_feed(page):
        logger.info("Already logged in via browser profile")
        if context:
            await session_manager.save_session(context)
        return True

    # 2. Visible browser → manual login (most reliable)
    if not is_headless:
        if await _wait_for_manual_login(page):
            if context:
                await session_manager.save_session(context)
            return True
        return False

    # 3. Headless → try automated login across multiple URLs
    if not login_email or not login_password:
        logger.error(
            "Not logged in. Run once with a visible browser o paste cookie:\n"
            "  python app.py --login"
        )
        return False

    logger.info("Attempting automated login (headless)...")

    for login_url in LOGIN_URLS:
        await page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2000)

        if await _fill_login_form(page, login_email, login_password):
            break
    else:
        await _save_debug_screenshot(page, "login_failed")
        logger.error(
            "LinkedIn blocked headless login (no form found).\n"
            "Run this once to log in manually — your session will be saved:\n"
            "  python app.py --login"
        )
        return False

    await page.wait_for_timeout(5000)

    try:
        await page.wait_for_url(
            lambda url: "feed" in url or "checkpoint" in url or "challenge" in url,
            timeout=30000,
        )
    except PlaywrightTimeout:
        pass

    if "checkpoint" in page.url or "challenge" in page.url:
        logger.error("Security challenge detected. Run: python app.py --login")
        return False

    if await _is_on_feed(page):
        if context:
            await session_manager.save_session(context)
        logger.info("Successfully logged in to LinkedIn")
        return True

    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
    if await _is_on_feed(page):
        if context:
            await session_manager.save_session(context)
        return True

    await _save_debug_screenshot(page, "login_failed_final")
    logger.error("Login failed (URL: %s). Run: python app.py --login", page.url)
    return False
