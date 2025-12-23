from django.contrib import admin
from .models import LicenseKey, License, Brand, Product, Activation


admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(LicenseKey)
admin.site.register(License)
admin.site.register(Activation)
