# models.py

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

import fitz  # PyMuPDF
from io import BytesIO

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
    cover = models.ImageField(
        upload_to='documents_covers/',
        null=True,
        blank=True,
        verbose_name="Portada",
        storage=MediaStorage()
    )

    def __str__(self):
        return self.title

    # Si ya tienes otro mecanismo que genera cover para Document,
    # puedes omitir este save(). Lo incluyo aquí por si quieres
    # auto-generar también para Document con PyMuPDF.
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file and self.file.name.lower().endswith('.pdf') and not self.cover:
            try:
                doc = fitz.open(self.file.path)
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("jpeg")
                doc.close()

                buf = BytesIO(img_data)
                filename = f"{self.pk}_doc_cover.jpg"
                self.cover.save(filename, ContentFile(buf.read()), save=False)
                buf.close()
                super().save(update_fields=['cover'])
            except Exception:
                pass


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
    cover = models.ImageField(
        upload_to='help_docs_covers/',
        null=True,
        blank=True,
        verbose_name="Portada",
        help_text="Miniatura generada a partir de la primera página del PDF",
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

    def save(self, *args, **kwargs):
        # Guardamos primero el HelpDocument para disponer de file.path
        super().save(*args, **kwargs)

        # Si es un PDF y aún no tiene portada, la generamos
        if self.file and self.file.name.lower().endswith('.pdf') and not self.cover:
            try:
                doc = fitz.open(self.file.path)
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("jpeg")
                doc.close()

                buf = BytesIO(img_data)
                filename = f"{self.pk}_help_cover.jpg"
                self.cover.save(filename, ContentFile(buf.read()), save=False)
                buf.close()
                super().save(update_fields=['cover'])
            except Exception:
                pass
