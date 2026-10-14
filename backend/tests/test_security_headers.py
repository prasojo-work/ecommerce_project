"""Response hardening: the `Content-Security-Policy` and the request id's exposure (`M6.3`).

`SECURITY-BASELINE.md` section 6 lists the headers this service answers with, and the CSP is the only
one that needed code rather than a setting: that baseline calls it a "Django 6 built-in", it is not,
and Django ships no CSP support at all. `core.middleware` supplies the header and `base.py` holds the
two policies, so what is asserted here is the pair and the boundary between them — strict for the API,
relaxed for Django's own console, and the relaxation as narrow as it can be.

The transport headers (`Strict-Transport-Security`, `nosniff`, the referrer policy, the secure
cookies) are deliberately *not* asserted from here. They are set in `prod.py`, and this suite runs
under the development settings, where they are off on purpose — a local request over plain HTTP that
redirected itself to a TLS port nothing is listening on would be a worse development environment, not
a safer one. Asserting them here would assert the development environment's lack of them, which is the
opposite of the thing worth proving. They were verified against the deployed URL at `M2.7` and are on
the checklist in `docs/06-quality/SECURITY-REVIEW.md`.

What a test client cannot do is enforce a policy. These tests pin the headers the browser will receive;
whether the console's pages actually work under theirs was checked by loading them in Chromium and
watching for CSP violations, and that is recorded in the review rather than here.
"""

import pytest
from django.conf import settings
from django.test import Client

ADMIN_LOGIN = "/admin/login/"


@pytest.fixture
def client() -> Client:
    return Client()


def test_the_api_answers_with_the_strict_policy(client: Client) -> None:
    response = client.get("/healthz")
    policy = response["Content-Security-Policy"]

    for directive in settings.CONTENT_SECURITY_POLICY.split("; "):
        assert directive in policy


def test_the_strict_policy_grants_nothing_beyond_this_host(client: Client) -> None:
    """The directive that decides whether an injected `script` runs, asserted by name.

    `script-src` is absent from the strict policy, which means it falls back to `default-src 'self'`:
    this host's own bundles and nothing else. Adding `'unsafe-inline'` or a third-party origin here
    would leave the other directives intact and fail nothing, so the absence is the assertion.
    """
    policy = client.get("/healthz")["Content-Security-Policy"]

    assert "script-src" not in policy
    assert "default-src 'self'" in policy


def test_the_console_gets_the_relaxed_policy(client: Client) -> None:
    response = client.get(ADMIN_LOGIN)

    assert response.status_code == 200
    assert response["Content-Security-Policy"] == settings.CONTENT_SECURITY_POLICY_ADMIN


def test_the_console_policy_adds_nothing_but_inline_script_and_style() -> None:
    """The concession is narrow on purpose, so the narrowness is the assertion.

    Checking only that `'unsafe-inline'` appears would pass just as happily if the console's policy had
    grown a wildcard origin or quietly lost `object-src` along the way. Subtracting the strict policy
    leaves exactly the two directives Django's own templates need — a third one appearing here is a
    widening of the exemption, and this is what makes that visible in review rather than in production.
    """
    strict = settings.CONTENT_SECURITY_POLICY.split("; ")
    added = [
        directive
        for directive in settings.CONTENT_SECURITY_POLICY_ADMIN.split("; ")
        if directive not in strict
    ]

    assert added == ["style-src 'self' 'unsafe-inline'", "script-src 'self' 'unsafe-inline'"]
