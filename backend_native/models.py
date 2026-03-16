import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import warnings
warnings.filterwarnings('ignore')
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

from ultralytics import YOLO

# --- Refined Fashion Taxonomy ---
FASHION_MAP = {
    "t-shirt": "Polo/T-Shirt", "jersey": "Sportswear", "polo": "Polo/T-Shirt",
    "shirt": "Casual Shirt", "blouse": "Casual Shirt",
    "jacket": "Active Jacket", "parka": "Winter Parka", "windbreaker": "Windbreaker", "cardigan": "Cardigan",
    "suit": "Business Suit", "tuxedo": "Formal Tuxedo", "blazer": "Business Suit",
    "coat": "Autumn Overcoat", "trench": "Trench Coat",
    "hoodie": "Hoodie", "sweatshirt": "Hoodie", "sweater": "Knit Sweater",
    "jean": "Denim Jeans", "denim": "Denim Jeans",
    "pant": "Classic Pants", "trouser": "Classic Pants", "chino": "Chinos",
    "shorts": "Active Shorts",
    "skirt": "Fashion Skirt", "miniskirt": "Short Skirt",
    "dress": "Evening Dress", "gown": "Gown", "abaya": "Abaya",
    "uniform": "Professional Uniform", "scrubs": "Medical Scrubs",
    "vest": "Vest", "waistcoat": "Waistcoat",
    "tank top": "Tank Top",
    "sweatpants": "Sweatpants", "joggers": "Joggers"
}

_models = None

def load_models():
    global _models
    if _models is not None:
        return _models
    
    print("[SYS] Loading Vision Core (Optimized Pro)...")
    try:
        pose = YOLO("yolo11m-pose.pt") # Optimized for Speed/Accuracy balance
        cls = YOLO("yolo11x-cls.pt")  # Heavy-duty for Classification
        print("[SYS] Intelligence Engined Loaded.")
    except:
        print("[WARN] Advanced models not found, using 'n' fallback.")
        pose = YOLO("yolo11n-pose.pt")
        cls = YOLO("yolo11n-cls.pt")
    
    _models = (pose, cls)
    return _models
