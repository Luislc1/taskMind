"""
llm_service.py
--------------
Camada de integração com a API da Anthropic (Claude).

Centraliza todas as chamadas ao LLM:
    - decomposição de tarefas em subtarefas
    - estimativa de tempo
    - priorização inteligente com justificativa
    - chat contextual sobre as tarefas do usuário
    - geração de relatório semanal de produtividade
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from typing import List, Optional

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# ---------------------------------------------------------------------------
# Configuração do cliente
# ---------------------------------------------------------------------------

def _configure_gemini():
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_api_key:
        raise RuntimeError(
            "Variável de ambiente GEMINI_API_KEY não configurada. "
            "Verifique o seu arquivo .env."
        )
    genai.configure(api_key=gemini_api_key)


def _call(system: str, user: str, max_tokens: int = 1024) -> str:
    """Faz uma chamada simples ao Gemini e retorna apenas o texto."""
    _configure_gemini()
    
    generation_config = genai.types.GenerationConfig(max_output_tokens=max_tokens)
    
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        system_instruction=system,
        generation_config=generation_config
    )
    
    response = model.generate_content(user)
    return response.text.strip()


def _extract_json(text: str) -> Optional[dict | list]:
    """
    Extrai o primeiro bloco JSON válido do texto.
    Tolerante a respostas com prefixos/sufixos ou cercadas por ```json.
    """
    if not text:
        return None

    # Remove blocos de markdown
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

    # Tenta parse direto
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Fallback: pega do primeiro { ou [ até o último } ou ]
    candidates = []
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = cleaned.find(open_c)
        end = cleaned.rfind(close_c)
        if start != -1 and end != -1 and end > start:
            candidates.append(cleaned[start : end + 1])

    for c in candidates:
        try:
            return json.loads(c)
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# Funcionalidades de IA
# ---------------------------------------------------------------------------

def decompose_task(title: str, description: str = "") -> List[str]:
    """
    Pede à LLM para decompor uma tarefa em 3 a 8 subtarefas acionáveis.
    Retorna lista de strings (ou lista vazia em caso de falha).
    """
    system = (
        "Você é um assistente de produtividade. Sua função é quebrar uma "
        "tarefa em subtarefas pequenas, executáveis e ordenadas. "
        "Responda SOMENTE com JSON válido no formato: "
        '{"subtasks": ["passo 1", "passo 2", ...]}'
    )
    user = (
        f"Tarefa: {title}\n"
        f"Descrição: {description or '(sem descrição)'}\n\n"
        "Gere de 3 a 8 subtarefas concretas, em português, "
        "começando com verbo no infinitivo (ex: 'Definir...', 'Pesquisar...')."
    )

    raw = _call(system, user, max_tokens=600)
    data = _extract_json(raw)
    if isinstance(data, dict) and isinstance(data.get("subtasks"), list):
        return [str(s).strip() for s in data["subtasks"] if str(s).strip()][:8]
    if isinstance(data, list):
        return [str(s).strip() for s in data if str(s).strip()][:8]
    return []


def estimate_time(title: str, description: str = "") -> Optional[int]:
    """
    Pede à LLM uma estimativa de tempo (em minutos) para a tarefa.
    Retorna inteiro ou None.
    """
    system = (
        "Você é um estimador de tempo realista para tarefas de trabalho/estudo. "
        'Responda SOMENTE com JSON: {"minutes": <int>}'
    )
    user = (
        f"Tarefa: {title}\n"
        f"Descrição: {description or '(sem descrição)'}\n\n"
        "Estime quantos minutos de trabalho focado essa tarefa exige. "
        "Considere uma pessoa de produtividade mediana. Valor entre 5 e 600."
    )
    raw = _call(system, user, max_tokens=120)
    data = _extract_json(raw)
    if isinstance(data, dict) and isinstance(data.get("minutes"), (int, float)):
        return max(5, min(600, int(data["minutes"])))
    return None


def prioritize_tasks(tasks: List[dict]) -> List[dict]:
    """
    Recebe a lista de tarefas (como dicts) e devolve uma lista com:
        [{"id": int, "score": int (0-100), "reasoning": str}, ...]
    ordenada do mais importante para o menos importante.
    """
    if not tasks:
        return []

    payload = [
        {
            "id": t["id"],
            "title": t["title"],
            "priority": t.get("priority"),
            "status": t.get("status"),
            "due_date": t.get("due_date"),
            "estimated_minutes": t.get("estimated_minutes"),
        }
        for t in tasks
        if t.get("status") != "concluida"
    ]

    today = date.today().isoformat()
    system = (
        "Você é um especialista em GTD e Matriz de Eisenhower. "
        "Recebe uma lista de tarefas e devolve scores de prioridade. "
        "Responda SOMENTE em JSON válido no formato: "
        '{"items": [{"id": <int>, "score": <0-100>, "reasoning": "<curto>"}, ...]}'
    )
    user = (
        f"Data de hoje: {today}\n"
        f"Tarefas:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Atribua um score de 0 a 100 (maior = mais prioritário) considerando "
        "urgência (prazo), importância declarada e esforço estimado. "
        "Inclua uma breve justificativa (até 120 caracteres) em português."
    )

    raw = _call(system, user, max_tokens=1500)
    data = _extract_json(raw)
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        items = []
        for it in data["items"]:
            try:
                items.append(
                    {
                        "id": int(it["id"]),
                        "score": max(0, min(100, int(it["score"]))),
                        "reasoning": str(it.get("reasoning", "")).strip(),
                    }
                )
            except Exception:
                continue
        items.sort(key=lambda x: x["score"], reverse=True)
        return items
    return []


def chat_about_tasks(user_message: str, tasks: List[dict], history: List[dict]) -> str:
    """
    Conversa com a LLM dando como contexto a lista atual de tarefas e
    o histórico recente do chat.
    """
    compact_tasks = [
        {
            "id": t["id"],
            "titulo": t["title"],
            "prioridade": t.get("priority"),
            "status": t.get("status"),
            "prazo": t.get("due_date"),
            "estimativa_min": t.get("estimated_minutes"),
        }
        for t in tasks
    ]
    system = (
        "Você é o TaskMind, um assistente pessoal de produtividade em português. "
        "Tem acesso à lista de tarefas do usuário (em JSON). "
        "Responda de forma direta, prática e amigável. "
        "Não invente tarefas que não existem na lista. "
        "Quando fizer sentido, sugira próximos passos concretos.\n\n"
        f"Lista atual de tarefas do usuário:\n"
        f"{json.dumps(compact_tasks, ensure_ascii=False, indent=2)}"
    )

    try:
        _configure_gemini()
    except RuntimeError:
        return "⚠️ A chave GEMINI_API_KEY não foi configurada. Adicione-a no seu arquivo .env para conversar com o assistente."
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system)

    # Constrói histórico no formato esperado pela API do Gemini
    gemini_history = []
    for h in history[-10:]:  # últimas 10 mensagens
        role = "user" if h["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [h["content"]]})

    try:
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(user_message)
        return response.text.strip()
    except Exception as e:
        return f"Erro ao comunicar com a IA do Google: {str(e)}"


def generate_productivity_report(tasks: List[dict]) -> str:
    """
    Gera um relatório semanal de produtividade em Markdown a partir das
    tarefas do usuário.
    """
    system = (
        "Você é um coach de produtividade. Gere um relatório curto e útil "
        "(máximo 400 palavras) em **Markdown** sobre o desempenho recente do "
        "usuário, com base na lista de tarefas. "
        "Inclua: (1) resumo numérico, (2) destaques positivos, "
        "(3) pontos de atenção, (4) 3 recomendações práticas para a próxima semana. "
        "Use tom motivacional, porém honesto. Escreva em português."
    )

    summary = []
    for t in tasks:
        summary.append(
            {
                "titulo": t["title"],
                "prioridade": t.get("priority"),
                "status": t.get("status"),
                "prazo": t.get("due_date"),
                "criada_em": t.get("created_at"),
                "concluida_em": t.get("completed_at"),
            }
        )

    user = (
        f"Data atual: {datetime.now().strftime('%d/%m/%Y')}\n"
        f"Tarefas do usuário ({len(summary)} no total):\n"
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}"
    )
    return _call(system, user, max_tokens=1200)
