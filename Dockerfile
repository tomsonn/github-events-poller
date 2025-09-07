FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /github-events-poller

COPY uv.lock pyproject.toml ./
ENV UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev pkg-config \
    && uv sync --locked

ENV PYTHONPATH=/github-events-poller

COPY . .
