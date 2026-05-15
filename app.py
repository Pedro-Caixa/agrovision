import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services import config
from services.event_repository import init_db, list_events
from services.video_monitor import monitor
from services.schemas import ChatRequest
from services.ollama_client import stream_chat, warmup
from services.monitoring_agent import build_agent_messages, agent_status

app = FastAPI(title="AgroVision AI")

os.makedirs("static/captures", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup_event():
    init_db()
    monitor.start()
    warmup()


# ── Pages ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html", {"events": list_events(20)})


# ── Health & status ────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "AgroVision AI"}


@app.get("/camera/status")
def camera_status():
    return JSONResponse(content=monitor.status())


@app.get("/agent/status")
def get_agent_status():
    events = list_events(config.AGENT_EVENT_LIMIT)
    return JSONResponse(content=agent_status(events))


# ── Video ──────────────────────────────────────────────────────────────────────

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        monitor.mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/frame")
def get_frame():
    jpeg = monitor.get_jpeg()
    if jpeg is None:
        return JSONResponse(content={"message": "Ainda sem frame disponível."}, status_code=503)
    return Response(content=jpeg, media_type="image/jpeg")


# ── Events ─────────────────────────────────────────────────────────────────────

@app.get("/events")
def get_events():
    return JSONResponse(content=list_events(50))


# ── Chat / agent ───────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(req: ChatRequest):
    events = list_events(config.AGENT_EVENT_LIMIT)
    messages = build_agent_messages(req.question, req.history, events)
    return StreamingResponse(
        stream_chat(messages),
        media_type="text/plain; charset=utf-8",
    )
