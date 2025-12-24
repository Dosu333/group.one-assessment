from functools import wraps
from rest_framework.response import Response
from .models import IdempotencyRecord


def idempotent_request():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view_instance, request, *args, **kwargs):
            key = request.headers.get('Idempotency-Key')
            brand = request.user

            if not key:
                return view_func(view_instance, request, *args, **kwargs)

            # Check if key exists for this brand
            existing_record = IdempotencyRecord.objects.filter(
                brand=brand, idempotency_key=key
            ).first()

            if existing_record:
                # Return the cached response immediately
                return Response(
                    existing_record.response_data,
                    status=existing_record.status_code
                )

            # Execute the original view logic
            response = view_func(view_instance, request, *args, **kwargs)

            # Cache the result if it was successful
            if 200 <= response.status_code < 300:
                IdempotencyRecord.objects.create(
                    brand=brand,
                    idempotency_key=key,
                    response_data=response.data,
                    status_code=response.status_code
                )

            return response
        return _wrapped_view
    return decorator
