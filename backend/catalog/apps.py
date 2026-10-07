from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "catalog"

    def ready(self) -> None:
        # Registers the receivers that retire cached reads on every catalog write.
        from catalog import signals  # noqa: F401
