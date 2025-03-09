from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título")
    uploaded_at = models.DateTimeField(auto_now_add=True) #uploaded_at se generará automáticamente.
    file = models.FileField(upload_to='documents/') #file almacenará el archivo en la carpeta documents/ dentro de la carpeta configurada para MEDIA_ROOT

    def __str__(self):
        return self.title
