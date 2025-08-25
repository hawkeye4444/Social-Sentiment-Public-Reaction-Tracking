import httpx
import numpy as np
import pandas as pd
import ruptures as rpt
from clickhouse_connect import get_client

# Configure ClickHouse client from environment
import os

CH = get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD", ""),
)


def fetch_unscored(limit: int = 200):
    """
    Return a DataFrame of raw posts that have not yet been enriched.
    """
    query = f"""
        SELECT pr.post_id, pr.platform, pr.created_at, pr.text
        FROM posts_raw pr
        LEFT JOIN posts_enriched pe ON pr.post_id = pe.post_id
        WHERE pe.post_id IS NULL
        ORDER BY pr.created_at ASC
        LIMIT {limit}
    """
    return CH.query_df(query)


def score_texts(df):
    """
    Call the NLP service for each row in the dataframe and insert results
    into posts_enriched.
    """
    rows = []
    if df.empty:
        return
    with httpx.Client(timeout=20.0) as client:
        for _, r in df.iterrows():
            resp = client.post(
                "http://nlp:8001/score", json={"text": r["text"]}
            )
            data = resp.json()
            rows.append(
                [
                    r.post_id,
                    r.platform,
                    r.created_at,
                    "en",
                    data["sentiment"],
                    data["emotions"],
                    data["toxicity"],
                    0.0,
                    -1,
                    1.0,
                ]
            )
    CH.insert(
        "posts_enriched",
        rows,
        column_names=[
            "post_id",
            "platform",
            "created_at",
            "lang",
            "sentiment",
            "emotions_json",
            "toxicity",
            "sarcasm",
            "topic_id",
            "quality_score",
        ],
    )


def detect_shifts(platform: str):
    """
    Compute hourly mean sentiment for the given platform and detect change points.
    Insert detected shifts into the shifts table.
    """
    df = CH.query_df(
        f"""
        SELECT toStartOfHour(created_at) AS ts,
               avg(sentiment) AS s
        FROM posts_enriched
        WHERE platform = '{platform}'
        GROUP BY ts
        ORDER BY ts
    """
    )
    if len(df) < 10:
        return
    series = df["s"].to_numpy().reshape(-1, 1)
    algo = rpt.Pelt(model="rbf").fit(series)
    # Set penalty to control sensitivity; adjust as needed.
    cps = algo.predict(pen=10.0)[:-1]
    prev_idx = 0
    for cp in cps:
        ts = df.iloc[cp - 1]["ts"]
        before_mean = float(df.iloc[prev_idx:cp]["s"].mean())
        after_mean = float(df.iloc[cp:]["s"].mean())
        score = abs(after_mean - before_mean)
        direction = 1 if after_mean > before_mean else -1
        CH.insert(
            "shifts",
            [
                [
                    os.urandom(16).hex(),
                    ts,
                    platform,
                    "global",
                    "sentiment_mean",
                    score,
                    direction,
                    6,
                    6,
                    f"mean {before_mean:.2f} -> {after_mean:.2f}",
                ]
            ],
            column_names=[
                "shift_id",
                "ts",
                "platform",
                "scope",
                "metric",
                "score",
                "direction",
                "window_before",
                "window_after",
                "explanation",
            ],
        )
        prev_idx = cp


def main():
    df = fetch_unscored()
    if not df.empty:
        score_texts(df)
    for platform in ["reddit", "x"]:
        detect_shifts(platform)


if __name__ == "__main__":
    main()
