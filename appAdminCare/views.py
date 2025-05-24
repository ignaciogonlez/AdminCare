# app/views.py
import os

import fitz  # PyMuPDF
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LogoutView
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import (
    DocumentForm,
    FAQForm,
    HelpDocumentForm,
    TagForm,
    UserRegisterForm,
)
from .models import Document, FAQ, HelpDocument, Tag


HELP_PAGE_SIZE = 10  # nº de documentos por página para vistas de ayudas


# ───────────────────────────────────────────────────────────
# Utilidades
# ───────────────────────────────────────────────────────────
def generar_portada_pdf(instance):
    """Extrae miniatura JPEG de la primera página de un PDF y la guarda en `instance.cover`."""
    if not instance.file or not instance.file.name.lower().endswith(".pdf"):
        return
    if instance.cover and instance.cover.name:
        return

    instance.file.open("rb")
    data = instance.file.read()
    instance.file.close()

    pdf = fitz.open(stream=data, filetype="pdf")
    if pdf.page_count < 1:
        pdf.close()
        return

    page = pdf.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    portada_bytes = pix.tobytes("jpeg")
    pdf.close()

    filename = f"{os.path.splitext(os.path.basename(instance.file.name))[0]}_cover.jpg"
    instance.cover.save(filename, ContentFile(portada_bytes))
    instance.save(update_fields=["cover"])


def _paginate(request, queryset, per_page=10):
    """Devuelve un objeto Page según el parámetro ?page= presente en la URL."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page") or 1
    return paginator.get_page(page_number)


def _docs_por_tag(nombre_tag):
    """Devuelve queryset de HelpDocument filtrado por nombre de tag (case-insensitive)."""
    try:
        tag = Tag.objects.get(name__iexact=nombre_tag)
        return HelpDocument.objects.filter(tags=tag).order_by("-id")
    except Tag.DoesNotExist:
        return HelpDocument.objects.none()


def _render_help(request, docs_qs, template_name):
    """Pequeño helper para no repetir código de paginación + render."""
    docs_page = _paginate(request, docs_qs, HELP_PAGE_SIZE)
    return render(request, template_name, {"docs": docs_page})


# ───────────────────────────────────────────────────────────
# Autenticación y vistas genéricas
# ───────────────────────────────────────────────────────────
class LogoutConfirmView(LogoutView):
    template_name = "logout_confirm.html"
    next_page = "index"
    http_method_names = ["get", "post", "head", "options", "trace"]

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        messages.success(request, "Has cerrado sesión correctamente.")
        return super().post(request, *args, **kwargs)


def index(request):
    return render(request, "index.html")


def faqs(request):
    faqs_list = FAQ.objects.all()
    return render(request, "faqs.html", {"faqs": faqs_list})


# ───────────────────────────────────────────────────────────
# Gestión de documentos del usuario
# ───────────────────────────────────────────────────────────
@login_required
def documentos(request):
    """
    Gestiona documentos del usuario:
    - Subida (POST)
    - Búsqueda por título (?q=)
    - Paginación (?page=)
    """
    # 1) Subir documento
    if request.method == "POST" and request.FILES.get("file"):
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            new_doc = form.save(commit=False)
            new_doc.user = request.user
            new_doc.save()
            generar_portada_pdf(new_doc)
            messages.success(request, "Documento subido correctamente.")
            return redirect("documentos")
    else:
        form = DocumentForm()

    # 2) Filtrado / búsqueda
    query = request.GET.get("q", "").strip()
    docs_qs = Document.objects.filter(user=request.user).order_by("-uploaded_at")
    if query:
        docs_qs = docs_qs.filter(title__icontains=query)

    # 3) Paginación
    documents_page = _paginate(request, docs_qs, 10)

    return render(
        request,
        "documentos.html",
        {
            "form": form,
            "documents": documents_page,
            "query": query,
        },
    )


@login_required
def eliminar_documento(request, doc_id):
    """Elimina un documento del usuario y redirige manteniendo ?page=&q="""
    doc = get_object_or_404(Document, id=doc_id)
    if doc.user == request.user or request.user.is_staff:
        doc.delete()
        messages.success(request, "Documento eliminado.")
    else:
        messages.error(request, "No tienes permiso para eliminar este documento.")

    page = request.GET.get("page", "1")
    q = request.GET.get("q", "")
    redirect_url = reverse("documentos") + f"?page={page}"
    if q:
        redirect_url += f"&q={q}"
    return redirect(redirect_url)


# ───────────────────────────────────────────────────────────
# Ayudas (vistas con paginación)
# ───────────────────────────────────────────────────────────
def ayudas(request):
    return render(request, "ayudas.html")


def ayuda_experiencia_familiar(request):
    return _render_help(
        request,
        _docs_por_tag("experiencia_familiar"),
        "ayudas_experiencia_familiar.html",
    )


def ayuda_estatal(request):
    return _render_help(request, _docs_por_tag("estatal"), "ayudas_estatal.html")


def ayuda_privada(request):
    return _render_help(request, _docs_por_tag("privada"), "ayudas_privada.html")


# Página principal de CC. AA. (no necesita paginar porque solo muestra el mapa)
def ayuda_autonomica(request):
    communities = [
        {"slug": "andalucia", "name": "Andalucía", "image": "images/andalucia.png"},
        {"slug": "aragon", "name": "Aragón", "image": "images/aragon.png"},
        {"slug": "asturias", "name": "Asturias", "image": "images/asturias.png"},
        {"slug": "canarias", "name": "Canarias", "image": "images/canarias.jpg"},
        {"slug": "cantabria", "name": "Cantabria", "image": "images/cantabria.png"},
        {
            "slug": "castilla_la_mancha",
            "name": "Castilla-La Mancha",
            "image": "images/clm.png",
        },
        {"slug": "castilla_y_leon", "name": "Castilla y León", "image": "images/cyl.png"},
        {"slug": "cataluna", "name": "Cataluña", "image": "images/cataluna.png"},
        {
            "slug": "ceuta_y_melilla",
            "name": "Ceuta y Melilla",
            "image": "images/ceuta_melilla.jpg",
        },
        {"slug": "comunidad_de_madrid", "name": "Comunidad de Madrid", "image": "images/madrid.png"},
        {"slug": "comunidad_valenciana", "name": "Comunidad Valenciana", "image": "images/cv.png"},
        {"slug": "extremadura", "name": "Extremadura", "image": "images/extremadura.png"},
        {"slug": "galicia", "name": "Galicia", "image": "images/galicia.png"},
        {"slug": "islas_baleares", "name": "Islas Baleares", "image": "images/baleares.png"},
        {"slug": "la_rioja", "name": "La Rioja", "image": "images/rioja.png"},
        {"slug": "murcia", "name": "Murcia", "image": "images/murcia.png"},
        {"slug": "navarra", "name": "Navarra", "image": "images/navarra.png"},
        {"slug": "pais_vasco", "name": "País Vasco", "image": "images/pais_vasco.png"},
    ]
    return render(request, "ayudas_autonomica.html", {"communities": communities})


# Helper genérico para las 17 vistas autonómicas
def _autonomica_view(request, slug, template_name):
    qs = HelpDocument.objects.filter(tags__name="autonomica").filter(tags__name=slug).order_by("-id")
    return _render_help(request, qs, template_name)


# Vistas autonómicas individuales
def ayuda_andalucia(request):
    return _autonomica_view(request, "andalucia", "ayuda_andalucia.html")


def ayuda_aragon(request):
    return _autonomica_view(request, "aragon", "ayuda_aragon.html")


def ayuda_asturias(request):
    return _autonomica_view(request, "asturias", "ayuda_asturias.html")


def ayuda_canarias(request):
    return _autonomica_view(request, "canarias", "ayuda_canarias.html")


def ayuda_cantabria(request):
    return _autonomica_view(request, "cantabria", "ayuda_cantabria.html")


def ayuda_castilla_la_mancha(request):
    return _autonomica_view(request, "castilla la mancha", "ayuda_castilla_la_mancha.html")


def ayuda_castilla_y_leon(request):
    return _autonomica_view(request, "castilla y leon", "ayuda_castilla_y_leon.html")


def ayuda_cataluna(request):
    return _autonomica_view(request, "cataluna", "ayuda_cataluna.html")


def ayuda_ceuta_y_melilla(request):
    return _autonomica_view(request, "ceuta y melilla", "ayuda_ceuta_y_melilla.html")


def ayuda_comunidad_de_madrid(request):
    return _autonomica_view(request, "comunidad de madrid", "ayuda_comunidad_de_madrid.html")


def ayuda_comunidad_valenciana(request):
    return _autonomica_view(request, "comunidad valenciana", "ayuda_comunidad_valenciana.html")


def ayuda_extremadura(request):
    return _autonomica_view(request, "extremadura", "ayuda_extremadura.html")


def ayuda_galicia(request):
    return _autonomica_view(request, "galicia", "ayuda_galicia.html")


def ayuda_islas_baleares(request):
    return _autonomica_view(request, "islas baleares", "ayuda_islas_baleares.html")


def ayuda_la_rioja(request):
    return _autonomica_view(request, "la rioja", "ayuda_la_rioja.html")


def ayuda_murcia(request):
    return _autonomica_view(request, "murcia", "ayuda_murcia.html")


def ayuda_navarra(request):
    return _autonomica_view(request, "navarra", "ayuda_navarra.html")


def ayuda_pais_vasco(request):
    return _autonomica_view(request, "pais vasco", "ayuda_pais_vasco.html")


# ───────────────────────────────────────────────────────────
# Login / Registro
# ───────────────────────────────────────────────────────────
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Bienvenido, {user.username}")
            return redirect("index")
        messages.error(request, "Credenciales inválidas.")
    return render(request, "login.html")


def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "Usuario creado correctamente. Ahora puedes iniciar sesión.")
            return redirect("login")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})


# ───────────────────────────────────────────────────────────
# Panel de administración (staff)
# ───────────────────────────────────────────────────────────
@user_passes_test(lambda u: u.is_staff)
def admin_panel(request):
    filter_tag = request.GET.get("filter_tag")
    if filter_tag:
        docs_qs = HelpDocument.objects.filter(tags__id=filter_tag).order_by("-id")
    else:
        docs_qs = HelpDocument.objects.all().order_by("-id")

    page_docs = _paginate(request, docs_qs, 20)

    tags = Tag.objects.all()
    faqs_list = FAQ.objects.all()

    help_doc_form = HelpDocumentForm()
    tag_form = TagForm()
    faq_form = FAQForm()

    if request.method == "POST":
        if "create_helpdoc" in request.POST:
            hd_form = HelpDocumentForm(request.POST, request.FILES)
            if hd_form.is_valid():
                new_help = hd_form.save()
                generar_portada_pdf(new_help)
                messages.success(request, "Documento de ayuda creado.")
                return redirect("admin_panel")
            help_doc_form = hd_form

        elif "delete_helpdoc_id" in request.POST:
            hd = get_object_or_404(HelpDocument, id=request.POST["delete_helpdoc_id"])
            hd.delete()
            messages.success(request, "Documento de ayuda eliminado.")
            return redirect("admin_panel")

        elif "create_tag" in request.POST:
            t_form = TagForm(request.POST)
            if t_form.is_valid():
                t_form.save()
                messages.success(request, "Tag creado.")
                return redirect("admin_panel")
            tag_form = t_form

        elif "delete_tag_id" in request.POST:
            t = get_object_or_404(Tag, id=request.POST["delete_tag_id"])
            t.delete()
            messages.success(request, "Tag eliminado.")
            return redirect("admin_panel")

        elif "create_faq" in request.POST:
            f_form = FAQForm(request.POST)
            if f_form.is_valid():
                f_form.save()
                messages.success(request, "FAQ creada correctamente.")
                return redirect("admin_panel")
            faq_form = f_form

        elif "delete_faq_id" in request.POST:
            faq_to_delete = get_object_or_404(FAQ, id=request.POST["delete_faq_id"])
            faq_to_delete.delete()
            messages.success(request, "FAQ eliminada correctamente.")
            return redirect("admin_panel")

    return render(
        request,
        "admin_panel.html",
        {
            "help_docs": page_docs,
            "tags": tags,
            "filter_tag": filter_tag,
            "faqs_list": faqs_list,
            "help_doc_form": help_doc_form,
            "tag_form": tag_form,
            "faq_form": faq_form,
        },
    )
