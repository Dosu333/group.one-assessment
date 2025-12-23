from licenses.models import LicenseKey


class GlobalLookupService:
    @staticmethod
    def get_all_licenses_by_email(email):
        """
        Lists all licenses associated with a given email across all brands.
        """
        # Fetch related brand and licenses with products
        return LicenseKey.objects.filter(
            customer_email__iexact=email
        ).select_related('brand').prefetch_related('licenses__product')
