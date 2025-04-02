from django import forms
from django.contrib.auth.models import User
from .models import FAQ, Document, HelpDocument, Tag

class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer']
        labels = {
            'question': 'Pregunta',
            'answer': 'Respuesta',
        }
        help_texts = {
            'question': '',
            'answer': '',
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file']
        labels = {
            'title': 'Título',
            'file': 'Archivo',
        }
        help_texts = {
            'title': '',
            'file': '',
        }

class HelpDocumentForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Etiquetas"
    )
    class Meta:
        model = HelpDocument
        fields = ['title', 'summary', 'file', 'tags']
        labels = {
            'title': 'Título',
            'summary': 'Resumen',
            'file': 'Archivo PDF',
        }
        help_texts = {
            'title': '',
            'summary': '',
            'file': '',
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        labels = {
            'name': 'Nombre',
        }
        help_texts = {
            'name': '',
        }

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
        }
        help_texts = {
            'username': '',
            'email': '',
        }
