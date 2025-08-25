# Social Sentiment & Public Reaction Tracking

This repository contains a minimal prototype for a “mood seismograph” – a system for tracking and visualising the public’s emotional response to news topics across social platforms.  It pulls posts from X (Twitter) and Reddit, scores each post with off‑the‑shelf language models for sentiment and emotions, aggregates these scores into hourly time‑series and detects narrative shifts.  A simple API exposes the aggregated metrics to a Next.js dashboard.

## Features

* **Ingest** – `services/ingest` periodically fetches recent posts from X and Reddit for a configurable set of keywords and writes them to a ClickHouse database.
* **NLP service** – `services/nlp` exposes a FastAPI endpoint that scores arbitrary text for sentiment, a six‑emotion palette and toxicity.  It uses publicly available Hugging Face models.
* **Analytics jobs** – `services/analytics` contains a script that enriches raw posts by calling the NLP service, computes hourly aggregates and detects change points in the sentiment trend.
* **API** – `services/api` is a lightweight FastAPI application that exposes aggregated series and detected shifts via JSON.
* **Dashboard** – `services/web` contains a minimal Next.js client that charts the mood timeline and lists detected narrative shifts.

## Running locally

1. Copy `.env.example` to `.env` and fill in your API credentials for X and Reddit.
2. Bring up the stack with Docker Compose:

```bash
docker compose up -d clickhouse nlp api
```

3. Populate the database by running the ingestion and analytics scripts periodically (for example via cron or a scheduler).

4. Start the Next.js dashboard:

```bash
cd services/web
npm install
npm run dev
```

Open http://localhost:3000 in your browser to view the dashboard.

## Disclaimer

This repository provides a proof‑of‑concept for research and educational purposes only.  It does not circumvent any platform terms of service and does not scrape data.  You should only ingest data you are authorised to access through official APIs or licensed sources.
