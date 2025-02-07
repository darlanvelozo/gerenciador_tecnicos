from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Tecnico, OrdemServico, Expediente, DiaSemana

@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'get_status', 'listar_grupos')
    list_filter = ('grupos',)  # Removido 'status' que estava causando erro
    search_fields = ('nome',)
    filter_horizontal = ('grupos',)

    def listar_grupos(self, obj):
        return ", ".join([g.name for g in obj.grupos.all()])
    listar_grupos.short_description = "Grupos de Permissão"


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ('numero_ordem_servico', 'tipo_os', 'cidade', 'status', 'data_cadastro')
    list_filter = ('tipo_os', 'cidade', 'data_cadastro')
    search_fields = ('numero_ordem_servico', 'id_cliente_servico')
    filter_horizontal = ('tecnicos',)
    readonly_fields = ('prazo',)
    date_hierarchy = 'data_cadastro'
    fieldsets = (
        ('Identificação', {
            'fields': ('id_ordem_servico', 'numero_ordem_servico', 'tipo_os')
        }),
        ('Datas', {
            'fields': (
                'data_cadastro', 
                'data_inicio_programado', 
                'data_termino_programado',
                'data_inicio_executado', 
                'data_termino_executado',
                'prazo'
            )
        }),
        ('Localização', {
            'fields': ('cidade', 'id_cliente_servico')
        }),
        ('Atribuições', {
            'fields': ('tecnicos', 'ultima_mensagem')
        }),
    )

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('grupo_permissao', 'escala', 'horario_inicio_expediente', 'horario_fim_expediente')
    list_filter = ('grupo_permissao', 'escala')
    search_fields = ('grupo_permissao__name',)
    filter_horizontal = ('dias_semana',)
    fieldsets = (
        (None, {
            'fields': ('grupo_permissao', 'escala')
        }),
        ('Horários', {
            'fields': ('horario_inicio_expediente', 'horario_fim_expediente', 
                      'horario_inicio_almoco', 'horario_fim_almoco')
        }),
        ('Dias de Trabalho', {
            'fields': ('dias_semana',)
        }),
    )

@admin.register(DiaSemana)
class DiaSemanaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
