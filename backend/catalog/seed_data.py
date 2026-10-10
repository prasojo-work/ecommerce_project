"""Curated catalogue definition for the seed.

Curated by hand from the reference image set in `some_source/` (`ADR-0012`). The source set
covers a whole house — appliances, cleaning tools, kitchenware — and this store sells furniture,
lighting, textiles, and decor, so 54 of the 100 keywords are deliberately not shipped and their
images are not vendored into `frontend/public/images/`.

**No `BY-ND` image ships.** That licence forbids derivatives, and a product grid cannot promise
never to crop or resize what it displays, so the three `BY-ND` keywords in the source set — bed
frame, bookshelf, and dining table — are excluded along with the rest. `ADR-0012` prefers `BY`,
`BY-SA`, and `PDM`; `CC0` sits alongside them. Every shipped image is therefore safe to crop and
resize.

This mapping is the single place curation is expressed. The seed command, the vendored image set,
and `M1.9`'s credits page all derive from it, so they cannot disagree.

Data only: this module imports nothing, so tooling can read it without Django.
"""

# Category name -> the manifest `keyword` of each product in it. Order is display order.
CATALOG: dict[str, tuple[str, ...]] = {
    "Living Room": (
        "armchair",
        "sofa",
        "coffee table",
        "side table",
        "rocking chair",
        "wooden bench",
    ),
    "Dining Room": (
        "dining chair",
        "bar stool",
    ),
    "Bedroom": (
        "mattress",
        "bedside table",
        "wardrobe",
        "chest of drawers",
    ),
    "Storage": (
        "shelving unit",
        "wall shelf",
        "storage box",
        "wicker basket",
        "laundry basket",
        "coat rack",
        "shoe rack",
    ),
    "Lighting": (
        "floor lamp",
        "table lamp",
        "pendant lamp",
        "ceiling lamp",
        "wall lamp",
        "lantern",
    ),
    "Textiles": (
        "rug",
        "carpet",
        "cushion",
        "cushion cover",
        "throw blanket",
        "blanket",
        "duvet",
        "pillow",
        "bed sheet",
        "bed linen",
        "curtain",
    ),
    "Decor": (
        "wall mirror",
        "bathroom mirror",
        "vase",
        "plant pot",
        "candle holder",
        "candle",
        "wall clock",
        "decorative bowl",
        "picture frame",
        "doormat",
    ),
}

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "Living Room": "Sofas, armchairs, and tables for the room you spend the evening in.",
    "Dining Room": "Tables and seating that hold up to long dinners.",
    "Bedroom": "Frames, mattresses, and storage for the quieter half of the house.",
    "Storage": "Open and closed storage that keeps a room calm.",
    "Lighting": "Warm, low-glare light for every hour of the day.",
    "Textiles": "Natural fibres, chosen to soften hard surfaces.",
    "Decor": "Mirrors, vessels, and small objects that finish a room.",
}

# Series names are invented; combined with a unique product type they give unique product names
# and slugs. Real designer and brand names are avoided on purpose (`ADR-0003`).
SERIES: tuple[str, ...] = (
    "Halden",
    "Voss",
    "Selje",
    "Tind",
    "Brisk",
    "Vidde",
    "Kolbe",
    "Ravn",
    "Skarv",
    "Ulva",
    "Gneis",
    "Heia",
)

# Product type -> material. Wood for case goods, metals and glass for lighting, fibres for
# textiles (`DATA-MODEL.md` section 2 `product.material`).
MATERIALS: dict[str, tuple[str, ...]] = {
    "Living Room": ("Oak", "Ash", "Walnut", "Birch", "Smoked Oak", "Rattan"),
    "Dining Room": ("Oak", "Ash", "Walnut", "Birch"),
    "Bedroom": ("Oak", "Ash", "Walnut", "Pine"),
    "Storage": ("Oak", "Ash", "Birch", "Blackened Steel"),
    "Lighting": ("Brass", "Blackened Steel", "Opal Glass", "Ceramic", "Rattan"),
    "Textiles": ("Linen", "Wool", "Cotton", "Boucle", "Velvet"),
    "Decor": ("Travertine", "Ceramic", "Smoked Glass", "Brass", "Stoneware"),
}

# Variant finishes. Each product gets one to three, so the cart and PDP have real choices.
FINISHES: tuple[str, ...] = ("Natural", "Sand", "Clay", "Graphite", "Charcoal", "Bone")

# Mid-range positioning (`STRATEGY.md`, "designed but affordable"), in integer cents.
# A product's `base_price_cents` is the cheapest of its variant prices, never a separate number.
PRICE_BANDS_CENTS: dict[str, tuple[int, int]] = {
    "Living Room": (45_000, 260_000),
    "Dining Room": (28_000, 190_000),
    "Bedroom": (35_000, 230_000),
    "Storage": (12_000, 95_000),
    "Lighting": (8_500, 52_000),
    "Textiles": (3_900, 32_000),
    "Decor": (2_400, 19_000),
}

# Width and depth in cm. `depth_cm` is None for wall-hung and flat goods, which exercises the
# nullable column from `DATA-MODEL.md` section 2.
DIMENSION_BANDS_CM: dict[str, tuple[tuple[int, int], tuple[int, int], tuple[int, int] | None]] = {
    "Living Room": ((50, 240), (40, 90), (40, 100)),
    "Dining Room": ((45, 220), (45, 105), (45, 100)),
    "Bedroom": ((40, 210), (40, 215), (40, 65)),
    "Storage": ((35, 200), (30, 210), (20, 50)),
    "Lighting": ((15, 60), (25, 180), None),
    "Textiles": ((40, 300), (1, 240), None),
    "Decor": ((10, 120), (10, 180), None),
}

# Product copy. `UX.md` section 9 asks for plain, warm, jargon-free writing, so descriptions come
# from these rather than from generated prose.
DESCRIPTION_TEMPLATES: tuple[str, ...] = (
    "{material} {keyword}, made to be lived with rather than looked at.",
    "A quiet {keyword} in {material}. Built for everyday use.",
    "{material} {keyword} with a low profile and an honest finish.",
    "Solid {material}, softened by a simple {keyword} form.",
    "A {keyword} in {material} that will take the daily knocks.",
)

# The seed must run in the deployed demo, so the data files ship with the application.
MANIFEST_PATH = "seed_data/manifest.csv"
IMAGE_URL_PREFIX = "/images"
