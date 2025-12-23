from django.contrib import admin
from .models import LicenseKey, License, Brand, Product, Activation


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'api_key', 'created_at')
    readonly_fields = ('api_key', 'slug')
    search_fields = ('name',)


admin.site.register(Product)
admin.site.register(LicenseKey)
admin.site.register(License)
admin.site.register(Activation)
