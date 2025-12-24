from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LicenseProvisioningView,
    ActivationView,
    DeactivationView,
    LicenseStatusView,
    GlobalCustomerLookupView,
    LicenseLifecycleView,
    ProductViewSet
)

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')


urlpatterns = [
     path("", include(router.urls)),
     path("provision/", LicenseProvisioningView.as_view(),
          name="license-provisioning"),
     path("activate/", ActivationView.as_view(), name="license-activation"),
     path("deactivate/", DeactivationView.as_view(),
          name="license-deactivation"),
     path("status/", LicenseStatusView.as_view(), name="license-status"),
     path("global-customer-lookup/", GlobalCustomerLookupView.as_view(),
          name="global-customer-lookup"),
     path("lifecycle/<str:pk>/", LicenseLifecycleView.as_view(),
          name="license-lifecycle"),
]
