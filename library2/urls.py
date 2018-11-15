from django.contrib import admin
from django.urls import include, path

urlpatterns = [

    path('', include('library_services.urls')),

    # Django Admin
    path('admin/', admin.site.urls),

    # User management
    path('users_accounts/', include('users_accounts.urls')),
    path('accounts/', include('allauth.urls')),
    
]