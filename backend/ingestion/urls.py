from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomAuthToken, CurrentUserView, IngestionJobViewSet,
    NormalizedActivityViewSet, AuditTrailViewSet
)

router = DefaultRouter()
router.register(r'jobs', IngestionJobViewSet, basename='job')
router.register(r'activities', NormalizedActivityViewSet, basename='activity')
router.register(r'audit-trail', AuditTrailViewSet, basename='audit-trail')

urlpatterns = [
    path('auth/login/', CustomAuthToken.as_view(), name='auth-login'),
    path('auth/me/', CurrentUserView.as_view(), name='auth-me'),
    path('', include(router.urls)),
]
