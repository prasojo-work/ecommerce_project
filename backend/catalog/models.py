"""Catalog models.

Physical design follows `docs/03-architecture/DATA-MODEL.md` section 2. Money is always stored
as integer minor units (cents) in a single currency, and every table carries
`created_at` / `updated_at` via `TimeStampedModel`.
"""

from django.db import models

from core.models import TimeStampedModel


class Category(TimeStampedModel):
    """A browsable grouping of products, optionally nested under a parent."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    position = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = ("position", "name")
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Product(TimeStampedModel):
    """A sellable item.

    `base_price_cents` is the display price; the authoritative price for a purchase is the
    variant's, per `DATA-MODEL.md` section 2. `attributes` carries extra specs that do not
    warrant their own column (JSONB).
    """

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    material = models.CharField(max_length=120, blank=True)
    color = models.CharField(max_length=60, blank=True)
    width_cm = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    depth_cm = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    base_price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True, db_index=True)
    attributes = models.JSONField(default=dict, blank=True)

    class Meta(TimeStampedModel.Meta):
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class ProductVariant(TimeStampedModel):
    """A concrete SKU — what stock and purchase price actually attach to."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    price_cents = models.PositiveIntegerField()
    stock_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta(TimeStampedModel.Meta):
        ordering = ("product_id", "id")

    def __str__(self) -> str:
        return f"{self.product.name} ({self.name})"


class ImageCredit(TimeStampedModel):
    """Attribution for one source image (`ADR-0012`, `SCOPE.md` `US-6.1`).

    Populated from the `some_source/manifest.csv` columns `source_title`, `creator`,
    `license`, `source`, and `source_page`.
    """

    # The vendored manifest carries source titles up to 255 characters, so this is bounded above
    # that rather than at a guess. `full_clean()` in the seed tests guards the headroom.
    title = models.CharField(max_length=300)
    creator = models.CharField(max_length=200)
    license = models.CharField(max_length=32)
    source = models.CharField(max_length=64)
    source_page_url = models.URLField(max_length=500, unique=True)

    class Meta(TimeStampedModel.Meta):
        ordering = ("title",)

    def __str__(self) -> str:
        return f"{self.title} by {self.creator}"


class ProductImage(TimeStampedModel):
    """An image belonging to a product, optionally attributed via `credit`."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    path = models.CharField(max_length=300)
    alt = models.CharField(max_length=200, blank=True)
    position = models.PositiveIntegerField(default=0)
    credit = models.ForeignKey(
        ImageCredit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="product_images",
    )

    class Meta(TimeStampedModel.Meta):
        ordering = ("position", "id")
        constraints = (
            models.UniqueConstraint(
                fields=("product", "path"), name="unique_image_path_per_product"
            ),
        )

    def __str__(self) -> str:
        return self.alt or f"{self.product.name} image at position {self.position}"
