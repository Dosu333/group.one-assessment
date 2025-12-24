from django.db import transaction
from django.utils import timezone
from licenses.models import LICENSE_STATUS_CHOICES, License
from core.logging_utils import get_logger
from rest_framework.exceptions import ValidationError


class LicenseLifecycleService:
    @staticmethod
    def update_status(brand, license_id, new_status, context):
        """
        Suspend, Resume, or Cancel a license.
        """
        log = get_logger(__name__, context)
        log.info(
            "License status update attempt",
            extra={"license_id": license_id, "new_status": new_status}
        )
        try:
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
                        log.warning(
                            "Attempt to reactivate a cancelled license",
                            extra={"license_id": license_id}
                        )
                        raise ValidationError(
                            "Cancelled licenses must be renewed.")
                    if new_status == old_status:
                        log.info(
                            "License already in desired status. No update.",
                            extra={
                                "license_id": license_id,
                                "status": new_status
                            }
                        )
                        return license_inst

                    license_inst.status = new_status
                    license_inst.save()
                    log.info(
                        "License status updated successfully",
                        extra={
                            "license_id": license_id,
                            "old_status": old_status,
                            "new_status": new_status,
                            "action": "US7_STATUS_UPDATE"
                        }
                    )
                    return license_inst
                except License.DoesNotExist:
                    log.warning(
                        "License status update failed: License not found",
                        extra={"license_id": license_id}
                    )
                    raise ValidationError("License not found for this brand.")
        except Exception as e:
            log.error(
                "License status update error",
                extra={"error": str(e), "license_id": license_id}
            )
            raise

    @staticmethod
    def renew_license(brand, license_id, extension_days, context):
        """
        Renew (extend) a license.
        """
        log = get_logger(__name__, context)
        log.info(
            "License renewal attempt",
            extra={"license_id": license_id, "extension_days": extension_days}
        )
        try:
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

                    log.info(
                        "License renewed successfully",
                        extra={
                            "license_id": license_id,
                            "new_expiration_date": (
                                license_inst.expiration_date
                            ),
                            "action": "US6_RENEW"
                        }
                    )
                    return license_inst
                except License.DoesNotExist:
                    log.warning(
                        "License renewal failed: License not found",
                        extra={"license_id": license_id}
                    )
                    raise ValidationError("License not found.")
        except Exception as e:
            log.error(
                "License renewal error",
                extra={"error": str(e), "license_id": license_id}
            )
            raise
