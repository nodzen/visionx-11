import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import warnings
warnings.filterwarnings('ignore')

import cv2
import time
import base64
import threading
import numpy as np
import imagehash
from collections import deque
from PIL import Image
from deepface import DeepFace
from .models import FASHION_MAP

def get_pose_info(keypoints, box, last_box=None):
    """
    Classify pose: Standing, Sitting, Lying
    Classify activity: Active (Moving/Standing), Passive (Sitting/Static)
    """
    try:
        if keypoints is None: return "Unknown", "Passive"
        
        # YOLOv11 Pose layout: 0-nose, 1-Leye, 2-Reye, 3-Lear, 4-Rear, 5-Lsho, 6-Rsho, 7-Lelb, 8-Relb, 
        # 9-Lwri, 10-Rwri, 11-Lhip, 12-Rhip, 13-Lkne, 14-Rkne, 15-Lank, 16-Rank
        kp = keypoints.data[0].cpu().numpy() # [17, 3] (x, y, conf)
        
        # Basic vertical analysis
        head_y = kp[0][1]
        hips_y = (kp[11][1] + kp[12][1]) / 2
        ankles_y = (kp[15][1] + kp[16][1]) / 2
        
        box_h = box[3] - box[1]
        box_w = box[2] - box[0]
        root_to_head = hips_y - head_y
        root_to_ankles = ankles_y - hips_y
        
        # 1. Pose Type
        pose_type = "Standing"
        ratio = box_h / (box_w + 1e-6)
        
        if ratio < 0.8: # Horizontal-ish
            pose_type = "Lying"
        elif root_to_ankles < root_to_head * 0.8: # Legs retracted/bent
            pose_type = "Sitting"
            
        # 2. Activity Type (Movement-based if we have last_box, otherwise posture-based)
        activity = "Passive"
        if pose_type == "Standing":
            activity = "Active"
            
        if last_box is not None:
            # Check for significant center movement
            c1 = [(box[0]+box[2])/2, (box[1]+box[3])/2]
            c2 = [(last_box[0]+last_box[2])/2, (last_box[1]+last_box[3])/2]
            dist = np.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
            if dist > 5: # Threshold for 'Moving'
                activity = "Active"
                if pose_type == "Standing":
                    pose_type = "Walking"
                
        return pose_type, activity
    except:
        return "Unknown", "Passive"

def get_smart_crop(frame, box, expand_torso=True):
    x1, y1, x2, y2 = map(int, box)
    h, w = frame.shape[:2]
    if expand_torso:
        width = x2 - x1
        height = y2 - y1
        target_h = int(height * 0.6)
        nx1 = max(0, x1 - int(width * 0.1))
        nx2 = min(w, x2 + int(width * 0.1))
        ny1 = max(0, y1 - int(height * 0.05))
        ny2 = min(h, y1 + target_h)
        return frame[ny1:ny2, nx1:nx2]
    return frame[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]

class StreamState:
    def __init__(self):
        self.running = False
        self.source = ""
        self.raw_q = deque(maxlen=2)
        self.proc_q = deque(maxlen=2)
        self.ident_q = deque(maxlen=2)
        self.mode = "local" # "local" or "remote"
        self.conf = 0.70

def clothing_ai(crop, cls_model):
    res = []
    try:
        # Higher resolution for more detail (448 or 640)
        p = cls_model.predict(crop, verbose=False, imgsz=448, conf=0.35)
        if p and p[0].probs:
            for idx in p[0].probs.top5:
                score = p[0].probs.data[idx].item()
                if score < 0.15: continue
                
                name = cls_model.names[int(idx)].lower()
                for k, v in FASHION_MAP.items():
                    if k in name:
                        res.append(v)
                        break
    except Exception as e:
        print(f"[DEBUG] Clothing AI Error: {e}")
    
    # Filter unique results, prioritize specific labels
    return list(dict.fromkeys(res)) if res else ["Casual Wear"]

def is_face_quality_ok(crop):
    """Check if the face crop is clear enough for ID"""
    try:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        # Blur check (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < 40: return False # Too blurry
        
        # Brightness check
        avg_bright = np.mean(gray)
        if avg_bright < 40 or avg_bright > 220: return False # Too dark or too bright
        return True
    except: return False

def analyst_worker(m_state, store, cls_model):
    print("[THREAD] Analyst Online")
    try: DeepFace.build_model("Facenet512")
    except: pass
    
    last_cleanup = time.time()

    while m_state.running:
        # Periodic DB Cleanup (every 4 hours)
        if time.time() - last_cleanup > 14400:
            store.cleanup_database()
            last_cleanup = time.time()

        if not m_state.ident_q:
            time.sleep(0.1); continue
            
        crop, t_id = m_state.ident_q.popleft()
        try:
            emb = None
            if is_face_quality_ok(crop):
                try:
                    # Align and verify face before representation
                    objs = DeepFace.represent(crop, model_name="Facenet512", detector_backend="opencv", enforce_detection=True, align=True)
                    if objs: emb = objs[0]["embedding"]
                except: 
                    # Fallback if enforcement fails
                    try:
                        objs = DeepFace.represent(crop, model_name="Facenet512", detector_backend="opencv", enforce_detection=False, align=True)
                        if objs: emb = objs[0]["embedding"]
                    except: pass
            
            clothes = clothing_ai(crop, cls_model)
            p_hash = str(imagehash.dhash(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))))
            _, buf = cv2.imencode('.jpg', cv2.resize(crop, (180, 240)))
            b64 = base64.b64encode(buf).decode('utf-8')
            
            # Extract current pose/activity from track data if available
            store_state = store.track_data.get(t_id, {})
            pose = store_state.get("last_pose", "Unknown")
            activity = store_state.get("last_activity", "Passive")
            
            store.confirm_identity(t_id, emb, p_hash, b64, clothes, pose, activity)
        except Exception as e:
            print(f"[ERR] Analyst: {e}")
        finally:
            # Done analysing this specific track ID
            if t_id in store.track_data:
                store.track_data[t_id]["analysing"] = False

def tracker_worker(m_state, store, pose_model):
    print("[THREAD] Tracker Online")
    frame_count = 0
    last_results = None

    while m_state.running:
        if not m_state.raw_q:
            time.sleep(0.005); continue
            
        frame = m_state.raw_q[0]
        frame_count += 1
        
        try:
            # FRAME SKIPPING: Process neural inference only every 2nd frame
            if frame_count % 2 == 0 or last_results is None:
                results = pose_model.track(frame, persist=True, classes=[0], verbose=False, conf=m_state.conf)
                last_results = results
            else:
                results = last_results
                
            annotated = results[0].plot(conf=False, labels=False)
            
            if results[0].boxes and results[0].boxes.id is not None:
                ids = results[0].boxes.id.int().cpu().tolist()
                boxes = results[0].boxes.xyxy.cpu().numpy()
                
                for box, t_id in zip(boxes, ids):
                    # Get pose and activity
                    kpts = results[0].keypoints if hasattr(results[0], 'keypoints') else None
                    last_b = store.track_data.get(t_id, {}).get("last_box")
                    pose_label, activity = get_pose_info(kpts, box, last_b)
                    
                    if t_id not in store.track_data:
                         store.track_data[t_id] = {"face_votes": [], "cloth_votes": [], "final_id": None, "locked": False}
                    
                    st = store.track_data[t_id]
                    st["last_box"] = box
                    st["last_pose"] = pose_label
                    st["last_activity"] = activity

                    if st["locked"]:
                        clothes_label = st.get('final_clothes', [''])[0]
                        label = f"ID:{st['final_id'][:4]} | {pose_label} | {clothes_label}"
                        x1, y1 = map(int, box[:2])
                        cv2.putText(annotated, label, (x1, max(30, y1-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (168, 85, 247), 2)
                    elif not st.get("analysing") and len(m_state.ident_q) < 2:
                        # OPTIMIZATION: Only add to queue if NOT already locked and NOT currently processing
                        st["analysing"] = True
                        crop = get_smart_crop(frame, box)
                        if crop.size > 0:
                            m_state.ident_q.append((crop, t_id))
            m_state.proc_q.append(annotated)
        except Exception as e:
            print(f"[ERR] Tracker: {e}")

def capture_worker(m_state):
    print("[THREAD] Capture Online")
    if m_state.mode == "remote":
        print("[THREAD] Capture: Remote mode, waiting for WS data.")
        return
    try:
        src = int(m_state.source) if m_state.source.isdigit() else m_state.source
        cap = cv2.VideoCapture(src, cv2.CAP_DSHOW if isinstance(src, int) else cv2.CAP_FFMPEG)
        if not cap.isOpened(): 
            m_state.running = False
            return
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        while m_state.running:
            if not cap.grab(): break
            ret, frame = cap.retrieve()
            if not ret: break
            m_state.raw_q.append(frame)
        cap.release()
    except Exception as e:
        print(f"[ERR] Capture: {e}")

m_state = StreamState()
