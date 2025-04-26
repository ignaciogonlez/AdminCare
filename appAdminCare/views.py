from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.db.models import Q

from .models import Document, FAQ, HelpDocument, Tag
from .forms import (
    DocumentForm, FAQForm, HelpDocumentForm, TagForm, UserRegisterForm
)

# PyMuPDF para generar portadas de PDF
import fitz
from django.core.files.base import ContentFile
import os


# ---------------------------------------------------------------------
# Logout con confirmación usando la vista genérica de Django
# ---------------------------------------------------------------------
class LogoutConfirmView(LogoutView):
    """
    GET  → muestra la plantilla 'logout_confirm.html'.
    POST → realiza el logout y redirige a 'index', añadiendo un mensaje.
    """
    template_name = 'logout_confirm.html'
    next_page = 'index'

    # Sobrescribimos GET para mostrar la confirmación sin cerrar sesión todavía
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    # Añadimos mensaje de éxito tras el logout
    def post(self, request, *args, **kwargs):
        messages.success(request, "Has cerrado sesión correctamente.")
        return super().post(request, *args, **kwargs)


# ---------------------------------------------------------------------
# Vistas de la aplicación
# ---------------------------------------------------------------------
def index(request):
    """Página de Inicio: Explicación del proyecto y enlaces a las secciones."""
    return render(request, 'index.html')


def faqs(request):
    """Muestra únicamente la lista de FAQs, sin permitir modificaciones."""
    faqs_list = FAQ.objects.all()
    return render(request, 'faqs.html', {'faqs': faqs_list})


def generar_portada_pdf(document):
    """
    Si el archivo es PDF, guarda la primera página en 'document.cover'.
    """
    if not document.file.name.lower().endswith('.pdf'):
        return

    data = document.file.read()
    doc = fitz.Document(stream=data)

    if doc.page_count < 1:
        doc.close()
        return

    page = doc.load_page(0)
    pix = page.get_pixmap()
    doc.close()

    portada_bytes = pix.tobytes("png")
    cover_filename = (
        f"{os.path.splitext(os.path.basename(document.file.name))[0]}_cover.png"
    )
    document.cover.save(cover_filename, ContentFile(portada_bytes))
    document.save()


@login_required
def documentos(request):
    """
    Gestión de documentos del usuario.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            new_doc = form.save(commit=False)
            new_doc.user = request.user
            new_doc.save()

            generar_portada_pdf(new_doc)

            messages.success(request, "Documento subido correctamente.")
            return redirect('documentos')
    else:
        form = DocumentForm()

    query = request.GET.get('q')
    if query:
        documents = Document.objects.filter(
            Q(title__icontains=query), user=request.user
        ).order_by('-uploaded_at')
    else:
        documents = Document.objects.filter(
            user=request.user
        ).order_by('-uploaded_at')

    context = {
        'form': form,
        'documents': documents,
        'query': query,
    }
    return render(request, 'documentos.html', context)


@login_required
def eliminar_documento(request, doc_id):
    """Eliminar un documento si pertenece al usuario o si el usuario es staff."""
    doc = get_object_or_404(Document, id=doc_id)
    if doc.user == request.user or request.user.is_staff:
        doc.delete()
        messages.success(request, "Documento eliminado.")
    else:
        messages.error(request, "No tienes permiso para eliminar este documento.")
    return redirect('documentos')


# ---------------- Sección Ayudas ----------------
def ayudas(request):
    return render(request, 'ayudas.html')


def _docs_por_tag(nombre_tag):
    try:
        tag = Tag.objects.get(name__iexact=nombre_tag)
        return HelpDocument.objects.filter(tags=tag)
    except Tag.DoesNotExist:
        return []


def ayuda_experiencia_familiar(request):
    return render(
        request,
        'ayudas_experiencia_familiar.html',
        {'docs': _docs_por_tag('experiencia_familiar')}
    )


def ayuda_autonomica(request):
    return render(
        request,
        'ayudas_autonomica.html',
        {'docs': _docs_por_tag('autonomica')}
    )


def ayuda_estatal(request):
    return render(
        request,
        'ayudas_estatal.html',
        {'docs': _docs_por_tag('estatal')}
    )


def ayuda_privada(request):
    return render(
        request,
        'ayudas_privada.html',
        {'docs': _docs_por_tag('privada')}
    )


# ---------------- Login / Registro ----------------
def login_view(request):
    """Vista de inicio de sesión."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Bienvenido, {user.username}")
            return redirect('index')
        messages.error(request, "Credenciales inválidas.")
    return render(request, 'login.html')


def register_view(request):
    """Registro de usuarios (opcional)."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(
                request,
                "Usuario creado correctamente. Ahora puedes iniciar sesión."
            )
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


# ---------------- Panel de administración interno ----------------
@user_passes_test(lambda u: u.is_staff)
def admin_panel(request):
    """
    Vista que solo pueden ver usuarios con is_staff=True.
    """
    help_docs = HelpDocument.objects.all()
    tags = Tag.objects.all()
    faqs_list = FAQ.objects.all()

    help_doc_form = HelpDocumentForm()
    tag_form = TagForm()
    faq_form = FAQForm()

    if request.method == 'POST':
        # Crear HelpDocument
        if 'create_helpdoc' in request.POST:
            hd_form = HelpDocumentForm(request.POST, request.FILES)
            if hd_form.is_valid():
                hd_form.save()
                messages.success(request, "Documento de ayuda creado.")
                return redirect('admin_panel')

        # Eliminar HelpDocument
        if 'delete_helpdoc_id' in request.POST:
            hd = get_object_or_404(HelpDocument, id=request.POST['delete_helpdoc_id'])
            hd.delete()
            messages.success(request, "Documento de ayuda eliminado.")
            return redirect('admin_panel')

        # Crear Tag
        if 'create_tag' in request.POST:
            t_form = TagForm(request.POST)
            if t_form.is_valid():
                t_form.save()
                messages.success(request, "Tag creado.")
                return redirect('admin_panel')

        # Eliminar Tag
        if 'delete_tag_id' in request.POST:
            t = get_object_or_404(Tag, id=request.POST['delete_tag_id'])
            t.delete()
            messages.success(request, "Tag eliminado.")
            return redirect('admin_panel')

        # Crear FAQ
        if 'create_faq' in request.POST:
            f_form = FAQForm(request.POST)
            if f_form.is_valid():
                f_form.save()
                messages.success(request, "FAQ creada correctamente.")
                return redirect('admin_panel')

        # Eliminar FAQ
        if 'delete_faq_id' in request.POST:
            faq_to_delete = get_object_or_404(FAQ, id=request.POST['delete_faq_id'])
            faq_to_delete.delete()
            messages.success(request, "FAQ eliminada correctamente.")
            return redirect('admin_panel')

    context = {
        'help_docs': help_docs,
        'help_doc_form': help_doc_form,
        'tags': tags,
        'tag_form': tag_form,
        'faqs_list': faqs_list,
        'faq_form': faq_form,
    }
    return render(request, 'admin_panel.html', context)
