from django.urls import path
from .views import tecnicos_em_expediente, detalhes_tecnico

urlpatterns = [
    path("tecnicos/", tecnicos_em_expediente, name="tecnicos_em_expediente"),
    path("tecnico/<int:tecnico_id>/", detalhes_tecnico, name="detalhes_tecnico"),
]
