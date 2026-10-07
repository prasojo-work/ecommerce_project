#!/usr/bin/env bash
#
# Lighthouse audit for the key routes — the mechanism behind the "Lighthouse ≥ 90
# on key pages" exit criterion and the `Validated by` column of `ARCHITECTURE.md`
# §9. Results land in $OUT as one JSON per route, then print as a summary.
#
# Needs a *production* build being served, because dev-mode numbers are not
# meaningful:
#
#   cd frontend && pnpm build && pnpm start      # terminal 1
#   bash scripts/lighthouse-audit.sh             # terminal 2
#
# Lighthouse needs a Chrome. Set CHROME_PATH, or this falls back to a
# Playwright-managed Chromium when one is installed (common on build agents).
#
# The routes below assume the seeded demo catalogue — the detail route needs a
# slug that exists.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-/tmp/nordvik-lighthouse}"
PORT="${PORT:-3000}"
CATEGORIES="${CATEGORIES:-performance,accessibility,best-practices,seo}"

if [[ -z "${CHROME_PATH:-}" ]]; then
  found="$(find "${HOME}/.cache/ms-playwright" -maxdepth 3 -type f -name chrome 2>/dev/null | head -1)"
  [[ -n "$found" ]] && export CHROME_PATH="$found"
fi

mkdir -p "$OUT"

for entry in "home:/" "products:/products" "detail:/products/sol-table-lamp"; do
  name="${entry%%:*}"
  path="${entry#*:}"
  echo "auditing ${path}"
  npx -y lighthouse "http://localhost:${PORT}${path}" \
    --only-categories="$CATEGORIES" \
    --chrome-flags="--headless --no-sandbox --disable-dev-shm-usage --disable-gpu" \
    --output=json --output-path="${OUT}/${name}.json" \
    --quiet
done

python3 - "$OUT" <<'PY'
import glob, json, sys

out = sys.argv[1]
cats = ("performance", "accessibility", "best-practices", "seo")
metrics = ("first-contentful-paint", "largest-contentful-paint",
           "total-blocking-time", "cumulative-layout-shift", "speed-index")

print(f"\n{'route':16}{'perf':>6}{'a11y':>6}{'bp':>6}{'seo':>6}   LCP      TBT     CLS")
for path in sorted(glob.glob(f"{out}/*.json")):
    data = json.load(open(path))
    scores = {k: (data["categories"].get(k) or {}).get("score") for k in cats}
    fmt = lambda v: round(v * 100) if v is not None else "-"  # noqa: E731
    audit = data["audits"]

    def metric(name):
        value = audit.get(name, {}).get("numericValue")
        if value is None:
            return "-"
        if name == "cumulative-layout-shift":
            return f"{value:.3f}"
        return f"{value / 1000:.2f}s"

    print(
        f"{path.split('/')[-1][:-5]:16}"
        f"{fmt(scores['performance']):>6}"
        f"{fmt(scores['accessibility']):>6}"
        f"{fmt(scores['best-practices']):>6}"
        f"{fmt(scores['seo']):>6}"
        f"  {metric('largest-contentful-paint'):>7}"
        f"  {metric('total-blocking-time'):>6}"
        f"  {metric('cumulative-layout-shift'):>5}"
    )
PY
