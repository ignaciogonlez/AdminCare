"""
URL configuration for adminCare project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from appAdminCare import views as app_views

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # Logout con confirmación (subclase de LogoutView)
    path('logout/', app_views.LogoutConfirmView.as_view(), name='logout'),

    # Rutas de la aplicación principal
    path('', include('appAdminCare.urls')),

    # Autenticación de Django (login, password-reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
