from django.urls import path
from .views import LicenseProvisioningView


urlpatterns = [
    path("provision/", LicenseProvisioningView.as_view(),
         name="license-provisioning"),
]
