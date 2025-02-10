from django.shortcuts import render
from django.utils.timezone import now
from .models import Tecnico
from django.shortcuts import render, get_object_or_404


def detalhes_tecnico(request, tecnico_id):
    tecnico = get_object_or_404(Tecnico, id=tecnico_id)
    ordens_servico = tecnico.ordens_servico.all()  # Obtém todas as OS do técnico

    return render(request, "tecnicos/detalhes_tecnico.html", {"tecnico": tecnico, "ordens_servico": ordens_servico})

def tecnicos_em_expediente(request):
    horario_atual = now().time()
    dia_atual = now().strftime("%A")  # Nome do dia da semana em inglês

    # Filtrar técnicos que estão dentro do expediente
    tecnicos = [
        tecnico for tecnico in Tecnico.objects.all() if tecnico.status != "Fora Expediente"
    ]

    return render(request, "expediente/tecnicos_em_expediente.html", {"tecnicos": tecnicos})
