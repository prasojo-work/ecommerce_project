"""The Django Ninja API instance.

Each bounded context (catalog, cart, orders, ...) contributes a router, added here as the
contexts are built. The generated OpenAPI schema is the shared contract with the frontend
(`ADR-0005`).
"""

from ninja import NinjaAPI

api = NinjaAPI(
    title="LYSHEIM API",
    version="0.1.0",
    description="Storefront API for LYSHEIM.",
    urls_namespace="lysheim-api",
)
