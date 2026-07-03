import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import BrowserContext, Page, async_playwright

from config.settings import get_settings
from linkedin.login import _save_debug_screenshot, login_to_linkedin
from linkedin.parser import enrich_post_metadata, parse_post_element
from schemas.post_schema import PostSchema
from utils.helpers import ensure_dir
from utils.logger import setup_logger

logger = setup_logger(__name__)

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

FEED_EXTRACT_JS = """
() => {
    const posts = [];
    const seen = new Set();

    // LinkedIn's 2025+ feed uses obfuscated classes — use aria-labels instead
    const menuButtons = Array.from(
        document.querySelectorAll('button[aria-label*="post by"]')
    ).filter((btn) => {
        const label = btn.getAttribute('aria-label') || '';
        return label.startsWith('Open control menu for post by');
    });

    function findPostContainer(button) {
        let el = button.parentElement;
        let best = null;
        for (let i = 0; i < 25 && el; i++) {
            const hasEngagement = el.querySelector(
                'button[aria-label="Comment"], button[aria-label*="Reaction button state"]'
            );
            const text = (el.innerText || '').trim();
            if (text.length > 100 && hasEngagement) return el;
            if (text.length > 100) best = el;
            el = el.parentElement;
        }
        return best || button.closest('div[componentkey]') || button.parentElement;
    }

    function cleanContent(raw, author) {
        let lines = raw.split('\\n').map((l) => l.trim()).filter(Boolean);
        // Drop lines that are UI chrome
        const skip = /^(Like|Comment|Repost|Send|Follow|Suggested|Feed post|\\d+[hdwmo]\\s*•|Premium|Promoted|• 3rd\\+|• 2nd|• 1st)/i;
        lines = lines.filter((l) => !skip.test(l) && l !== author);
        // Remove author title lines (short lines right after author often metadata)
        const content = lines.join('\\n').trim();
        return content;
    }

    function pickProfileUrl(container) {
        const link = container.querySelector('a[href*="/in/"]');
        return link ? link.href.split('?')[0] : null;
    }

    function pickAuthorTitle(container, author) {
        const lines = (container.innerText || '').split('\\n').map((l) => l.trim()).filter(Boolean);
        const idx = lines.findIndex((l) => l === author || l.startsWith(author));
        if (idx >= 0) {
            for (let i = idx + 1; i < Math.min(idx + 4, lines.length); i++) {
                const line = lines[i];
                if (!line || line === author) continue;
                if (/^(Follow|Like|Comment|Repost|Send|Suggested|Feed post|\\d)/i.test(line)) continue;
                if (/^•\\s*(1st|2nd|3rd)/i.test(line)) continue;
                if (line.length > 5 && line.length < 150) return line.replace(/\\s*•.*$/, '').trim();
            }
        }
        return null;
    }

    function pickTime(container) {
        const text = container.innerText || '';
        const patterns = [
            /(\\d+\\s*(?:s|sec|secs|second|seconds))\\s*•/i,
            /(\\d+\\s*(?:m|min|mins|minute|minutes))\\s*•/i,
            /(\\d+\\s*(?:h|hr|hrs|hour|hours))\\s*•/i,
            /(\\d+\\s*(?:d|day|days))\\s*•/i,
            /(\\d+\\s*(?:w|wk|week|weeks))\\s*•/i,
            /(\\d+\\s*(?:mo|mos|month|months))\\s*•/i,
            /(\\d+\\s*(?:y|yr|yrs|year|years))\\s*•/i,
            /(just now)\\s*•/i,
            /(\\d+[hdwmo])\\s*•/i,
            /([A-Z][a-z]{2,9}\\s+\\d{1,2}(?:,\\s*\\d{4})?)\\s*•/,
        ];
        for (const re of patterns) {
            const m = text.match(re);
            if (m) return m[1].trim();
        }
        return null;
    }

    function pickReactionCount(container) {
        const reactionBtn = container.querySelector('button[aria-label*="Reaction button state"]');
        if (reactionBtn) {
            const label = reactionBtn.getAttribute('aria-label') || '';
            const match = label.match(/(\\d[\\d,]*\\s*[km]?)/i);
            if (match) return match[1].trim();
        }
        const menuBtn = container.querySelector('button[aria-label="Open reactions menu"]');
        if (menuBtn) {
            const siblingText = (menuBtn.parentElement?.innerText || '').trim();
            const match = siblingText.match(/(\\d[\\d,]*\\s*[km]?)/i);
            if (match) return match[1].trim();
        }
        return '0';
    }

    function pickCommentCount(container) {
        const commentBtn = container.querySelector('button[aria-label="Comment"]');
        if (commentBtn) {
            for (const span of commentBtn.querySelectorAll('span')) {
                const text = (span.innerText || '').trim();
                if (/^\\d[\\d,]*$/.test(text)) return text;
            }
        }
        const text = container.innerText || '';
        const match = text.match(/(\\d[\\d,]*)\\s+comments?/i);
        return match ? match[1] : '0';
    }

    function pickPostUrl(container) {
        const patterns = [
            'a[href*="/feed/update/"]',
            'a[href*="/posts/"]',
            'a[href*="activity:"]',
            'a[href*="/pulse/"]',
        ];
        for (const sel of patterns) {
            const link = container.querySelector(sel);
            if (link && link.href) return link.href.split('?')[0];
        }
        for (const a of container.querySelectorAll('a[href*="linkedin.com"]')) {
            const href = a.href || '';
            if (
                href.includes('/feed/update/') ||
                href.includes('/posts/') ||
                href.includes('activity') ||
                href.includes('/pulse/')
            ) {
                return href.split('?')[0];
            }
        }
        return null;
    }

    menuButtons.forEach((btn, index) => {
        const label = btn.getAttribute('aria-label') || '';
        const match = label.match(/post by (.+)$/i);
        if (!match) return;

        const author = match[1].trim();
        const container = findPostContainer(btn);
        if (!container) return;

        const raw = container.innerText || '';
        const content = cleanContent(raw, author);
        if (!content || content.length < 15) return;

        const key = author + ':' + content.slice(0, 80);
        if (seen.has(key)) return;
        seen.add(key);

        posts.push({
            linkedin_post_id: `post-${index}-${author.replace(/\\s+/g, '-')}`,
            author_name: author,
            author_title: pickAuthorTitle(container, author),
            author_profile_url: pickProfileUrl(container),
            content,
            posted_time: pickTime(container),
            reactions_count: pickReactionCount(container),
            comments_count: pickCommentCount(container),
            post_url: pickPostUrl(container),
            image_urls: [],
        });
    });

    return {
        posts,
        cards_found: menuButtons.length,
        page_url: window.location.href,
        main_exists: !!document.querySelector('main'),
    };
}
"""

ENGAGE_WITH_POST_JS = """
({ authorName, authorProfileUrl, contentSnippet, action, commentText }) => {
    document.querySelectorAll('[data-cursor-target="1"]').forEach((el) => {
        try { el.removeAttribute('data-cursor-target'); } catch(e) {}
    });

    const norm = (s) => (s || "").toLowerCase().replace(/\\s+/g, " ").trim();
    const authorNorm = norm(authorName);
    const snippetNorm = norm(contentSnippet);
    const profileNorm = norm((authorProfileUrl || "").split("?")[0]).replace(/\\/$/, "");
    const snippetHead = snippetNorm.slice(0, 80);

    const menuButtons = Array.from(
        document.querySelectorAll('button[aria-label^="Open control menu for post by"]')
    );
    const btn = menuButtons.find((b) => norm(b.getAttribute('aria-label') || '').includes(authorNorm));

    function findPostContainer(button) {
        let el = button.parentElement;
        let best = null;
        for (let i = 0; i < 25 && el; i++) {
            const txt = (el.innerText || "").trim();
            if (txt.length > 120) best = el;
            if (snippetNorm && norm(txt).includes(snippetNorm)) return el;
            el = el.parentElement;
        }
        return best;
    }

    let container = null;
    if (btn) {
        container = findPostContainer(btn);
    }

    function scoreContainer(el) {
        const txt = norm(el.innerText || "");
        if (!txt || txt.length < 80) return -1;
        const hasAction = el.querySelector('button[aria-label="Comment"], button[aria-label*="Like"]');
        if (!hasAction) return -1;

        let score = 0;
        if (authorNorm && txt.includes(authorNorm)) score += 3;
        if (snippetHead && txt.includes(snippetHead)) score += 6;
        else if (snippetNorm && txt.includes(snippetNorm.slice(0, 40))) score += 4;

        if (profileNorm) {
            const profileLink = Array.from(el.querySelectorAll('a[href*="/in/"]'))
                .map((a) => norm((a.href || "").split("?")[0]).replace(/\\/$/, ""))
                .find((href) => href && (href === profileNorm || href.endsWith(profileNorm.split("/").pop() || "")));
            if (profileLink) score += 5;
        }
        return score;
    }

    if (!container) {
        const candidates = Array.from(document.querySelectorAll("main div"));
        let best = null;
        let bestScore = -1;
        for (const el of candidates) {
            const s = scoreContainer(el);
            if (s > bestScore) {
                bestScore = s;
                best = el;
            }
        }
        if (bestScore >= 4) container = best;
    }

    if (!container) return { ok: false, error: "Post container not found by author or snippet" };
    container.setAttribute('data-cursor-target', '1');

    if (action === "like") {
        const likeButton = container.querySelector('button[aria-label="Like"], button[aria-label*="Like "]');
        if (!likeButton) return { ok: false, error: "Like button not found" };
        const pressed = likeButton.getAttribute("aria-pressed") === "true";
        if (pressed) return { ok: true, status: "already_liked" };
        likeButton.click();
        container.removeAttribute('data-cursor-target');
        return { ok: true, status: "liked" };
    }

    if (action === "comment") {
        const commentBtn = container.querySelector('button[aria-label="Comment"]');
        if (!commentBtn) return { ok: false, error: "Comment button not found" };
        commentBtn.click();
        return { ok: true, status: "comment_opened" };
    }

    return { ok: false, error: "Unsupported action" };
}
"""


class LinkedInCrawler:
    def __init__(
        self,
        headless: bool | None = None,
        browser_profile: str | None = None,
        session_path: str | None = None,
    ):
        self.settings = get_settings()
        self._headless = headless if headless is not None else self.settings.linkedin_headless
        self._browser_profile = browser_profile or self.settings.linkedin_browser_profile
        self._session_path = session_path or self.settings.linkedin_session_path
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()

    async def start(self):
        self._playwright = await async_playwright().start()
        profile_dir = Path(self._browser_profile)
        profile_dir.mkdir(parents=True, exist_ok=True)

        launch_kwargs = {
            "user_data_dir": str(profile_dir),
            "headless": self._headless,
            "viewport": {"width": 1280, "height": 900},
            "locale": "en-US",
            "args": STEALTH_ARGS,
            "ignore_default_args": ["--enable-automation"],
        }

        try:
            self._context = await self._playwright.chromium.launch_persistent_context(
                channel="chrome",
                **launch_kwargs,
            )
            logger.info("Launched Chrome with persistent profile at %s", profile_dir)
        except Exception:
            self._context = await self._playwright.chromium.launch_persistent_context(
                **launch_kwargs,
            )
            logger.info("Launched Chromium with persistent profile at %s", profile_dir)

        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        await self._page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

    async def stop(self):
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()

    async def ensure_logged_in(self) -> bool:
        try:
            return await login_to_linkedin(
                self._page,
                self._context,
                session_path=self._session_path,
                headless=self._headless,
            )
        except Exception as exc:
            msg = str(exc).lower()
            recoverable = "frame was detached" in msg or "net::err_aborted" in msg
            if not recoverable:
                raise
            logger.warning("Login check failed due to detached frame; recreating page and retrying once.")
            try:
                if self._page:
                    await self._page.close()
            except Exception:
                pass
            self._page = await self._context.new_page()
            await self._page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )
            return await login_to_linkedin(self._page, self._context)

    async def _prepare_feed_page(self):
        page = self._page
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)

        # Wait for main feed area
        try:
            await page.wait_for_selector("main", timeout=30000)
        except Exception:
            logger.warning("Main feed area did not load in time")

        await page.wait_for_timeout(3000)

        # Dismiss popups / modals
        for selector in [
            'button[aria-label="Dismiss"]',
            ".artdeco-modal__dismiss",
            'button:has-text("Not now")',
            'button:has-text("Skip")',
        ]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=1000):
                    await btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

        # Expand truncated posts
        await page.evaluate(
            """() => {
                document.querySelectorAll(
                    'button.feed-shared-inline-show-more-text, ' +
                    'button[aria-label*="see more"], ' +
                    'button[aria-label*="See more"]'
                ).forEach((btn) => { try { btn.click(); } catch(e) {} });
            }"""
        )
        await page.wait_for_timeout(1500)

        # Initial scroll to trigger lazy-loaded posts
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 600)")
            await page.wait_for_timeout(1200)

    async def fetch_feed_posts(self, max_posts: Optional[int] = None) -> list[PostSchema]:
        max_posts = max_posts or self.settings.linkedin_max_posts
        if not await self.ensure_logged_in():
            logger.error("Cannot fetch posts — not logged in")
            return []

        logger.info("Fetching up to %d posts from LinkedIn feed...", max_posts)
        await self._prepare_feed_page()

        posts: list[PostSchema] = []
        seen_ids: set[str] = set()
        scroll_attempts = 0
        max_scroll_attempts = 25
        last_card_count = 0

        while len(posts) < max_posts and scroll_attempts < max_scroll_attempts:
            result = await self._page.evaluate(FEED_EXTRACT_JS)
            raw_posts = result.get("posts", [])
            cards_found = result.get("cards_found", 0)

            if scroll_attempts == 0:
                logger.info(
                    "Feed scan: %d cards on page, %d with text (url: %s)",
                    cards_found, len(raw_posts), result.get("page_url", ""),
                )

            if cards_found > last_card_count:
                last_card_count = cards_found

            for raw in raw_posts:
                post = parse_post_element(raw)
                if post and post.id not in seen_ids:
                    post = enrich_post_metadata(post)
                    posts.append(post)
                    seen_ids.add(post.id)
                    if len(posts) >= max_posts:
                        break

            if len(posts) >= max_posts:
                break

            # Stop early if we've scrolled many times with no new cards
            if scroll_attempts > 8 and len(posts) == 0 and cards_found == 0:
                break

            await self._scroll_feed()
            scroll_attempts += 1
            await asyncio.sleep(self.settings.linkedin_scroll_pause)

        if len(posts) == 0:
            await _save_debug_screenshot(self._page, "feed_empty")
            debug_dir = ensure_dir(Path(self.settings.export_dir).parent / "debug")
            html_path = debug_dir / "feed_page.html"
            html_path.write_text(await self._page.content())
            logger.warning(
                "No posts extracted. Debug files saved to %s — "
                "LinkedIn may have changed its layout or the feed is empty.",
                debug_dir,
            )

        logger.info("Fetched %d posts", len(posts))
        return posts

    async def _scroll_feed(self):
        await self._page.evaluate(
            """() => {
                window.scrollBy(0, window.innerHeight * 0.85);
                document.querySelectorAll(
                    'button.feed-shared-inline-show-more-text, ' +
                    'button[aria-label*="see more"]'
                ).forEach((btn) => { try { btn.click(); } catch(e) {} });
            }"""
        )
        await self._page.wait_for_timeout(int(self.settings.linkedin_scroll_pause * 1000))

    async def debug_feed(self) -> dict:
        if not await self.ensure_logged_in():
            return {"error": "not logged in"}
        await self._prepare_feed_page()
        result = await self._page.evaluate(FEED_EXTRACT_JS)
        await _save_debug_screenshot(self._page, "feed_debug")
        return result

    async def engage_with_post(
        self,
        author_name: str,
        author_profile_url: str | None,
        content_snippet: str,
        action: str,
        comment_text: str | None = None,
        dry_run: bool = True,
    ) -> dict:
        if not await self.ensure_logged_in():
            return {"ok": False, "error": "Not logged in"}
        await self._prepare_feed_page()
        if dry_run:
            return {"ok": True, "status": "dry_run", "action": action}

        action = action.lower().strip()
        if action not in {"like", "comment"}:
            return {"ok": False, "error": f"Unsupported action '{action}'"}

        result = await self._page.evaluate(
            ENGAGE_WITH_POST_JS,
            {
                "authorName": author_name,
                "authorProfileUrl": author_profile_url or "",
                "contentSnippet": (content_snippet or "")[:120],
                "action": action,
                "commentText": comment_text or "",
            },
        )
        if not result.get("ok"):
            return result

        if action == "comment":
            try:
                target = self._page.locator('[data-cursor-target="1"]').first
                box = target.locator(
                    'div[role="textbox"][contenteditable="true"]:visible, div.ql-editor[contenteditable="true"]:visible'
                ).first
                if await box.count() == 0:
                    box = self._page.locator(
                        'div[role="textbox"][contenteditable="true"]:visible, div.ql-editor[contenteditable="true"]:visible'
                    ).first
                await box.wait_for(timeout=5000)
                await box.click()
                await box.fill("")
                await box.type(comment_text or "", delay=25)
                submit = target.locator(
                    'button.comments-comment-box__submit-button:not([disabled]), '
                    'button[aria-label="Post comment"]:not([disabled]), '
                    'button[aria-label*="Post"]:not([disabled])'
                ).first
                if await submit.count() == 0:
                    submit = self._page.locator(
                        'button.comments-comment-box__submit-button:not([disabled]), '
                        'button[aria-label="Post comment"]:not([disabled]), '
                        'button[aria-label*="Post"]:not([disabled])'
                    ).first
                await submit.wait_for(timeout=5000)
                await submit.click()
                await self._page.wait_for_timeout(1200)
                await self._page.evaluate(
                    "() => document.querySelectorAll('[data-cursor-target=\"1\"]').forEach((el) => el.removeAttribute('data-cursor-target'))"
                )
                return {"ok": True, "status": "commented"}
            except Exception as exc:
                await _save_debug_screenshot(self._page, "comment_failed")
                return {"ok": False, "error": f"Comment submit failed: {exc}"}
        return result


async def fetch_posts(
    max_posts: Optional[int] = None,
    browser_profile: str | None = None,
    session_path: str | None = None,
) -> list[PostSchema]:
    """Fetch feed in headless mode (no visible browser window)."""
    async with LinkedInCrawler(
        headless=True,
        browser_profile=browser_profile,
        session_path=session_path,
    ) as crawler:
        return await crawler.fetch_feed_posts(max_posts)


async def interactive_login() -> bool:
    async with LinkedInCrawler(headless=False) as crawler:
        return await crawler.ensure_logged_in()


async def run_manual_engagement(
    author_name: str,
    author_profile_url: str | None,
    content_snippet: str,
    action: str,
    comment_text: str | None = None,
    dry_run: bool = True,
) -> dict:
    # Manual actions are more reliable in visible mode on LinkedIn.
    async with LinkedInCrawler(headless=False) as crawler:
        return await crawler.engage_with_post(
            author_name=author_name,
            author_profile_url=author_profile_url,
            content_snippet=content_snippet,
            action=action,
            comment_text=comment_text,
            dry_run=dry_run,
        )
