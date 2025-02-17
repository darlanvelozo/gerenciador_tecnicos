from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Count, F, ExpressionWrapper, fields
from .models import Tecnico, OrdemServico
from datetime import timedelta

def alarme_tecnico(request):
    # Obter a data e hora atuais
    agora = timezone.localtime(timezone.now())

    # Lista para armazenar os dados dos técnicos
    tecnicos_com_dados = []

    # Filtrar técnicos que estão em expediente (status diferente de "Fora Expediente") 
    # e que possuem ordens de serviço pendentes maiores que 0
    tecnicos = Tecnico.objects.filter(
        ordens_servico__status__in=["Pendente", "Concluída", "Em Andamento"]
    ).annotate(
        qtd_ordens=Count('ordens_servico')
    ).filter(qtd_ordens__gt=0).distinct()

    for tecnico in tecnicos:
        # Filtrar ordens de serviço do técnico
        ordens_tecnico = tecnico.ordens_servico.all()

        # Quantidade de ordens pendentes (todas as pendentes)
        qtd_pendente = ordens_tecnico.filter(status="Pendente").count()

        # Quantidade de ordens concluídas no dia atual
        hoje = agora.date()
        qtd_concluida_hoje = ordens_tecnico.filter(
            status="Concluída",
            data_termino_executado__date=hoje
        ).count()

        # Verificar situações de alarme
        alarme = None
        
        # Situação 1: Técnico está disponível por mais de 20 minutos
        if tecnico.status == "Disponível":
            tempo_disponivel = agora - tecnico.ultima_atualizacao_status
            if tempo_disponivel > timedelta(minutes=20):
                alarme = "Ultrapassou Tempo Limite Disponível para Iniciar"

        # Situação 2: Técnico está em atividade e ultrapassou o prazo para finalizar uma OS
        if not alarme and tecnico.status == "Em Atividade":
            for os in ordens_tecnico.filter(status="Em Andamento"):
                
                if os.data_inicio_programado and os.data_termino_programado and os.data_inicio_executado:
                    # Calcula o prazo programado para finalizar a OS
                    prazo_programado = os.data_termino_programado - os.data_inicio_programado
                    
                    # Calcula o tempo limite considerando o início da execução + prazo programado + 20 minutos
                    tempo_limite_fim = os.data_inicio_executado + prazo_programado  #+ timedelta(minutes=20)
                    print("limite:" ,tempo_limite_fim)
                    print('agora:', agora)
                    # Verifica se o tempo atual ultrapassou o tempo limite
                    if agora > tempo_limite_fim:
                        alarme = "Ultrapassou Tempo Limite Disponível para Finalizar"
                        break
        # Adicionar dados do técnico à lista
        tecnicos_com_dados.append({
            "tecnico": tecnico,
            "qtd_pendente": qtd_pendente,
            "qtd_concluida_hoje": qtd_concluida_hoje,
            "alarme": alarme,
            "ultima_atualizacao_status": tecnico.ultima_atualizacao_status,
        })

    # Renderizar a página com os dados
    return render(
        request,
        "tecnicos/alarme_tecnico.html",
        {"tecnicos_com_dados": tecnicos_com_dados},
    )

def formatar_tempo(duracao):
    if duracao is None:
        return "-"

    total_segundos = int(duracao.total_seconds())
    dias = total_segundos // 86400
    horas = (total_segundos % 86400) // 3600
    minutos = (total_segundos % 3600) // 60

    if dias > 0:
        return f"{dias}d {horas}h {minutos}m"
    elif horas > 0:
        return f"{horas}h {minutos}m"
    else:
        return f"{minutos}m"

def detalhes_tecnico(request, tecnico_id):
    tecnico = get_object_or_404(Tecnico, id=tecnico_id)
    ordens_servico = tecnico.ordens_servico.exclude(status="Concluída").order_by(
        F('status').asc(),  # Primeiro, ordena pelo status
        F('data_inicio_programado').desc()  # Depois, pela data de início programado
    )

    ordens_com_atraso = []
    for os in ordens_servico:
        # Cálculo do atraso na execução
        atraso_execucao = None
        if os.data_inicio_executado and os.data_inicio_programado:
            atraso_execucao = os.data_inicio_executado - os.data_inicio_programado

        # Cálculo do atraso na conclusão
        atraso_conclusao = None
        if os.data_termino_executado and os.data_termino_programado:
            atraso_conclusao = os.data_termino_executado - os.data_termino_programado

        ordens_com_atraso.append({
            "os": os,
            "atraso_execucao": formatar_tempo(atraso_execucao),
            "atraso_conclusao": formatar_tempo(atraso_conclusao),
        })

    return render(request, "tecnicos/detalhes_tecnico.html", {
        "tecnico": tecnico,
        "ordens_com_atraso": ordens_com_atraso,
    })

def tecnicos_em_expediente(request):
    # Filtrar técnicos que possuem ordens de serviço nos status desejados e não estão fora do expediente
    tecnicos = Tecnico.objects.filter(
        ordens_servico__status__in=["Pendente", "Concluída", "Em Execução", "Em Andamento"]
    ).exclude(status="Fora Expediente").distinct()

    tecnicos_com_dados = []

    for tecnico in tecnicos:
        # Filtrar ordens de serviço do técnico
        ordens_tecnico = tecnico.ordens_servico.all()

        # Cálculo de Média de Atraso na Execução
        media_atraso_execucao = ordens_tecnico.exclude(
            data_inicio_executado__isnull=True
        ).aggregate(
            media=Avg(ExpressionWrapper(
                F("data_inicio_executado") - F("data_inicio_programado"),
                output_field=fields.DurationField()
            ))
        )["media"]

        # Cálculo de Média de Atraso na Conclusão
        media_atraso_conclusao = ordens_tecnico.exclude(
            data_termino_executado__isnull=True
        ).aggregate(
            media=Avg(ExpressionWrapper(
                F("data_termino_executado") - F("data_termino_programado"),
                output_field=fields.DurationField()
            ))
        )["media"]

        # Cálculo do Tempo Médio de Resolução (TMR)
        tmr = ordens_tecnico.exclude(
            data_inicio_executado__isnull=True, data_termino_executado__isnull=True
        ).aggregate(
            media=Avg(ExpressionWrapper(
                F("data_termino_executado") - F("data_inicio_executado"),
                output_field=fields.DurationField()
            ))
        )["media"]

        # Contagem de OSs nos status específicos
        qtd_pendente = ordens_tecnico.filter(status="Pendente").count()
        qtd_concluida = ordens_tecnico.filter(status="Concluída").count()
        qtd_em_execucao = ordens_tecnico.filter(status="Em Execução").count()

        tecnicos_com_dados.append({
            "tecnico": tecnico,
            "media_atraso_execucao": formatar_tempo(media_atraso_execucao),
            "media_atraso_conclusao": formatar_tempo(media_atraso_conclusao),
            "tmr": formatar_tempo(tmr),
            "qtd_pendente": qtd_pendente,
            "qtd_concluida": qtd_concluida,
            "qtd_em_execucao": qtd_em_execucao,  # Adicionado para manter consistência
        })

    return render(
        request,
        "expediente/tecnicos_em_expediente.html",
        {"tecnicos_com_dados": tecnicos_com_dados},
    )


