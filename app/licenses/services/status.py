from licenses.models import LicenseKey, License
from core.logging_utils import get_logger
from django.db.models import Prefetch


class StatusService:
    @staticmethod
    def get_license_status(brand, key_string, context):
        """
        Retrieves the full status of a license key, including all product
        entitlements and their current seat usage.
        """
        log = get_logger(__name__, context)
        log.info("License status check", extra={"key": key_string})

        try:
            license_key = LicenseKey.objects.prefetch_related(
                Prefetch(
                    "licenses",
                    queryset=License.objects.select_related("product").prefetch_related(
                        "activations"
                    ),
                )
            ).get(brand=brand, key_string=key_string)
            log.info(
                "Status check successful",
                extra={"key": key_string, "action": "US4_STATUS"},
            )
            return license_key
        except LicenseKey.DoesNotExist:
            log.warning("Status check failed: Key not found", extra={"key": key_string})
            return None
