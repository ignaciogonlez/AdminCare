from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q

from .models import Document, FAQ, HelpDocument, Tag
from .forms import (
    DocumentForm, FAQForm, HelpDocumentForm, TagForm, UserRegisterForm
)

# <-- NUEVO: importamos PyMuPDF y herramientas para manejar archivos en memoria
import fitz
from django.core.files.base import ContentFile
import os


def index(request):
    """Página de Inicio: Explicación del proyecto y enlaces a las secciones."""
    return render(request, 'index.html')


def faqs(request):
    """ Muestra únicamente la lista de FAQs, sin permitir modificaciones. """
    faqs_list = FAQ.objects.all()
    return render(request, 'faqs.html', {'faqs': faqs_list})


# <-- NUEVO: Función para generar la portada de un PDF usando PyMuPDF
def generar_portada_pdf(document):
    """
    Recibe una instancia de Document.
    Si 'document.file' es un PDF, extrae la primera página y la guarda en 'document.cover'.
    """
    # Verificar la extensión (puedes refinar este chequeo según tu proyecto)
    if not document.file.name.lower().endswith('.pdf'):
        return  # Salir si no es un PDF

    # Abrir el PDF con PyMuPDF
    # pdf_path = document.file.path  # ruta en disco al archivo subido
    # doc = fitz.open(pdf_path)
    data = document.file.read()  # leer el archivo en memoria
    doc = fitz.Document(stream=data)


    # Asegurarnos de que tenga al menos 1 página
    if doc.page_count < 1:
        doc.close()
        return

    # Cargar la primera página
    page = doc.load_page(0)
    # Obtener pixmap (imagen) de esa página
    pix = page.get_pixmap()
    doc.close()

    # Convertir el pixmap en bytes (formato PNG)
    portada_bytes = pix.tobytes("png")

    # Crear un nombre para la portada basado en el título o ID
    cover_filename = f"{os.path.splitext(os.path.basename(document.file.name))[0]}_cover.png"
    print(f"Portada generada: {cover_filename}")
    # Guardar la portada en el campo 'cover' del modelo
    document.cover.save(cover_filename, ContentFile(portada_bytes))
    document.save()


@login_required
def documentos(request):
    """
    Página de gestión de documentos: 
    - Subida y visualización de archivos.
    - Filtrado por título.
    Solo usuarios autenticados pueden subir documentos.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            new_doc = form.save(commit=False)
            new_doc.user = request.user
            new_doc.save()
            
            # <-- NUEVO: Generar portada del PDF (si aplica)
            generar_portada_pdf(new_doc)

            messages.success(request, "Documento subido correctamente.")
            return redirect('documentos')
    else:
        form = DocumentForm()

    # Filtrado por título (GET ?q=...)
    query = request.GET.get('q')
    if query:
        documents = Document.objects.filter(
            Q(title__icontains=query),
            user=request.user
        ).order_by('-uploaded_at')
    else:
        documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')

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


def ayudas(request):
    """Página principal de ayudas: índice con enlaces a las 4 subsecciones."""
    return render(request, 'ayudas.html')


def ayuda_experiencia_familiar(request):
    docs = []
    try:
        tag = Tag.objects.get(name__iexact='experiencia_familiar')
        docs = HelpDocument.objects.filter(tags=tag)
    except Tag.DoesNotExist:
        pass
    context = {'docs': docs}
    return render(request, 'ayudas_experiencia_familiar.html', context)


def ayuda_autonomica(request):
    docs = []
    try:
        tag = Tag.objects.get(name__iexact='autonomica')
        docs = HelpDocument.objects.filter(tags=tag)
    except Tag.DoesNotExist:
        pass
    context = {'docs': docs}
    return render(request, 'ayudas_autonomica.html', context)


def ayuda_estatal(request):
    docs = []
    try:
        tag = Tag.objects.get(name__iexact='estatal')
        docs = HelpDocument.objects.filter(tags=tag)
    except Tag.DoesNotExist:
        pass
    context = {'docs': docs}
    return render(request, 'ayudas_estatal.html', context)


def ayuda_privada(request):
    docs = []
    try:
        tag = Tag.objects.get(name__iexact='privada')
        docs = HelpDocument.objects.filter(tags=tag)
    except Tag.DoesNotExist:
        pass
    context = {'docs': docs}
    return render(request, 'ayudas_privada.html', context)


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
        else:
            messages.error(request, "Credenciales inválidas.")
    return render(request, 'login.html')


@login_required
def logout_confirm_view(request):
    """
    Vista previa para confirmar logout. Aquí aparece la opción de ir a Admin si es staff.
    """
    if request.method == 'POST':
        # Si confirma el logout con un POST
        logout(request)
        messages.success(request, "Has cerrado sesión correctamente.")
        return redirect('index')

    # Si es GET, simplemente muestra la plantilla de confirmación.
    return render(request, 'logout_confirm.html')


def register_view(request):
    """Ejemplo de registro de usuarios (opcional)."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Usuario creado correctamente. Ahora puedes iniciar sesión.")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


@user_passes_test(lambda u: u.is_staff)
def admin_panel(request):
    """
    Vista que solo pueden ver usuarios con is_staff=True.
    Desde aquí el admin puede crear y eliminar:
      - HelpDocuments
      - Tags
      - FAQs
    """
    # HelpDocuments
    help_docs = HelpDocument.objects.all()
    help_doc_form = HelpDocumentForm()

    # Tags
    tags = Tag.objects.all()
    tag_form = TagForm()

    # FAQs
    faqs_list = FAQ.objects.all()
    faq_form = FAQForm()

    if request.method == 'POST':
        # 1) Crear HelpDocument
        if 'create_helpdoc' in request.POST:
            hd_form = HelpDocumentForm(request.POST, request.FILES)  # <-- IMPORTANTE
            if hd_form.is_valid():
                hd_form.save()
                messages.success(request, "Documento de ayuda creado.")
                return redirect('admin_panel')

        # 2) Eliminar HelpDocument
        if 'delete_helpdoc_id' in request.POST:
            hd_id = request.POST['delete_helpdoc_id']
            hd = get_object_or_404(HelpDocument, id=hd_id)
            hd.delete()
            messages.success(request, "Documento de ayuda eliminado.")
            return redirect('admin_panel')

        # 3) Crear Tag
        if 'create_tag' in request.POST:
            t_form = TagForm(request.POST)
            if t_form.is_valid():
                t_form.save()
                messages.success(request, "Tag creado.")
                return redirect('admin_panel')

        # 4) Eliminar Tag
        if 'delete_tag_id' in request.POST:
            t_id = request.POST['delete_tag_id']
            t = get_object_or_404(Tag, id=t_id)
            t.delete()
            messages.success(request, "Tag eliminado.")
            return redirect('admin_panel')

        # 5) Crear FAQ
        if 'create_faq' in request.POST:
            f_form = FAQForm(request.POST)
            if f_form.is_valid():
                f_form.save()
                messages.success(request, "FAQ creada correctamente.")
                return redirect('admin_panel')

        # 6) Eliminar FAQ
        if 'delete_faq_id' in request.POST:
            faq_id = request.POST['delete_faq_id']
            faq_to_delete = get_object_or_404(FAQ, id=faq_id)
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