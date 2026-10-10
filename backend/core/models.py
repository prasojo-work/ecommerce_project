"""Shared model behaviour."""

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base giving every table `created_at` / `updated_at`.

    See `docs/03-architecture/DATA-MODEL.md` section 2: every table carries both columns.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
