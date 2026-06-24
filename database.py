"""
database.py
-----------
Camada de persistência do TaskMind AI.

Define os modelos ORM (SQLAlchemy) e funções utilitárias de CRUD
para tarefas, subtarefas e relatórios.
"""

from __future__ import annotations

from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker,
    Session,
    joinedload,
)

# ---------------------------------------------------------------------------
# Configuração do banco
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "data" / "taskmind.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

ENGINE = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(
    bind=ENGINE,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

class Task(Base):
    """Tarefa principal do usuário."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    priority = Column(String(20), default="média")        # baixa, média, alta, urgente
    status = Column(String(20), default="pendente")       # pendente, em_andamento, concluida
    due_date = Column(Date, nullable=True)
    estimated_minutes = Column(Integer, nullable=True)    # estimativa da LLM
    ai_priority_score = Column(Integer, nullable=True)    # 0-100 sugerido pela LLM
    ai_reasoning = Column(Text, default="")               # justificativa da LLM
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    subtasks = relationship(
        "Subtask",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_minutes": self.estimated_minutes,
            "ai_priority_score": self.ai_priority_score,
            "ai_reasoning": self.ai_reasoning,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "subtasks": [s.to_dict() for s in self.subtasks],
        }


class Subtask(Base):
    """Subtarefa derivada da decomposição feita pela LLM."""

    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    done = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    task = relationship("Task", back_populates="subtasks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "order_index": self.order_index,
        }


class Report(Base):
    """Relatórios de produtividade gerados pela LLM."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """Histórico do chat com o assistente."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    role = Column(String(20), nullable=False)   # user | assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Cria as tabelas se ainda não existirem."""
    Base.metadata.create_all(ENGINE)


def get_session() -> Session:
    """Retorna uma nova sessão do SQLAlchemy."""
    return SessionLocal()


# ---------------------------------------------------------------------------
# Operações de CRUD — Tasks
# ---------------------------------------------------------------------------

def create_task(
    title: str,
    description: str = "",
    priority: str = "média",
    due_date: Optional[date] = None,
) -> Task:
    with get_session() as s:
        task = Task(
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            due_date=due_date,
        )
        s.add(task)
        s.commit()
        s.refresh(task)
        return task


def list_tasks(status: Optional[str] = None) -> List[Task]:
    with get_session() as s:
        q = s.query(Task).options(joinedload(Task.subtasks))
        if status:
            q = q.filter(Task.status == status)
        return q.order_by(Task.created_at.desc()).all()


def get_task(task_id: int) -> Optional[Task]:
    with get_session() as s:
        return (
            s.query(Task)
            .options(joinedload(Task.subtasks))
            .filter(Task.id == task_id)
            .first()
        )


def update_task(task_id: int, **fields) -> Optional[Task]:
    with get_session() as s:
        task = (
            s.query(Task)
            .options(joinedload(Task.subtasks))
            .filter(Task.id == task_id)
            .first()
        )
        if not task:
            return None
        for k, v in fields.items():
            if hasattr(task, k):
                setattr(task, k, v)
        if fields.get("status") == "concluida" and task.completed_at is None:
            task.completed_at = datetime.utcnow()
        s.commit()
        return task


def delete_task(task_id: int) -> bool:
    with get_session() as s:
        task = s.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        s.delete(task)
        s.commit()
        return True


# ---------------------------------------------------------------------------
# Operações de CRUD — Subtasks
# ---------------------------------------------------------------------------

def add_subtasks(task_id: int, titles: List[str]) -> List[Subtask]:
    with get_session() as s:
        # Remove subtarefas antigas para não duplicar
        s.query(Subtask).filter(Subtask.task_id == task_id).delete()
        created = []
        for i, title in enumerate(titles):
            sub = Subtask(task_id=task_id, title=title.strip(), order_index=i)
            s.add(sub)
            created.append(sub)
        s.commit()
        for c in created:
            s.refresh(c)
        return created


def toggle_subtask(subtask_id: int) -> Optional[Subtask]:
    with get_session() as s:
        sub = s.query(Subtask).filter(Subtask.id == subtask_id).first()
        if not sub:
            return None
        sub.done = not sub.done
        s.commit()
        s.refresh(sub)
        return sub


# ---------------------------------------------------------------------------
# Relatórios e chat
# ---------------------------------------------------------------------------

def save_report(period_start: date, period_end: date, content: str) -> Report:
    with get_session() as s:
        r = Report(period_start=period_start, period_end=period_end, content=content)
        s.add(r)
        s.commit()
        s.refresh(r)
        return r


def list_reports(limit: int = 10) -> List[Report]:
    with get_session() as s:
        return s.query(Report).order_by(Report.created_at.desc()).limit(limit).all()


def save_chat_message(role: str, content: str) -> ChatMessage:
    with get_session() as s:
        m = ChatMessage(role=role, content=content)
        s.add(m)
        s.commit()
        s.refresh(m)
        return m


def load_chat_history(limit: int = 50) -> List[ChatMessage]:
    with get_session() as s:
        msgs = (
            s.query(ChatMessage)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(msgs))


def clear_chat_history() -> None:
    with get_session() as s:
        s.query(ChatMessage).delete()
        s.commit()


# ---------------------------------------------------------------------------
# Estatísticas (para o dashboard)
# ---------------------------------------------------------------------------

def stats_overview() -> dict:
    with get_session() as s:
        total = s.query(Task).count()
        done = s.query(Task).filter(Task.status == "concluida").count()
        doing = s.query(Task).filter(Task.status == "em_andamento").count()
        pending = s.query(Task).filter(Task.status == "pendente").count()
        urgent = s.query(Task).filter(Task.priority == "urgente",
                                      Task.status != "concluida").count()
        return {
            "total": total,
            "concluidas": done,
            "em_andamento": doing,
            "pendentes": pending,
            "urgentes": urgent,
            "taxa_conclusao": round((done / total * 100) if total else 0, 1),
        }
