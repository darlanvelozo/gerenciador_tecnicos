from django.db import models

from django.db import models
from django.contrib.auth.models import Group  # Importa os grupos de permissão do Django
from django.utils.timezone import localtime, now
from datetime import time

class Tecnico(models.Model):
    STATUS_CHOICES = [
        ("Em Atividade", "Em Atividade"),
        ("Fora Expediente", "Fora Expediente"),
        ("Disponível", "Disponível"),
    ]

    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=100, verbose_name="Nome do Técnico")
    grupos = models.ManyToManyField(Group, related_name="tecnicos", verbose_name="Grupos de Permissão")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Fora Expediente", verbose_name="Status")
    
    def atualizar_status(self):
        """
        Atualiza o status do técnico com base no horário de expediente e nas ordens de serviço.
        """
        horario_atual = now().time()
        dia_atual = now().strftime("%A")  # Nome do dia da semana em inglês

        # Obtém o expediente do grupo do técnico
        expediente = Expediente.objects.filter(grupo_permissao__in=self.grupos.all(), dias_semana__nome=dia_atual).first()

        if expediente:
            if expediente.horario_inicio_expediente <= horario_atual <= expediente.horario_fim_expediente:
                # Verifica as ordens de serviço atribuídas
                ordens = self.ordens_servico.all()
                if any(os.status == "Em Andamento" for os in ordens):
                    self.status = "Em Atividade"
                else:
                    self.status = "Disponível"
            else:
                self.status = "Fora Expediente"
        else:
            self.status = "Fora Expediente"

        self.save()

    def __str__(self):
        return f"{self.nome} ({self.status})"

class Expediente(models.Model): 
    DIAS_DA_SEMANA = [
        ("Segunda-feira", "Segunda-feira"),
        ("Terça-feira", "Terça-feira"),
        ("Quarta-feira", "Quarta-feira"),
        ("Quinta-feira", "Quinta-feira"),
        ("Sexta-feira", "Sexta-feira"),
        ("Sábado", "Sábado"),
        ("Domingo", "Domingo"),
    ]

    ESCALAS_TRABALHO = [
        ("5x2", "5x2 - Segunda a Sexta"),
        ("6x1", "6x1 - Segunda a Sábado"),
        ("12x36", "12x36 - 12h de trabalho, 36h de descanso"),
        ("Turno Fixo", "Turno Fixo (exemplo: 08h às 18h)"),
        ("Turno Noturno", "Turno Noturno (exemplo: 22h às 06h)"),
        ("Personalizado", "Personalizado"),
    ]

    id = models.AutoField(primary_key=True)
    grupo_permissao = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="expedientes", verbose_name="Grupo de Permissão"
    )
    escala = models.CharField(
        max_length=20, choices=ESCALAS_TRABALHO, default="5x2", verbose_name="Escala de Trabalho"
    )
    dias_semana = models.ManyToManyField("DiaSemana", verbose_name="Dias da Semana")
    horario_inicio_expediente = models.TimeField(verbose_name="Início do Expediente")
    horario_fim_expediente = models.TimeField(verbose_name="Fim do Expediente")
    horario_inicio_almoco = models.TimeField(verbose_name="Início do Almoço", null=True, blank=True)
    horario_fim_almoco = models.TimeField(verbose_name="Fim do Almoço", null=True, blank=True)

    def __str__(self):
        return f"{self.grupo_permissao.name} - {self.escala}: {self.horario_inicio_expediente} às {self.horario_fim_expediente}"
class DiaSemana(models.Model):
    nome = models.CharField(max_length=20, choices=Expediente.DIAS_DA_SEMANA, unique=True)

    def __str__(self):
        return self.nome

class OrdemServico(models.Model):
    id_ordem_servico = models.BigIntegerField(
        primary_key=True, unique=True, verbose_name="ID da Ordem de Serviço"
    )
    numero_ordem_servico = models.CharField(max_length=50, verbose_name="Número da Ordem de Serviço")
    data_cadastro = models.DateTimeField(verbose_name="Data de Cadastro")
    data_inicio_programado = models.DateTimeField(verbose_name="Data de Início Programado")
    data_termino_programado = models.DateTimeField(verbose_name="Data de Término Programado")
    data_inicio_executado = models.DateTimeField(null=True, blank=True, verbose_name="Data de Início Executado")
    data_termino_executado = models.DateTimeField(null=True, blank=True, verbose_name="Data de Término Executado")
    prazo = models.DurationField(verbose_name="Prazo")
    id_cliente_servico = models.CharField(max_length=50, verbose_name="ID do Cliente")
    tipo_os = models.CharField(max_length=50, verbose_name="Tipo da OS")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    tecnicos = models.ManyToManyField("Tecnico", related_name="ordens_servico", verbose_name="Técnicos")
    ultima_mensagem = models.TextField(blank=True, null=True, verbose_name="Última Mensagem")
    status = models.CharField(max_length=20, verbose_name="status_os")
    def __str__(self):
        return f"OS {self.numero_ordem_servico} - {self.tipo_os}"

    def calcular_status(self):
        if self.data_termino_executado:
            return "Concluída"
        elif self.data_inicio_executado:
            return "Em Andamento"
        else:
            return "Pendente"

    def atualizar_status(self):
        if self.data_termino_executado:
            self.status = "Concluída"
        elif self.data_inicio_executado and not self.data_termino_executado:
            self.status = "Em Andamento"
        else:
            self.status = "Pendente"
        self.save()