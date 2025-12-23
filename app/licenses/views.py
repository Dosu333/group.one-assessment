from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .serializers import (
    ProvisionLicenseSerializer,
    LicenseInstanceActionSerializer,
    LicenseStatusResponseSerializer
)
from .services.provisioning import ProvisioningService
from .services.activation import ActivationService
from .services.status import StatusService


class LicenseProvisioningView(APIView):
    def post(self, request):
        serializer = ProvisionLicenseSerializer(
                        data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        try:
            license_key = ProvisioningService.provision_license_bundle(
                brand=request.user,
                customer_email=data['customer_email'],
                product_ids=data['product_ids'],
                existing_key=data.get('existing_key'),
                expiration_days=data.get('expiration_days', 365)
            )

            return Response({
                "key": license_key.key_string,
                "customer_email": license_key.customer_email,
                "products": [
                    p.name
                    for p in license_key.licenses.select_related('product')
                ],
                "status": "active"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST)


class ActivationView(APIView):
    def post(self, request):
        serializer = LicenseInstanceActionSerializer(
                        data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        try:
            ActivationService.activate_instance(
                brand=request.user,
                key_string=data['license_key'],
                instance_id=data['instance_id']
            )
            return Response({"status": "activated"}, status=200)
        except ValidationError as e:
            return Response({"error": e.detail}, status=400)


class DeactivationView(APIView):
    def post(self, request):
        serializer = LicenseInstanceActionSerializer(
                        data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        try:
            ActivationService.deactivate_instance(
                brand=request.user,
                key_string=data['license_key'],
                instance_id=data['instance_id']
            )
            return Response({"status": "deactivated"}, status=200)
        except ValidationError as e:
            return Response({"error": e.detail}, status=400)


class LicenseStatusView(APIView):
    """
    End-user product or customer can check the status and entitlements.
    """
    def get(self, request, key_string):
        license_key_obj = StatusService.get_license_status(request.user,
                                                           key_string)

        if not license_key_obj:
            return Response(
                {"error": "License key not found for this brand."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LicenseStatusResponseSerializer(license_key_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
