FROM python:3.12-slim

# git is needed for `git clone` of source repos in the worker.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Place the venv OUTSIDE /app: docker-compose.yml bind-mounts ./backend:/app
# for live-reload, which would otherwise shadow an in-/app .venv built here.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
RUN uv sync --no-install-project

COPY . .

RUN uv sync \
    && chmod +x scripts/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["scripts/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
