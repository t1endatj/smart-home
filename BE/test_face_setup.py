import sys
from pathlib import Path

# Them thu muc BE vao python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

print("==================================================")
print("   SMART HOME - FACE ID SYSTEM SETUP & TEST       ")
print("==================================================")

# 1. Kiem tra moi truong Python
print(f"[*] Phien ban Python: {sys.version}")

# 2. Kiem tra thu vien OpenCV & Numpy
try:
    import cv2
    import numpy as np
    print(f"[*] OpenCV version: {cv2.__version__}")
    print(f"[*] Numpy version: {np.__version__}")
except ImportError as e:
    print(f"[!] LOI: Thieu thu vien OpenCV hoac Numpy.")
    print("    Vui long cai dat day du dependencies bang lenh:")
    print("    pip install -r requirements.txt")
    sys.exit(1)

# 3. Import face_service va chay khoi tao mo hinh
try:
    from smarthome_api.face_service import init_models, MODELS_DIR, YUNET_PATH, SFACE_PATH, FACES_DIR
    print("[*] Dang khoi tao mo hinh (Tu dong tai xuong cac tep ONNX neu chua co)...")
    init_models()
    
    print("\n================ BAO CAO THIET LAP ================")
    print(f"- Thu muc chua anh mau: {FACES_DIR}")
    print(f"- Thu muc chua mo hinh: {MODELS_DIR}")
    print(f"- Trang thai mo hinh phat hien (YuNet): {'DA TAI XUONG' if YUNET_PATH.exists() else 'THAT BAI'}")
    print(f"- Trang thai mo hinh nhan dang (SFace): {'DA TAI XUONG' if SFACE_PATH.exists() else 'THAT BAI'}")
    
    # Kiem tra xem co anh mau nao trong faces/ chua
    valid_suffixes = {".jpg", ".jpeg", ".png"}
    face_files = [p for p in FACES_DIR.iterdir() if p.suffix.lower() in valid_suffixes]
    print(f"- So luong anh mau da co trong thu muc faces/: {len(face_files)}")
    for f in face_files:
        print(f"  + {f.name} (Ten nhan dien: {f.stem})")
        
    if not face_files:
        print("\n[!] LUU Y CHO DEVELOPER BACKEND:")
        print("    Vui long sao chep it nhat mot anh chan dung cua thanh vien vao thu muc:")
        print(f"    {FACES_DIR}")
        print("    Vi du: 'phuc.jpg' hoac 'dat.png' de lam du lieu doi chieu.")

    print("\n[*] Thiet lap Face ID hoan tat thanh cong! San sang chay FastAPI server.")
    print("    Hay chay: uvicorn smarthome_api.app:app --reload --port 8000")
    print("==================================================")
except Exception as e:
    print(f"[!] Loi khi thiet lap Face ID: {e}")
    sys.exit(1)
