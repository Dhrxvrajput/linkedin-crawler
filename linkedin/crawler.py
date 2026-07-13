import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure consistent Playwright browser cache location across headless/cloud user environments
if sys.platform != "darwin":
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/tmp/pw-browsers"

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
        const skip = /^(Like|Comment|Repost|Send|Follow|Suggested|Feed post|\\d+[hdwmo]\\s*•|Premium|Promoted|• 3rd\\+|• 2nd|• 1st)/i;
        const reactionLine = /\\b(loves|liked|reposted|celebrates)\\s+this\\b/i;
        lines = lines.filter((l) => !skip.test(l) && l !== author && !reactionLine.test(l));
        let content = lines.join('\\n').trim();
        content = content.replace(/\\s+\\d[\\d,]*\\s+\\d[\\d,]*(?:\\s+\\d[\\d,]*)?\\s*$/, '');
        content = content.replace(/\\s+\\d[\\d,]*\\s+comments?\\s*$/i, '');
        content = content.replace(/\\s*…\\s*more\\s*$/i, '');
        content = content.replace(/\\s*\\.\\.\\.\\s*more\\s*$/i, '');
        return content.trim();
    }

    function isGenericPostListingUrl(href) {
        if (!href) return true;
        const path = href.split('?')[0].replace(/\\/$/, '');
        if (/\\/posts\\/?$/.test(path)) return true;
        if (/\\/recent-activity\\/?$/.test(path)) return true;
        return false;
    }

    function scorePostUrl(href) {
        if (!href || isGenericPostListingUrl(href)) return -1;
        if (href.includes('/feed/update/')) return 100;
        if (href.includes('/posts/') && href.includes('_activity-')) return 90;
        if (href.includes('activity:')) return 85;
        if (href.includes('/pulse/')) return 80;
        if (href.includes('/posts/')) return 10;
        return 0;
    }

    function urnToFeedUrl(urn) {
        if (!urn || !urn.includes('activity:')) return null;
        return 'https://www.linkedin.com/feed/update/' + urn + '/';
    }

    function pickProfileUrl(container, author) {
        const links = Array.from(container.querySelectorAll('a[href*="/in/"]'));
        const authorLower = (author || '').toLowerCase().trim();
        
        // Priority 1: Exact or highly similar text match
        for (const link of links) {
            const text = (link.innerText || '').toLowerCase().trim();
            if (text === authorLower || text.includes(authorLower)) {
                return link.href.split('?')[0];
            }
        }
        
        // Priority 2: Check alt text on images inside links (avatars)
        for (const link of links) {
            const img = link.querySelector('img');
            if (img && (img.alt || '').toLowerCase().includes(authorLower)) {
                return link.href.split('?')[0];
            }
        }

        // Priority 3: Handle "Liked by X" scenarios
        // In these cards, the person who liked it is often the first link.
        if (links.length > 1 && container.innerText.toLowerCase().includes('liked')) {
             // Look for a link that is NOT the first one if the first one doesn't match name
             return links[1].href.split('?')[0];
        }

        return links.length ? links[0].href.split('?')[0] : null;
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
        const candidates = [];

        // Strategy 1: Extract URN from data attributes
        let el = container;
        for (let i = 0; i < 8 && el; i++) {
            for (const attr of ['data-urn', 'data-activity-urn', 'data-id', 'data-post-id']) {
                const urn = el.getAttribute(attr);
                if (urn && urn.includes('activity:')) {
                    const feedUrl = urnToFeedUrl(urn);
                    if (feedUrl) candidates.push({ url: feedUrl, score: 100 });
                }
            }
            el = el.parentElement;
        }

        // Strategy 2: Look for common post URL selectors
        const selectors = [
            'a[href*="/feed/update/"]',
            'a[href*="/posts/"][href*="_activity-"]',
            'a[href*="activity:"]',
            'a[href*="/pulse/"]',
            'span[data-test-id="timestamp"] a',
            'time a',
            'a[role="link"][href*="/posts/"]',
            'a[href*="/posts/"]',
        ];
        for (const sel of selectors) {
            for (const link of container.querySelectorAll(sel)) {
                const href = (link.href || '').split('?')[0];
                const score = scorePostUrl(href);
                if (score >= 0) candidates.push({ url: href, score });
            }
        }

        // Strategy 3: Try all links in the container
        for (const a of container.querySelectorAll('a[href*="linkedin.com"]')) {
            const href = (a.href || '').split('?')[0];
            const score = scorePostUrl(href);
            if (score >= 0) candidates.push({ url: href, score });
        }

        // Strategy 4: For promoted posts, try to find the learn more link or company page link
        for (const a of container.querySelectorAll('a')) {
            const href = (a.href || '').split('?')[0];
            const text = (a.textContent || '').trim().toLowerCase();
            // If it's a /company/ link, it's likely a promoted company post
            if (href.includes('/company/') && !href.includes('linkedin.com/'))  {
                const score = 5;
                candidates.push({ url: href, score });
            }
            // Look for "learn more" type links that might point to the post
            if ((text.includes('learn') || text.includes('see') || text.includes('view')) && href.includes('linkedin.com')) {
                const score = 30;
                candidates.push({ url: href, score });
            }
        }

        candidates.sort((a, b) => b.score - a.score);
        return candidates.length ? candidates[0].url : null;
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
            author_profile_url: pickProfileUrl(container, author),
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
    const snippetHead = snippetNorm.slice(0, 60);

    function hasEngagementButtons(el) {
        return el.querySelector('button[aria-label="Comment"], button[aria-label*="Like"], button[aria-label*="Reaction"]');
    }

    function scoreContainer(el) {
        const txt = norm(el.innerText || "");
        const htmlText = norm(el.innerHTML || "");
        
        if (!txt || txt.length < 40) return -1;
        if (!hasEngagementButtons(el)) return -1;

        let score = 0;
        
        // Author name match
        if (authorNorm && txt.includes(authorNorm)) score += 10;
        
        // Content snippet matching - be flexible
        if (snippetNorm) {
            if (txt.includes(snippetHead)) score += 20;  // exact match at start
            else if (txt.includes(snippetNorm.slice(0, 40))) score += 15;  // 40 char match
            else if (txt.includes(snippetNorm.slice(0, 20))) score += 8;   // 20 char match
        }
        
        // Profile URL matching
        if (profileNorm) {
            const profileLinks = Array.from(el.querySelectorAll('a[href*="/in/"]'));
            for (const link of profileLinks) {
                const href = norm((link.href || "").split("?")[0]).replace(/\\/$/, "");
                if (href && (href === profileNorm || href.includes(profileNorm.split("/").pop() || ""))) {
                    score += 12;
                    break;
                }
            }
        }
        
        return score;
    }

    let container = null;

    // Strategy 1: Find by menu button with author name
    const menuButtons = Array.from(
        document.querySelectorAll('button[aria-label^="Open control menu for post by"]')
    );
    
    for (const btn of menuButtons) {
        const btnLabel = norm(btn.getAttribute('aria-label') || '');
        if (authorNorm && btnLabel.includes(authorNorm)) {
            let el = btn.parentElement;
            for (let i = 0; i < 30 && el; i++) {
                if (hasEngagementButtons(el)) {
                    container = el;
                    break;
                }
                el = el.parentElement;
            }
            if (container) break;
        }
    }

    // Strategy 2: Brute force search with better scoring
    if (!container) {
        const candidates = Array.from(document.querySelectorAll("main article, main div[role='article'], main li div[role='article'], main div[class*='feed'] div[class*='post']"));
        let bestContainer = null;
        let bestScore = -1;
        
        for (const el of candidates) {
            const score = scoreContainer(el);
            if (score > bestScore) {
                bestScore = score;
                bestContainer = el;
            }
        }
        
        // Accept if we have any decent match
        if (bestScore >= 8) {
            container = bestContainer;
        }
    }

    // Strategy 3: More aggressive search - find any post containers
    if (!container) {
        const allPosts = Array.from(document.querySelectorAll("div[class*='artdeco-card'], [class*='feed-update'], [class*='post-container']"));
        for (const post of allPosts) {
            if (hasEngagementButtons(post) && post.offsetHeight > 0) {
                const score = scoreContainer(post);
                if (score >= 5 || (authorNorm && post.innerText.toLowerCase().includes(authorNorm))) {
                    container = post;
                    break;
                }
            }
        }
    }

    // Strategy 4: Last resort - find first visible post with comment button
    if (!container) {
        const allPosts = Array.from(document.querySelectorAll("button[aria-label='Comment']"));
        for (const btn of allPosts) {
            let el = btn.parentElement;
            for (let i = 0; i < 15 && el; i++) {
                if (el.offsetHeight > 100 && el.innerText.length > 40) {
                    container = el;
                    break;
                }
                el = el.parentElement;
            }
            if (container) break;
        }
    }

    if (!container) return { ok: false, error: "Post container not found - try scrolling to ensure post is visible" };
    container.setAttribute('data-cursor-target', '1');

    if (action === "like") {
        const likeBtn = container.querySelector('button[aria-label*="Like"], button[aria-label*="Reaction"]');
        if (!likeBtn) return { ok: false, error: "Like button not found in post" };
        const pressed = likeBtn.getAttribute("aria-pressed") === "true";
        if (pressed) return { ok: true, status: "already_liked" };
        likeBtn.click();
        container.removeAttribute('data-cursor-target');
        return { ok: true, status: "liked" };
    }

    if (action === "comment") {
        const commentBtn = container.querySelector('button[aria-label="Comment"]');
        if (!commentBtn) return { ok: false, error: "Comment button not found in post" };
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
        li_at: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ):
        self.settings = get_settings()
        from utils.helpers import is_headless_env
        self._headless = headless if headless is not None else self.settings.linkedin_headless
        if not self._headless and is_headless_env():
            logger.warning("No display server detected or running on Streamlit Cloud. Forcing headless=True.")
            self._headless = True
        self._browser_profile = browser_profile or self.settings.linkedin_browser_profile
        self._session_path = session_path or self.settings.linkedin_session_path
        self._li_at = li_at
        self._email = email
        self._password = password
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

        from utils.helpers import is_headless_env
        if self._headless or is_headless_env():
            self._context = await self._playwright.chromium.launch_persistent_context(
                **launch_kwargs,
            )
            logger.info("Launched headless Chromium persistent profile at %s", profile_dir)
        else:
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
        
        # High-speed optimizations: Block heavy resources (Images, Media, CSS)
        async def block_resources(route):
            if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                await route.abort()
            else:
                await route.continue_()

        await self._page.route("**/*", block_resources)

        await self._page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

    async def stop(self):
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()

    async def ensure_logged_in(self) -> bool:
        # Clear stale cookies on a fresh login/injection attempt to prevent ERR_TOO_MANY_REDIRECTS
        if self._li_at or (self._email and self._password):
            try:
                await self._context.clear_cookies()
                logger.info("Cleared stale cookies from context for fresh login attempt")
            except Exception as e:
                logger.warning("Could not clear cookies: %s", e)

        if self._li_at:
            try:
                await self._context.add_cookies([
                    {
                        "name": "li_at",
                        "value": self._li_at,
                        "domain": ".linkedin.com",
                        "path": "/",
                    }
                ])
                logger.info("Injected li_at cookie into browser context")
            except Exception as e:
                logger.error("Failed to inject li_at cookie: %s", e)
        try:
            return await login_to_linkedin(
                self._page,
                self._context,
                session_path=self._session_path,
                headless=self._headless,
                email=self._email,
                password=self._password,
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
        for _ in range(4):
            await page.evaluate("window.scrollBy(0, 1000)")
            await page.wait_for_timeout(800)

    async def fetch_feed_posts(self, max_posts: Optional[int] = None) -> list[PostSchema]:
        max_posts = max_posts or self.settings.linkedin_max_posts
        if not await self.ensure_logged_in():
            raise RuntimeError("LinkedIn login failed or session expired. Please reconnect your account.")

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

        # Scroll the page to make sure the post is visible
        await self._page.evaluate(
            """() => {
                // Scroll to center of page to load more posts
                const main = document.querySelector('main');
                if (main) {
                    main.scrollTop = main.scrollHeight / 2;
                } else {
                    window.scrollBy(0, window.innerHeight);
                }
            }"""
        )
        await self._page.wait_for_timeout(800)

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
                await self._page.wait_for_timeout(800)
                
                # Find the comment textbox with multiple selector strategies
                box = None
                box_selectors = [
                    'div[data-placeholder="Start a post"]',
                    'div[role="textbox"][contenteditable="true"]',
                    'div.ql-editor[contenteditable="true"]',
                    'div[data-cursor-target="1"] div[contenteditable="true"]',
                    '[data-cursor-target="1"] div[contenteditable="true"]',
                    'div[contenteditable="true"]',
                ]
                
                for selector in box_selectors:
                    box_candidate = self._page.locator(selector).first
                    if await box_candidate.count() > 0:
                        try:
                            await box_candidate.wait_for(state="visible", timeout=2000)
                            box = box_candidate
                            break
                        except:
                            continue
                
                if not box or await box.count() == 0:
                    return {"ok": False, "error": "Comment textbox not found"}
                
                # Click and focus the textbox
                await box.click()
                await self._page.wait_for_timeout(300)
                
                # Clear and type the comment
                await box.evaluate("el => el.textContent = ''")
                await box.type(comment_text or "", delay=15)
                await self._page.wait_for_timeout(400)
                
                # Find and click the submit button with multiple selector strategies
                submit = None
                submit_selectors = [
                    'button[aria-label="Post comment"]',
                    'button[aria-label="Publish comment"]',
                    'button.comments-comment-box__submit-button',
                    '[data-cursor-target="1"] button:has-text("Post")',
                    'button:has-text("Post")',
                    'div[data-cursor-target="1"] button[type="button"]:not([disabled])',
                ]
                
                for selector in submit_selectors:
                    submit_candidate = self._page.locator(selector).first
                    if await submit_candidate.count() > 0:
                        try:
                            await submit_candidate.wait_for(state="visible", timeout=2000)
                            submit = submit_candidate
                            break
                        except:
                            continue
                
                if not submit or await submit.count() == 0:
                    return {"ok": False, "error": "Submit button not found"}
                
                await submit.click()
                await self._page.wait_for_timeout(1500)
                
                # Clean up the marker
                try:
                    await self._page.evaluate(
                        "() => document.querySelectorAll('[data-cursor-target=\"1\"]').forEach((el) => el.removeAttribute('data-cursor-target'))"
                    )
                except:
                    pass
                
                return {"ok": True, "status": "commented"}
            except Exception as exc:
                await _save_debug_screenshot(self._page, "comment_failed")
                logger.error("Comment submit failed: %s", exc)
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
    # Manual actions are performed in headless mode by default now.
    async with LinkedInCrawler(headless=True) as crawler:
        return await crawler.engage_with_post(
            author_name=author_name,
            author_profile_url=author_profile_url,
            content_snippet=content_snippet,
            action=action,
            comment_text=comment_text,
            dry_run=dry_run,
        )
