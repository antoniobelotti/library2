from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.SignUpViewCustom.as_view(), name='signup'),
    path('password/change/', views.PasswordChangeViewCustom.as_view(), name='change_password'),
]