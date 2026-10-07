from django.contrib import admin

from catalog.models import Category, Product, ProductImage, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "position", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "status",
        "base_price",
        "currency",
        "updated_at",
    )
    list_filter = ("status", "category", "currency")
    search_fields = ("title", "brand")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductVariantInline, ProductImageInline]


admin.site.register(ProductVariant)
admin.site.register(ProductImage)
