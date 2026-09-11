# NexusOps API / worker / scheduler share one image.
FROM python:3.13-slim

# psycopg/argon2/cryptography ship binary wheels; slim + uv keeps this lean.
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /srv/app

# Dependency layer: cached unless the lockfile changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini pyproject.toml ./
COPY alembic ./alembic
COPY app ./app
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && useradd --system --uid 10001 --home /srv/app nexusops \
    && chown -R nexusops:nexusops /srv/app

USER nexusops
ENV PATH="/srv/app/.venv/bin:${PATH}" \
    PYTHONPATH=/srv/app

EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
# Default CMD; compose overrides per service.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
