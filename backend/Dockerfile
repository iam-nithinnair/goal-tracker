FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv

# dependencies first so rebuilds are fast (keep requirements.txt in sync with pyproject.toml)
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# run as an unprivileged user
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000
# Render/Fly/etc. provide $PORT; default to 8000 locally
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
