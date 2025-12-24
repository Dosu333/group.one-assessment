from django.db import transaction
from django.utils import timezone
from licenses.models import LICENSE_STATUS_CHOICES, License
from rest_framework.exceptions import ValidationError


class LicenseLifecycleService:
    @staticmethod
    def update_status(brand, license_id, new_status):
        """
        Suspend, Resume, or Cancel a license.
        """
        valid_statuses = [choice[0] for choice in LICENSE_STATUS_CHOICES]
        if new_status not in valid_statuses:
            raise ValidationError(
                f"Invalid status. Must be one of: {valid_statuses}")

        with transaction.atomic():
            try:
                license_inst = License.objects.select_for_update().get(
                    id=license_id, license_key__brand=brand
                )

                old_status = license_inst.status

                if new_status == 'valid' and old_status == 'cancelled':
                    raise ValidationError(
                        "Cancelled licenses must be renewed.")
                if new_status == old_status:
                    return license_inst

                license_inst.status = new_status
                license_inst.save()
                return license_inst
            except License.DoesNotExist:
                raise ValidationError("License not found for this brand.")

    @staticmethod
    def renew_license(brand, license_id, extension_days):
        """
        Renew (extend) a license.
        """
        with transaction.atomic():
            try:
                license_inst = License.objects.select_for_update().get(
                    id=license_id, license_key__brand=brand
                )
                # Extend from the current expiration or 'now',
                # whichever is later
                current_expiry = license_inst.expiration_date
                base_date = max(current_expiry, timezone.now())

                license_inst.expiration_date = (
                    base_date + timezone.timedelta(days=extension_days))
                license_inst.status = 'valid'
                license_inst.save()
                return license_inst
            except License.DoesNotExist:
                raise ValidationError("License not found.")
