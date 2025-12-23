from rest_framework import serializers
from .models import Product


class ProvisionLicenseSerializer(serializers.Serializer):
    customer_email = serializers.EmailField()
    product_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1
    )
    existing_key = serializers.CharField(required=False)

    def validate_product_ids(self, value):
        brand = self.context['request'].user  # Authenticated brand
        products = Product.objects.filter(id__in=value, brand=brand)
        if products.count() != len(value):
            raise serializers.ValidationError(
                "One or more products are invalid for this brand.")
        return value
