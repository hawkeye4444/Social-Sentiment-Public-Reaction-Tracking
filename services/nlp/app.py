from fastapi import FastAPI
from pydantic import BaseModel
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TextClassificationPipeline,
)

app = FastAPI()

# Pre-trained model checkpoints for sentiment, emotion and toxicity.
SENTIMENT_CKPT = "cardiffnlp/twitter-roberta-base-sentiment-latest"
EMOTION_CKPT = "joeddav/distilbert-base-uncased-go-emotions-student"
TOXICITY_CKPT = "unitary/toxic-bert"

# Lazy-load models once at startup.
sentiment = TextClassificationPipeline(
    model=AutoModelForSequenceClassification.from_pretrained(SENTIMENT_CKPT),
    tokenizer=AutoTokenizer.from_pretrained(SENTIMENT_CKPT),
    return_all_scores=True,
)
emotions = TextClassificationPipeline(
    model=AutoModelForSequenceClassification.from_pretrained(EMOTION_CKPT),
    tokenizer=AutoTokenizer.from_pretrained(EMOTION_CKPT),
    top_k=None,
    function_to_apply="sigmoid",
)
toxicity = TextClassificationPipeline(
    model=AutoModelForSequenceClassification.from_pretrained(TOXICITY_CKPT),
    tokenizer=AutoTokenizer.from_pretrained(TOXICITY_CKPT),
    return_all_scores=True,
)


class TextInput(BaseModel):
    text: str


@app.post("/score")
def score(item: TextInput):
    """
    Score a block of text for sentiment, six basic emotions and toxicity.
    Sentiment is returned as a float in [-1,1], emotions are returned as
    a dictionary of labels to probabilities, and toxicity as a single float.
    """
    s_scores = sentiment(item.text)[0]
    label_to_val = {"negative": -1, "neutral": 0, "positive": 1}
    s_val = sum(label_to_val[x["label"]] * x["score"] for x in s_scores)

    e_scores = {x["label"]: float(x["score"]) for x in emotions(item.text)[0]}
    tox = max(x["score"] for x in toxicity(item.text)[0])
    return {"sentiment": s_val, "emotions": e_scores, "toxicity": float(tox)}
