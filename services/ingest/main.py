import os
import datetime as dt
import httpx
import praw
from clickhouse_connect import get_client

# Configure keywords to track.  You can modify this list as needed.
KEYWORDS = ["news", "election", "hurricane"]

PLATFORM_REDDIT = "reddit"
PLATFORM_X = "x"

# Initialise ClickHouse client using environment variables.
CH = get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD", ""),
)


def insert_raw(rows):
    """
    Insert a batch of raw posts into the posts_raw table.
    Rows should be a list of lists ordered as:
    [post_id, platform, author_id, created_at, text, meta_json]
    """
    if not rows:
        return
    CH.insert(
        "posts_raw",
        rows,
        column_names=[
            "post_id",
            "platform",
            "author_id",
            "created_at",
            "text",
            "meta_json",
        ],
    )


def ingest_reddit():
    """Fetch recent Reddit posts matching the configured keywords."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "SocialSentiment/0.1 by unknown")
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    rows = []
    for query in KEYWORDS:
        for submission in reddit.subreddit("all").search(query, sort="new", limit=200):
            created_at = dt.datetime.utcfromtimestamp(submission.created_utc)
            text = f"{submission.title or ''}\n{submission.selftext or ''}"
            meta = {
                "subreddit": submission.subreddit.display_name,
                "score": submission.score,
            }
            rows.append(
                [
                    submission.id,
                    PLATFORM_REDDIT,
                    str(submission.author or "unknown"),
                    created_at,
                    text,
                    meta,
                ]
            )
    insert_raw(rows)


def ingest_x():
    """Fetch recent tweets matching the configured keywords."""
    bearer_token = os.getenv("X_BEARER_TOKEN")
    if not bearer_token:
        return
    headers = {"Authorization": f"Bearer {bearer_token}"}
    rows = []
    with httpx.Client(timeout=30.0) as client:
        for query in KEYWORDS:
            params = {
                "query": f"{query} lang:en -is:retweet",
                "max_results": "50",
                "tweet.fields": "created_at,public_metrics,lang,author_id",
            }
            resp = client.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers=headers,
                params=params,
            )
            if resp.status_code != 200:
                continue
            for tweet in resp.json().get("data", []):
                created_at = dt.datetime.fromisoformat(
                    tweet["created_at"].replace("Z", "+00:00")
                )
                rows.append(
                    [
                        tweet["id"],
                        PLATFORM_X,
                        tweet.get("author_id", ""),
                        created_at,
                        tweet.get("text", ""),
                        {
                            "public_metrics": tweet.get("public_metrics", {}),
                            "lang": tweet.get("lang", ""),
                        },
                    ]
                )
    insert_raw(rows)


def main():
    ingest_reddit()
    ingest_x()


if __name__ == "__main__":
    main()
