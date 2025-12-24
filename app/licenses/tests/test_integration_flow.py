# api/tests/test_integration_flow.py
from rest_framework.test import APITestCase
from rest_framework import status
from licenses.models import Brand, Product


class FullFlowIntegrationTest(APITestCase):
    def setUp(self):
        # Setup Brand and Product
        self.brand = Brand.objects.create(name="WP Rocket", slug="wpr",
                                          api_key="sk_rocket_123")
        self.product = Product.objects.create(brand=self.brand, name="Plugin",
                                              slug="plugin")

        # Endpoints
        self.provision_url = '/api/v1/licenses/provision/'
        self.activate_url = '/api/v1/licenses/activate/'
        self.status_url = lambda key: f'/api/v1/licenses/status/{key}/'

    def test_full_license_lifecycle_flow(self):
        """
        Integration: Full flow from Brand provisioning to User activation.
        """
        # BRAND PROVISIONS
        provision_payload = {
            "customer_email": "customer@site.com",
            "product_ids": [self.product.id]
        }
        brand_headers = {
            'HTTP_X_BRAND_API_KEY': 'sk_rocket_123',
            'HTTP_IDEMPOTENCY_KEY': 'tx-001'
        }

        resp_p = self.client.post(self.provision_url, provision_payload,
                                  **brand_headers)
        self.assertEqual(resp_p.status_code, status.HTTP_201_CREATED)
        license_key = resp_p.data['key']

        # USER CHECKS STATUS (Using Public Brand Slug)
        user_headers = {'HTTP_X_BRAND_SLUG': 'wpr'}
        resp_s = self.client.get(self.status_url(license_key), **user_headers)
        self.assertEqual(resp_s.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_s.data['entitlements'][0]['status'], 'valid')

        # USER ACTIVATES (Using Public Brand Slug)
        activate_payload = {
            "license_key": license_key,
            "instance_id": "my-wordpress-site.local",
            "product_id": self.product.id
        }
        resp_a = self.client.post(self.activate_url, activate_payload,
                                  **user_headers)
        self.assertEqual(resp_a.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_a.data['status'], 'activated')

        # VERIFY SECURITY: Brand A cannot see Brand B's data
        other_brand_headers = {'HTTP_X_BRAND_SLUG': 'other-slug'}
        resp_fail = self.client.get(self.status_url(license_key),
                                    **other_brand_headers)
        self.assertEqual(resp_fail.status_code, status.HTTP_403_FORBIDDEN)
