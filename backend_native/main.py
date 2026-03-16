import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import warnings
warnings.filterwarnings('ignore')
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import cv2
import time
import threading
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import store
from .models import load_models
from .vision import m_state, capture_worker, tracker_worker, analyst_worker

import logging

app = FastAPI(title="VisionX-11 Pro Modular Backend")

# Silence noisy uvicorn/starlette disconnect errors on Windows (WinError 10054)
class NoConnectionResetFilter(logging.Filter):
    def filter(self, record):
        return "10054" not in record.getMessage()
logging.getLogger("uvicorn.error").addFilter(NoConnectionResetFilter())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Engines will be loaded on demand via singleton
def get_models():
    return load_models()

@app.post("/api/stream/start")
async def start_stream(url: str):
    if m_state.running:
        m_state.running = False
        time.sleep(0.5)
    
    m_state.source = url
    m_state.mode = "remote" if url == "remote" else "local"
    m_state.running = True
    store.track_data = {} 
    
    pose, cls = load_models()
    
    threading.Thread(target=capture_worker, args=(m_state,), daemon=True).start()
    threading.Thread(target=tracker_worker, args=(m_state, store, pose), daemon=True).start()
    threading.Thread(target=analyst_worker, args=(m_state, store, cls), daemon=True).start()
    
    return {"status": "started", "mode": m_state.mode}

@app.websocket("/api/stream/ws")
async def stream_websocket(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client connected for remote streaming")
    try:
        while True:
            data = await websocket.receive_bytes()
            if not m_state.running or m_state.mode != "remote":
                continue
            
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                m_state.raw_q.append(frame)
    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")

@app.post("/api/stream/stop")
async def stop_stream():
    m_state.running = False
    return {"status": "stopped"}

@app.get("/api/stream/video")
async def video_feed():
    def gen():
        while True:
            if m_state.proc_q and m_state.running:
                _, buffer = cv2.imencode('.jpg', m_state.proc_q[-1], [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            else:
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(img, "OFFLINE", (250, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (80, 80, 80), 2)
                _, buffer = cv2.imencode('.jpg', img)
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.01)
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/stream/raw")
async def raw_feed():
    def gen():
        while True:
            if m_state.raw_q and m_state.running:
                _, buffer = cv2.imencode('.jpg', m_state.raw_q[-1], [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            else:
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(img, "RAW FEED", (250, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 50), 2)
                _, buffer = cv2.imencode('.jpg', img)
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.01)
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/gallery")
async def get_gallery(): 
    return store.get_gallery()

@app.get("/api/events")
async def get_events(): 
    return store.get_events()

if __name__ == "__main__":
    import uvicorn
    # Important: run with module path to support relative imports
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run(
        "backend_native.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False,
        ssl_keyfile=os.path.join(base_dir, "key.pem"),
        ssl_certfile=os.path.join(base_dir, "cert.pem")
    )
