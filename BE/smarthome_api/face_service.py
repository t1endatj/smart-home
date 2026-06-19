import base64
import os
import urllib.request
from pathlib import Path
import cv2
import numpy as np

# Đường dẫn thư mục
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
REFERENCE_IMAGE_PATH = BASE_DIR / "reference_face.jpg"

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
        # Sử dụng request chuyên biệt có cấu hình User-Agent để tránh bị chặn
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
    """Khởi tạo mô hình phát hiện (YuNet) và nhận dạng (SFace).

    Nếu không có, tự động tải xuống. Nếu tải hoặc nạp thất bại, kích hoạt chế độ fallback.
    """
    global _detector, _recognizer, _use_fallback

    if _use_fallback:
        return

    # Nếu đã khởi tạo thành công trước đó
    if _detector is not None and _recognizer is not None:
        return

    try:
        # Tải mô hình nếu chưa có
        if not YUNET_PATH.exists():
            download_file(YUNET_URL, YUNET_PATH)
        if not SFACE_PATH.exists():
            download_file(SFACE_URL, SFACE_PATH)

        # Nạp mô hình YuNet
        # Lưu ý: Cần set input size tạm thời (ví dụ: 320x320), sau này khi detect sẽ cập nhật theo ảnh đầu vào
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

        # Nạp mô hình SFace
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
    """Giải mã chuỗi base64 thành ảnh OpenCV (numpy array BGR)."""
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
        
        # Cắt khuôn mặt đầu tiên phát hiện được và chuyển về size 128x128
        x, y, w, h = faces[0]
        face_img = gray[y:y+h, x:x+w]
        return cv2.resize(face_img, (128, 128))
    except Exception as exc:
        print(f"[FaceService] Fallback detection error: {exc}")
        return None


def verify_face_fallback(ref_img: np.ndarray, query_img: np.ndarray) -> bool:
    """Fallback: So khớp hai mặt dùng thuật toán trích xuất đặc trưng ORB."""
    try:
        ref_face = detect_and_crop_face_fallback(ref_img)
        query_face = detect_and_crop_face_fallback(query_img)

        if ref_face is None or query_face is None:
            return False

        # Khởi tạo bộ trích xuất đặc trưng ORB
        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(ref_face, None)
        kp2, des2 = orb.detectAndCompute(query_face, None)

        if des1 is None or des2 is None:
            return False

        # Đối sánh đặc trưng qua BFMatcher
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        # Lọc các điểm khớp có khoảng cách nhỏ (tương đồng cao)
        good_matches = [m for m in matches if m.distance < 50]
        
        # Nếu có tối thiểu 15 điểm khớp chất lượng tốt
        print(f"[FaceService] ORB Fallback matches: {len(good_matches)}")
        return len(good_matches) >= 15
    except Exception as exc:
        print(f"[FaceService] Fallback verification error: {exc}")
        return False

# ----------------- MAIN SERVICE FUNCTIONS -----------------

def register_face(base64_str: str) -> dict:
    """Đăng ký khuôn mặt gốc (lưu làm reference_face.jpg)."""
    img = decode_base64_image(base64_str)
    if img is None:
        return {"result": False, "message": "Dữ liệu ảnh không hợp lệ."}

    init_models()

    if _use_fallback:
        # Sử dụng Haar Cascade để kiểm thử khuôn mặt trước khi lưu
        face = detect_and_crop_face_fallback(img)
        if face is None:
            return {"result": False, "message": "Không tìm thấy khuôn mặt trong ảnh để đăng ký."}
    else:
        # Sử dụng YuNet
        h, w, _ = img.shape
        _detector.setInputSize((w, h))
        retval, faces = _detector.detect(img)
        if retval == 0 or faces is None:
            return {"result": False, "message": "Không tìm thấy khuôn mặt trong ảnh để đăng ký."}

    # Lưu ảnh đối chiếu gốc
    try:
        cv2.imwrite(str(REFERENCE_IMAGE_PATH), img)
        print(f"[FaceService] Registered new face template to {REFERENCE_IMAGE_PATH}")
        return {"result": True, "message": "Đăng ký khuôn mặt đối chiếu thành công!"}
    except Exception as exc:
        return {"result": False, "message": f"Không thể lưu ảnh đối chiếu: {exc}"}


def verify_face(base64_str: str) -> dict:
    """So khớp khuôn mặt base64 nhận được với khuôn mặt đối chiếu đã lưu."""
    if not REFERENCE_IMAGE_PATH.exists():
        return {"result": False, "error": "Chưa đăng ký khuôn mặt đối chiếu."}

    query_img = decode_base64_image(base64_str)
    if query_img is None:
        return {"result": False, "error": "Ảnh chụp từ camera không hợp lệ."}

    ref_img = cv2.imread(str(REFERENCE_IMAGE_PATH))
    if ref_img is None:
        return {"result": False, "error": "Tệp đối chiếu cũ bị hỏng hoặc lỗi."}

    init_models()

    # Chạy Fallback nếu được kích hoạt
    if _use_fallback:
        matched = verify_face_fallback(ref_img, query_img)
        return {"result": matched, "method": "fallback_orb"}

    try:
        # 1. Phát hiện khuôn mặt trong ảnh đối chiếu
        h_ref, w_ref, _ = ref_img.shape
        _detector.setInputSize((w_ref, h_ref))
        retval_ref, faces_ref = _detector.detect(ref_img)
        if retval_ref == 0 or faces_ref is None:
            return {"result": False, "error": "Khuôn mặt đối chiếu đã lưu không rõ nét."}

        # 2. Phát hiện khuôn mặt trong ảnh quét mới
        h_q, w_q, _ = query_img.shape
        _detector.setInputSize((w_q, h_q))
        retval_q, faces_q = _detector.detect(query_img)
        if retval_q == 0 or faces_q is None:
            return {"result": False, "message": "Không phát hiện thấy khuôn mặt trong ảnh quét."}

        # 3. Cắt và xoay chỉnh khuôn mặt (Align & Crop)
        face_ref_align = _recognizer.alignCrop(ref_img, faces_ref[0])
        face_query_align = _recognizer.alignCrop(query_img, faces_q[0])

        # 4. Trích xuất đặc trưng khuôn mặt (Face Embeddings)
        feat_ref = _recognizer.feature(face_ref_align)
        feat_query = _recognizer.feature(face_query_align)

        # 5. Tính toán khoảng cách Cosine Similarity
        cosine_score = _recognizer.match(feat_ref, feat_query, cv2.FaceRecognizerSF_FR_COSINE)
        matched = cosine_score >= COSINE_THRESHOLD

        print(f"[FaceService] Cosine similarity: {cosine_score:.4f} (Matched: {matched})")
        return {"result": bool(matched), "score": float(cosine_score), "method": "sface"}

    except Exception as exc:
        print(f"[FaceService] SFace verify error: {exc}. Trying fallback...")
        matched = verify_face_fallback(ref_img, query_img)
        return {"result": matched, "method": "fallback_orb"}


def delete_face() -> dict:
    """Xóa ảnh đối chiếu đã lưu."""
    try:
        if REFERENCE_IMAGE_PATH.exists():
            REFERENCE_IMAGE_PATH.unlink()
            print("[FaceService] Deleted face template file.")
            return {"result": True, "message": "Đã xóa ảnh khuôn mặt đối chiếu."}
        return {"result": True, "message": "Không có khuôn mặt nào để xóa."}
    except Exception as exc:
        return {"result": False, "message": f"Lỗi khi xóa ảnh đối chiếu: {exc}"}


def has_reference_face() -> bool:
    """Kiểm tra xem đã có ảnh đối chiếu chưa."""
    return REFERENCE_IMAGE_PATH.exists()
