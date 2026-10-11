#!/bin/sh
# Container start-up for the API: migrate, seed, then serve.
#
# This lives in the image rather than in a host's start-command field, and that is a deliberate
# correction. Render's "Docker Command" is a string the platform parses: it strips a leading
# `/bin/sh -c` and hands the remainder to its own shell, so a compound command wrapped in quotes
# collapses into a single word and the deploy dies as
# `python manage.py migrate --noinput && ... --port 10000: not found`. One token, no quoting, and the
# work written where it can be read, tested and linted. See `RUNBOOK.md` section 7.4.
#
# Render's pre-deploy command is limited to paid instance types, so these two steps have no separate
# stage to run in. Both are safe on every boot: `migrate` is a no-op when there is nothing to apply
# (0.74s, almost all of it interpreter start), and `seed` is idempotent by contract. **Never add
# `--reset`**: it clears the seeded rows first, so every cold start would wipe the catalogue.
set -e

python manage.py migrate --noinput
python manage.py seed

# The port is not ours to choose. Render assigns it through `$PORT` (10000 by default) and its health
# check waits on the result, so binding a hardcoded port is the difference between a deploy that goes
# live and one that never passes. 8000 is the Dockerfile's `EXPOSE` and the development default, so a
# plain `docker run` still works with nothing set.
#
# `exec` so the server replaces this shell and receives the platform's SIGTERM itself: without it a
# deploy waits out the shutdown delay for a shell that is not listening for anything.
exec uvicorn config.asgi:application --host 0.0.0.0 --port "${PORT:-8000}"
