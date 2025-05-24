# views.py
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Document
from .forms import DocumentForm


@login_required
def documentos(request):
    """
    Vista principal de gestión de documentos:
    - Muestra documentos propios con búsqueda y paginación.
    - Permite subir nuevos documentos (POST).
    """
    # ----------  BÚSQUEDA ----------
    query = request.GET.get("q", "").strip()
    documentos_qs = Document.objects.filter(user=request.user).order_by("-uploaded_at")
    if query:
        documentos_qs = documentos_qs.filter(title__icontains=query)

    # ----------  PAGINACIÓN ----------
    paginator = Paginator(documentos_qs, 10)  # ← cambia 10 si quieres otro tamaño
    page_number = request.GET.get("page") or 1
    try:
        documentos_page = paginator.page(page_number)
    except PageNotAnInteger:
        documentos_page = paginator.page(1)
    except EmptyPage:
        documentos_page = paginator.page(paginator.num_pages)

    # ----------  SUBIDA DE DOCUMENTOS ----------
    if request.method == "POST" and "file" in request.FILES:
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            # Redirige a la misma página (página 1) para evitar duplicar POST
            return redirect(reverse("documentos") + f"?page=1&q={query}")
    else:
        form = DocumentForm()

    context = {
        "form": form,
        "documents": documentos_page,
        "query": query,
    }
    return render(request, "documentos.html", context)


@login_required
def eliminar_documento(request, pk):
    """
    Elimina un documento del usuario y redirige de vuelta a la lista.
    Se llama desde el botón de la papelera (POST).
    """
    documento = get_object_or_404(Document, pk=pk, user=request.user)

    if request.method == "POST":
        documento.delete()

    # Regresa a la página actual si la había, para no perder la posición
    page = request.GET.get("page", "1")
    query = request.GET.get("q", "")
    return redirect(reverse("documentos") + f"?page={page}&q={query}")
