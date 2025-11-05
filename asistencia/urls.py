from django.urls import path
from . import views

urlpatterns = [
    # PÚBLICO: cualquiera puede marcar asistencia
    path('', views.marcacion_publica, name='marcacion_publica'),

    # PROTEGIDO: dashboard para usuarios autenticados
    path('dashboard/', views.dashboard, name='dashboard'),

    # Acciones
    path('marcar/', views.marcar_asistencia, name='marcar_asistencia'),  # sigue siendo pública
    path('reporte/', views.exportar_excel, name='exportar_excel'),      # protegida
]