from django.urls import path, include
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views


from rest_framework.routers import DefaultRouter

from .views import PaymentListView, RegisterUserView, CreateStripePaymentView

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path(
        "token/",
        extend_schema_view(
            post=extend_schema(tags=["Users"])
        )(TokenObtainPairView.as_view()),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        extend_schema_view(
            post=extend_schema(tags=["Users"])
        )(TokenRefreshView.as_view()),
        name="token_refresh",
    ),
    path("", include(router.urls)),
]

urlpatterns += [
    path("payments/", PaymentListView.as_view(), name="payments-list"),
    path('payments/create/', CreateStripePaymentView.as_view(), name='create-payment'),
]