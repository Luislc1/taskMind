# 🧠 Arquitetura do TaskMind AI

O **TaskMind AI** é um gerenciador de tarefas inteligente construído com Python. Ele combina uma interface visual interativa (Frontend), um banco de dados local para salvar as informações (Backend/Banco de Dados) e uma integração com Inteligência Artificial para facilitar o seu dia a dia (Serviços de IA).

O projeto é dividido basicamente em três grandes "blocos" de código. Abaixo, explico a responsabilidade de cada um deles:

---

## 1. Interface de Usuário (`app.py`)
> [!NOTE]
> Este é o coração visual do projeto, construído usando a biblioteca **Streamlit**.

O arquivo `app.py` é responsável por tudo que você vê na tela e onde você clica. Ele é dividido em várias "páginas" na barra lateral:
- **📊 Dashboard:** Puxa os dados do banco e usa o `plotly` para desenhar gráficos em formato de pizza e barras, mostrando como está o seu progresso.
- **➕ Nova tarefa:** Um formulário para você digitar os dados da tarefa. Quando você clica em "Criar", ele salva no banco de dados e pode automaticamente chamar a IA para estimar o tempo e quebrar a tarefa em passos menores.
- **📋 Minhas tarefas:** Mostra a lista de tudo que você tem a fazer, permitindo marcar status, checar as subtarefas ou acionar a IA manualmente.
- **💬 Chat com IA:** A tela de conversa. Ele pega o seu histórico de mensagens do banco de dados, a sua lista de tarefas, e manda tudo para a IA responder de forma personalizada.

---

## 2. Persistência de Dados (`database.py`)
> [!IMPORTANT]
> Responsável por salvar as informações para que nada se perca quando você fechar o programa. Utiliza **SQLAlchemy** e **SQLite**.

O SQLite cria um pequeno arquivo local (`data/taskmind.db`) que funciona como o banco de dados. O `database.py` cria "Modelos" (Tabelas) para organizar essas informações:
- **Tabela `Task`:** Guarda as informações da tarefa principal (título, prazo, status).
- **Tabela `Subtask`:** Guarda as subtarefas geradas pela IA, conectadas à tarefa principal.
- **Tabela `Report`:** Salva os relatórios semanais que a IA cria.
- **Tabela `ChatMessage`:** Guarda o histórico da sua conversa com o Chat.

Além das tabelas, este arquivo contém várias funções (CRUD - Create, Read, Update, Delete) como `create_task`, `list_tasks`, `save_chat_message`. O `app.py` chama essas funções sempre que precisa salvar ou ler algo.

---

## 3. Inteligência Artificial (`llm_service.py`)
> [!TIP]
> O cérebro por trás da automação do app. Ele faz a comunicação com as APIs externas (Anthropic e Google Gemini).

Sempre que a aplicação precisa "pensar", ela usa as funções deste arquivo. Ele monta um *Prompt* (as instruções que enviamos para a IA), junta com os dados da tarefa e faz o pedido para a nuvem. Ele tem funções específicas para cada funcionalidade:
- `decompose_task`: Pede para a IA listar subtarefas em formato JSON.
- `estimate_time`: Pede para a IA retornar um número em minutos estimado.
- `prioritize_tasks`: Envia todas as tarefas pendentes para a IA retornar uma nota de 0 a 100 para cada uma.
- `chat_about_tasks`: (Que acabamos de modificar para o **Gemini**). Envia o histórico da conversa e suas tarefas para gerar a resposta do bate-papo.
- `generate_productivity_report`: Pede para a IA analisar a semana e escrever dicas em formato Markdown.

---

## Como tudo se conecta?
1. Você preenche a **"Nova Tarefa"** no navegador (`app.py`).
2. O `app.py` chama o `database.py` para salvar no banco de dados SQLite.
3. Se você marcou para "Decompor com IA", o `app.py` chama o `llm_service.py`.
4. O `llm_service.py` envia a tarefa para a IA na nuvem e recebe os passos.
5. O `app.py` pega esses passos e pede para o `database.py` salvá-los no banco conectados à tarefa principal.
6. A tela atualiza e você vê tudo mágico acontecendo!
