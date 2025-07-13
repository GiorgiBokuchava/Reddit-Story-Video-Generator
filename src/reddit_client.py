from praw import Reddit
from .config import settings

def init_reddit() -> Reddit:
    return Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )