from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('faqs/', views.faqs, name='faqs'),
    path('documentos/', views.documentos, name='documentos'),
    path('ayudas/', views.ayudas, name='ayudas'),
    
    #Páginas de ayudas
    path('ayudas/experiencia-familiar/', views.ayuda_experiencia_familiar, name='ayuda_experiencia_familiar'),
    path('ayudas/autonomica/', views.ayuda_autonomica, name='ayuda_autonomica'),
    path('ayudas/estatal/', views.ayuda_estatal, name='ayuda_estatal'),
    path('ayudas/privada/', views.ayuda_privada, name='ayuda_privada'),
]
