from linkedin.crawler import LinkedInCrawler
from services.auth_service import refresh_user, set_linkedin_connected
from database.crud import get_user_by_id
from database.db import get_db
from utils.user_paths import linkedin_profile_dir, linkedin_session_file


def get_user_linkedin_paths(user_id: int) -> tuple[str, str]:
    with get_db() as db:
        user = get_user_by_id(db, user_id)
        if user and user.linkedin_browser_profile and user.linkedin_session_path:
            return user.linkedin_browser_profile, user.linkedin_session_path
    profile = linkedin_profile_dir(user_id)
    profile.mkdir(parents=True, exist_ok=True)
    return str(profile), str(linkedin_session_file(user_id))


async def connect_user_linkedin(user_id: int) -> tuple[bool, str]:
    profile, session = get_user_linkedin_paths(user_id)
    async with LinkedInCrawler(
        headless=False,
        browser_profile=profile,
        session_path=session,
    ) as crawler:
        ok = await crawler.ensure_logged_in()
    if ok:
        set_linkedin_connected(user_id)
        return True, "LinkedIn connected successfully."
    return False, "LinkedIn login was not completed. Finish sign-in in the browser and try again."
