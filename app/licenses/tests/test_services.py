# core/tests/test_services.py
from django.test import TestCase
from django.utils import timezone
from licenses.models import Brand, Product
from licenses.services.activation import ActivationService
from licenses.services.provisioning import ProvisioningService
from rest_framework.exceptions import ValidationError


class LicenseServiceTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="RankMath", slug="rm", api_key="sk_test")
        self.product_a = Product.objects.create(
            brand=self.brand, name="Pro", slug="pro"
        )
        self.product_b = Product.objects.create(
            brand=self.brand, name="Content AI", slug="ai"
        )
        self.ctx = {"request_id": "unit-test-id", "brand_id": self.brand.id}

    def test_bundle_provisioning_integrity(self):
        """
        US1: Ensure one key correctly maps to multiple isolated product
        licenses.
        """
        key = ProvisioningService.provision_license_bundle(
            brand=self.brand,
            customer_email="user@example.com",
            product_ids=[self.product_a.id, self.product_b.id],
            context=self.ctx,
        )
        self.assertEqual(key.licenses.count(), 2)
        self.assertEqual(key.licenses.filter(status="valid").count(), 2)

    def test_seat_limit_concurrency_safety(self):
        """US3: Verify that seat limits are strictly enforced."""
        key = ProvisioningService.provision_license_bundle(
            brand=self.brand,
            customer_email="a@b.com",
            product_ids=[self.product_a.id],
            context=self.ctx,
        )
        lic = key.licenses.get(product=self.product_a)
        lic.seat_limit = 1
        lic.save()

        # Occupy first seat
        ActivationService.activate_instance(
            brand=self.brand,
            key_string=key.key_string,
            instance_id="site-1.com",
            product_id=self.product_a.id,
            context=self.ctx,
        )

        # Attempt second seat
        with self.assertRaises(ValidationError) as cm:
            ActivationService.activate_instance(
                brand=self.brand,
                key_string=key.key_string,
                instance_id="site-2.com",
                product_id=self.product_a.id,
                context=self.ctx,
            )
        self.assertIn("Seat limit reached", str(cm.exception))

    def test_expiration_logic(self):
        """US4: Expired licenses must block activation."""
        key = ProvisioningService.provision_license_bundle(
            brand=self.brand,
            customer_email="a@b.com",
            product_ids=[self.product_a.id],
            context=self.ctx,
        )
        lic = key.licenses.first()
        lic.expiration_date = timezone.now() - timezone.timedelta(days=1)
        lic.save()

        with self.assertRaises(ValidationError):
            ActivationService.activate_instance(
                brand=self.brand,
                key_string=key.key_string,
                instance_id="site-1.com",
                product_id=self.product_a.id,
                context=self.ctx,
            )
