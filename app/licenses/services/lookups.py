from licenses.models import LicenseKey
from core.logging_utils import get_logger


class GlobalLookupService:
    @staticmethod
    def get_all_licenses_by_email(email, context):
        """
        Lists all licenses associated with a given email across all brands.
        """
        log = get_logger(__name__, context)
        log.info(
            "Cross-brand global lookup initiated",
            extra={"target_email": email}
        )
        try:
            # Fetch related brand and licenses with products
            results = LicenseKey.objects.filter(
                customer_email__iexact=email
            ).select_related('brand').prefetch_related('licenses__product')
            log.info("Global lookup completed", extra={
                "target_email": email,
                "results_count": results.count(),
                "action": "US6_GLOBAL_LOOKUP"
            })
            return results
        except Exception as e:
            log.error(
                "Global lookup failed",
                extra={"target_email": email, "error": str(e)}
            )
            return None
