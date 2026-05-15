import os
from dotenv import load_dotenv

load_dotenv()

_cam = os.getenv("CAMERA_SOURCE", "0")
CAMERA_SOURCE = int(_cam) if _cam.isdigit() else _cam

CAMERA_RECONNECT_SECONDS = int(os.getenv("CAMERA_RECONNECT_SECONDS", "5"))
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))
SAVE_DIR = os.getenv("SAVE_DIR", "static/captures")
DB_PATH = os.getenv("DB_PATH", "detections.db")
TARGET_CLASSES = set(os.getenv("TARGET_CLASSES", "person,car,motorcycle,truck,bus").split(","))
MIN_CONSECUTIVE_FRAMES = int(os.getenv("MIN_CONSECUTIVE_FRAMES", "3"))
ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "20"))

# Ollama / agent
OLLAMA_URL        = os.getenv("OLLAMA_URL",       "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL      = os.getenv("OLLAMA_MODEL",     "llama3")
OLLAMA_TIMEOUT    = int(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
AGENT_EVENT_LIMIT = int(os.getenv("AGENT_EVENT_LIMIT", "12"))
