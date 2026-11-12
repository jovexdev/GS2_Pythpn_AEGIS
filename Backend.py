"""AEGIS — dados demonstrativos, regras operacionais, algoritmos e API pública."""

from collections import deque
from datetime import date, timedelta
import csv
import io
import requests

PERFIS = ("Cidadão", "Empresa", "Agente", "Gestor")
FATORES = {
    "agua_parada": "Água parada",
    "recipientes_expostos": "Recipientes expostos",
    "reservatorio_aberto": "Reservatório aberto",
    "recorrencia": "Problema recorrente",
}
PONTOS = {"Crítica": 5, "Instável": 3, "OK": 1}
FINALIZADAS = ("Concluída", "Encerrada")


def classificar(fatores):
    """Regra demonstrativa, baseada SOMENTE nos fatores declarados."""
    pesos = {"agua_parada": 2, "recipientes_expostos": 2,
             "reservatorio_aberto": 3, "recorrencia": 1}
    total = sum(pesos[chave] for chave in pesos if fatores.get(chave))
    nivel = "Crítica" if total >= 5 else "Instável" if total >= 2 else "OK"
    presentes = [rotulo for chave, rotulo in FATORES.items() if fatores.get(chave)]
    motivo = ", ".join(presentes) if presentes else "Nenhum fator relevante declarado"
    return nivel, motivo


def criar_dados():
    """Cria a base fictícia inicial; modificações ficam na sessão Streamlit."""
    cidadaos = [
        {"id": "CID-01", "nome": "Mariana Oliveira", "bairro": "Vila Mariana"},
        {"id": "CID-02", "nome": "Lucas Ferreira", "bairro": "Santana"},
        {"id": "CID-03", "nome": "Ana Ribeiro", "bairro": "Mooca"},
    ]
    empresas = [
        {"id": "EMP-01", "nome": "Almeida Distribuição (fictícia)",
         "responsavel": "Ricardo Almeida", "cnpj": "00.000.000/0001-01",
         "bairro": "Lapa", "endereco": "Rua Exemplo, 100", "atividade": "Logística",
         "instalacoes": "Galpão, pátio de carga, depósitos e reservatórios"},
        {"id": "EMP-02", "nome": "Centro Logístico Aurora (fictícia)",
         "responsavel": "Fernanda Costa", "cnpj": "00.000.000/0001-02",
         "bairro": "Tatuapé", "endereco": "Av. Exemplo, 200", "atividade": "Armazenagem",
         "instalacoes": "Depósito, docas, área externa de cargas"},
        {"id": "EMP-03", "nome": "Mercado Horizonte (fictícia)",
         "responsavel": "João Martins", "cnpj": "00.000.000/0001-03",
         "bairro": "Ipiranga", "endereco": "Rua Exemplo, 300", "atividade": "Comércio",
         "instalacoes": "Loja, estoque e área de recebimento"},
    ]
    equipes = [
        {"id": "EQ-01", "nome": "Equipe Norte", "agente": "Camila Rocha"},
        {"id": "EQ-02", "nome": "Equipe Sul", "agente": "Pedro Lima"},
        {"id": "EQ-03", "nome": "Equipe Leste", "agente": "Beatriz Santos"},
        {"id": "EQ-04", "nome": "Equipe Oeste", "agente": "Gabriel Souza"},
    ]
    # Rede fictícia de setores e conexões usadas na análise de grafos.
    grafo = {
        "Centro de Operações": ["Consolação", "Sé", "Vila Mariana"],
        "Consolação": ["Centro de Operações", "Pinheiros", "Lapa"],
        "Sé": ["Centro de Operações", "Mooca", "Cambuci", "Santana"],
        "Vila Mariana": ["Centro de Operações", "Ipiranga", "Santo Amaro"],
        "Pinheiros": ["Consolação", "Butantã", "Itaim Bibi"],
        "Lapa": ["Consolação", "Butantã"],
        "Mooca": ["Sé", "Tatuapé", "Ipiranga"],
        "Cambuci": ["Sé", "Ipiranga"],
        "Santana": ["Sé", "Tatuapé"],
        "Ipiranga": ["Vila Mariana", "Mooca", "Cambuci"],
        "Santo Amaro": ["Vila Mariana", "Itaim Bibi"],
        "Butantã": ["Pinheiros", "Lapa"],
        "Itaim Bibi": ["Pinheiros", "Santo Amaro"],
        "Tatuapé": ["Mooca", "Santana"],
    }

    base = [
        ("EMP-01", "Lapa", "Pneus e embalagens com água no pátio", "1101", 4, "Recebida"),
        ("CID-01", "Vila Mariana", "Recipientes expostos à chuva em terreno", "0100", 2, "Recebida"),
        ("EMP-02", "Tatuapé", "Reservatório aberto na área de cargas", "1011", 3, "Pendente"),
        ("CID-02", "Santana", "Vasilhas descobertas em área compartilhada", "0100", 2, "Recebida"),
        ("EMP-03", "Ipiranga", "Inspeção preventiva sem problemas declarados", "0000", 1, "Recebida"),
        ("CID-03", "Mooca", "Caixa d'água destampada e poças", "1011", 3, "Pendente"),
        ("EMP-01", "Lapa", "Materiais armazenados ao ar livre", "0100", 2, "Pendente"),
        ("CID-01", "Vila Mariana", "Água acumulada no quintal", "1000", 1, "Pendente"),
        ("EMP-02", "Tatuapé", "Embalagens com água no pátio externo", "1101", 4, "Pendente"),
        ("CID-02", "Santana", "Barril sem tampa em área comum", "0010", 3, "Agendada"),
        ("EMP-03", "Ipiranga", "Depósito com recipientes expostos", "1100", 3, "Em andamento"),
        ("CID-03", "Mooca", "Entulho e poças após chuvas", "1101", 2, "Em andamento"),
        ("EMP-01", "Lapa", "Reservatório já inspecionado", "0010", 2, "Concluída"),
        ("CID-01", "Vila Mariana", "Recipientes inspecionados pela equipe", "0100", 1, "Concluída"),
        # Vistorias adicionais já atribuídas para demonstrar a memoização do Agente.
        ("EMP-02", "Tatuapé", "Calhas externas com água após chuva", "1101", 2, "Agendada"),
        ("CID-01", "Vila Mariana", "Reservatório sem tampa em área externa", "1011", 3, "Agendada"),
        ("EMP-01", "Lapa", "Pátio de cargas com resíduos e recipientes", "1101", 4, "Agendada"),
        ("CID-03", "Mooca", "Vasilhas expostas junto à calçada", "0100", 1, "Agendada"),
        ("EMP-03", "Ipiranga", "Reservatório descoberto próximo ao estoque", "1011", 3, "Agendada"),
        ("EMP-02", "Tatuapé", "Acúmulo de água nas docas", "1101", 2, "Agendada"),
    ]
    ocorrencias = []
    for numero, (dono, bairro, relato, marcas, horas, status) in enumerate(base, 1):
        fatores = {chave: int(marca) for chave, marca in zip(FATORES, marcas)}
        nivel, motivo = classificar(fatores)
        ocorrencias.append({
            "id": f"OC-{numero:03d}", "dono": dono,
            "tipo": "Empresa" if dono.startswith("EMP") else "Cidadão",
            "bairro": bairro, "relato": relato, "fatores": fatores,
            "classificacao": nivel, "motivo": motivo, "horas": horas,
            "status": status, "data": f"2026-11-{min(numero + 1, 12):02d}",
            "historico": ["Ocorrência registrada (dado fictício)."],
        })
    vistorias = [
        {"id": "VIS-001", "ocorrencia": "OC-010", "equipe": "EQ-03",
         "data": "2026-11-14", "status": "Agendada", "inspecao": "", "recomendacoes": ""},
        {"id": "VIS-002", "ocorrencia": "OC-011", "equipe": "EQ-01",
         "data": "2026-11-12", "status": "Em andamento", "inspecao": "", "recomendacoes": ""},
        {"id": "VIS-003", "ocorrencia": "OC-012", "equipe": "EQ-02",
         "data": "2026-11-12", "status": "Em andamento", "inspecao": "", "recomendacoes": ""},
        {"id": "VIS-004", "ocorrencia": "OC-013", "equipe": "EQ-03",
         "data": "2026-11-05", "status": "Concluída",
         "inspecao": "Reservatório avaliado em simulação.",
         "recomendacoes": "Manter a cobertura e revisar a vedação."},
        {"id": "VIS-005", "ocorrencia": "OC-014", "equipe": "EQ-01",
         "data": "2026-11-03", "status": "Concluída",
         "inspecao": "Recipientes removidos (simulação).",
         "recomendacoes": "Manter inspeções periódicas."},
        {"id": "VIS-006", "ocorrencia": "OC-015", "equipe": "EQ-01",
         "data": "2026-11-15", "status": "Agendada", "inspecao": "", "recomendacoes": ""},
        {"id": "VIS-007", "ocorrencia": "OC-016", "equipe": "EQ-01",
         "data": "2026-11-16", "status": "Agendada", "inspecao": "", "recomendacoes": ""},
        {"id": "VIS-008", "ocorrencia": "OC-017", "equipe": "EQ-01",
         "data": "2026-11-17", "status": "Agendada", "inspecao": "", "recomendacoes": ""},
        {"id": "VIS-009", "ocorrencia": "OC-018", "equipe": "EQ-02",
         "data": "2026-11-15", "status": "Agendada", "inspecao": "", "recomendacoes": ""},
        {"id": "VIS-010", "ocorrencia": "OC-019", "equipe": "EQ-02",
         "data": "2026-11-16", "status": "Agendada", "inspecao": "", "recomendacoes": ""},
        {"id": "VIS-011", "ocorrencia": "OC-020", "equipe": "EQ-03",
         "data": "2026-11-18", "status": "Agendada", "inspecao": "", "recomendacoes": ""},
    ]
    diario = {
        "CID-01": {
            "2026-11-08": ["Vasos", "Ralos"],
            "2026-11-10": ["Calhas", "Caixa-d'água"],
            "2026-11-11": ["Vasos", "Ralos", "Quintal"],
        }, "CID-02": {"2026-11-11": ["Vasos"]}, "CID-03": {},
    }
    return {
        "cidadaos": cidadaos, "empresas": empresas, "equipes": equipes,
        "ocorrencias": ocorrencias, "vistorias": vistorias, "grafo": grafo,
        "diario": diario,
        "serie_demo": [
            {"semana": i + 1, "casos": valor, "fonte": "Simulação"}
            for i, valor in enumerate([140, 150, 162, 181, 206, 196, 231, 252, 244, 262, 250, 238])
        ],
    }


def buscar_ocorrencia(dados, codigo):
    return next((o for o in dados["ocorrencias"] if o["id"] == codigo), None)


def buscar_vistoria(dados, codigo):
    return next((v for v in dados["vistorias"] if v["id"] == codigo), None)


def equipe_livre(dados, codigo):
    return not any(v["equipe"] == codigo and v["status"] != "Concluída"
                   for v in dados["vistorias"])


def minhas_ocorrencias(dados, id_usuario):
    return [o for o in dados["ocorrencias"] if o["dono"] == id_usuario]


def minhas_vistorias(dados, id_equipe):
    return [v for v in dados["vistorias"] if v["equipe"] == id_equipe]


def registrar_ocorrencia(dados, dono, bairro, relato, fatores, horas=2):
    if not relato.strip():
        raise ValueError("Descreva a ocorrência.")
    todos = {**{chave: 0 for chave in FATORES}, **fatores}
    nivel, motivo = classificar(todos)
    usados = [int(o["id"].split("-")[-1]) for o in dados["ocorrencias"]]
    codigo = f"OC-{max(usados, default=0) + 1:03d}"
    tipo = "Empresa" if dono.startswith("EMP") else "Cidadão"
    novo = {"id": codigo, "dono": dono, "tipo": tipo, "bairro": bairro,
            "relato": relato.strip(), "fatores": todos, "classificacao": nivel,
            "motivo": motivo, "horas": int(horas), "status": "Recebida",
            "data": date.today().isoformat(),
            "historico": ["Ocorrência registrada pelo perfil de demonstração."]}
    dados["ocorrencias"].append(novo)
    return novo


def solicitar_vistoria(dados, codigo, id_empresa):
    """Permite a empresa solicitar avaliação de um relato próprio ainda recebido."""
    ocorrencia = buscar_ocorrencia(dados, codigo)
    if not ocorrencia or ocorrencia["dono"] != id_empresa or ocorrencia["tipo"] != "Empresa":
        raise ValueError("Esta solicitação não pertence à empresa selecionada.")
    if ocorrencia["status"] != "Recebida" or ocorrencia.get("vistoria_solicitada"):
        raise ValueError("Esta solicitação já foi encaminhada ou registrada.")
    ocorrencia["vistoria_solicitada"] = True
    ocorrencia["historico"].append("Empresa solicitou avaliação ambiental.")


def encaminhar_ocorrencia(dados, codigo, encerrar=False):
    ocorrencia = buscar_ocorrencia(dados, codigo)
    if not ocorrencia or ocorrencia["status"] != "Recebida":
        raise ValueError("Esta ocorrência não está aguardando análise.")
    ocorrencia["status"] = "Encerrada" if encerrar else "Pendente"
    ocorrencia["historico"].append("Gestor encerrou o relato sem vistoria." if encerrar
                                    else "Gestor encaminhou a solicitação para vistoria.")


def revisar_prioridade(dados, codigo, prioridade):
    ocorrencia = buscar_ocorrencia(dados, codigo)
    if not ocorrencia or ocorrencia["status"] not in ("Recebida", "Pendente"):
        raise ValueError("Não é possível revisar esta ocorrência neste estado.")
    if prioridade not in PONTOS:
        raise ValueError("Prioridade inválida.")
    ocorrencia["classificacao"] = prioridade
    ocorrencia["historico"].append(f"Gestor revisou a prioridade para {prioridade}.")


def agendar_vistoria(dados, codigo, id_equipe, data):
    ocorrencia = buscar_ocorrencia(dados, codigo)
    if not ocorrencia or ocorrencia["status"] != "Pendente":
        raise ValueError("É necessário encaminhar a ocorrência antes de agendar.")
    if not any(e["id"] == id_equipe for e in dados["equipes"]):
        raise ValueError("Equipe não encontrada.")
    if not equipe_livre(dados, id_equipe):
        raise ValueError("Esta equipe já possui uma vistoria ativa.")
    numeros = [int(v["id"].split("-")[-1]) for v in dados["vistorias"]]
    codigo_vis = f"VIS-{max(numeros, default=0) + 1:03d}"
    vistoria = {"id": codigo_vis, "ocorrencia": codigo, "equipe": id_equipe,
                "data": str(data), "status": "Agendada", "inspecao": "",
                "recomendacoes": ""}
    dados["vistorias"].append(vistoria)
    ocorrencia["status"] = "Agendada"
    ocorrencia["historico"].append(f"Gestor agendou {codigo_vis} para {id_equipe} em {data}.")
    return vistoria


def iniciar_vistoria(dados, codigo, id_equipe):
    vistoria = buscar_vistoria(dados, codigo)
    if not vistoria or vistoria["equipe"] != id_equipe or vistoria["status"] != "Agendada":
        raise ValueError("Vistoria não disponível para iniciar.")
    vistoria["status"] = "Em andamento"
    ocorrencia = buscar_ocorrencia(dados, vistoria["ocorrencia"])
    ocorrencia["status"] = "Em andamento"
    ocorrencia["historico"].append(f"Agente iniciou a vistoria {codigo}.")


def concluir_vistoria(dados, codigo, id_equipe, inspecao, recomendacoes):
    vistoria = buscar_vistoria(dados, codigo)
    if not vistoria or vistoria["equipe"] != id_equipe or vistoria["status"] != "Em andamento":
        raise ValueError("Esta vistoria não pode ser concluída por este agente.")
    if not inspecao.strip():
        raise ValueError("Registre as observações da inspeção.")
    vistoria.update({"status": "Concluída", "inspecao": inspecao.strip(),
                     "recomendacoes": recomendacoes.strip()})
    ocorrencia = buscar_ocorrencia(dados, vistoria["ocorrencia"])
    ocorrencia["status"] = "Concluída"
    ocorrencia["historico"].append(f"Agente concluiu {codigo} e registrou os resultados.")


# =====================================================
# ATIVIDADES FICTÍCIAS PARA OS PERFIS
# Nenhum ponto numérico constitui medida sanitária oficial.
# =====================================================

TAREFAS_CIDADAO = [
    {"id": "PREV-01", "nome": "Verificar vasos e pratinhos", "minutos": 10, "pontos": 3,
     "descricao": "Identificar recipientes que possam acumular água."},
    {"id": "PREV-02", "nome": "Conferir tampas de reservatórios", "minutos": 15, "pontos": 6,
     "descricao": "Verificar se tampas estão bem ajustadas."},
    {"id": "PREV-03", "nome": "Verificar ralos e áreas molhadas", "minutos": 10, "pontos": 4,
     "descricao": "Revisar pontos de possível acúmulo."},
    {"id": "PREV-04", "nome": "Inspecionar recipientes no quintal", "minutos": 20, "pontos": 7,
     "descricao": "Conferir pneus, baldes e outros recipientes."},
    {"id": "PREV-05", "nome": "Verificar calhas acessíveis com segurança", "minutos": 25, "pontos": 5,
     "descricao": "Inspeção visual, sem subir em locais perigosos."},
    {"id": "PREV-06", "nome": "Conferir bebedouros dos animais", "minutos": 5, "pontos": 2,
     "descricao": "Verificar a necessidade de limpeza e troca de água."},
    {"id": "PREV-07", "nome": "Revisar área de serviço", "minutos": 15, "pontos": 4,
     "descricao": "Procurar objetos que possam reter água."},
]

ACOES_EMPRESA = [
    {"id": "EMP-A01", "nome": "Revisar reservatórios e tampas", "horas": 3, "pontos": 8,
     "descricao": "Inspeção preventiva simulada da vedação."},
    {"id": "EMP-A02", "nome": "Verificar calhas e drenagem", "horas": 4, "pontos": 7,
     "descricao": "Verificação de pontos de água acumulada."},
    {"id": "EMP-A03", "nome": "Organizar materiais no pátio", "horas": 2, "pontos": 6,
     "descricao": "Reorganização fictícia de materiais expostos à chuva."},
    {"id": "EMP-A04", "nome": "Inspecionar docas e depósitos", "horas": 2, "pontos": 5,
     "descricao": "Checklist de áreas externas e de estoque."},
    {"id": "EMP-A05", "nome": "Revisar recipientes da manutenção", "horas": 1, "pontos": 3,
     "descricao": "Levantamento de recipientes desprotegidos."},
    {"id": "EMP-A06", "nome": "Fazer verificação preventiva geral", "horas": 3, "pontos": 4,
     "descricao": "Avaliação de rotina do estabelecimento."},
]


def adaptar_atividades(atividades, campo_tempo="horas", unidade=1):
    """Converte atividades em itens do problema de seleção com capacidade limitada.

    'horas' é o campo interno de capacidade da função original. Para tarefas
    domésticas, cada unidade representa cinco minutos, e NÃO uma hora.
    """
    if unidade <= 0:
        raise ValueError("A unidade de tempo deve ser positiva.")
    adaptadas = []
    for tarefa in atividades:
        tempo = tarefa[campo_tempo]
        if not isinstance(tempo, int) or tempo <= 0 or tempo % unidade != 0:
            raise ValueError("Todos os tempos devem ser inteiros positivos e divisíveis pela unidade.")
        item = tarefa.copy()
        item["horas"] = tempo // unidade
        adaptadas.append(item)
    return adaptadas


# =====================================================
# ALGORITMOS DE PROGRAMAÇÃO DINÂMICA E GRAFOS
# =====================================================


def preparar_para_planejamento(ocorrencias):
    """Organiza as ocorrências para a seleção por pontos e capacidade de horas.

    Não modifica as ocorrências originais nem recalcula prioridades.
    """
    resultado = []
    for ocorrencia in ocorrencias:
        copia = ocorrencia.copy()
        copia["pontos"] = PONTOS[ocorrencia["classificacao"]]
        resultado.append(copia)
    return resultado


# =========================================================
# 3. PROGRAMAÇÃO DINÂMICA — MEMOIZAÇÃO (TOP-DOWN)
# =========================================================


def selecionar_vistorias_memo(ocorrencias, capacidade):
    """Seleciona subconjunto de ocorrências com maior soma de prioridades.

    Capacidade e durações são inteiros em horas. Cada ocorrência entra
    no máximo uma vez. O deslocamento NÃO está incluído no tempo.
    """
    if capacidade < 0:
        raise ValueError("A capacidade precisa ser maior ou igual a zero.")

    quantidade = len(ocorrencias)
    memoria = {}
    chamadas = 0
    acertos_cache = 0

    def calcular(indice, horas_restantes):
        nonlocal chamadas, acertos_cache
        chamadas += 1
        chave = (indice, horas_restantes)

        # Se já calculamos este subproblema, reutilizamos o resultado.
        if chave in memoria:
            acertos_cache += 1
            return memoria[chave]

        # Caso base: não há mais ocorrências ou tempo disponível.
        if indice == quantidade or horas_restantes == 0:
            memoria[chave] = (0, ())
            return memoria[chave]

        ocorrencia = ocorrencias[indice]
        valor_sem, ids_sem = calcular(indice + 1, horas_restantes)
        melhor_valor, melhores_ids = valor_sem, ids_sem

        if ocorrencia["horas"] <= horas_restantes:
            valor_com, ids_com = calcular(
                indice + 1, horas_restantes - ocorrencia["horas"]
            )
            valor_com += ocorrencia["pontos"]
            if valor_com > melhor_valor:
                melhor_valor = valor_com
                melhores_ids = (ocorrencia["id"],) + ids_com

        memoria[chave] = (melhor_valor, melhores_ids)
        return memoria[chave]

    valor, ids = calcular(0, int(capacidade))
    horas = sum(o["horas"] for o in ocorrencias if o["id"] in ids)
    return {
        "pontos": valor, "ids": list(ids), "horas": horas,
        "estados": len(memoria), "chamadas": chamadas,
        "reutilizacoes": acertos_cache, "tecnica": "Memoização (Top-Down)",
    }


# =========================================================
# 4. PROGRAMAÇÃO DINÂMICA — TABULAÇÃO (BOTTOM-UP)
# =========================================================


def selecionar_vistorias_tabela(ocorrencias, capacidade):
    """Resolve o mesmo problema da memoização preenchendo uma matriz."""
    if capacidade < 0:
        raise ValueError("A capacidade precisa ser maior ou igual a zero.")

    capacidade = int(capacidade)
    quantidade = len(ocorrencias)
    tabela = [[0] * (capacidade + 1) for _ in range(quantidade + 1)]
    estados = 0

    # Preenche de baixo para cima: tabela[i][h] mostra o melhor resultado
    # possível usando as ocorrências a partir do índice i.
    # Assim, empates seguem exatamente o critério da memoização.
    for i in range(quantidade - 1, -1, -1):
        ocorrencia = ocorrencias[i]
        for h in range(1, capacidade + 1):
            sem_escolher = tabela[i + 1][h]
            melhor = sem_escolher

            if ocorrencia["horas"] <= h:
                com_escolher = ocorrencia["pontos"] + tabela[i + 1][h - ocorrencia["horas"]]
                if com_escolher > melhor:
                    melhor = com_escolher

            tabela[i][h] = melhor
            estados += 1

    # Reconstrói o resultado seguindo as decisões calculadas.
    ids = []
    h = capacidade
    for i in range(quantidade):
        ocorrencia = ocorrencias[i]
        if ocorrencia["horas"] <= h:
            com_escolher = ocorrencia["pontos"] + tabela[i + 1][h - ocorrencia["horas"]]
            sem_escolher = tabela[i + 1][h]
            if com_escolher > sem_escolher:
                ids.append(ocorrencia["id"])
                h -= ocorrencia["horas"]

    horas = sum(o["horas"] for o in ocorrencias if o["id"] in ids)
    return {
        "pontos": tabela[0][capacidade], "ids": ids,
        "horas": horas, "estados": estados, "tabela": tabela,
        "tecnica": "Tabulação (Bottom-Up)",
    }


# =========================================================
# 5. GRAFOS — BFS, DFS E MENOR CAMINHO EM ARESTAS
# =========================================================


def busca_largura(grafo, origem):
    """Percorre grafo com BFS, usando fila (listas de adjacências)."""
    if origem not in grafo:
        return []
    visitados = []
    fila = deque([origem])
    descobertos = {origem}

    while fila:
        atual = fila.popleft()
        visitados.append(atual)
        for vizinho in grafo[atual]:
            if vizinho not in descobertos:
                descobertos.add(vizinho)
                fila.append(vizinho)
    return visitados


def busca_profundidade(grafo, origem):
    """Percorre grafo com DFS, utilizando pilha."""
    if origem not in grafo:
        return []
    visitados = []
    pilha = [origem]
    vistos = set()
    while pilha:
        atual = pilha.pop()
        if atual not in vistos:
            vistos.add(atual)
            visitados.append(atual)
            for vizinho in reversed(grafo[atual]):
                if vizinho not in vistos:
                    pilha.append(vizinho)
    return visitados


def menor_caminho_bfs(grafo, origem, destino):
    """Encontra menor caminho em NÚMERO DE CONEXÕES (sem pesos)."""
    if origem not in grafo or destino not in grafo:
        return []
    fila = deque([[origem]])
    visitados = {origem}

    while fila:
        caminho = fila.popleft()
        atual = caminho[-1]
        if atual == destino:
            return caminho
        for vizinho in grafo[atual]:
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append(caminho + [vizinho])
    return []


# =====================================================
# INFO DENGUE: DADOS SEMANAIS OFICIAIS
# =====================================================

def _numero(valor):
    if valor is None or str(valor).strip().lower() in ("", "nan", "none", "null"):
        return None
    try:
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _interpretar_registros(registros, ano):
    """SE vem como AAAASS (ex.: 202501), não apenas 01."""
    serie = {}
    for item in registros:
        if not isinstance(item, dict):
            continue
        codigo = _numero(item.get("SE", item.get("se", item.get("week"))))
        if codigo is None:
            continue
        codigo = int(codigo)
        ano_item = codigo // 100 if codigo >= 10000 else ano
        semana = codigo % 100 if codigo >= 10000 else codigo
        if ano_item != ano or not 1 <= semana <= 53:
            continue
        casos = _numero(item.get("casos_est"))
        if casos is None:
            casos = _numero(item.get("casos"))
        if casos is None or casos < 0:
            continue
        serie[semana] = {"semana": semana, "casos": round(casos, 1),
                         "fonte": "InfoDengue", "ano": ano}
    return [serie[s] for s in sorted(serie)]


def consultar_infodengue(ano=2025):
    """Consulta a API oficial; não substitui erros por números fictícios."""
    url = "https://info.dengue.mat.br/api/alertcity"
    parametros = {"geocode": 3550308, "disease": "dengue", "format": "json",
                  "ew_start": 1, "ew_end": 53, "ey_start": int(ano), "ey_end": int(ano)}
    try:
        resposta = requests.get(url, params=parametros, timeout=25,
                                headers={"User-Agent": "AEGIS-Academico/1.0"})
        resposta.raise_for_status()
        try:
            conteudo = resposta.json()
        except ValueError:
            conteudo = None
        if isinstance(conteudo, list):
            registros = conteudo
        elif isinstance(conteudo, dict):
            registros = conteudo.get("data", conteudo.get("results", []))
            if isinstance(registros, dict):
                registros = registros.get("data", [])
        else:
            registros = []
        serie = _interpretar_registros(registros, int(ano))
        if serie:
            return serie, f"{len(serie)} semanas oficiais recebidas para {ano}."
        # Segundo formato documentado pela fonte: CSV.
        parametros["format"] = "csv"
        resposta = requests.get(url, params=parametros, timeout=25,
                                headers={"User-Agent": "AEGIS-Academico/1.0"})
        resposta.raise_for_status()
        registros = list(csv.DictReader(io.StringIO(resposta.text.lstrip("\ufeff"))))
        serie = _interpretar_registros(registros, int(ano))
        if serie:
            return serie, f"{len(serie)} semanas oficiais recebidas para {ano} (CSV)."
        return [], ("A consulta foi concluída, mas o InfoDengue não disponibilizou "
                    f"semanas válidas para São Paulo em {ano}. Experimente outro ano.")
    except (requests.RequestException, ValueError, TypeError) as erro:
        return [], f"Não foi possível obter dados oficiais: {type(erro).__name__}."


# =====================================================
# MINHA SAÚDE — QUESTIONÁRIO EDUCATIVO, NÃO DIAGNÓSTICO
# Referência: Ministério da Saúde / dengue, sintomas e sinais de alarme
# https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/d/dengue
# =====================================================

# Cada pergunta contém: (identificador, texto, tipo).
# Mantemos 8 sintomas comuns e 7 sinais de alarme/agravamento.
PERGUNTAS_SAUDE = [
    ("febre", "Teve febre nos últimos sete dias, especialmente de início repentino?", "sintoma"),
    ("cabeca", "Está com dor de cabeça?", "sintoma"),
    ("olhos", "Sente dor atrás dos olhos?", "sintoma"),
    ("musculos", "Está com dores musculares ou no corpo?", "sintoma"),
    ("articulacoes", "Sente dores nas articulações?", "sintoma"),
    ("enjoo", "Sente enjoo ou falta de apetite?", "sintoma"),
    ("manchas", "Apareceram manchas avermelhadas na pele?", "sintoma"),
    ("fraqueza", "Sente cansaço ou fraqueza fora do habitual?", "sintoma"),
    ("abdomen", "Tem dor forte e contínua na barriga?", "alarme"),
    ("vomitos", "Está vomitando repetidamente, sem conseguir melhorar?", "alarme"),
    ("sangramento", "Percebeu sangramento no nariz, gengiva, vômito ou fezes?", "alarme"),
    ("desmaio", "Teve tontura muito forte, desmaio ou sensação de desmaio ao levantar?", "alarme"),
    ("respiracao", "Está com dificuldade para respirar?", "alarme"),
    ("sonolencia", "Apresenta sonolência extrema, confusão ou irritabilidade incomum?", "alarme"),
    ("piora", "Depois que a febre diminuiu, houve piora importante do estado geral?", "alarme"),
]


def avaliar_questionario_saude(respostas):
    """Gera orientação conservadora sobre atendimento, SEM diagnosticar dengue.

    Resultados não estimam probabilidade de infecção ou gravidade clínica.
    """
    opcoes = ("Sim", "Não", "Não sei")
    if not isinstance(respostas, dict):
        raise ValueError("Respostas inválidas.")
    for chave, pergunta, tipo in PERGUNTAS_SAUDE:
        if respostas.get(chave) not in opcoes:
            raise ValueError("Responda às 15 perguntas antes de ver a orientação.")

    alarmes = [pergunta for chave, pergunta, tipo in PERGUNTAS_SAUDE
               if tipo == "alarme" and respostas[chave] == "Sim"]
    alarmes_duvidosos = [pergunta for chave, pergunta, tipo in PERGUNTAS_SAUDE
                        if tipo == "alarme" and respostas[chave] == "Não sei"]
    sintomas = [pergunta for chave, pergunta, tipo in PERGUNTAS_SAUDE
                if tipo == "sintoma" and respostas[chave] == "Sim"]
    duvidas = [pergunta for chave, pergunta, tipo in PERGUNTAS_SAUDE
              if tipo == "sintoma" and respostas[chave] == "Não sei"]

    if alarmes or alarmes_duvidosos:
        return {
            "nivel": "urgencia",
            "titulo": "Procure atendimento de urgência imediatamente",
            "mensagem": ("Foi assinalado um sinal de alarme ou existe dúvida sobre ele. "
                         "Procure avaliação presencial imediata em um serviço de urgência; "
                         "não espere a conclusão do questionário para buscar ajuda."),
            "motivos": alarmes + alarmes_duvidosos,
        }
    if sintomas or duvidas:
        return {
            "nivel": "atendimento",
            "titulo": "Procure uma unidade de saúde para avaliação",
            "mensagem": ("Você relatou sintomas ou incertezas que merecem avaliação profissional "
                         "o quanto antes. O questionário não permite confirmar nem excluir dengue. "
                         "Se aparecer qualquer sinal de alarme, procure urgência imediatamente."),
            "motivos": sintomas + duvidas,
        }
    return {
        "nivel": "observacao",
        "titulo": "Nenhum sintoma ou sinal de alarme foi relatado",
        "mensagem": ("Pelas respostas fornecidas, não foi identificada uma indicação de urgência "
                     "neste momento. Isso NÃO descarta dengue ou outras doenças. "
                     "Se surgirem sintomas, procure uma unidade de saúde; se surgir um sinal "
                     "de alarme, procure urgência imediatamente."),
        "motivos": [],
    }
