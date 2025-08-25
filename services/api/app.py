from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Any, Dict
import os
from clickhouse_connect import get_client

app = FastAPI()

CH = get_client(
    host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD", ""),
)


class SeriesPoint(BaseModel):
    ts: str
    sentiment_mean: float
    volume: int


@app.get("/series/{platform}", response_model=List[SeriesPoint])
def get_series(platform: str):
    """
    Return hourly sentiment mean and volume for the specified platform.
    """
    df = CH.query_df(
        f"""
        SELECT toStartOfHour(created_at) AS ts,
               avg(sentiment) AS sentiment_mean,
               count() AS volume
        FROM posts_enriched
        WHERE platform = '{platform}'
        GROUP BY ts
        ORDER BY ts
    """
    )
    return [
        SeriesPoint(
            ts=str(row.ts),
            sentiment_mean=float(row.sentiment_mean or 0.0),
            volume=int(row.volume),
        )
        for _, row in df.iterrows()
    ]


@app.get("/shifts/{platform}")
def get_shifts(platform: str) -> List[Dict[str, Any]]:
    """
    Return detected shifts for the specified platform.
    """
    df = CH.query_df(
        f"""
        SELECT ts, metric, score, direction, explanation
        FROM shifts
        WHERE platform = '{platform}'
        ORDER BY ts
    """
    )
    return df.to_dict(orient="records")
