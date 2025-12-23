from licenses.models import LicenseKey, License
from django.db.models import Prefetch


class StatusService:
    @staticmethod
    def get_license_status(brand, key_string):
        """
        Retrieves the full status of a license key, including all product
        entitlements and their current seat usage.
        """
        try:
            return LicenseKey.objects.prefetch_related(
                Prefetch(
                    'licenses',
                    queryset=License.objects.select_related('product')
                    .prefetch_related('activations')
                )
            ).get(brand=brand, key_string=key_string)
        except LicenseKey.DoesNotExist:
            return None
