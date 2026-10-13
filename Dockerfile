FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home creator && mkdir -p /tmp/likeboost && chown creator:creator /tmp/likeboost

COPY app.py manage.py integrations.py video_package.py local_ai.py hosted_ai.py database.py server.py ./
COPY static ./static

ENV DATABASE_PATH=/tmp/likeboost/likeboost.sqlite3 MEDIA_ROOT=/tmp/likeboost/private-media COOKIE_SECURE=true EPHEMERAL_STORAGE=true WORKER_CONCURRENCY=1

USER creator
EXPOSE 10000
CMD ["python", "server.py"]
