from ninja import NinjaAPI

api = NinjaAPI(title="NORDVIK API", version="0.1.0")


@api.get("/health", tags=["system"])
def health(request):
    return {"status": "ok"}
