from rest_framework import authentication, exceptions
from .models import Brand


class BrandApiKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key = request.META.get("HTTP_X_BRAND_API_KEY")
        if not api_key:
            return None

        try:
            brand = Brand.objects.get(api_key=api_key)
        except (Brand.DoesNotExist, ValueError):
            raise exceptions.AuthenticationFailed("Invalid Brand API Key.")
        return (brand, None)


class ProductPublicAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        brand_slug = request.headers.get("X-Brand-Slug")
        if not brand_slug:
            return None

        try:
            brand = Brand.objects.get(slug=brand_slug)
        except Brand.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid Brand identifier.")
        return (brand, None)
