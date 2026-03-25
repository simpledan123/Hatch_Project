FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY app /app/app

CMD ["sh", "-c", "uvicorn app.main:app --host ${BACKEND_HOST:-0.0.0.0} --port ${BACKEND_PORT:-8000}"]
