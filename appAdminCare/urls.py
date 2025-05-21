# app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.index, name='index'),

    # FAQs y Gestión de documentos
    path('faqs/',                             views.faqs,                          name='faqs'),
    path('documentos/',                       views.documentos,                    name='documentos'),
    path('documentos/eliminar/<int:doc_id>/', views.eliminar_documento,            name='eliminar_documento'),

    # Ayudas generales
    path('ayudas/',                           views.ayudas,                        name='ayudas'),
    path('ayudas/experiencia-familiar/',      views.ayuda_experiencia_familiar,   name='ayuda_experiencia_familiar'),
    path('ayudas/autonomica/',                views.ayuda_autonomica,              name='ayuda_autonomica'),
    path('ayudas/estatal/',                   views.ayuda_estatal,                 name='ayuda_estatal'),
    path('ayudas/privada/',                   views.ayuda_privada,                 name='ayuda_privada'),

    # Ayudas por comunidad autónoma
    path('ayudas/autonomica/andalucia/',            views.ayuda_andalucia,               name='ayuda_andalucia'),
    path('ayudas/autonomica/aragon/',               views.ayuda_aragon,                  name='ayuda_aragon'),
    path('ayudas/autonomica/asturias/',             views.ayuda_asturias,                name='ayuda_asturias'),
    path('ayudas/autonomica/canarias/',             views.ayuda_canarias,                name='ayuda_canarias'),
    path('ayudas/autonomica/cantabria/',            views.ayuda_cantabria,               name='ayuda_cantabria'),
    path('ayudas/autonomica/castilla-la-mancha/',   views.ayuda_castilla_la_mancha,      name='ayuda_castilla_la_mancha'),
    path('ayudas/autonomica/castilla-y-leon/',      views.ayuda_castilla_y_leon,         name='ayuda_castilla_y_leon'),
    path('ayudas/autonomica/cataluna/',             views.ayuda_cataluna,                name='ayuda_cataluna'),
    path('ayudas/autonomica/ceuta-y-melilla/',      views.ayuda_ceuta_y_melilla,         name='ayuda_ceuta_y_melilla'),
    path('ayudas/autonomica/comunidad-de-madrid/',  views.ayuda_comunidad_de_madrid,     name='ayuda_comunidad_de_madrid'),
    path('ayudas/autonomica/comunidad-valenciana/', views.ayuda_comunidad_valenciana,    name='ayuda_comunidad_valenciana'),
    path('ayudas/autonomica/extremadura/',          views.ayuda_extremadura,             name='ayuda_extremadura'),
    path('ayudas/autonomica/galicia/',              views.ayuda_galicia,                 name='ayuda_galicia'),
    path('ayudas/autonomica/islas-baleares/',       views.ayuda_islas_baleares,          name='ayuda_islas_baleares'),
    path('ayudas/autonomica/la-rioja/',             views.ayuda_la_rioja,                name='ayuda_la_rioja'),
    path('ayudas/autonomica/murcia/',               views.ayuda_murcia,                  name='ayuda_murcia'),
    path('ayudas/autonomica/navarra/',              views.ayuda_navarra,                 name='ayuda_navarra'),
    path('ayudas/autonomica/pais-vasco/',           views.ayuda_pais_vasco,              name='ayuda_pais_vasco'),

    # Autenticación
    path('login/',      views.login_view,               name='login'),
    path('logout/',     views.LogoutConfirmView.as_view(), name='logout_confirm'),
    path('register/',   views.register_view,            name='register'),

    # Panel de administración interna
    path('admin-panel/', views.admin_panel,            name='admin_panel'),
]
