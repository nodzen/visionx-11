import os
import json
import time
import threading
import numpy as np
import uuid
import imagehash
from collections import deque, Counter

def get_cosine_dist(a, b):
    try:
        a = np.array(a, dtype=np.float32).flatten()
        b = np.array(b, dtype=np.float32).flatten()
        if a.shape != b.shape: return 1.0
        sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
        return 1.0 - sim
    except: return 1.0

class PersistentStore:
    def __init__(self, db_path="d:/pd/database.json"):
        self.db_path = db_path
        self.gallery = {} 
        self.face_db = [] 
        self.events = deque(maxlen=50)
        self.track_data = {} # t_id -> {face_votes: [], cloth_votes: [], final_id: None, locked: False}
        self.lock = threading.Lock()
        self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.gallery = data.get("gallery", {})
                    self.face_db = [{"emb": np.array(x["emb"], dtype=np.float32), "hash": x["hash"]} 
                                   for x in data.get("face_db", [])]
                    print(f"[DB] Loaded {len(self.gallery)} identities.")
            except Exception as e:
                print(f"[DB] Load error: {e}")

    def _save(self):
        with self.lock:
            try:
                data = {
                    "gallery": self.gallery,
                    "face_db": [{"emb": x["emb"].tolist(), "hash": x["hash"]} for x in self.face_db]
                }
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            except Exception as e:
                print(f"[DB] Save error: {e}")

    def match_face(self, emb, threshold=0.15): # Ultra-tight for Pro precision
        if emb is None: return None
        best, min_d = None, threshold
        for e in self.face_db:
            d = get_cosine_dist(emb, e['emb'])
            if d < min_d: min_d, best = d, e['hash']
        return best

    def confirm_identity(self, t_id, embedding, p_hash, photo_b64, raw_clothes, pose="Unknown", activity="Passive"):
        """Temporal Consensus Logic"""
        if t_id not in self.track_data:
            self.track_data[t_id] = {"face_votes": [], "cloth_votes": [], "final_id": None, "locked": False}
        
        state = self.track_data[t_id]
        if state["locked"]: return state["final_id"]

        face_match = self.match_face(embedding)
        if face_match: state["face_votes"].append(face_match)
        state["cloth_votes"].extend(raw_clothes)

        # Require high consistency for Pro identities
        if len(state["face_votes"]) >= 10 or len(state["cloth_votes"]) >= 15:
            if state["face_votes"]:
                target_id = Counter(state["face_votes"]).most_common(1)[0][0]
            else:
                # Body-only fallback
                target_id = f"GUEST_{str(uuid.uuid4())[:8]}"
            
            best_clothes = []
            if state["cloth_votes"]:
                counts = Counter(state["cloth_votes"]).most_common(2)
                best_clothes = [c[0] for c in counts]

            if target_id not in self.gallery:
                if embedding is not None:
                    self.face_db.append({"emb": np.array(embedding, dtype=np.float32), "hash": target_id})
                
                self.gallery[target_id] = {
                    "hash": p_hash, "id": target_id, "photo": photo_b64,
                    "clothes": best_clothes, "pose": pose, "activity": activity,
                    "timestamp": time.time()
                }
                self.log_event(target_id, "Appearance Confirmed", best_clothes, pose, activity)
                threading.Thread(target=self._save).start()
            
            state["final_id"] = target_id
            state["final_clothes"] = best_clothes
            state["locked"] = True
            return target_id
        
        return None

    def log_event(self, p_id, action, clothes, pose="Unknown", activity="Passive"):
        self.events.appendleft({
            "time": time.strftime("%H:%M:%S"), 
            "hash": p_id[:8], 
            "action": action, 
            "clothes": clothes,
            "pose": pose,
            "activity": activity
        })

    def get_gallery(self):
        res = list(self.gallery.values())
        return sorted(res, key=lambda x: x['timestamp'], reverse=True)

    def get_events(self):
        return list(self.events)

    def cleanup_database(self):
        """Remove identities older than 24h to keep Registry clean"""
        now = time.time()
        cutoff = now - 86400
        with self.lock:
            to_remove = [k for k, v in self.gallery.items() if v.get('timestamp', 0) < cutoff]
            for k in to_remove:
                del self.gallery[k]
                # Cleanup face_db too
                self.face_db = [x for x in self.face_db if x['hash'] != k]
            if to_remove:
                print(f"[DB] Cleanup: Removed {len(to_remove)} legacy identities.")
                self._save()

store = PersistentStore()
