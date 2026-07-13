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
    from utils.helpers import is_headless_env
    profile, session = get_user_linkedin_paths(user_id)
    headless = is_headless_env()
    
    try:
        async with LinkedInCrawler(
            headless=headless,
            browser_profile=profile,
            session_path=session,
        ) as crawler:
            ok = await crawler.ensure_logged_in()
    except Exception as e:
        logger.error("Failed to execute LinkedIn crawler login: %s", e, exc_info=True)
        if headless:
            return False, (
                "Failed to run automated headless login. Please verify that the Playwright browser is installed "
                "on your server (e.g. running 'playwright install'), or configure your credentials."
            )
        else:
            return False, (
                f"Failed to open browser window: {str(e)}. If you are running this app on a remote server/Streamlit Cloud, "
                "the app must run in headless mode. Please configure LINKEDIN_EMAIL and LINKEDIN_PASSWORD in your environment/secrets."
            )
            
    if ok:
        set_linkedin_connected(user_id)
        return True, "LinkedIn connected successfully."
        
    if headless:
        return False, (
            "Automated headless login failed. Please verify that your credentials (LINKEDIN_EMAIL and LINKEDIN_PASSWORD) "
            "are set correctly in your environment variables or Streamlit secrets."
        )
    return False, "Please finish signing in to LinkedIn in the browser window, then try again."

