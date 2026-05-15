import os
import cv2
import time
import uuid
import threading
from datetime import datetime
from collections import defaultdict
from ultralytics import YOLO

from services import config
from services.event_repository import save_event


class VideoMonitor:
    def __init__(self):
        self._frame = None
        self._lock = threading.Lock()
        self._online = False
        self._detection_state = defaultdict(int)
        self._last_alert_time = defaultdict(lambda: 0.0)
        self._model = YOLO(config.MODEL_PATH)
        os.makedirs(config.SAVE_DIR, exist_ok=True)

    def start(self):
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def get_jpeg(self) -> bytes | None:
        with self._lock:
            if self._frame is None:
                return None
            ok, buf = cv2.imencode(".jpg", self._frame)
            return buf.tobytes() if ok else None

    def status(self) -> dict:
        with self._lock:
            return {
                "online": self._online,
                "connected": self._online,
                "has_live_frame": self._frame is not None,
                "source_type": "webcam" if isinstance(config.CAMERA_SOURCE, int) else "stream",
            }

    def mjpeg_stream(self):
        while True:
            jpeg = self.get_jpeg()
            if jpeg is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                )
            time.sleep(0.05)

    # --- private ---

    def _draw_box(self, frame, x1, y1, x2, y2, label, conf):
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame, f"{label} {conf:.2f}", (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2,
        )

    def _should_alert(self, label: str) -> bool:
        return (time.time() - self._last_alert_time[label]) > config.ALERT_COOLDOWN_SECONDS

    def _process_frame(self, frame):
        results = self._model(frame, conf=config.CONFIDENCE_THRESHOLD, verbose=False)
        found = set()
        best_conf = {}

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                label = self._model.names[cls_id]
                if label not in config.TARGET_CLASSES:
                    continue
                found.add(label)
                if conf > best_conf.get(label, 0):
                    best_conf[label] = conf
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                self._draw_box(frame, x1, y1, x2, y2, label, conf)

        for label in config.TARGET_CLASSES:
            self._detection_state[label] = (
                self._detection_state[label] + 1 if label in found else 0
            )

        for label in found:
            if (self._detection_state[label] >= config.MIN_CONSECUTIVE_FRAMES
                    and self._should_alert(label)):
                self._save_alert(frame, label, best_conf[label])

    def _save_alert(self, frame, label: str, confidence: float):
        event_id = str(uuid.uuid4())[:8]
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{label}_{event_id}.jpg"
        filepath = os.path.join(config.SAVE_DIR, filename)
        cv2.imwrite(filepath, frame)
        save_event(event_id, label, confidence, f"/static/captures/{filename}")
        self._last_alert_time[label] = time.time()
        print(f"[ALERTA] {label} detectado. Evidência salva em {filepath}")

    def _loop(self):
        while True:
            cap = cv2.VideoCapture(config.CAMERA_SOURCE)
            if not cap.isOpened():
                print("[VideoMonitor] Não foi possível abrir a câmera. Tentando novamente...")
                self._online = False
                time.sleep(config.CAMERA_RECONNECT_SECONDS)
                continue

            self._online = True
            print("[VideoMonitor] Câmera iniciada.")

            while True:
                ok, frame = cap.read()
                if not ok:
                    print("[VideoMonitor] Stream perdido. Reconectando...")
                    self._online = False
                    cap.release()
                    time.sleep(config.CAMERA_RECONNECT_SECONDS)
                    break

                self._process_frame(frame)

                with self._lock:
                    self._frame = frame.copy()

                time.sleep(0.05)


monitor = VideoMonitor()
