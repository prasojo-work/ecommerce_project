"""The Django Ninja API instance.

Each bounded context (catalog, cart, orders, ...) contributes a router, added here as the
contexts are built. The generated OpenAPI schema is the shared contract with the frontend
(`ADR-0005`).
"""

from ninja import NinjaAPI

from accounts.addresses_api import router as addresses_router
from accounts.api import router as accounts_router
from cart.api import router as cart_router
from catalog.api import router as catalog_router
from core.errors import install_error_handlers

api = NinjaAPI(
    title="LYSHEIM API",
    version="0.1.0",
    description="Storefront API for LYSHEIM.",
    urls_namespace="lysheim-api",
)

install_error_handlers(api)

# The catalog routes sit at the API root (`/api/v1/products`, `/api/v1/categories`) as `API.md`
# section 4 documents them, so this router adds no prefix of its own.
api.add_router("", catalog_router)

# `API.md` section 5 documents the cart at the root too (`/cart`), and every route on it requires a
# bearer token (`ADR-0017`).
api.add_router("", cart_router)

# `API.md` section 2 documents the auth routes under `/auth`.
api.add_router("auth", accounts_router)

# `API.md` section 8 documents the address book under `/addresses`.
api.add_router("addresses", addresses_router)
