# AEGIS | CitizenTech

**FIAP · Global Solution 2026.2**

## Integrantes

| Nome | RM |
| --- | --- |
| Enzo Fernandes Ramos | 563705 |
| Felipe Henrique de Souza Cerazi | 562746 |
| Gustavo Peaguda de Castro | 562923 |
| Lorenzo Coque | 563385 |

## Visão geral

O **AEGIS** é uma aplicação acadêmica em Python e Streamlit que simula um serviço de prevenção à dengue e acompanhamento de ocorrências ambientais. Um cidadão ou uma empresa pode relatar situações como água parada ou reservatórios abertos. O gestor analisa o relato, decide se é necessário encaminhá-lo e agenda a vistoria. O agente registra o que encontrou e as recomendações. O solicitante pode acompanhar o resultado pelo mesmo código de ocorrência.

O projeto também demonstra duas formas de resolver um problema de planejamento com tempo limitado, **memoização** e **tabulação**, e aplica **grafos** para representar conexões entre locais e encontrar trajetos. Os dados iniciais são fictícios e já vêm carregados. A consulta ao InfoDengue é a fonte externa de dados oficiais.

## Como rodar no PyCharm

**Pré-requisitos:** Git e Python 3.14. Os comandos abaixo foram validados no Windows com PowerShell.

1. Abra o PyCharm, clique em **Clone** ou **Get from VCS** e use a URL do repositório. Se ele estiver privado, entre no GitHub com uma conta autorizada.

   ```text
   https://github.com/jovexdev/GS2_Pythpn_AEGIS.git
   ```

2. Em **Settings → Python → Interpreter**, crie um ambiente virtual chamado `.venv` na pasta do projeto, usando o Python 3.14.
3. No terminal do PyCharm, a partir da pasta que contém `AEGIS.py`, execute:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m streamlit run AEGIS.py
   ```

4. Abra o endereço local no navegador e escolha um perfil. Para encerrar o aplicativo, pressione **Ctrl+C** no terminal. [Abrir o AEGIS em localhost](http://127.0.0.1:8501)

## Funcionalidades implementadas

| Perfil | O que é possível fazer |
| --- | --- |
| **Cidadão** | Registrar e acompanhar ocorrências, montar um plano de prevenção doméstica, explorar trajetos até destinos de saúde, consultar indicadores de dengue e responder a um questionário educativo. |
| **Empresa** | Registrar relatos sobre o estabelecimento, solicitar avaliação ambiental, acompanhar vistorias e comparar duas formas de escolher ações preventivas dentro das horas disponíveis. |
| **Agente** | Consultar as vistorias atribuídas à sua equipe, organizar o turno, explorar a rede de atendimentos e registrar observações e recomendações de uma inspeção. |
| **Gestor** | Analisar relatos, revisar a prioridade, encaminhar ou encerrar ocorrências, designar equipes e comparar planos de vistoria. |

O portal oferece contas de demonstração sem login. Use **Voltar aos perfis** para alternar entre elas na mesma sessão do navegador e acompanhar uma ocorrência do início ao fim. Os relatos e as vistorias simulados ficam em memória durante a sessão.

## Algoritmos abordados

### Memoização e tabulação

O planejamento funciona como um **problema da mochila 0/1**. Cada tarefa ou vistoria tem uma duração e uma pontuação. O algoritmo escolhe a combinação que maximiza a soma dos pontos dentro do tempo disponível, podendo incluir cada item uma vez. No planejamento de vistorias, uma ocorrência **Crítica** vale 5 pontos, **Instável** vale 3 e **OK** vale 1.

- **Memoização (`selecionar_vistorias_memo`)** percorre as opções recursivamente. Para cada item, compara ignorá-lo com incluí-lo, se ele couber no tempo restante. Um dicionário guarda os resultados pela chave `(índice do item, tempo restante)` para reutilizar subproblemas já calculados.
- **Tabulação (`selecionar_vistorias_tabela`)** preenche uma matriz de baixo para cima. A célula `tabela[i][h]` guarda a melhor pontuação possível considerando os itens a partir do índice `i` e a capacidade `h`. Ao final, o algoritmo percorre a matriz para recuperar os itens selecionados.

As duas versões usam o mesmo critério de desempate. A interface mostra os itens escolhidos, o tempo usado e a pontuação. Nas telas de comparação da **Empresa** e do **Gestor**, também é possível abrir a matriz de tabulação. O planejador do **Cidadão** usa blocos de cinco minutos para reutilizar o mesmo algoritmo de seleção.

### Grafos, BFS e DFS

O grafo é representado por **listas de adjacência**. Cada vértice guarda os pontos aos quais está conectado. A **BFS**, ou busca em largura, usa uma fila e percorre a rede por níveis. Como as conexões têm o mesmo peso, o primeiro caminho que chega ao destino tem o menor número de trechos. A **DFS**, ou busca em profundidade, usa uma pilha e mostra outra ordem de visita aos pontos.

Em **Cidadão → Rede de regiões**, a residência é a origem fixa. Ao selecionar **Hospital Municipal**, por exemplo, a interface destaca **Residência do cidadão → UBS do Bairro → UPA Regional → Hospital Municipal**, com três trechos. A rede é fictícia e o cálculo usa o número de conexões. O **NetworkX** posiciona os vértices, o **Plotly** desenha o grafo e a implementação da busca está no `Backend.py`.

## Integração com o InfoDengue

Em **Cidadão → Indicadores de dengue**, o usuário escolhe o ano e consulta a série semanal de casos estimados para o município de São Paulo. A função `consultar_infodengue` tenta obter registros válidos em JSON e, se o JSON não produzir uma série válida, tenta o formato CSV. A interface apresenta os dados em gráfico e tabela.

A consulta requer internet. Se houver falha, a tela informa o erro e permite abrir uma série identificada como fictícia pelo botão **Exibir dados demonstrativos**.

## Organização do código

| Arquivo | Responsabilidade |
| --- | --- |
| [`AEGIS.py`](AEGIS.py) | Interface Streamlit, navegação por perfil, formulários, tabelas e visualização dos grafos. |
| [`Backend.py`](Backend.py) | Dados de demonstração, classificação de relatos, fluxo de vistorias, algoritmos de programação dinâmica, buscas em grafos e integração com o InfoDengue. |
| [`requirements.txt`](requirements.txt) | Dependências usadas para instalar e executar o aplicativo. |
| [`.streamlit/config.toml`](.streamlit/config.toml) | Tema visual e configuração do servidor local. |
