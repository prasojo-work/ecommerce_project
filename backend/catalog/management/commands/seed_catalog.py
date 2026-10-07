from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalog.models import Category, Product, ProductImage, ProductVariant

CATEGORIES: list[tuple[str, str]] = [
    ("Living room", "living-room"),
    ("Bedroom", "bedroom"),
    ("Dining & kitchen", "dining-kitchen"),
    ("Storage & small space", "storage-small-space"),
    ("Home accessories", "home-accessories"),
]

PRODUCTS: list[dict[str, Any]] = [
    {
        "category": "living-room",
        "title": "Nordvik 3-Seater Sofa",
        "base_price": 4_500_000,
        "description": (
            "A compact three-seater with a deep seat and removable, washable covers, "
            "sized for apartment living rooms without feeling cramped."
        ),
        "variants": [
            {
                "name": "Fog grey",
                "sku": "NORD-SOFA-FOG",
                "attributes": {"colour": "Fog grey"},
                "stock_qty": 8,
            },
            {
                "name": "Deep green",
                "sku": "NORD-SOFA-GREEN",
                "attributes": {"colour": "Deep green"},
                "stock_qty": 5,
            },
        ],
    },
    {
        "category": "living-room",
        "title": "Fjord Coffee Table",
        "base_price": 1_290_000,
        "description": "A low, rounded coffee table in solid wood with a small footprint and a generous surface.",
        "variants": [
            {
                "name": "Oak",
                "sku": "FJORD-CT-OAK",
                "attributes": {"finish": "Oak"},
                "stock_qty": 12,
            },
            {
                "name": "Walnut",
                "sku": "FJORD-CT-WAL",
                "attributes": {"finish": "Walnut"},
                "stock_qty": 6,
            },
        ],
    },
    {
        "category": "bedroom",
        "title": "Lund Bed Frame",
        "base_price": 3_200_000,
        "description": "A low-profile bed frame with a slatted base. Simple, sturdy, and easy to assemble.",
        "variants": [
            {
                "name": "Single 90 x 200 cm",
                "sku": "LUND-BED-90",
                "attributes": {"size": "90 x 200 cm"},
                "stock_qty": 6,
            },
            {
                "name": "Double 140 x 200 cm",
                "sku": "LUND-BED-140",
                "attributes": {"size": "140 x 200 cm"},
                "stock_qty": 4,
            },
        ],
    },
    {
        "category": "bedroom",
        "title": "Vik Nightstand",
        "base_price": 890_000,
        "description": "A slim nightstand with one drawer and an open shelf, designed to hug the bedside.",
        "variants": [
            {
                "name": "White",
                "sku": "VIK-NS-WHITE",
                "attributes": {"colour": "White"},
                "stock_qty": 15,
            },
            {
                "name": "Oak",
                "sku": "VIK-NS-OAK",
                "attributes": {"colour": "Oak"},
                "stock_qty": 10,
            },
        ],
    },
    {
        "category": "dining-kitchen",
        "title": "Skog Dining Table",
        "base_price": 2_890_000,
        "description": "A solid-wood dining table that seats four to six, built to be lived on every day.",
        "variants": [
            {
                "name": "120 cm",
                "sku": "SKOG-DT-120",
                "attributes": {"length": "120 cm"},
                "stock_qty": 5,
            },
            {
                "name": "160 cm",
                "sku": "SKOG-DT-160",
                "attributes": {"length": "160 cm"},
                "stock_qty": 3,
            },
        ],
    },
    {
        "category": "dining-kitchen",
        "title": "Skog Dining Chair (Set of 2)",
        "base_price": 1_490_000,
        "description": "A pair of stackable wooden dining chairs with a gently curved back.",
        "variants": [
            {
                "name": "Natural",
                "sku": "SKOG-DC-NAT",
                "attributes": {"finish": "Natural"},
                "stock_qty": 20,
            },
            {
                "name": "Black",
                "sku": "SKOG-DC-BLK",
                "attributes": {"finish": "Black"},
                "stock_qty": 14,
            },
        ],
    },
    {
        "category": "storage-small-space",
        "title": "Berg Storage Bench",
        "base_price": 1_190_000,
        "description": "A hall bench with hidden storage under the lid, doubling as extra seating.",
        "variants": [
            {
                "name": "Oak",
                "sku": "BERG-SB-OAK",
                "attributes": {"finish": "Oak"},
                "stock_qty": 9,
            },
        ],
    },
    {
        "category": "storage-small-space",
        "title": "Vik Bookshelf",
        "base_price": 990_000,
        "description": "A narrow bookshelf that fits tight walls and awkward corners.",
        "variants": [
            {
                "name": "4 shelves",
                "sku": "VIK-BS-4",
                "attributes": {"shelves": 4},
                "stock_qty": 10,
            },
            {
                "name": "5 shelves",
                "sku": "VIK-BS-5",
                "attributes": {"shelves": 5},
                "stock_qty": 7,
            },
        ],
    },
    {
        "category": "home-accessories",
        "title": "Hav Ceramic Vase",
        "base_price": 249_000,
        "description": "A matte-glazed ceramic vase with a soft, organic silhouette.",
        "variants": [
            {
                "name": "Small",
                "sku": "HAV-VASE-S",
                "attributes": {"size": "Small"},
                "stock_qty": 30,
            },
            {
                "name": "Medium",
                "sku": "HAV-VASE-M",
                "attributes": {"size": "Medium"},
                "stock_qty": 25,
            },
            {
                "name": "Large",
                "sku": "HAV-VASE-L",
                "attributes": {"size": "Large"},
                "stock_qty": 15,
            },
        ],
    },
    {
        "category": "home-accessories",
        "title": "Sol Table Lamp",
        "base_price": 449_000,
        "description": "A warm, dimmable table lamp that casts a soft pool of light for evenings.",
        "variants": [
            {
                "name": "Sand",
                "sku": "SOL-LAMP-SAND",
                "attributes": {"colour": "Sand"},
                "stock_qty": 18,
            },
            {
                "name": "Charcoal",
                "sku": "SOL-LAMP-CHAR",
                "attributes": {"colour": "Charcoal"},
                "stock_qty": 12,
            },
        ],
    },
]


def _image_urls(slug: str, count: int = 2) -> list[str]:
    return [
        f"https://picsum.photos/seed/{slug}-{i}/800/600" for i in range(1, count + 1)
    ]


class Command(BaseCommand):
    help = "Seed the catalog with sample categories, products, variants, and images."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing catalog data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        if options["flush"]:
            ProductImage.objects.all().delete()
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Flushed existing catalog data."))

        categories: dict[str, Any] = {}
        for name, slug in CATEGORIES:
            category, _ = Category.objects.get_or_create(
                slug=slug, defaults={"name": name}
            )
            categories[slug] = category

        product_count = 0
        new_variants = 0
        for spec in PRODUCTS:
            slug = slugify(spec["title"])
            product, _ = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "category": categories[spec["category"]],
                    "title": spec["title"],
                    "description": spec.get("description", ""),
                    "brand": spec.get("brand", "Nordvik"),
                    "status": Product.Status.ACTIVE,
                    "base_price": spec["base_price"],
                    "currency": "IDR",
                },
            )
            product_count += 1

            for variant in spec["variants"]:
                _, created = ProductVariant.objects.get_or_create(
                    sku=variant["sku"],
                    defaults={
                        "product": product,
                        "name": variant["name"],
                        "attributes": variant.get("attributes", {}),
                        "price": variant.get("price"),
                        "stock_qty": variant.get("stock_qty", 0),
                    },
                )
                new_variants += int(created)

            for position, url in enumerate(_image_urls(slug)):
                ProductImage.objects.get_or_create(
                    product=product,
                    url=url,
                    defaults={"alt": product.title, "position": position},
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(categories)} categories, {product_count} products, "
                f"{new_variants} new variants."
            )
        )
