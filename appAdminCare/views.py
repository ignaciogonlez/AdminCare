# app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Document, FAQ, HelpDocument, Tag
from .forms import (
    DocumentForm, FAQForm, HelpDocumentForm, TagForm, UserRegisterForm
)

import fitz  # PyMuPDF
from django.core.files.base import ContentFile
import os


def generar_portada_pdf(instance):
    """Extrae miniatura JPEG de la primera página del PDF."""
    if not instance.file or not instance.file.name.lower().endswith('.pdf'):
        return
    if instance.cover and instance.cover.name:
        return

    instance.file.open('rb')
    data = instance.file.read()
    instance.file.close()

    pdf = fitz.open(stream=data, filetype='pdf')
    if pdf.page_count < 1:
        pdf.close()
        return

    page = pdf.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    portada_bytes = pix.tobytes('jpeg')
    pdf.close()

    filename = f"{os.path.splitext(os.path.basename(instance.file.name))[0]}_cover.jpg"
    instance.cover.save(filename, ContentFile(portada_bytes))
    instance.save(update_fields=['cover'])


class LogoutConfirmView(LogoutView):
    template_name = 'logout_confirm.html'
    next_page = 'index'
    http_method_names = ['get', 'post', 'head', 'options', 'trace']

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        messages.success(request, "Has cerrado sesión correctamente.")
        return super().post(request, *args, **kwargs)


def index(request):
    return render(request, 'index.html')


def faqs(request):
    faqs_list = FAQ.objects.all()
    return render(request, 'faqs.html', {'faqs': faqs_list})


@login_required
def documentos(request):
    """Gestión de documentos del usuario."""
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

    return render(request, 'documentos.html', {
        'form': form,
        'documents': documents,
        'query': query,
    })


@login_required
def eliminar_documento(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if doc.user == request.user or request.user.is_staff:
        doc.delete()
        messages.success(request, "Documento eliminado.")
    else:
        messages.error(request, "No tienes permiso para eliminar este documento.")
    return redirect('documentos')


def ayudas(request):
    return render(request, 'ayudas.html')


def _docs_por_tag(nombre_tag):
    try:
        tag = Tag.objects.get(name__iexact=nombre_tag)
        return HelpDocument.objects.filter(tags=tag)
    except Tag.DoesNotExist:
        return HelpDocument.objects.none()


def ayuda_experiencia_familiar(request):
    return render(request, 'ayudas_experiencia_familiar.html', {
        'docs': _docs_por_tag('experiencia_familiar')
    })


def ayuda_autonomica(request):
    # Página principal con enlaces a cada comunidad
    communities = [
        {'slug': 'andalucia',            'name': 'Andalucía',           'image': 'images/andalucia.png'},
        {'slug': 'aragon',               'name': 'Aragón',              'image': 'images/aragon.png'},
        {'slug': 'asturias',             'name': 'Asturias',            'image': 'images/asturias.png'},
        {'slug': 'canarias',             'name': 'Canarias',            'image': 'images/canarias.jpg'},
        {'slug': 'cantabria',            'name': 'Cantabria',           'image': 'images/cantabria.png'},
        {'slug': 'castilla_la_mancha',   'name': 'Castilla-La Mancha',  'image': 'images/clm.png'},
        {'slug': 'castilla_y_leon',      'name': 'Castilla y León',     'image': 'images/cyl.png'},
        {'slug': 'cataluna',             'name': 'Cataluña',            'image': 'images/cataluna.png'},
        {'slug': 'ceuta_y_melilla',      'name': 'Ceuta y Melilla',     'image': 'images/ceuta_melilla.jpg'},
        {'slug': 'comunidad_de_madrid',  'name': 'Comunidad de Madrid', 'image': 'images/madrid.png'},
        {'slug': 'comunidad_valenciana', 'name': 'Comunidad Valenciana','image': 'images/cv.png'},
        {'slug': 'extremadura',          'name': 'Extremadura',         'image': 'images/extremadura.png'},
        {'slug': 'galicia',              'name': 'Galicia',             'image': 'images/galicia.png'},
        {'slug': 'islas_baleares',       'name': 'Islas Baleares',      'image': 'images/baleares.png'},
        {'slug': 'la_rioja',             'name': 'La Rioja',            'image': 'images/rioja.png'},
        {'slug': 'murcia',               'name': 'Murcia',              'image': 'images/murcia.png'},
        {'slug': 'navarra',              'name': 'Navarra',             'image': 'images/navarra.png'},
        {'slug': 'pais_vasco',           'name': 'País Vasco',          'image': 'images/pais_vasco.png'},
    ]
    return render(request, 'ayudas_autonomica.html', {
        'communities': communities
    })


def ayuda_estatal(request):
    return render(request, 'ayudas_estatal.html', {
        'docs': _docs_por_tag('estatal')
    })


def ayuda_privada(request):
    return render(request, 'ayudas_privada.html', {
        'docs': _docs_por_tag('privada')
    })


# Vistas por cada comunidad autónoma: filtran HelpDocument por tags 'autonomica' + '<slug>'
def ayuda_andalucia(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='andalucia')
    return render(request, 'ayuda_andalucia.html', {'docs': docs})

def ayuda_aragon(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='aragon')
    return render(request, 'ayuda_aragon.html', {'docs': docs})

def ayuda_asturias(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='asturias')
    return render(request, 'ayuda_asturias.html', {'docs': docs})

def ayuda_canarias(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='canarias')
    return render(request, 'ayuda_canarias.html', {'docs': docs})

def ayuda_cantabria(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='cantabria')
    return render(request, 'ayuda_cantabria.html', {'docs': docs})

def ayuda_castilla_la_mancha(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='castilla la mancha')
    return render(request, 'ayuda_castilla_la_mancha.html', {'docs': docs})

def ayuda_castilla_y_leon(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='castilla y leon')
    return render(request, 'ayuda_castilla_y_leon.html', {'docs': docs})

def ayuda_cataluna(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='cataluna')
    return render(request, 'ayuda_cataluna.html', {'docs': docs})

def ayuda_ceuta_y_melilla(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='ceuta y melilla')
    return render(request, 'ayuda_ceuta_y_melilla.html', {'docs': docs})

def ayuda_comunidad_de_madrid(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='comunidad de madrid')
    return render(request, 'ayuda_comunidad_de_madrid.html', {'docs': docs})

def ayuda_comunidad_valenciana(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='comunidad valenciana')
    return render(request, 'ayuda_comunidad_valenciana.html', {'docs': docs})

def ayuda_extremadura(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='extremadura')
    return render(request, 'ayuda_extremadura.html', {'docs': docs})

def ayuda_galicia(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='galicia')
    return render(request, 'ayuda_galicia.html', {'docs': docs})

def ayuda_islas_baleares(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='islas baleares')
    return render(request, 'ayuda_islas_baleares.html', {'docs': docs})

def ayuda_la_rioja(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='la rioja')
    return render(request, 'ayuda_la_rioja.html', {'docs': docs})

def ayuda_murcia(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='murcia')
    return render(request, 'ayuda_murcia.html', {'docs': docs})

def ayuda_navarra(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='navarra')
    return render(request, 'ayuda_navarra.html', {'docs': docs})

def ayuda_pais_vasco(request):
    docs = HelpDocument.objects.filter(tags__name='autonomica').filter(tags__name='pais vasco')
    return render(request, 'ayuda_pais_vasco.html', {'docs': docs})


def login_view(request):
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
    # Filtrado por etiqueta
    filter_tag = request.GET.get('filter_tag')
    if filter_tag:
        docs_qs = HelpDocument.objects.filter(tags__id=filter_tag).order_by('-id')
    else:
        docs_qs = HelpDocument.objects.all().order_by('-id')

    # Paginación
    paginator = Paginator(docs_qs, 20)
    page_number = request.GET.get('page')
    page_docs = paginator.get_page(page_number)

    tags      = Tag.objects.all()
    faqs_list = FAQ.objects.all()

    help_doc_form = HelpDocumentForm()
    tag_form      = TagForm()
    faq_form      = FAQForm()

    if request.method == 'POST':
        if 'create_helpdoc' in request.POST:
            hd_form = HelpDocumentForm(request.POST, request.FILES)
            if hd_form.is_valid():
                new_help = hd_form.save()
                generar_portada_pdf(new_help)
                messages.success(request, "Documento de ayuda creado.")
                return redirect('admin_panel')
            help_doc_form = hd_form

        elif 'delete_helpdoc_id' in request.POST:
            hd = get_object_or_404(HelpDocument, id=request.POST['delete_helpdoc_id'])
            hd.delete()
            messages.success(request, "Documento de ayuda eliminado.")
            return redirect('admin_panel')

        elif 'create_tag' in request.POST:
            t_form = TagForm(request.POST)
            if t_form.is_valid():
                t_form.save()
                messages.success(request, "Tag creado.")
                return redirect('admin_panel')
            tag_form = t_form

        elif 'delete_tag_id' in request.POST:
            t = get_object_or_404(Tag, id=request.POST['delete_tag_id'])
            t.delete()
            messages.success(request, "Tag eliminado.")
            return redirect('admin_panel')

        elif 'create_faq' in request.POST:
            f_form = FAQForm(request.POST)
            if f_form.is_valid():
                f_form.save()
                messages.success(request, "FAQ creada correctamente.")
                return redirect('admin_panel')
            faq_form = f_form

        elif 'delete_faq_id' in request.POST:
            faq_to_delete = get_object_or_404(FAQ, id=request.POST['delete_faq_id'])
            faq_to_delete.delete()
            messages.success(request, "FAQ eliminada correctamente.")
            return redirect('admin_panel')

    return render(request, 'admin_panel.html', {
        'help_docs': page_docs,
        'paginator': paginator,
        'tags': tags,
        'filter_tag': filter_tag,
        'faqs_list': faqs_list,
        'help_doc_form': help_doc_form,
        'tag_form': tag_form,
        'faq_form': faq_form,
    })
