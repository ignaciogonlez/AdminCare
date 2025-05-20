# appAdminCare/forms.py – versión sin campo “Resumen”

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
        fields = ['title', 'file', 'tags']
        labels = {
            'title': 'Título',
            'file': 'Archivo PDF',
        }
        help_texts = {
            'title': '',
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
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        error_messages={'required': 'El correo electrónico es obligatorio.'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña"
    )

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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
