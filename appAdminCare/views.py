from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import Document

def index(request):
    #Página de Inicio: Explicación del proyecto y enlaces a las diferentes secciones.
    return render(request, 'index.html')

def faqs(request):
    #Página de FAQs: sección con preguntas frecuentes y respuestas.
    return render(request, 'faqs.html')

def documentos(request):
    #Página de gestión de documentos: subida y visualización de los archivos.
    if request.method == 'POST' and request.FILES.get('uploaded_file'):
        uploaded_file = request.FILES['uploaded_file']
        title = request.POST.get('title', 'Documento sin título')
        new_doc = Document(file=uploaded_file, title=title)
        new_doc.save()
        return redirect('documentos')  # redirige para evitar reenvíos duplicados al recargar
    
    documents = Document.objects.all().order_by('-uploaded_at')
    return render(request, 'documentos.html', {'documents': documents})

def ayudas(request):
    #Página principal de ayudas: índice con enlaces a las 4 subsecciones.
    return render(request, 'ayudas.html')

def ayuda_experiencia_familiar(request):
    #Página de Información sobre experiencia familiar 
    return render(request, 'ayudas_experiencia_familiar.html')

def ayuda_autonomica(request):
    #Página de Información sobre ayuda autonómica
    return render(request, 'ayudas_autonomica.html')

def ayuda_estatal(request):
    #Página de Información sobre ayuda estatal 
    return render(request, 'ayudas_estatal.html')

def ayuda_privada(request):
    #Página de Información sobre ayudas privadas 
    return render(request, 'ayudas_privada.html')
