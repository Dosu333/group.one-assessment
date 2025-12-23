from django.urls import path
from .views import (
    LicenseProvisioningView,
    ActivationView,
    DeactivationView
)


urlpatterns = [
    path("provision/", LicenseProvisioningView.as_view(),
         name="license-provisioning"),
    path("activate/", ActivationView.as_view(), name="license-activation"),
    path("deactivate/", DeactivationView.as_view(),
         name="license-deactivation"),
]
