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

        try:
            license_key = ProvisioningService.provision_license_bundle(
                brand=request.user,
                customer_email=email,
                product_ids=product_ids
            )

            return Response({
                "key": license_key.key_string,
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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
