# syntax=docker/dockerfile:1

# LYSHEIM API — Django 6 + Django Ninja behind Uvicorn.
# Built by compose.yml; see docs/04-delivery/RUNBOOK.md section 2.

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir uv==0.12.5

WORKDIR /app

# Dependencies first, so this layer stays cached until pyproject.toml or uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# `collectstatic` at build time, under production settings, so the manifest `CompressedManifestStaticFilesStorage`
# reads is inside the image. It has to be here rather than on the boot path: the console's stylesheets
# are immutable, so collecting them once per deploy buys nothing and slows every cold start — and
# Render's free plan runs a single instance whose boot is already doing migrations.
#
# The secret below is a build-time placeholder and signs nothing; it exists because `prod.py` refuses
# to import without one. Production's real key arrives as an environment variable at run time.
RUN DJANGO_ENV=prod DJANGO_SECRET_KEY=build-time-placeholder DJANGO_ALLOWED_HOSTS=example.invalid \
    python manage.py collectstatic --noinput

# The start-up work — migrate, seed, then serve — lives in a script rather than in a host's
# start-command field, which is where it was and where it broke (`RUNBOOK.md` section 7.4). The exec
# bit is set here rather than trusted from the host filesystem, because a build context can lose it.
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

CMD ["/app/docker-entrypoint.sh"]
