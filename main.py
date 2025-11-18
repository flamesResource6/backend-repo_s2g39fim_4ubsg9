import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import asyncio

from database import db, create_document, get_documents, update_document_by_id, get_document_by_id
from schemas import CallTask, TranscriptLog, User, Product

app = FastAPI(title="NovaCall Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "NovaCall API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the NovaCall backend API!"}

# ---- Health & DB test ----
@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response: Dict[str, Any] = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:  # noqa: BLE001
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:  # noqa: BLE001
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ---- Schema exposure for builder tooling ----
class SchemaResponse(BaseModel):
    schemas: List[str]

@app.get("/schema", response_model=SchemaResponse)
def get_schema_definitions():
    # We expose names of available schemas to aid frontends/admin tools
    return SchemaResponse(schemas=["user", "product", "calltask", "transcriptlog"])


# ---- NovaCall: Background simulation (placeholder for real telephony) ----
async def simulate_call_flow(call_id: str):
    """Simulate an outbound call by logging a few transcript steps and updating status.
    This is a stand-in until a real telephony/voice provider is integrated.
    """
    # Mark in-progress
    update_document_by_id("calltask", call_id, {"status": "in_progress"})

    # Fetch task to tailor messages
    task = get_document_by_id("calltask", call_id) or {}
    intent = task.get("intent", "the stated purpose")
    voice = task.get("voice_model_id", "manohar-voice-v1")

    steps = [
        ("system", f"Dialing target {task.get('target_phone', '')} using voice model {voice} ..."),
        ("assistant", "Hello! This is Nova calling on behalf of Manohar. Is now a good time?"),
        ("callee", "Yes, I have a minute."),
        ("assistant", f"Great. The purpose of my call is {intent}."),
    ]

    for role, text in steps:
        log = TranscriptLog(call_id=call_id, role=role, text=text, timestamp=datetime.now(timezone.utc))
        create_document("transcriptlog", log)
        await asyncio.sleep(0.6)

    # Finish
    create_document(
        "transcriptlog",
        TranscriptLog(
            call_id=call_id,
            role="system",
            text="Call completed successfully.",
            timestamp=datetime.now(timezone.utc),
            outcome="completed",
        ),
    )
    update_document_by_id("calltask", call_id, {"status": "completed"})


# ---- NovaCall: Call task creation & logging ----
@app.post("/api/call-tasks")
def create_call_task(payload: CallTask, background_tasks: BackgroundTasks):
    try:
        call_id = create_document("calltask", payload)
        # Auto-start simulated call in background (replace with real call integration later)
        background_tasks.add_task(asyncio.run, simulate_call_flow(call_id))
        return {"id": call_id, "status": "queued"}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


class TranscriptPayload(BaseModel):
    call_id: str
    role: str
    text: str
    outcome: Optional[str] = None

@app.post("/api/transcripts")
def log_transcript(payload: TranscriptPayload):
    try:
        log = TranscriptLog(
            call_id=payload.call_id,
            role=payload.role,
            text=payload.text,
            timestamp=datetime.now(timezone.utc),
            outcome=payload.outcome,
        )
        _ = create_document("transcriptlog", log)
        return {"ok": True}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


# Utility fetch for a call session transcript preview (limited)
@app.get("/api/transcripts/{call_id}")
def get_transcripts(call_id: str, limit: int = 100):
    try:
        docs = get_documents("transcriptlog", {"call_id": call_id}, limit=limit)
        # Normalize ObjectId for the UI if needed
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])  # type: ignore[assignment]
            if isinstance(d.get("timestamp"), datetime):
                d["timestamp"] = d["timestamp"].isoformat()
        return {"items": docs}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
