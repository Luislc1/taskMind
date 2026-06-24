"""
app.py
------
Aplicação principal do TaskMind AI — interface Streamlit.

Executar com:
    streamlit run app.py
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
import llm_service as llm

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="TaskMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializa o banco
db.init_db()

PRIORITY_OPTIONS = ["baixa", "média", "alta", "urgente"]
STATUS_OPTIONS = ["pendente", "em_andamento", "concluida"]
STATUS_LABELS = {
    "pendente": "⏳ Pendente",
    "em_andamento": "🔄 Em andamento",
    "concluida": "✅ Concluída",
}
PRIORITY_COLORS = {
    "baixa": "#10b981",
    "média": "#3b82f6",
    "alta": "#f59e0b",
    "urgente": "#ef4444",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_llm_call(fn, *args, spinner="Pensando...", **kwargs):
    """Executa uma chamada de LLM exibindo spinner e tratando erros."""
    try:
        with st.spinner(spinner):
            return fn(*args, **kwargs)
    except RuntimeError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:
        st.error(f"Erro ao chamar a LLM: {e}")
    return None


# ---------------------------------------------------------------------------
# Sidebar — navegação
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("# 🧠 TaskMind AI")
    st.caption("Gerenciador inteligente de tarefas")
    st.divider()

    page = st.radio(
        "Navegar",
        [
            "📊 Dashboard",
            "➕ Nova tarefa",
            "📋 Minhas tarefas",
            "🤖 Priorização IA",
            "💬 Chat com IA",
            "📈 Relatório semanal",
            "⚙️ Sobre",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    stats = db.stats_overview()
    st.metric("Tarefas totais", stats["total"])
    st.metric("Taxa de conclusão", f"{stats['taxa_conclusao']}%")
    if stats["urgentes"] > 0:
        st.warning(f"🚨 {stats['urgentes']} urgente(s)")


# ---------------------------------------------------------------------------
# Página: Dashboard
# ---------------------------------------------------------------------------

if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    st.caption("Visão geral da sua produtividade")

    stats = db.stats_overview()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", stats["total"])
    c2.metric("✅ Concluídas", stats["concluidas"])
    c3.metric("🔄 Em andamento", stats["em_andamento"])
    c4.metric("⏳ Pendentes", stats["pendentes"])

    st.divider()

    tasks = db.list_tasks()
    if not tasks:
        st.info("Você ainda não tem tarefas. Vá em **Nova tarefa** para começar.")
    else:
        df = pd.DataFrame([t.to_dict() for t in tasks])

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Tarefas por status")
            status_count = df["status"].value_counts().reset_index()
            status_count.columns = ["status", "qtd"]
            status_count["status"] = status_count["status"].map(STATUS_LABELS)
            fig = px.pie(
                status_count,
                names="status",
                values="qtd",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(showlegend=True, height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Tarefas por prioridade")
            prio_count = df["priority"].value_counts().reset_index()
            prio_count.columns = ["priority", "qtd"]
            fig = px.bar(
                prio_count,
                x="priority",
                y="qtd",
                color="priority",
                color_discrete_map=PRIORITY_COLORS,
                text="qtd",
            )
            fig.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("⏰ Próximos prazos")
        upcoming = [t for t in tasks if t.due_date and t.status != "concluida"]
        upcoming.sort(key=lambda t: t.due_date)
        if upcoming:
            rows = []
            for t in upcoming[:10]:
                days = (t.due_date - date.today()).days
                if days < 0:
                    prazo = f"⚠️ Atrasada há {-days} dia(s)"
                elif days == 0:
                    prazo = "🔥 Hoje"
                elif days <= 3:
                    prazo = f"⏰ Em {days} dia(s)"
                else:
                    prazo = f"📅 Em {days} dia(s)"
                rows.append(
                    {
                        "Tarefa": t.title,
                        "Prioridade": t.priority,
                        "Status": STATUS_LABELS.get(t.status, t.status),
                        "Prazo": prazo,
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma tarefa com prazo definido.")


# ---------------------------------------------------------------------------
# Página: Nova tarefa
# ---------------------------------------------------------------------------

elif page == "➕ Nova tarefa":
    st.title("➕ Nova tarefa")
    st.caption("Crie uma tarefa — a IA pode decompô-la e estimar tempo automaticamente.")

    with st.form("nova_tarefa", clear_on_submit=False):
        title = st.text_input("Título *", placeholder="Ex.: Escrever introdução do TCC")
        description = st.text_area(
            "Descrição (opcional)",
            placeholder="Detalhes que ajudem a IA a entender a tarefa...",
            height=100,
        )
        c1, c2 = st.columns(2)
        with c1:
            priority = st.selectbox("Prioridade", PRIORITY_OPTIONS, index=1)
        with c2:
            due_date = st.date_input(
                "Prazo (opcional)",
                value=None,
                min_value=date.today(),
                format="DD/MM/YYYY",
            )

        c3, c4 = st.columns(2)
        with c3:
            ai_decompose = st.checkbox("🤖 Decompor com IA", value=True)
        with c4:
            ai_estimate = st.checkbox("⏱️ Estimar tempo com IA", value=True)

        submitted = st.form_submit_button("Criar tarefa", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("O título é obrigatório.")
        else:
            task = db.create_task(
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
            )
            st.success(f"Tarefa #{task.id} criada!")

            if ai_estimate:
                minutes = safe_llm_call(
                    llm.estimate_time,
                    title,
                    description,
                    spinner="⏱️ Estimando tempo...",
                )
                if minutes:
                    db.update_task(task.id, estimated_minutes=minutes)
                    st.info(f"⏱️ Estimativa da IA: **{minutes} minutos** "
                            f"(~{round(minutes/60, 1)} h)")

            if ai_decompose:
                subs = safe_llm_call(
                    llm.decompose_task,
                    title,
                    description,
                    spinner="🤖 Decompondo em subtarefas...",
                )
                if subs:
                    db.add_subtasks(task.id, subs)
                    st.success(f"🤖 {len(subs)} subtarefas geradas:")
                    for s in subs:
                        st.markdown(f"- {s}")

            st.balloons()


# ---------------------------------------------------------------------------
# Página: Minhas tarefas
# ---------------------------------------------------------------------------

elif page == "📋 Minhas tarefas":
    st.title("📋 Minhas tarefas")

    c1, c2 = st.columns([3, 1])
    with c1:
        filter_status = st.multiselect(
            "Filtrar por status",
            STATUS_OPTIONS,
            default=["pendente", "em_andamento"],
            format_func=lambda s: STATUS_LABELS.get(s, s),
        )
    with c2:
        st.write("")
        st.write("")
        order_by_ai = st.checkbox("Ordenar por IA", value=False)

    tasks = db.list_tasks()
    if filter_status:
        tasks = [t for t in tasks if t.status in filter_status]

    if order_by_ai:
        tasks.sort(
            key=lambda t: (t.ai_priority_score or -1),
            reverse=True,
        )

    if not tasks:
        st.info("Nenhuma tarefa encontrada com esses filtros.")
    else:
        for t in tasks:
            with st.container(border=True):
                head_cols = st.columns([6, 2, 2, 1])
                with head_cols[0]:
                    st.markdown(f"### {t.title}")
                    if t.description:
                        st.caption(t.description)
                with head_cols[1]:
                    st.markdown(
                        f"**Prioridade**<br>"
                        f"<span style='color:{PRIORITY_COLORS[t.priority]}'>"
                        f"● {t.priority}</span>",
                        unsafe_allow_html=True,
                    )
                with head_cols[2]:
                    st.markdown(f"**Status**<br>{STATUS_LABELS.get(t.status, t.status)}",
                                unsafe_allow_html=True)
                with head_cols[3]:
                    if t.ai_priority_score is not None:
                        st.metric("IA", f"{t.ai_priority_score}")

                meta_cols = st.columns(4)
                if t.due_date:
                    meta_cols[0].markdown(f"📅 **Prazo:** {t.due_date.strftime('%d/%m/%Y')}")
                if t.estimated_minutes:
                    h = round(t.estimated_minutes / 60, 1)
                    meta_cols[1].markdown(f"⏱️ **Estimativa:** {t.estimated_minutes} min ({h} h)")
                meta_cols[2].markdown(
                    f"🗓️ **Criada em:** {t.created_at.strftime('%d/%m/%Y')}"
                )

                if t.ai_reasoning:
                    st.info(f"💡 **IA:** {t.ai_reasoning}")

                # Subtarefas
                if t.subtasks:
                    with st.expander(f"📌 Subtarefas ({sum(1 for s in t.subtasks if s.done)}/{len(t.subtasks)})"):
                        for sub in sorted(t.subtasks, key=lambda s: s.order_index):
                            checked = st.checkbox(
                                sub.title,
                                value=sub.done,
                                key=f"sub_{sub.id}",
                            )
                            if checked != sub.done:
                                db.toggle_subtask(sub.id)
                                st.rerun()

                # Ações
                action_cols = st.columns(5)
                with action_cols[0]:
                    new_status = st.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(t.status),
                        key=f"status_{t.id}",
                        label_visibility="collapsed",
                        format_func=lambda s: STATUS_LABELS.get(s, s),
                    )
                    if new_status != t.status:
                        db.update_task(t.id, status=new_status)
                        st.rerun()

                with action_cols[1]:
                    if st.button("🤖 Decompor", key=f"dec_{t.id}", use_container_width=True):
                        subs = safe_llm_call(
                            llm.decompose_task, t.title, t.description,
                            spinner="Decompondo...",
                        )
                        if subs:
                            db.add_subtasks(t.id, subs)
                            st.rerun()

                with action_cols[2]:
                    if st.button("⏱️ Estimar", key=f"est_{t.id}", use_container_width=True):
                        m = safe_llm_call(
                            llm.estimate_time, t.title, t.description,
                            spinner="Estimando...",
                        )
                        if m:
                            db.update_task(t.id, estimated_minutes=m)
                            st.rerun()

                with action_cols[4]:
                    if st.button("🗑️ Excluir", key=f"del_{t.id}", use_container_width=True):
                        db.delete_task(t.id)
                        st.rerun()


# ---------------------------------------------------------------------------
# Página: Priorização IA
# ---------------------------------------------------------------------------

elif page == "🤖 Priorização IA":
    st.title("🤖 Priorização inteligente")
    st.caption(
        "A IA analisa todas as suas tarefas não-concluídas e devolve um "
        "score (0-100) com justificativa."
    )

    tasks = [t for t in db.list_tasks() if t.status != "concluida"]
    if not tasks:
        st.info("Você não tem tarefas pendentes para priorizar.")
    else:
        st.write(f"**{len(tasks)} tarefa(s)** serão analisadas.")

        if st.button("⚡ Analisar agora", type="primary"):
            payload = [t.to_dict() for t in tasks]
            result = safe_llm_call(
                llm.prioritize_tasks,
                payload,
                spinner="🤖 Analisando suas tarefas...",
            )
            if result:
                for item in result:
                    db.update_task(
                        item["id"],
                        ai_priority_score=item["score"],
                        ai_reasoning=item["reasoning"],
                    )
                st.success(f"✅ {len(result)} tarefas priorizadas pela IA!")

        # Exibe ranking atual
        st.divider()
        st.subheader("Ranking atual (segundo a IA)")
        ranked = [t for t in tasks if t.ai_priority_score is not None]
        ranked.sort(key=lambda t: t.ai_priority_score, reverse=True)

        if not ranked:
            st.info("Clique em **Analisar agora** para gerar o ranking.")
        else:
            for i, t in enumerate(ranked, 1):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 6, 2])
                    c1.markdown(f"### #{i}")
                    c2.markdown(f"**{t.title}**")
                    if t.ai_reasoning:
                        c2.caption(f"💡 {t.ai_reasoning}")
                    c3.metric("Score", t.ai_priority_score)


# ---------------------------------------------------------------------------
# Página: Chat com IA
# ---------------------------------------------------------------------------

elif page == "💬 Chat com IA":
    st.title("💬 Converse com seu assistente")
    st.caption("A IA tem acesso à sua lista de tarefas para responder.")

    col_a, col_b = st.columns([6, 1])
    with col_b:
        if st.button("🧹 Limpar histórico"):
            db.clear_chat_history()
            st.rerun()

    history = db.load_chat_history()

    # Renderiza o histórico
    for msg in history:
        with st.chat_message(msg.role):
            st.markdown(msg.content)

    # Caixa de input
    user_input = st.chat_input("Pergunte algo sobre suas tarefas...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        db.save_chat_message("user", user_input)

        tasks_payload = [t.to_dict() for t in db.list_tasks()]
        history_payload = [{"role": m.role, "content": m.content} for m in history]

        with st.chat_message("assistant"):
            with st.spinner("🤖 Pensando..."):
                try:
                    reply = llm.chat_about_tasks(user_input, tasks_payload, history_payload)
                except Exception as e:
                    reply = f"⚠️ Erro ao consultar a IA: {e}"
            st.markdown(reply)
        db.save_chat_message("assistant", reply)


# ---------------------------------------------------------------------------
# Página: Relatório semanal
# ---------------------------------------------------------------------------

elif page == "📈 Relatório semanal":
    st.title("📈 Relatório de produtividade")
    st.caption("A IA analisa seu histórico e gera insights práticos.")

    if st.button("✨ Gerar novo relatório", type="primary"):
        tasks_payload = [t.to_dict() for t in db.list_tasks()]
        if not tasks_payload:
            st.warning("Você ainda não tem tarefas cadastradas.")
        else:
            report = safe_llm_call(
                llm.generate_productivity_report,
                tasks_payload,
                spinner="📊 Gerando relatório...",
            )
            if report:
                today = date.today()
                start = today - timedelta(days=7)
                db.save_report(start, today, report)
                st.success("Relatório gerado!")

    st.divider()
    reports = db.list_reports(limit=5)
    if not reports:
        st.info("Nenhum relatório gerado ainda.")
    else:
        for r in reports:
            with st.expander(
                f"📅 Relatório de "
                f"{r.created_at.strftime('%d/%m/%Y %H:%M')}",
                expanded=(r == reports[0]),
            ):
                st.markdown(r.content)


# ---------------------------------------------------------------------------
# Página: Sobre
# ---------------------------------------------------------------------------

elif page == "⚙️ Sobre":
    st.title("⚙️ Sobre o TaskMind AI")
    st.markdown(
        """
        **TaskMind AI** é um gerenciador de tarefas que usa um modelo de
        linguagem (LLM) como copiloto de produtividade.

        ### Funcionalidades
        - ➕ CRUD completo de tarefas com prazo, prioridade e status
        - 🤖 Decomposição automática em subtarefas (LLM)
        - ⏱️ Estimativa de tempo com IA
        - 📊 Priorização inteligente com score e justificativa
        - 💬 Chat contextual sobre suas tarefas
        - 📈 Relatório semanal de produtividade
        - 📉 Dashboard com gráficos interativos

        ### Stack técnica
        | Camada | Tecnologia |
        | --- | --- |
        | Interface | Streamlit |
        | LLM | Anthropic Claude (API) |
        | Persistência | SQLite + SQLAlchemy |
        | Visualização | Plotly Express |
        | Configuração | python-dotenv |

        ### Configuração
        Para rodar localmente, crie um arquivo `.env` na raiz com:
        ```
        ANTHROPIC_API_KEY=sk-ant-...
        ANTHROPIC_MODEL=claude-sonnet-4-6
        ```

        ### Executar
        ```bash
        pip install -r requirements.txt
        streamlit run app.py
        ```
        """
    )
