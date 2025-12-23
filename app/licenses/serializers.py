from rest_framework import serializers
from .models import Product, LicenseKey


class ProvisionLicenseSerializer(serializers.Serializer):
    customer_email = serializers.EmailField()
    product_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=1
    )
    existing_key = serializers.CharField(required=False)
    expiration_days = serializers.IntegerField(
        required=False, default=365, min_value=1
    )

    def validate_product_ids(self, value):
        brand = self.context['request'].user  # Authenticated brand
        products = Product.objects.filter(id__in=value, brand=brand)
        if products.count() != len(value):
            raise serializers.ValidationError(
                "One or more products are invalid for this brand.")
        return value


class LicenseInstanceActionSerializer(serializers.Serializer):
    """
    Base serializer for actions performed by end-user products.
    Covers site activation and deactivation.
    """
    license_key = serializers.CharField(
        required=True,
        help_text="The license key string provided to the end-user."
    )
    instance_id = serializers.CharField(
        required=True,
        max_length=255,
        help_text="The specific instance being managed."
    )

    def validate_license_key(self, value):
        """
        Ensure the key exists and belongs to the authenticated brand.
        This prevents 'ID Enumeration' where Brand A tries to guess Brand B's
        keys.
        """
        brand = self.context['request'].user
        if not LicenseKey.objects.filter(key_string=value,
                                         brand=brand).exists():
            raise serializers.ValidationError(
                                    "Invalid license key for this brand.")
        return value
