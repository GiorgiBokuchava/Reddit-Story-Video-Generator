import json
import os
import random
from praw.models import Submission
from .config import settings

def _load_used() -> tuple[list[dict], set[str]]:
    path = settings.used_posts_file
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)
        return [], set()
    with open(path, "r") as f:
        records = json.load(f)
    used_ids = {rec["id"] for rec in records if "id" in rec}
    return records, used_ids

def _save_used(records: list[dict]) -> None:
    with open(settings.used_posts_file, "w") as f:
        json.dump(records, f, indent=2)

def find_next_post(reddit) -> Submission:
    """
    Scan every hot post in each subreddit (up to Reddit's internal cap) 
    and return the first one that hasn't been used that meets the criteria.
    """
    subs = settings.subreddits
    if not subs:
        raise RuntimeError("No subreddits configured in SUBREDDITS")

    random.shuffle(subs)
    print(f"[+] Scanning subreddits: {', '.join(subs)} (allow_nsfw={settings.allow_nsfw})")

    records, used_ids = _load_used()

    for subreddit_name in subs:
        print(f"[~] Scanning r/{subreddit_name}…")
        sub = reddit.subreddit(subreddit_name)

        for post in sub.hot(limit=None):
            if post.id in used_ids:
                continue
            if post.num_comments < settings.min_comments:
                continue
            if len(post.selftext or "") < settings.min_post_length:
                continue
            if post.over_18 and not settings.allow_nsfw:
                continue

            # Found a valid one. record and return it
            record = {"id": post.id, "url": f"https://reddit.com{post.permalink}"}
            records.append(record)
            _save_used(records)

            print(f"[+] Selected r/{subreddit_name} • {post.id} (NSFW={post.over_18})")
            return post

    raise RuntimeError(f"No matching posts found in any of: {', '.join(subs)}")
