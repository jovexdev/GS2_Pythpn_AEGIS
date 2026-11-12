# AEGIS | CitizenTech

Projeto acadêmico da FIAP, Global Solution 2026.2. A aplicação usa dados fictícios para demonstrar a prevenção da dengue e o acompanhamento de ocorrências e vistorias ambientais.

- `AEGIS.py` contém a interface Streamlit, o portal e os menus dos quatro perfis.
- `Backend.py` contém os dados demonstrativos, as regras de ocorrências e vistorias, os algoritmos de memoização, tabulação, BFS e DFS e a consulta ao InfoDengue.

## Clonar e executar no PyCharm

1. Na tela inicial do PyCharm, clique em **Clone** ou **Get from VCS**. Se já estiver com um projeto aberto, use **File → New → Project from Version Control**.
2. Cole `https://github.com/jovexdev/GS2_Pythpn_AEGIS.git`, escolha a pasta de destino e clique em **Clone**. Como o repositório é privado, entre no GitHub com uma conta que tenha acesso.
3. Em **Settings → Python → Interpreter**, selecione ou crie um ambiente virtual local (`.venv`) usando Python 3.14.
4. Abra o **Terminal** do PyCharm na pasta que contém `AEGIS.py`. Com o ambiente virtual ativo, execute:

   ```powershell
   python -m pip install -r requirements.txt
   python -m streamlit run AEGIS.py
   ```

   No Windows, se o terminal não ativar a `.venv` automaticamente, use `.\.venv\Scripts\python.exe` no lugar de `python` nos dois comandos.

5. Abra [http://127.0.0.1:8501](http://127.0.0.1:8501) no navegador. Para encerrar o servidor, pressione **Ctrl+C** no terminal.

Se quiser iniciar pelo botão **Run** do PyCharm, vá a **Run → Edit Configurations**, adicione uma configuração **Python**, selecione **Module name** e informe `streamlit`. Use `run AEGIS.py` em **Parameters**, a raiz do projeto em **Working directory** e selecione o interpretador da `.venv`.

## Experimentar o aplicativo

- **Cidadão** → **Planejador de prevenção** e **Rede de regiões** para demonstrar memoização e grafos.
- **Empresa** → **Planejamento de ações** para comparar memoização e tabulação.
- **Agente** → **Rede de atendimentos** para explorar as conexões entre regiões.
- **Gestor** → **Planejamento de vistorias** para comparar os algoritmos e abrir a matriz de tabulação.

Em **Cidadão → Indicadores de dengue**, a consulta ao InfoDengue requer internet. A tela também oferece dados demonstrativos. Alterações em relatos e vistorias ficam na sessão atual do Streamlit.
