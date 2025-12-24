import secrets
from django.db import transaction, IntegrityError
from django.utils import timezone
from licenses.models import LicenseKey, License, Product
from rest_framework.exceptions import ValidationError


class ProvisioningService:
    @staticmethod
    def provision_license_bundle(*, brand, customer_email, product_ids,
                                 expiration_days=365, existing_key=None):
        """
        Handles the atomic creation of a license key and its associated
        licenses.
        Includes validation of product ownership and expiration logic.
        """
        # Validate all products belong to this brand
        products = Product.objects.filter(brand=brand, id__in=product_ids)
        if products.count() != len(product_ids):
            raise ValidationError(
                "One or more product IDs are invalid for this brand.")

        with transaction.atomic():
            if existing_key:
                try:
                    license_key = LicenseKey.objects.select_for_update().get(
                        brand=brand,
                        key_string=existing_key,
                        customer_email=customer_email
                    )
                except LicenseKey.DoesNotExist:
                    raise ValidationError("License key not found.")
            else:
                license_key = ProvisioningService._create_unique_key(
                    brand=brand, customer_email=customer_email
                )

            # Identify existing valid licenses for these specific products
            existing_licenses = License.objects.filter(
                license_key__customer_email=customer_email,
                product__id__in=product_ids,
                status='valid'
            ).select_for_update()

            existing_product_ids = set(
                existing_licenses.values_list('product__id', flat=True)
            )

            # Create licenses only for new products
            new_product_ids = [
                p_id
                for p_id in product_ids if p_id not in existing_product_ids
            ]
            expiration_date = (
                timezone.now() + timezone.timedelta(days=expiration_days)
            )

            if new_product_ids:
                new_license_objs = [
                    License(
                        license_key=license_key,
                        product_id=p_id,
                        expiration_date=expiration_date,
                        status='valid'
                    ) for p_id in new_product_ids
                ]
                License.objects.bulk_create(new_license_objs)

        return license_key

    @staticmethod
    def _create_unique_key(*, brand, customer_email):
        """
        Creates a unique license key for the given brand and customer email.
        """
        for _ in range(3):
            try:
                return LicenseKey.objects.create(
                    brand=brand,
                    customer_email=customer_email,
                    key_string=f"G1-{secrets.token_hex(12).upper()}",
                )
            except IntegrityError:
                continue
        raise ValidationError("Unable to generate a unique license key.")
