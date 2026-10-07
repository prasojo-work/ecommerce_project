from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "status", "amount", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("order__number", "provider_reference")
    readonly_fields = ("order", "provider", "amount", "provider_reference", "created_at")
