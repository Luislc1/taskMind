from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import database as db
import llm_service as llm

app = FastAPI(title="TaskMind API")

db.init_db()

# Montando arquivos estáticos para o frontend
import os
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# --- Models ---
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "média"
    due_date: Optional[date] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_minutes: Optional[int] = None
    ai_priority_score: Optional[int] = None
    ai_reasoning: Optional[str] = None

class ChatRequest(BaseModel):
    message: str

# --- Endpoints ---

@app.get("/api/stats")
def get_stats():
    return db.stats_overview()

@app.get("/api/tasks")
def get_tasks(status: Optional[str] = None):
    tasks = db.list_tasks(status)
    return [t.to_dict() for t in tasks]

@app.post("/api/tasks")
def create_task(task: TaskCreate):
    new_task = db.create_task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date
    )
    return new_task.to_dict()

@app.put("/api/tasks/{task_id}")
def update_task_endpoint(task_id: int, update: TaskUpdate):
    data = {k: v for k, v in update.dict().items() if v is not None}
    updated = db.update_task(task_id, **data)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated.to_dict()

@app.delete("/api/tasks/{task_id}")
def delete_task_endpoint(task_id: int):
    success = db.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "ok"}

@app.post("/api/tasks/{task_id}/decompose")
def decompose_task_endpoint(task_id: int):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        subs = llm.decompose_task(task.title, task.description)
        if subs:
            db.add_subtasks(task.id, subs)
        return {"subtasks": subs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/{task_id}/estimate")
def estimate_task_endpoint(task_id: int):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        mins = llm.estimate_time(task.title, task.description)
        if mins:
            db.update_task(task.id, estimated_minutes=mins)
        return {"estimated_minutes": mins}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/subtasks/{subtask_id}/toggle")
def toggle_subtask_endpoint(subtask_id: int):
    sub = db.toggle_subtask(subtask_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return sub.to_dict()

@app.post("/api/tasks/prioritize")
def prioritize_tasks_endpoint():
    tasks = db.list_tasks()
    tasks_dict = [t.to_dict() for t in tasks if t.status != "concluida"]
    if not tasks_dict:
        return {"status": "no pending tasks"}
    
    try:
        result = llm.prioritize_tasks(tasks_dict)
        if result:
            for item in result:
                db.update_task(
                    item["id"],
                    ai_priority_score=item["score"],
                    ai_reasoning=item["reasoning"]
                )
        return {"status": "ok", "prioritized": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat")
def get_chat():
    history = db.load_chat_history()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in history]

@app.post("/api/chat")
def post_chat(req: ChatRequest):
    db.save_chat_message("user", req.message)
    tasks_payload = [t.to_dict() for t in db.list_tasks()]
    history = db.load_chat_history()
    history_payload = [{"role": m.role, "content": m.content} for m in history]
    
    try:
        reply = llm.chat_about_tasks(req.message, tasks_payload, history_payload)
        db.save_chat_message("assistant", reply)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat")
def clear_chat():
    db.clear_chat_history()
    return {"status": "ok"}

@app.get("/api/reports")
def get_reports():
    reports = db.list_reports(limit=5)
    return [{"id": r.id, "content": r.content, "date": r.created_at} for r in reports]

@app.post("/api/reports")
def generate_report():
    tasks_payload = [t.to_dict() for t in db.list_tasks()]
    if not tasks_payload:
        raise HTTPException(status_code=400, detail="No tasks")
    try:
        report = llm.generate_productivity_report(tasks_payload)
        if report:
            today = date.today()
            from datetime import timedelta
            start = today - timedelta(days=7)
            db.save_report(start, today, report)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
