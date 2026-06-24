# 🧠 TaskMind AI

> Gerenciador inteligente de tarefas com LLM como copiloto de produtividade.

**Projeto Final de Disciplina** — implementação funcional combinando
**LLM + API + Persistência + Interface Web**.

---

## ✨ Funcionalidades

| Recurso | Descrição |
| --- | --- |
| ➕ **CRUD de tarefas** | Cria, lista, atualiza e exclui tarefas com prazo, prioridade e status |
| 🤖 **Decomposição com IA** | A LLM quebra uma tarefa grande em 3-8 subtarefas executáveis |
| ⏱️ **Estimativa de tempo** | A LLM estima quantos minutos cada tarefa exige |
| 📊 **Priorização inteligente** | A LLM atribui um score 0-100 com justificativa baseada em prazo, esforço e urgência |
| 💬 **Chat contextual** | Converse com a IA — ela conhece todas as suas tarefas |
| 📈 **Relatório semanal** | A LLM gera análise de produtividade com recomendações |
| 📉 **Dashboard** | Gráficos interativos de status, prioridade e prazos |

---

## 🛠️ Stack técnica

| Camada | Tecnologia |
| --- | --- |
| Interface Web | [Streamlit](https://streamlit.io/) |
| LLM (API) | [Anthropic Claude](https://www.anthropic.com/api) |
| ORM / Persistência | [SQLAlchemy](https://www.sqlalchemy.org/) + SQLite |
| Visualização | [Plotly Express](https://plotly.com/python/plotly-express/) |
| Configuração | [python-dotenv](https://pypi.org/project/python-dotenv/) |

---

## 📁 Estrutura

```
taskmind-ai/
├── app.py              # Interface Streamlit (entrypoint)
├── database.py         # Modelos ORM e operações CRUD
├── llm_service.py      # Integração com a API do Claude
├── requirements.txt    # Dependências Python
├── .env.example        # Modelo de variáveis de ambiente
├── README.md           # Este arquivo
├── DOCUMENTACAO.pdf    # Documento de entrega
└── data/
    └── taskmind.db     # SQLite (criado automaticamente no 1º uso)
```

---

## 🚀 Como executar

### 1. Pré-requisitos
- Python 3.10+
- Conta na [Anthropic Console](https://console.anthropic.com/) com uma API key

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
# Edite o arquivo .env e coloque sua chave da API:
# ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Execução
```bash
streamlit run app.py
```
A aplicação abrirá em `http://localhost:8501`.

---

## 🧠 Como a IA é usada

O arquivo `llm_service.py` concentra **cinco funções principais** que
consomem a API do Claude:

1. **`decompose_task(title, description)`** → retorna lista de subtarefas
   acionáveis, obrigando resposta em JSON.
2. **`estimate_time(title, description)`** → retorna um inteiro em minutos.
3. **`prioritize_tasks(tasks)`** → recebe a lista completa do usuário e
   devolve scores 0-100 com justificativa, considerando prazos e
   estimativas.
4. **`chat_about_tasks(message, tasks, history)`** → chat com **contexto
   injetado** (tarefas atuais + histórico recente) no system prompt.
5. **`generate_productivity_report(tasks)`** → gera relatório em
   Markdown com resumo, destaques, pontos de atenção e recomendações.

Todas as respostas que precisam ser estruturadas usam **JSON forçado via
system prompt**, com função `_extract_json()` tolerante a formatos
imperfeitos (remove cercas de markdown, tenta fallback).

---

## 💾 Modelo de dados

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

## 📝 Licença

Projeto acadêmico — uso livre para fins educacionais.
