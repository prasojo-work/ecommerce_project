"""The console loads its own stylesheets and scripts.

Found at `M7.3`, and late. Nothing served `/static/` in any environment: there was no `STATIC_ROOT`,
no WhiteNoise in `MIDDLEWARE`, and no `collectstatic` in the image, so every `/static/admin/...`
request was a `404` and Django's admin rendered as **unstyled HTML** — the console looked like
something half-built rather than like Django's admin. It survived a milestone that screenshotted the
console, because no test asserted the page could load its own assets and unstyled HTML still behaves:
the headings render, the tables have rows, the links work, and every behavioural assertion passes.

These are the assertions that were missing. They run against `config.settings.dev`, where WhiteNoise
serves from the static finders (`WHITENOISE_USE_FINDERS`), so they also stand in for "a checkout has a
working console without running `collectstatic` first".
"""

from django.test import Client


def test_the_stylesheet_the_console_depends_on_is_served(client: Client) -> None:
    """The one file whose absence is invisible to every behavioural test."""
    response = client.get("/static/admin/css/base.css")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/css")


def test_a_console_script_is_served(client: Client) -> None:
    """A second asset, so a fix that special-cased one path would not pass."""
    response = client.get("/static/admin/js/theme.js")

    assert response.status_code == 200
