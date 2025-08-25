FROM python:3.11-slim

# Install the minimal dependencies required for the NLP service.
RUN pip install --no-cache-dir fastapi uvicorn transformers torch

WORKDIR /app
COPY app.py .

ENV HF_HOME=/root/.cache/huggingface

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]