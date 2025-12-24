from django.db import transaction
from django.utils import timezone
from licenses.models import License, Activation
from rest_framework.exceptions import ValidationError


class ActivationService:
    @staticmethod
    def activate_instance(brand, key_string, instance_id):
        """
        Activates a license for a specific instance while enforcing
        seat limits.
        Uses database row-level locking to prevent race conditions.
        """
        with transaction.atomic():
            # Fetch license with lock
            try:
                license_inst = License.objects.select_for_update().get(
                    license_key__brand=brand,
                    license_key__key_string=key_string,
                    status='valid'
                )
            except License.DoesNotExist:
                raise ValidationError("Valid license not found for this key.")

            # Check Expiration
            if license_inst.expiration_date < timezone.now():
                raise ValidationError("License has expired.")

            # Check if already activated for this instance
            if Activation.objects.filter(
                    license=license_inst, instance_identifier=instance_id
                    ).exists():
                return True

            # Enforce Seat Limits
            current_seats = license_inst.activations.count()
            if (license_inst.seat_limit and
                    current_seats >= license_inst.seat_limit):
                raise ValidationError(
                    f"Seat limit reached ({license_inst.seat_limit}).")

            # Register Activation
            Activation.objects.create(
                license=license_inst,
                instance_identifier=instance_id
            )
        return True

    @staticmethod
    def deactivate_instance(brand, key_string, instance_id):
        """
        Deactivates a specific instance to free up a seat
        """
        deleted_count, _ = Activation.objects.filter(
            license_license_key__brand=brand,
            license__license_key__key_string=key_string,
            instance_identifier=instance_id
        ).delete()

        if deleted_count == 0:
            raise ValidationError("Activation record not found.")
        return True
