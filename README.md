# TaskMind

> Gerenciador inteligente de tarefas com IA (Gemini) como copiloto de produtividade.

**Projeto Final de Disciplina** — implementação funcional combinando
**IA + API FastAPI + Persistência + Frontend Web Premium**.

---

## Funcionalidades

| Recurso | Descrição |
| --- | --- |
| **CRUD de tarefas** | Cria, lista, atualiza e exclui tarefas com prazo, prioridade e status |
| **Decomposição com IA** | O modelo quebra uma tarefa grande em 3-8 subtarefas executáveis |
| **Estimativa de tempo** | O modelo estima quantos minutos cada tarefa exige |
| **Priorização inteligente** | O modelo atribui um score 0-100 com justificativa baseada em prazo, esforço e urgência |
| **Chat contextual** | Converse com a IA — ela conhece todas as suas tarefas |
| **Relatório semanal** | A IA gera análise de produtividade com recomendações |
| **Dashboard** | Visão geral limpa com as estatísticas de uso (pendentes, concluídas, etc.) |

---

## Stack técnica

| Camada | Tecnologia |
| --- | --- |
| Frontend Web | **HTML5, CSS3 (Vanilla), JavaScript** (Design Premium SPA) |
| Backend API | **FastAPI** + Uvicorn |
| LLM (API) | **Google Gemini** (gemini-2.5-flash) |
| ORM / Persistência | **SQLAlchemy** + SQLite |
| Configuração | **python-dotenv** |

---

## Estrutura

```
taskmind-ai/
├── main.py             # Servidor Backend (FastAPI) e rotas
├── database.py         # Modelos ORM e operações CRUD
├── llm_service.py      # Integração com a API do Google Gemini
├── requirements.txt    # Dependências Python
├── .env.example        # Modelo de variáveis de ambiente
├── README.md           # Este arquivo
├── DOCUMENTACAO.pdf    # Documento original de entrega
├── static/             # Frontend
│   ├── index.html      # Estrutura HTML SPA
│   ├── style.css       # Design System Premium Customizado
│   └── app.js          # Lógica de interface e chamadas para API
└── data/
    └── taskmind.db     # SQLite (criado automaticamente no 1º uso)
```

---

## Como executar

### 1. Pré-requisitos
- Python 3.10+
- Conta no [Google AI Studio](https://aistudio.google.com/) com uma API key

### 2. Instalação
```bash
# Clone ou descompacte o projeto, então:
cd taskmind-ai

# Crie um ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração
```bash
cp .env.example .env
# Edite o arquivo .env e coloque sua chave da API do Google:
# GEMINI_API_KEY=sua-chave-aqui
```

### 4. Execução
```bash
uvicorn main:app --reload
```
A aplicação abrirá no endereço padrão: `http://localhost:8000` (ou `http://127.0.0.1:8000`).

---

## Como a IA é usada

O arquivo `llm_service.py` concentra **cinco funções principais** que
consomem a API do Google Gemini (`gemini-2.5-flash`):

1. **`decompose_task(title, description)`** → retorna lista de subtarefas
   acionáveis, obrigando resposta em JSON.
2. **`estimate_time(title, description)`** → retorna um inteiro em minutos.
3. **`prioritize_tasks(tasks)`** → recebe a lista completa do usuário e
   devolve scores 0-100 com justificativa, considerando prazos e
   estimativas.
4. **`chat_about_tasks(message, tasks, history)`** → chat com **contexto
   injetado** (tarefas atuais + histórico recente) no system_instruction.
5. **`generate_productivity_report(tasks)`** → gera relatório em
   Markdown com resumo, destaques, pontos de atenção e recomendações.

Todas as respostas que precisam ser estruturadas usam **JSON forçado via
instrução de sistema**, com função `_extract_json()` tolerante a formatos
imperfeitos (remove cercas de markdown, tenta fallback).

---

## Modelo de dados

```text
Task (1) ─── (N) Subtask
  │
  ├── id, title, description
  ├── priority, status, due_date
  ├── estimated_minutes        ← preenchido pela IA
  ├── ai_priority_score        ← preenchido pela IA
  ├── ai_reasoning             ← preenchido pela IA
  └── created_at, completed_at

Report
  ├── period_start, period_end
  └── content (Markdown gerado pela IA)

ChatMessage
  ├── role (user | assistant)
  ├── content
  └── created_at
```

---

## Licença

Projeto acadêmico — uso livre para fins educacionais.
