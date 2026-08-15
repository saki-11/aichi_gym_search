FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY webapp.py .
COPY search.py .
COPY static ./static

CMD exec uvicorn webapp:app --host 0.0.0.0 --port ${PORT:-8080}
