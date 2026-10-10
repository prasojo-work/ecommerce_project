"""The Django Ninja API instance.

Each bounded context (catalog, cart, orders, ...) contributes a router, added here as the
contexts are built. The generated OpenAPI schema is the shared contract with the frontend
(`ADR-0005`).
"""

from ninja import NinjaAPI

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
