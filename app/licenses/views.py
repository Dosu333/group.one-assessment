from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .serializers import (
    ProvisionLicenseSerializer,
    LicenseInstanceActionSerializer,
    LicenseStatusResponseSerializer,
    GlobalLicenseKeySerializer,
    ProductSerializer
)
from .authentication import (
    BrandApiKeyAuthentication,
    ProductPublicAuthentication,
)
from .models import Product
from .permissions import IsAuthenticatedBrandSystem
from .services.provisioning import ProvisioningService
from .services.activation import ActivationService
from .services.status import StatusService
from .services.lookups import GlobalLookupService
from .services.lifecycle import LicenseLifecycleService
from .decorators import idempotent_request


class ProductViewSet(ModelViewSet):
    """
    Provides a list of available products for the authenticated brand.
    Required for the Brand System to know which IDs to use in US1.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    authentication_classes = [BrandApiKeyAuthentication]
    permission_classes = [IsAuthenticatedBrandSystem]
    http_method_names = ['get']


class LicenseProvisioningView(APIView):
    authentication_classes = [BrandApiKeyAuthentication]
    permission_classes = [IsAuthenticatedBrandSystem]

    @idempotent_request()
    def post(self, request):
        serializer = ProvisionLicenseSerializer(
                        data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        ctx = {
            'request_id': getattr(request, 'request_id', 'N/A'),
            'brand_id': request.user.id,
            'brand_name': request.user.name,
            'ip_address': request.META.get('REMOTE_ADDR')
        }
        data = serializer.validated_data

        try:
            license_key = ProvisioningService.provision_license_bundle(
                brand=request.user,
                customer_email=data['customer_email'],
                product_ids=data['product_ids'],
                existing_key=data.get('existing_key'),
                expiration_days=data.get('expiration_days', 365),
                context=ctx
            )

            return Response({
                "key": license_key.key_string,
                "customer_email": license_key.customer_email,
                "products": [
                    {
                        "id": str(li.product.id),
                        "name": li.product.name,
                    }
                    for li in license_key.licenses.select_related('product')
                ],
                "status": "active"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST)


class ActivationView(APIView):
    authentication_classes = [ProductPublicAuthentication]

    def post(self, request):
        serializer = LicenseInstanceActionSerializer(
                        data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        ctx = {
            'request_id': getattr(request, 'request_id', 'N/A'),
            'brand_id': request.user.id,
            'brand_name': request.user.name
        }

        try:
            ActivationService.activate_instance(
                brand=request.user,
                key_string=data['license_key'],
                instance_id=data['instance_id'],
                context=ctx
            )
            return Response({"status": "activated"})
        except ValidationError as e:
            return Response({"error": e.detail},
                            status=status.HTTP_400_BAD_REQUEST)


class DeactivationView(APIView):
    authentication_classes = [ProductPublicAuthentication]

    def post(self, request):
        serializer = LicenseInstanceActionSerializer(
                        data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        ctx = {
            'request_id': getattr(request, 'request_id', 'N/A'),
            'brand_id': request.user.id,
            'brand_name': request.user.name
        }

        try:
            ActivationService.deactivate_instance(
                brand=request.user,
                key_string=data['license_key'],
                instance_id=data['instance_id'],
                context=ctx
            )
            return Response({"status": "deactivated"})
        except ValidationError as e:
            return Response({"error": e.detail},
                            status=status.HTTP_400_BAD_REQUEST)


class LicenseStatusView(APIView):
    """
    End-user product or customer can check the status and entitlements.
    """
    authentication_classes = [ProductPublicAuthentication]

    def get(self, request, key_string):
        ctx = {
            'request_id': getattr(request, 'request_id', 'N/A'),
            'brand_id': request.user.id,
            'brand_name': request.user.name
        }
        license_key_obj = StatusService.get_license_status(
            brand=request.user,
            key_string=key_string,
            context=ctx
        )

        if not license_key_obj:
            return Response(
                {"error": "License key not found for this brand."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LicenseStatusResponseSerializer(license_key_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GlobalCustomerLookupView(APIView):
    """
    Brands can list licenses by customer email across all brands.
    """
    authentication_classes = [BrandApiKeyAuthentication]
    permission_classes = [IsAuthenticatedBrandSystem]

    def get(self, request):
        email = request.query_params.get('email')
        ctx = {
            'request_id': getattr(request, 'request_id', 'N/A'),
            'brand_id': request.user.id,
            'brand_name': request.user.name
        }
        if not email:
            return Response({"error": "Email parameter is required."},
                            status=400)

        results = GlobalLookupService.get_all_licenses_by_email(email, ctx)

        serializer = GlobalLicenseKeySerializer(results, many=True)
        return Response({
            "customer_email": email,
            "total_keys_found": results.count(),
            "licenses": serializer.data
        })


class LicenseLifecycleView(APIView):
    authentication_classes = [BrandApiKeyAuthentication]
    permission_classes = [IsAuthenticatedBrandSystem]

    @idempotent_request()
    def patch(self, request, pk):
        """
        Handles Renew, Suspend, Resume, Cancel.
        """
        action_type = request.data.get('action')  # 'renew', 'update_status'

        try:
            if action_type == 'renew':
                days = int(request.data.get('days', 365))
                license_inst = LicenseLifecycleService.renew_license(
                    request.user, pk, days
                )
            elif action_type == 'update_status':
                status_val = request.data.get('status')
                license_inst = LicenseLifecycleService.update_status(
                    request.user, pk, status_val
                )
            else:
                return Response({"error": "Invalid action."},
                                status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "id": license_inst.id,
                "status": license_inst.status,
                "expiration_date": license_inst.expiration_date
            })
        except ValidationError as e:
            return Response({"error": e.detail},
                            status=status.HTTP_400_BAD_REQUEST)
