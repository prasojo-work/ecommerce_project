"""The operator console's catalog (`M5.1`, `ADR-0007`, `US-5.1`-`US-5.3`).

`ADR-0007` chose Django admin for v1 and asked for it to be "genuinely usable" rather than merely
present. That is what the classes below spend their lines on: a filter and a search box on every
table an operator touches, the variants and the images edited *on the product that owns them*
instead of a page away, and `US-5.3`'s low-stock indicator as a column with a filter beside it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from catalog.models import Category, ImageCredit, Product, ProductImage, ProductVariant

# `US-5.3` asks for "a low-stock indicator" and names no number. Five is what this console uses: low
# enough that a shop down to its last handful is flagged, high enough that ordinary stock is not. It
# is a display choice and not a domain rule — nothing server-side reads it, and `ProductVariant`'s
# own constraint is still "not below zero".
LOW_STOCK_THRESHOLD = 5


class LowStockFilter(admin.SimpleListFilter):
    """`US-5.3`'s indicator as something sorted *by*, not only read from a column."""

    title = "stock"
    parameter_name = "stock"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        return [("low", "Low stock"), ("out", "Out of stock")]

    def queryset(
        self, request: HttpRequest, queryset: QuerySet[ProductVariant]
    ) -> QuerySet[ProductVariant]:
        if self.value() == "low":
            return queryset.filter(stock_qty__lte=LOW_STOCK_THRESHOLD)
        if self.value() == "out":
            return queryset.filter(stock_qty=0)
        return queryset


class ProductVariantInline(admin.TabularInline):
    """`US-5.2`'s variants and `US-5.3`'s stock, edited where the product is."""

    model = ProductVariant
    extra = 0
    fields = ("sku", "name", "price_cents", "stock_qty", "is_active")
    show_change_link = True


class ProductImageInline(admin.TabularInline):
    """`US-5.2`'s images, with the credit `ADR-0012` attributes them to."""

    model = ProductImage
    extra = 0
    fields = ("path", "alt", "position", "credit")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """`US-5.1`. The slug is unique on the model, and `prepopulated_fields` fills it from the name."""

    list_display = ("name", "slug", "parent", "position")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields: ClassVar[dict[str, Sequence[str]]] = {"slug": ("name",)}
    ordering = ("position", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """`US-5.2`. Each price is shown in cents because that is how it is stored (`DATA-MODEL.md` §5);
    the variant is the authoritative price, which is why both appear."""

    list_display = ("name", "slug", "category", "base_price_cents", "currency", "is_active")
    list_filter = ("is_active", "currency", "category")
    search_fields = ("name", "slug", "material")
    prepopulated_fields: ClassVar[dict[str, Sequence[str]]] = {"slug": ("name",)}
    list_select_related = ("category",)
    inlines = (ProductVariantInline, ProductImageInline)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "description")}),
        ("Presentation", {"fields": ("material", "color", "is_active")}),
        ("Price", {"fields": ("base_price_cents", "currency")}),
        ("Dimensions", {"fields": ("width_cm", "height_cm", "depth_cm")}),
        ("Extra", {"fields": ("attributes",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """`US-5.3`. Stock is editable straight from the list, because "set stock levels" for a season's
    worth of SKUs is one page of edits, not one SKU at a time."""

    list_display = (
        "sku",
        "name",
        "product",
        "price_cents",
        "stock_qty",
        "stock_state",
        "is_active",
    )
    list_filter = ("is_active", LowStockFilter)
    search_fields = ("sku", "name", "product__name")
    list_select_related = ("product",)
    list_editable = ("stock_qty",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="stock", ordering="stock_qty")
    def stock_state(self, variant: ProductVariant) -> str:
        if variant.stock_qty == 0:
            return "Out of stock"
        if variant.stock_qty <= LOW_STOCK_THRESHOLD:
            return "Low"
        return "In stock"


@admin.register(ImageCredit)
class ImageCreditAdmin(admin.ModelAdmin):
    """`ADR-0012`'s attribution rows — what `US-6.1`'s credits page renders (`M6`).

    An image points at one or at none: `ProductImage.credit` is nullable, so this table is where an
    attribution is edited rather than a condition on adding an image.
    """

    list_display = ("title", "creator", "license", "source")
    list_filter = ("license", "source")
    search_fields = ("title", "creator", "source_page_url")
