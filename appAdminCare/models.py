from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.storage import FileSystemStorage

# Definimos el storage según USE_S3
if getattr(settings, "USE_S3", False):
    from storages.backends.s3boto3 import S3Boto3Storage

    class MediaStorage(S3Boto3Storage):
        location = "media"
        file_overwrite = False
else:
    class MediaStorage(FileSystemStorage):
        # Usará MEDIA_ROOT y MEDIA_URL definidos en settings.py
        location = settings.MEDIA_ROOT
        base_url = settings.MEDIA_URL


class Document(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(
        upload_to='documents/',
        verbose_name="Archivo",
        help_text="Sube el archivo",
        storage=MediaStorage()
    )
    # Campo para almacenar la portada (thumbnail) de tu PDF.
    cover = models.ImageField(
        upload_to='documents_covers/',
        null=True,
        blank=True,
        verbose_name="Portada",
        storage=MediaStorage()
    )

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="Pregunta")
    answer = models.TextField(verbose_name="Respuesta")

    def __str__(self):
        return self.question


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")

    def __str__(self):
        return self.name


class HelpDocument(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título")
    summary = models.TextField(
        blank=True,
        null=True,
        verbose_name="Resumen",
        help_text="Escribe un breve resumen del documento"
    )
    file = models.FileField(
        upload_to='help_docs/',
        blank=True,
        null=True,
        verbose_name="Archivo PDF",
        help_text="Sube el archivo en PDF",
        storage=MediaStorage()
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='help_documents',
        blank=True,
        verbose_name="Etiquetas"
    )

    def __str__(self):
        return self.title
