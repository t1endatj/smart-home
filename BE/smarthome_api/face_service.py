import base64
import os
import urllib.request
from pathlib import Path
import cv2
import numpy as np

# Đường dẫn thư mục
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
FACES_DIR = BASE_DIR / "faces"

# Đảm bảo thư mục faces tồn tại
FACES_DIR.mkdir(parents=True, exist_ok=True)

# URL tải mô hình ONNX
YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

YUNET_PATH = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
SFACE_PATH = MODELS_DIR / "face_recognition_sface_2021dec.onnx"

# Ngưỡng Cosine Similarity cho SFace
COSINE_THRESHOLD = 0.363

# Caching models
_detector = None
_recognizer = None
_use_fallback = False


def download_file(url: str, dest_path: Path):
    """Tải tệp từ internet lưu vào dest_path."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[FaceService] Downloading {url} to {dest_path}...")
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, "wb") as out_file:
            out_file.write(response.read())
        print(f"[FaceService] Successfully downloaded to {dest_path}")
    except Exception as exc:
        print(f"[FaceService] Error downloading model {url}: {exc}")
        raise exc


def init_models():
    """Khởi tạo mô hình phát hiện (YuNet) và nhận dạng (SFace)."""
    global _detector, _recognizer, _use_fallback

    if _use_fallback:
        return

    if _detector is not None and _recognizer is not None:
        return

    try:
        if not YUNET_PATH.exists():
            download_file(YUNET_URL, YUNET_PATH)
        if not SFACE_PATH.exists():
            download_file(SFACE_URL, SFACE_PATH)

        _detector = cv2.FaceDetectorYN.create(
            model=str(YUNET_PATH),
            config="",
            input_size=(320, 320),
            score_threshold=0.9,
            nms_threshold=0.3,
            top_k=5000,
            backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
            target_id=cv2.dnn.DNN_TARGET_CPU
        )

        _recognizer = cv2.FaceRecognizerSF.create(
            model=str(SFACE_PATH),
            config="",
            backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
            target_id=cv2.dnn.DNN_TARGET_CPU
        )

        print("[FaceService] YuNet & SFace models initialized successfully.")

    except Exception as exc:
        print(f"[FaceService] Failed to load ONNX models. Activating ORB Fallback mode: {exc}")
        _use_fallback = True


def decode_base64_image(base64_str: str) -> np.ndarray | None:
    """Giải mã chuỗi base64 thành ảnh BGR."""
    try:
        if "," in base64_str:
            _, encoded = base64_str.split(",", 1)
        else:
            encoded = base64_str
        image_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(image_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as exc:
        print(f"[FaceService] Error decoding base64 image: {exc}")
        return None


# ---------------- FALLBACK ORB IMPLEMENTATION ----------------

def detect_and_crop_face_fallback(img: np.ndarray) -> np.ndarray | None:
    """Fallback: Phát hiện và cắt mặt dùng Haar Cascade."""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            return None
        
        x, y, w, h = faces[0]
        face_img = gray[y:y+h, x:x+w]
        return cv2.resize(face_img, (128, 128))
    except Exception as exc:
        print(f"[FaceService] Fallback detection error: {exc}")
        return None


def verify_face_fallback(ref_img: np.ndarray, query_img: np.ndarray) -> bool:
    """Fallback: So khớp hai mặt dùng thuật toán ORB."""
    try:
        ref_face = detect_and_crop_face_fallback(ref_img)
        query_face = detect_and_crop_face_fallback(query_img)

        if ref_face is None or query_face is None:
            return False

        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(ref_face, None)
        kp2, des2 = orb.detectAndCompute(query_face, None)

        if des1 is None or des2 is None:
            return False

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        good_matches = [m for m in matches if m.distance < 50]
        
        print(f"[FaceService] ORB Fallback matches: {len(good_matches)}")
        return len(good_matches) >= 15
    except Exception as exc:
        print(f"[FaceService] Fallback verification error: {exc}")
        return False

# ----------------- MAIN SERVICE FUNCTIONS -----------------

def verify_face(base64_str: str) -> dict:
    """Giải mã ảnh quét và so khớp với toàn bộ các ảnh chân dung có trong thư mục faces/."""
    query_img = decode_base64_image(base64_str)
    if query_img is None:
        return {"result": False, "error": "Ảnh chụp từ camera không hợp lệ."}

    # Quét tất cả các tệp hình ảnh trong thư mục faces
    valid_suffixes = {".jpg", ".jpeg", ".png"}
    face_files = [p for p in FACES_DIR.iterdir() if p.suffix.lower() in valid_suffixes]

    if not face_files:
        return {
            "result": False,
            "error": "Thư mục đối chiếu trống. Hãy thêm ít nhất một ảnh chân dung vào thư mục BE/faces/."
        }

    init_models()

    # Trích xuất đặc trưng của ảnh quét mới (nếu không dùng fallback)
    feat_query = None
    faces_q = None
    if not _use_fallback:
        try:
            h_q, w_q, _ = query_img.shape
            _detector.setInputSize((w_q, h_q))
            retval_q, faces_q = _detector.detect(query_img)
            if retval_q > 0 and faces_q is not None:
                face_query_align = _recognizer.alignCrop(query_img, faces_q[0])
                feat_query = _recognizer.feature(face_query_align)
            else:
                return {"result": False, "message": "Không phát hiện thấy khuôn mặt trong ảnh quét."}
        except Exception as exc:
            print(f"[FaceService] SFace error on query image. Activating fallback: {exc}")
            # Nếu gặp lỗi dnn khi trích xuất query image, tự kích hoạt fallback
            pass

    # Duyệt qua từng ảnh mẫu trong thư mục để so khớp
    for file_path in face_files:
        ref_img = cv2.imread(str(file_path))
        if ref_img is None:
            continue

        # Chạy thuật toán chính hoặc fallback
        if not _use_fallback and feat_query is not None:
            try:
                h_ref, w_ref, _ = ref_img.shape
                _detector.setInputSize((w_ref, h_ref))
                retval_ref, faces_ref = _detector.detect(ref_img)
                if retval_ref == 0 or faces_ref is None:
                    continue

                face_ref_align = _recognizer.alignCrop(ref_img, faces_ref[0])
                feat_ref = _recognizer.feature(face_ref_align)

                cosine_score = _recognizer.match(feat_ref, feat_query, cv2.FaceRecognizerSF_FR_COSINE)
                if cosine_score >= COSINE_THRESHOLD:
                    print(f"[FaceService] Match found: {file_path.name} (score: {cosine_score:.4f})")
                    return {
                        "result": True,
                        "name": file_path.stem,
                        "score": float(cosine_score),
                        "method": "sface"
                    }
            except Exception as exc:
                print(f"[FaceService] Error processing template {file_path.name} with SFace: {exc}")
                # Thử dùng fallback ORB cho ảnh này
                if verify_face_fallback(ref_img, query_img):
                    return {
                        "result": True,
                        "name": file_path.stem,
                        "method": "fallback_orb"
                    }
        else:
            # Chế độ Fallback ORB
            if verify_face_fallback(ref_img, query_img):
                print(f"[FaceService] Match found in fallback: {file_path.name}")
                return {
                    "result": True,
                    "name": file_path.stem,
                    "method": "fallback_orb"
                }

    # Không khớp với bất kỳ ảnh nào
    return {"result": False, "message": "Khuôn mặt không trùng khớp với bất kỳ mẫu nào."}
