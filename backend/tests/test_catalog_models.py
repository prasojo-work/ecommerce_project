from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from catalog.models import Category, ImageCredit, Product, ProductImage, ProductVariant

pytestmark = pytest.mark.django_db


@pytest.fixture
def category() -> Category:
    return Category.objects.create(name="Seating", slug="seating")


@pytest.fixture
def product(category: Category) -> Product:
    return Product.objects.create(
        category=category,
        name="Aalto Chair",
        slug="aalto-chair",
        base_price_cents=129900,
        material="Oak",
        width_cm=Decimal("60.0"),
    )


@pytest.fixture
def credit() -> ImageCredit:
    return ImageCredit.objects.create(
        title="Slipcovered Vintage Armchair",
        creator="DesignFolly.com",
        license="BY-SA-2.0",
        source="Openverse",
        source_page_url="https://www.flickr.com/photos/9243453@N02/3147627493",
    )


def test_str_methods_return_human_readable_labels(category: Category, product: Product) -> None:
    variant = ProductVariant.objects.create(
        product=product, sku="AAL-01", name="Oak", price_cents=129900
    )

    assert str(category) == "Seating"
    assert str(product) == "Aalto Chair"
    assert str(variant) == "Aalto Chair (Oak)"


def test_str_for_credit(credit: ImageCredit) -> None:
    assert str(credit) == "Slipcovered Vintage Armchair by DesignFolly.com"


def test_category_slug_is_unique(category: Category) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Category.objects.create(name="Duplicate", slug="seating")


def test_product_slug_is_unique(product: Product) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.create(
            category=product.category,
            name="Duplicate",
            slug="aalto-chair",
            base_price_cents=1,
        )


def test_variant_sku_is_unique(product: Product) -> None:
    ProductVariant.objects.create(product=product, sku="AAL-01", name="Oak", price_cents=1)

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductVariant.objects.create(product=product, sku="AAL-01", name="Walnut", price_cents=1)


def test_categories_nest_one_level(category: Category) -> None:
    child = Category.objects.create(name="Armchairs", slug="armchairs", parent=category)

    assert list(Category.objects.filter(parent=category)) == [child]


def test_deleting_a_category_with_products_is_protected(product: Product) -> None:
    with pytest.raises(ProtectedError):
        product.category.delete()


def test_deleting_a_product_cascades_to_variants_and_images(product: Product) -> None:
    ProductVariant.objects.create(product=product, sku="AAL-01", name="Oak", price_cents=1)
    ProductImage.objects.create(product=product, path="images/armchair.webp")

    product.delete()

    assert ProductVariant.objects.count() == 0
    assert ProductImage.objects.count() == 0


def test_deleting_a_credit_keeps_the_image(product: Product, credit: ImageCredit) -> None:
    image = ProductImage.objects.create(product=product, path="images/armchair.webp", credit=credit)

    credit.delete()
    image.refresh_from_db()

    assert image.credit is None


def test_images_order_by_position_then_id(product: Product) -> None:
    third = ProductImage.objects.create(product=product, path="c.webp", position=2)
    first = ProductImage.objects.create(product=product, path="a.webp", position=0)
    second = ProductImage.objects.create(product=product, path="b.webp", position=0)

    assert list(ProductImage.objects.filter(product=product)) == [first, second, third]


def test_negative_stock_fails_validation(product: Product) -> None:
    variant = ProductVariant(product=product, sku="AAL-01", name="Oak", price_cents=1, stock_qty=-1)

    with pytest.raises(ValidationError):
        variant.full_clean()


def test_negative_price_fails_validation(category: Category) -> None:
    product = Product(category=category, name="Free Chair", slug="free-chair", base_price_cents=-1)

    with pytest.raises(ValidationError):
        product.full_clean()


def test_product_and_variant_defaults(product: Product) -> None:
    variant = ProductVariant.objects.create(
        product=product, sku="AAL-02", name="Walnut", price_cents=139900
    )

    assert product.currency == "USD"
    assert product.attributes == {}
    assert variant.stock_qty == 0
    assert variant.is_active is True
