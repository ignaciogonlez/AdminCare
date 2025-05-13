import os
from django.apps import AppConfig

class AppadmincareConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appAdminCare'

    def ready(self):
        # Creación automática de superusuario si no existe
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = 'adiminstradorAdminCare'
        email = ''  # Email en blanco
        password = 'fdaT77Hjd!'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
