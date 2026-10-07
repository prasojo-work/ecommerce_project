from ninja import NinjaAPI

from accounts.api import router as accounts_router
from catalog.api import router as catalog_router

api = NinjaAPI(title="NORDVIK API", version="0.1.0")
api.add_router("", catalog_router)
api.add_router("", accounts_router)


@api.get("/health", tags=["system"])
def health(request):
    return {"status": "ok"}
