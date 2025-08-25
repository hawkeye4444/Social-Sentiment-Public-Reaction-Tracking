CREATE TABLE IF NOT EXISTS posts_raw
(
  post_id String,
  platform LowCardinality(String),
  author_id String,
  created_at DateTime,
  text String,
  meta_json JSON
) ENGINE = MergeTree
ORDER BY (platform, created_at);

CREATE TABLE IF NOT EXISTS posts_enriched
(
  post_id String,
  platform LowCardinality(String),
  created_at DateTime,
  lang LowCardinality(String),
  sentiment Float32,
  emotions_json JSON,
  toxicity Float32,
  sarcasm Float32,
  topic_id Int32,
  quality_score Float32
) ENGINE = MergeTree
ORDER BY (platform, created_at);

CREATE TABLE IF NOT EXISTS shifts
(
  shift_id UUID,
  ts DateTime,
  platform LowCardinality(String),
  scope String,
  metric String,
  score Float32,
  direction Int8,
  window_before UInt16,
  window_after UInt16,
  explanation String
) ENGINE = MergeTree
ORDER BY (platform, ts);
