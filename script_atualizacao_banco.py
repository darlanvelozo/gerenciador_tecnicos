import psycopg2
from psycopg2 import sql
from datetime import datetime, time
import time
# Configurações do banco HubSoft (origem)
DB_CONFIG_HUBSOFT = {
    'dbname': 'hubsoft',
    'user': 'mega_leitura',
    'password': '4630a1512ee8e738f935a73a65cebf75b07fcab5',
    'host': '177.10.118.77',
    'port': '9432'
}

# Configurações do banco TecInfo (destino)
DB_CONFIG_TECINFO = {
    'dbname': 'tecinfo',
    'user': 'admin',
    'password': 'qualidade@trunks.57',
    'host': '187.62.153.52',
    'port': '5432'
}

# Função para conectar ao banco de dados
def connect_to_db(db_config):
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Função para realizar a consulta no banco de origem e retornar os dados
def fetch_ordens_servico(conn):
    query = """
    select
    os.id_ordem_servico,
    os.numero_ordem_servico,
    os.data_cadastro,
    os.data_inicio_programado,
    os.data_termino_programado,
    os.data_inicio_executado,
    os.data_termino_executado,
    extract(hour from (os.data_termino_programado - os.data_inicio_programado)) as prazo,
    os.id_cliente_servico,
    initcap(tos.descricao) as tipo_os,
    initcap(ci.nome) as cidade,
    initcap(u.name) as tecnico,
    u.id as tecnico_id,
    (
        select initcap(osm.mensagem) as ultima_mensagem
        from ordem_servico_mensagem osm
        where osm.id_ordem_servico = os.id_ordem_servico and osm.deleted_at is null
        order by osm.data_cadastro desc
        limit 1
    )
from
    ordem_servico os
left join
    tipo_ordem_servico tos on os.id_tipo_ordem_servico = tos.id_tipo_ordem_servico
left join
    cliente_servico_endereco cse on os.id_cliente_servico = cse.id_cliente_servico
left join
    endereco_numero en on cse.id_endereco_numero = en.id_endereco_numero
left join
    cidade ci on en.id_cidade = ci.id_cidade
left join
    ordem_servico_tecnico ost on os.id_ordem_servico = ost.id_ordem_servico
left join
    users u on ost.id_usuario = u.id
where
    os.data_inicio_programado >= current_date - interval '20 days'
    and cse.tipo = 'instalacao'
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        return []

def inserir_na_tabela_tecnicos_ordemservico_tecnicos(conn, ordemservico_id, tecnico_id):
    print(f"Inserindo/atualizando vínculo OS {ordemservico_id} <-> Técnico {tecnico_id}...")
    """
    Insere ou atualiza um vínculo entre a ordem de serviço e o técnico na tabela tecnicos_ordemservico_tecnicos.
    """
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO tecnicos_ordemservico_tecnicos (ordemservico_id, tecnico_id)
            VALUES (%s, %s)
            ON CONFLICT (ordemservico_id) DO UPDATE SET
                tecnico_id = EXCLUDED.tecnico_id;
            """
            cursor.execute(sql, (ordemservico_id, tecnico_id))
        conn.commit()
        print(f"Vínculo OS {ordemservico_id} <-> Técnico {tecnico_id} inserido/atualizado com sucesso.")
    except Exception as e:
        print(f"Erro ao inserir/atualizar vínculo OS {ordemservico_id} <-> Técnico {tecnico_id}: {e}")
        conn.rollback() 

def inserir_na_tabela_tecnicos_ordemservico(
    conn,
    id_ordem_servico,
    numero_ordem_servico,
    data_cadastro,
    data_inicio_programado,
    data_termino_programado,
    data_inicio_executado,
    data_termino_executado,
    prazo,
    id_cliente_servico,
    tipo_os,
    cidade,
    ultima_mensagem,
    status
):
    """
    Função para inserir dados na tabela tecnicos_ordemservico.

    Parâmetros:
        conn: Conexão com o banco de dados.
        id_ordem_servico (str): ID da ordem de serviço.
        numero_ordem_servico (str): Número da ordem de serviço.
        data_cadastro (datetime): Data de cadastro da ordem de serviço.
        data_inicio_programado (datetime): Data de início programado.
        data_termino_programado (datetime): Data de término programado.
        data_inicio_executado (datetime): Data de início executado.
        data_termino_executado (datetime): Data de término executado.
        prazo (float): Prazo em horas (será convertido para intervalo).
        id_cliente_servico (str): ID do cliente/serviço.
        tipo_os (str): Tipo da ordem de serviço.
        cidade (str): Cidade da ordem de serviço.
        ultima_mensagem (str): Última mensagem associada à ordem de serviço.
    """
    query = sql.SQL("""
        INSERT INTO tecnicos_ordemservico (
            id_ordem_servico, numero_ordem_servico, data_cadastro, data_inicio_programado,
            data_termino_programado, data_inicio_executado, data_termino_executado,
            prazo, id_cliente_servico, tipo_os, cidade, ultima_mensagem, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, make_interval(hours => %s), %s, %s, %s, %s, %s)
        ON CONFLICT (id_ordem_servico) DO UPDATE SET
            numero_ordem_servico = EXCLUDED.numero_ordem_servico,
            data_cadastro = EXCLUDED.data_cadastro,
            data_inicio_programado = EXCLUDED.data_inicio_programado,
            data_termino_programado = EXCLUDED.data_termino_programado,
            data_inicio_executado = EXCLUDED.data_inicio_executado,
            data_termino_executado = EXCLUDED.data_termino_executado,
            prazo = EXCLUDED.prazo,
            id_cliente_servico = EXCLUDED.id_cliente_servico,
            tipo_os = EXCLUDED.tipo_os,
            cidade = EXCLUDED.cidade,
            ultima_mensagem = EXCLUDED.ultima_mensagem,
            status = EXCLUDED.status;
    """)
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, (
            id_ordem_servico, numero_ordem_servico, data_cadastro, data_inicio_programado,
            data_termino_programado, data_inicio_executado, data_termino_executado,
            prazo, id_cliente_servico, tipo_os, cidade, ultima_mensagem, status
        ))
        conn.commit()
        print(f"Dados da ordem de serviço {id_ordem_servico} inseridos/atualizados com sucesso.")
    except Exception as e:
        print(f"Erro ao inserir/atualizar na tabela tecnicos_ordemservico: {e}")
        conn.rollback()
    finally:
        cursor.close()


def fetch_ordens_servico_tecinfo(conn, id_ordem):
    query = """
    select
    id
    from tecnicos_ordemservico
    where id_ordem_servico = %s
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, (id_ordem,))  # Passando o parâmetro como tupla
        return cursor.fetchall()
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        return []



# Função principal para transferir os dados
def transfer_data():
    # Conectar aos bancos
    conn_hubsoft = connect_to_db(DB_CONFIG_HUBSOFT)
    conn_tecinfo = connect_to_db(DB_CONFIG_TECINFO)

    if conn_hubsoft and conn_tecinfo:
        # Buscar ordens de serviço do banco HubSoft
        ordens_servico = fetch_ordens_servico(conn_hubsoft)
        #fetch_ordens_servico_tecinfo(conn_tecinfo, str(ordens_servico[0][0]))[0][0]
        if ordens_servico:
            # Preencher as tabelas no banco TecInfo
            
            inserir_na_tabela_tecnicos_ordemservico(conn_tecinfo, ordens_servico[0][0], ordens_servico[0][1], ordens_servico[0][2], ordens_servico[0][3], ordens_servico[0][4], ordens_servico[0][5], ordens_servico[0][6], int(ordens_servico[0][7]), ordens_servico[0][8], ordens_servico[0][9], ordens_servico[0][10], ordens_servico[0][13])
            inserir_na_tabela_tecnicos_ordemservico_tecnicos(conn_tecinfo,ordens_servico[0][0], ordens_servico[0][12])
            
            return print('id_ordem_servico: ',ordens_servico[0][0] , '\nnumero_ordem_servico: ',ordens_servico[0][1], '\ndata_cadastro: ',ordens_servico[0][2], '\ndata_inicio_programado: ',ordens_servico[0][3], '\ndata_termino_programado: ',ordens_servico[0][4], '\ndata_inicio_executado: ',ordens_servico[0][5], '\ndata_termino_executado: ',ordens_servico[0][6], '\nprazo: ', int(ordens_servico[0][7]), '\nid_cliente_servico: ',ordens_servico[0][8], '\ntipo_os: ',ordens_servico[0][9], '\ncidade: ',ordens_servico[0][10],'\nultima_mensagem:', ordens_servico[0][13])

        # Fechar conexões
        conn_hubsoft.close()
        conn_tecinfo.close()

# Função principal para transferir os dados
def transfer_data1():
    pendente = 0
    concluido = 0
    andamento = 0

    # Conectar aos bancos
    conn_hubsoft = connect_to_db(DB_CONFIG_HUBSOFT)
    conn_tecinfo = connect_to_db(DB_CONFIG_TECINFO)
    
    if conn_hubsoft and conn_tecinfo:
        # Buscar ordens de serviço do banco HubSoft
        ordens_servico = fetch_ordens_servico(conn_hubsoft)

        if ordens_servico:
            # Iterar sobre todas as ordens de serviço
            for ordem in ordens_servico:
                # Determinar o status baseado nas datas
                if ordem[6] is not None:  # data_termino_executado
                    concluido += 1
                    status = 'Concluída'
                elif ordem[5] is not None:  # data_inicio_executado
                    andamento += 1
                    status = 'Em Andamento'
                else:
                    pendente += 1
                    status = 'Pendente'

                # Inserir dados na tabela tecnicos_ordemservico
                inserir_na_tabela_tecnicos_ordemservico(
                    conn_tecinfo, 
                    ordem[0], ordem[1], ordem[2], ordem[3], ordem[4], 
                    ordem[5], ordem[6], int(ordem[7]), ordem[8], 
                    ordem[9], ordem[10], ordem[13], status
                )

                # Validar tecnico_id antes de inserir
                if ordem[12] is not None:  # Verifica se tecnico_id não é None
                    inserir_na_tabela_tecnicos_ordemservico_tecnicos(
                        conn_tecinfo, 
                        ordem[0], ordem[12]
                    )
                else:
                    print(f"Erro: tecnico_id é None para a OS {ordem[0]}. Vínculo não será criado.")

                # Exibir informações da ordem de serviço
                print('id_ordem_servico: ', ordem[0], 
                      '\nnumero_ordem_servico: ', ordem[1], 
                      '\ndata_cadastro: ', ordem[2], 
                      '\ndata_inicio_programado: ', ordem[3], 
                      '\ndata_termino_programado: ', ordem[4], 
                      '\ndata_inicio_executado: ', ordem[5], 
                      '\ndata_termino_executado: ', ordem[6], 
                      '\nprazo: ', int(ordem[7]), 
                      '\nid_cliente_servico: ', ordem[8], 
                      '\ntipo_os: ', ordem[9], 
                      '\ncidade: ', ordem[10], 
                      '\nultima_mensagem:', ordem[13],
                      '\nstatus:', status
                      )
                print('Pendente: ', pendente, 'Concluído: ', concluido, 'Em Andamento: ', andamento)
                print('-' * 40)  # Separador entre as ordens de serviço

        # Fechar conexões
        conn_hubsoft.close()
        conn_tecinfo.close()


def consultar_status_tecnico(conn):
    query = """
    SELECT 
    tc.table_name AS Tabela,
    kcu.column_name AS Coluna,
    CASE 
        WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'Chave Primária'
        WHEN tc.constraint_type = 'FOREIGN KEY' THEN 'Chave Estrangeira'
        ELSE 'Outro'
    END AS Tipo_Chave
FROM 
    information_schema.table_constraints AS tc
JOIN 
    information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE 
    tc.table_schema = 'public' -- ou outro schema se necessário
    AND (tc.constraint_type = 'PRIMARY KEY' OR tc.constraint_type = 'FOREIGN KEY')
ORDER BY 
    tc.table_name, kcu.column_name;

SELECT 
    g.name AS grupo_permissao,
    e.horario_inicio_expediente,
    e.horario_fim_expediente,
    STRING_AGG(ds.nome, ', ') AS dias_semana,  -- Concatena os dias da semana
    t.nome AS tecnico,
    t.status AS status_tecnico
FROM 
    auth_group g
JOIN 
    tecnicos_expediente e ON g.id = e.grupo_permissao_id
JOIN 
    tecnicos_expediente_dias_semana eds ON e.id = eds.expediente_id
JOIN 
    tecnicos_diasemana ds ON eds.diasemana_id = ds.id
JOIN 
    tecnicos_tecnico_grupos tg ON g.id = tg.group_id
JOIN 
    tecnicos_tecnico t ON tg.tecnico_id = t.id
GROUP BY 
    g.name, e.horario_inicio_expediente, e.horario_fim_expediente, t.nome, t.status
ORDER BY 
    g.name, t.nome;


SELECT 
    g.name AS grupo_permissao,
    e.horario_inicio_expediente,
    e.horario_fim_expediente,
    STRING_AGG(ds.nome, ', ') AS dias_semana,  -- Concatena os dias da semana
    t.nome AS tecnico,
    t.status AS status_tecnico,
    COALESCE(
        JSON_AGG(
            CASE 
                WHEN os.status = 'Em Andamento' THEN
                    JSON_BUILD_OBJECT(
                        'id_os', os.id_ordem_servico ,
                        'status', os.status
                    )
                ELSE null
            END
        ) FILTER (WHERE os.status IS NOT NULL), '[]'
    ) AS ordens_servico  -- Agrega as OS em formato JSON
FROM 
    auth_group g
JOIN 
    tecnicos_expediente e ON g.id = e.grupo_permissao_id
JOIN 
    tecnicos_expediente_dias_semana eds ON e.id = eds.expediente_id
JOIN 
    tecnicos_diasemana ds ON eds.diasemana_id = ds.id
JOIN 
    tecnicos_tecnico_grupos tg ON g.id = tg.group_id
JOIN 
    tecnicos_tecnico t ON tg.tecnico_id = t.id
LEFT JOIN 
    tecnicos_ordemservico_tecnicos ot ON t.id = ot.tecnico_id
LEFT JOIN 
    tecnicos_ordemservico os ON ot.ordemservico_id = os.id_ordem_servico
GROUP BY 
    g.name, e.horario_inicio_expediente, e.horario_fim_expediente, t.nome, t.status
ORDER BY 
    g.name, t.nome;
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        return []
def atualizar_status_tecnico(conn, status):
    """
    Atualiza o status de todos os técnicos na tabela.

    :param conn: Conexão com o banco de dados.
    :param status: Novo status a ser atribuído (ex: "Em Atividade", "Fora Expediente", "Disponível", ).
    """
    query = """
    UPDATE tecnicos_tecnico
    SET status = %s
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, (status,))  # Passa o status como parâmetro
        conn.commit()  # Confirma a transação
        print(f"Status dos técnicos atualizado para '{status}' com sucesso!")
    except Exception as e:
        print(f"Erro ao atualizar o status dos técnicos: {e}")
        conn.rollback()  # Reverte a transação em caso de erro



def atualizar_status_tecnicos_com_regras(conn):
    """
    Atualiza o status dos técnicos com base nas regras fornecidas:
    - Se o técnico tem alguma OS em andamento: "Em Atividade".
    - Se o técnico só tem OS pendentes ou concluídas e está no horário de expediente: "Disponível".
    - Se o técnico está fora do horário e dia de expediente: "Fora Expediente".
    - Se o técnico não tem horário ou dias de expediente definidos: "Horário Indefinido".
    Atualiza o campo ultima_atualizacao_status apenas quando o status é alterado.
    """
    # Obter a data e hora atuais
    agora = datetime.now()
    dia_semana_atual = agora.strftime("%A")  # Dia da semana atual em inglês
    horario_atual = agora.time()  # Horário atual

    # Mapeamento de dias da semana em português para inglês
    dias_semana_map = {
        "Domingo": "Sunday",
        "Segunda-feira": "Monday",
        "Terça-feira": "Tuesday",
        "Quarta-feira": "Wednesday",
        "Quinta-feira": "Thursday",
        "Sexta-feira": "Friday",
        "Sábado": "Saturday",
    }

    # Query para buscar técnicos e suas OS
    query = """
    SELECT 
        t.id,
        t.nome,
        t.status,
        t.ultima_atualizacao_status,
        e.horario_inicio_expediente,
        e.horario_fim_expediente,
        STRING_AGG(DISTINCT ds.nome, ', ') AS dias_semana,  -- Remover duplicatas aqui
        COUNT(os.id_ordem_servico) FILTER (WHERE os.data_termino_executado IS NULL) AS os_pendentes,
        COUNT(os.id_ordem_servico) FILTER (WHERE os.data_termino_executado IS NOT NULL) AS os_concluidas,
        COUNT(os.id_ordem_servico) FILTER (WHERE os.status = 'Em Andamento') AS os_em_andamento
    FROM 
        tecnicos_tecnico t
    LEFT JOIN 
        tecnicos_tecnico_grupos tg ON t.id = tg.tecnico_id
    LEFT JOIN 
        tecnicos_expediente e ON tg.group_id = e.grupo_permissao_id
    LEFT JOIN 
        tecnicos_expediente_dias_semana eds ON e.id = eds.expediente_id
    LEFT JOIN 
        tecnicos_diasemana ds ON eds.diasemana_id = ds.id
    LEFT JOIN 
        tecnicos_ordemservico_tecnicos ot ON t.id = ot.tecnico_id
    LEFT JOIN 
        tecnicos_ordemservico os ON ot.ordemservico_id = os.id_ordem_servico
    GROUP BY 
        t.id, e.horario_inicio_expediente, e.horario_fim_expediente
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        tecnicos = cursor.fetchall()

        for tecnico in tecnicos:
            (
                tecnico_id,
                nome,
                status_atual,
                ultima_atualizacao_status,
                horario_inicio,
                horario_fim,
                dias_semana,
                os_pendentes,
                os_concluidas,
                os_em_andamento,
            ) = tecnico

            # Verificar se o técnico tem horário e dias de expediente definidos
            if not dias_semana or not horario_inicio or not horario_fim:
                novo_status = "Horário Indefinido"
            else:
                # Verificar se o técnico está dentro do horário de expediente
                dias_trabalho = [dias_semana_map[dia.strip()] for dia in dias_semana.split(",")]
                dentro_expediente = (dia_semana_atual in dias_trabalho) and (horario_inicio <= horario_atual <= horario_fim)

                # Definir o status com base nas regras
                if os_em_andamento > 0:
                    novo_status = "Em Atividade"
                elif os_pendentes > 0 or os_concluidas > 0:
                    novo_status = "Disponível" if dentro_expediente else "Fora Expediente"
                else:
                    novo_status = "Disponível" if dentro_expediente else "Fora Expediente"

            # Adicionando impressão da informação se está dentro do horário e dia
            print(f"Técnico: {nome} (ID: {tecnico_id}) - Dentro do horário de expediente: {'Sim' if dentro_expediente else 'Não'}")

            # Print para avaliar o status
            print(f"Técnico: {nome} (ID: {tecnico_id}) - Status Atual: {status_atual} | Novo Status: {novo_status} | Dia Atual: {dia_semana_atual} | Horário de Início: {horario_inicio} | Horário de Fim: {horario_fim} | Dias em Expediente: {dias_semana}")

            # Atualizar o status do técnico e o campo ultima_atualizacao_status apenas se o status mudar
            if status_atual != novo_status and status_atual != "Ajudante":
                # Atualizar o status e o campo ultima_atualizacao_status
                query_atualizacao = """
                UPDATE tecnicos_tecnico
                SET status = %s, ultima_atualizacao_status = %s
                WHERE id = %s
                """
                cursor.execute(query_atualizacao, (novo_status, agora, tecnico_id))
                conn.commit()
                print(f"Status do técnico {nome} (ID: {tecnico_id}) atualizado para {novo_status}.")

        print("Status dos técnicos atualizados com base nas regras.")
    except Exception as e:
        print(f"Erro ao atualizar o status dos técnicos: {e}")
        conn.rollback()

def atualizar_status_tecnico(conn, status, tecnico_id=None):
    """
    Atualiza o status de um técnico específico ou de todos os técnicos.

    :param conn: Conexão com o banco de dados.
    :param status: Novo status a ser atribuído.
    :param tecnico_id: ID do técnico (opcional). Se None, atualiza todos os técnicos.
    """
    query = """
    UPDATE tecnicos_tecnico
    SET status = %s
    """
    if tecnico_id:
        query += " WHERE id = %s"
        params = (status, tecnico_id)
    else:
        params = (status,)

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        print(f"Status do técnico {tecnico_id} atualizado para '{status}'." if tecnico_id else f"Status de todos os técnicos atualizado para '{status}'.")
    except Exception as e:
        print(f"Erro ao atualizar o status do técnico: {e}")
        conn.rollback()
        
if __name__ == "__main__":
    while True:
        try:
            conn_tecinfo = connect_to_db(DB_CONFIG_TECINFO)
            
            transfer_data1()
            time.sleep(2)
            atualizar_status_tecnicos_com_regras(conn_tecinfo)
            time.sleep(28)
            
            conn_tecinfo.close()
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            time.sleep(10)  # Espera antes de tentar novamente
    
