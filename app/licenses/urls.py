from django.urls import path
from .views import (
    LicenseProvisioningView,
    ActivationView,
    DeactivationView,
    LicenseStatusView,
    GlobalCustomerLookupView
)


urlpatterns = [
    path("provision/", LicenseProvisioningView.as_view(),
         name="license-provisioning"),
    path("activate/", ActivationView.as_view(), name="license-activation"),
    path("deactivate/", DeactivationView.as_view(),
         name="license-deactivation"),
    path("status/", LicenseStatusView.as_view(), name="license-status"),
    path("global-customer-lookup/", GlobalCustomerLookupView.as_view(),
         name="global-customer-lookup"),
]
