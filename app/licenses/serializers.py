from rest_framework import serializers
from .models import Product, LicenseKey


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]


class ProvisionLicenseSerializer(serializers.Serializer):
    customer_email = serializers.EmailField()
    product_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    existing_key = serializers.CharField(required=False)
    expiration_days = serializers.IntegerField(required=False, default=365, min_value=1)

    def validate_product_ids(self, value):
        brand = self.context["request"].user  # Authenticated brand
        products = Product.objects.filter(id__in=value, brand=brand)
        if products.count() != len(value):
            raise serializers.ValidationError(
                "One or more products are invalid for this brand."
            )
        return value


class LicenseInstanceActionSerializer(serializers.Serializer):
    """
    Base serializer for actions performed by end-user products.
    Covers site activation and deactivation.
    """

    license_key = serializers.CharField(
        required=True, help_text="The license key string provided to the end-user."
    )
    instance_id = serializers.CharField(
        required=True, max_length=255, help_text="The specific instance being managed."
    )
    product_id = serializers.UUIDField(
        required=True, help_text="The product ID associated with the license."
    )

    def validate_license_key(self, value):
        """
        Ensure the key exists and belongs to the authenticated brand.
        This prevents 'ID Enumeration' where Brand A tries to guess Brand B's
        keys.
        """
        brand = self.context["request"].user
        if not LicenseKey.objects.filter(key_string=value, brand=brand).exists():
            raise serializers.ValidationError("Invalid license key for this brand.")
        return value


class EntitlementSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    product_id = serializers.UUIDField(source="product.id")
    product_name = serializers.CharField(source="product.name")
    product_slug = serializers.CharField(source="product.slug")
    status = serializers.CharField()
    expiration_date = serializers.DateTimeField()
    seat_limit = serializers.IntegerField()
    seats_used = serializers.SerializerMethodField()
    seats_remaining = serializers.SerializerMethodField()

    def get_seats_used(self, obj):
        return obj.activations.count()

    def get_seats_remaining(self, obj):
        seat_limit = 0 if not obj.seat_limit else obj.seat_limit
        return max(0, seat_limit - obj.activations.count())


class LicenseStatusResponseSerializer(serializers.Serializer):
    key = serializers.CharField(source="key_string")
    customer_email = serializers.EmailField()
    entitlements = EntitlementSerializer(source="licenses", many=True)


class GlobalLicenseKeySerializer(serializers.Serializer):
    brand_name = serializers.CharField(source="brand.name")
    key = serializers.CharField(source="key_string")
    customer_email = serializers.EmailField()
    created_at = serializers.DateTimeField()
    entitlements = EntitlementSerializer(source="licenses", many=True)


class LicenseLifecycleActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["renew", "update_status"])
    status = serializers.ChoiceField(
        choices=["valid", "suspended", "cancelled"], required=False
    )
    days = serializers.IntegerField(required=False, min_value=1)

    def validate(self, data):
        if data["action"] == "update_status" and not data.get("status"):
            raise serializers.ValidationError(
                "Status is required for update_status action."
            )
        if data["action"] == "renew" and not data.get("days"):
            data["days"] = 365  # Default extension
        return data
