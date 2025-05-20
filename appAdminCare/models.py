# appAdminCare/models.py – versión robusta para S3 y filesystem

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

import fitz  # PyMuPDF
from io import BytesIO

# ---------------------------------------------------------------------------
# Storage configurable (S3 o local)
# ---------------------------------------------------------------------------
if getattr(settings, "USE_S3", False):
    from storages.backends.s3boto3 import S3Boto3Storage

    class MediaStorage(S3Boto3Storage):
        location = "media"
        file_overwrite = False
else:
    class MediaStorage(FileSystemStorage):
        location = settings.MEDIA_ROOT
        base_url = settings.MEDIA_URL

# ---------------------------------------------------------------------------
# Utilidad común para generar miniatura PDF -> JPEG
# ---------------------------------------------------------------------------

def _generate_cover(instance, field_name: str, prefix: str):
    """Extrae la primera página del PDF y la guarda en el ImageField indicado.

    - Lee desde el propio FileField (funciona con S3 y local).
    - Guarda la imagen en JPG en el mismo storage.
    """
    file_field = getattr(instance, field_name)
    if not file_field or file_field.name is None:
        return  # no file aún

    name_lower = file_field.name.lower()
    if not name_lower.endswith(".pdf"):
        return  # solo PDFs

    # No sobrescribas si ya existe portada
    cover_field = instance.cover if hasattr(instance, "cover") else None
    if cover_field and cover_field.name:
        return

    try:
        # Leemos el PDF en memoria (vale para S3 o FS)
        file_field.open("rb")
        pdf_bytes = file_field.read()
        file_field.close()

        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = pdf_doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2× resolución
        img_bytes = pix.tobytes("jpeg")
        pdf_doc.close()

        filename = f"{instance.pk}_{prefix}_cover.jpg"
        cover_field.save(filename, ContentFile(img_bytes), save=False)
    except Exception:
        # Silenciosamente ignora (PDF corrupto, etc.)
        pass

# ---------------------------------------------------------------------------
# MODELOS
# ---------------------------------------------------------------------------

class Document(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(
        upload_to="documents/",
        verbose_name="Archivo",
        help_text="Sube el archivo",
        storage=MediaStorage(),
    )
    cover = models.ImageField(
        upload_to="documents_covers/",
        null=True,
        blank=True,
        verbose_name="Portada (auto)",
        storage=MediaStorage(),
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        initial = self.pk is None
        super().save(*args, **kwargs)

        # Genera portada sólo tras tener PK y archivo subido
        if initial and self.file:
            _generate_cover(self, "file", "doc")
            if self.cover and not kwargs.get("update_fields"):
                super().save(update_fields=["cover"])


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
        help_text="Escribe un breve resumen del documento",
    )
    file = models.FileField(
        upload_to="help_docs/",
        blank=True,
        null=True,
        verbose_name="Archivo PDF",
        help_text="Sube el archivo en PDF",
        storage=MediaStorage(),
    )
    cover = models.ImageField(
        upload_to="help_docs_covers/",
        null=True,
        blank=True,
        verbose_name="Portada (auto)",
        storage=MediaStorage(),
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="help_documents",
        blank=True,
        verbose_name="Etiquetas",
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        initial = self.pk is None
        super().save(*args, **kwargs)

        if initial and self.file:
            _generate_cover(self, "file", "help")
            if self.cover and not kwargs.get("update_fields"):
                super().save(update_fields=["cover"])
