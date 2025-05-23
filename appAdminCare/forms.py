# app/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import (
    validate_password,
    password_validators_help_text_html,
)

from .models import FAQ, Document, HelpDocument, Tag


# ──────────────────────────────
# Formularios de contenido
# ──────────────────────────────
class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ["question", "answer"]
        labels = {"question": "Pregunta", "answer": "Respuesta"}
        help_texts = {"question": "", "answer": ""}


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "file"]
        labels = {"title": "Título", "file": "Archivo"}
        help_texts = {"title": "", "file": ""}


class HelpDocumentForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Etiquetas",
        error_messages={"required": "Selecciona al menos una etiqueta."},
    )

    class Meta:
        model = HelpDocument
        fields = ["title", "file", "tags"]
        labels = {"title": "Título", "file": "Archivo PDF"}
        help_texts = {"title": "", "file": ""}


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
        labels = {"name": "Nombre"}
        help_texts = {"name": ""}


# ──────────────────────────────
# Registro de usuario
# ──────────────────────────────
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        error_messages={"required": "El correo electrónico es obligatorio."},
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "Nombre de usuario",
            "email": "Correo electrónico",
            "password1": "Contraseña",
            "password2": "Confirmar contraseña",
        }
        help_texts = {"username": "", "email": ""}

    # --- Personalización ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplica la clase Bootstrap a todos los campos visibles
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        # Muestra los requisitos de contraseña (@AUTH_PASSWORD_VALIDATORS)
        self.fields["password1"].help_text = password_validators_help_text_html()

    # --- Validación ---
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        # Valida con los validadores configurados en settings.py
        validate_password(password1, self.instance)
        return password1

    # --- Guardado ---
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
