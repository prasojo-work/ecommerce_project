"""Keep cached catalog reads honest.

Registered from `CatalogConfig.ready()`. Every catalog write retires the current
cache generation, so an operator's edit is visible on the next request rather
than after the TTL. Stock decrements during checkout go through
`variant.save(update_fields=[...])` (`orders/services.py`), which fires
`post_save`, so they are covered too.
"""

from typing import Any

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from catalog.cache import invalidate_catalog_cache
from catalog.models import Category, Product, ProductImage, ProductVariant


@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=ProductVariant)
@receiver([post_save, post_delete], sender=ProductImage)
def _invalidate_catalog_cache(**kwargs: Any) -> None:
    invalidate_catalog_cache()
