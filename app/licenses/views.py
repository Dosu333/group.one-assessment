from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProvisionLicenseSerializer
from .services.provisioning import ProvisioningService


class LicenseProvisioningView(APIView):
    def post(self, request):
        serializer = ProvisionLicenseSerializer(
                        data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['customer_email']
        product_ids = serializer.validated_data['product_ids']
        existing_key = serializer.validated_data.get('existing_key')
        expiration_days = serializer.validated_data.get('expiration_days', 365)

        try:
            license_key = ProvisioningService.provision_license_bundle(
                brand=request.user,
                customer_email=email,
                product_ids=product_ids,
                existing_key=existing_key,
                expiration_days=expiration_days
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
