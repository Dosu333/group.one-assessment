from django.db import transaction
from django.utils import timezone
from licenses.models import License, Activation
from core.logging_utils import get_logger
from rest_framework.exceptions import ValidationError


class ActivationService:
    @staticmethod
    def activate_instance(brand, key_string, instance_id, product_id, context):
        """
        Activates a license for a specific instance while enforcing
        seat limits.
        Uses database row-level locking to prevent race conditions.
        """
        log = get_logger(__name__, context)
        log.info(
            "License activation attempt",
            extra={
                "key": key_string,
                "instance": instance_id,
                "product": product_id
            }
        )
        try:
            with transaction.atomic():
                # Fetch license with lock
                try:
                    license_inst = License.objects.select_for_update().get(
                        license_key__brand=brand,
                        license_key__key_string=key_string,
                        product__id=product_id,
                        status='valid'
                    )
                except License.DoesNotExist:
                    log.warning(
                        "Activation failed: Invalid or inactive key",
                        extra={"key": key_string, "product": product_id}
                    )
                    raise ValidationError(
                        "Valid license not found for this key and product.")

                # Check Expiration
                if license_inst.expiration_date < timezone.now():
                    log.warning(
                        "Activation failed: Expired",
                        extra={
                            "key": key_string,
                            "expiration_date": license_inst.expiration_date
                        }
                    )
                    raise ValidationError("License has expired.")

                # Check if already activated for this instance
                if Activation.objects.filter(
                        license=license_inst, instance_identifier=instance_id
                        ).exists():
                    log.info(
                        "Instance already active. Activation skipped.",
                        extra={"instance": instance_id}
                    )
                    return True

                # Enforce Seat Limits
                current_seats = license_inst.activations.count()
                if (license_inst.seat_limit and
                        current_seats >= license_inst.seat_limit):
                    log.warning(
                        "Activation failed: Seat limit reached",
                        extra={"limit": license_inst.seat_limit}
                    )
                    raise ValidationError(
                        f"Seat limit reached ({license_inst.seat_limit}).")

                # Register Activation
                Activation.objects.create(
                    license=license_inst,
                    instance_identifier=instance_id
                )
                log.info(
                    "Activation successful",
                    extra={"instance": instance_id, "action": "US3_ACTIVATE"}
                )
            return True
        except Exception as e:
            log.error(
                "Activation failed",
                extra={"error": str(e), "action": "US3_ACTIVATE_FAILURE"}
            )
            raise

    @staticmethod
    def deactivate_instance(brand, key_string, instance_id,
                            product_id, context):
        """
        Deactivates a specific instance to free up a seat
        """
        log = get_logger(__name__, context)
        log.info(
            "License deactivation attempt",
            extra={
                "key": key_string,
                "instance": instance_id,
                "product": product_id
            }
        )
        try:
            deleted_count, _ = Activation.objects.filter(
                license__license_key__brand=brand,
                license__license_key__key_string=key_string,
                license__product__id=product_id,
                instance_identifier=instance_id
            ).delete()

            if deleted_count == 0:
                log.warning(
                    "Deactivation failed: Instance not found",
                    extra={"instance": instance_id}
                )
                raise ValidationError("Activation record not found.")
            log.info(
                "Deactivation successful",
                extra={"instance": instance_id, "action": "US5_DEACTIVATE"}
            )
            return True
        except Exception as e:
            log.error(
                "Deactivation failed",
                extra={"error": str(e), "action": "US5_DEACTIVATE_FAILURE"}
            )
            raise
