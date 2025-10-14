from django.urls import path
from .views import UserRegisterView, UserLoginView, UserDetailView

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("login/", UserLoginView.as_view(), name="user-login"),
    path("<int:user_id>/", UserDetailView.as_view(), name="user-detail"),
]
