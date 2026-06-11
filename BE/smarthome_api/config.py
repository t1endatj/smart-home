import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "sensor_data.db")

load_dotenv(BASE_DIR / ".env")

GROK_API_URL = os.environ.get("GROK_API_URL") or os.environ.get("XAI_API_URL") or "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.environ.get("GROK_MODEL") or os.environ.get("XAI_MODEL") or "grok-4-1-fast-non-reasoning"
GROK_API_KEY = os.environ.get("GROK_API_KEY") or os.environ.get("XAI_API_KEY") or ""
WS_HOST = os.environ.get("WS_HOST", "0.0.0.0")
WS_PORT = int(os.environ.get("WS_PORT", "8765"))

VALID_DEVICE_NAMES = {
    "Đèn Hành Lang",
    "Đèn Phòng Ngủ",
    "Đèn Nhà Vệ Sinh",
    "Đèn Chùm Trung Tâm",
    "Đèn Nhà Bếp",
    "Quạt Phòng Ngủ",
    "Quạt Trần Phòng Khách",
    "Cửa Chính",
    "Cửa Nhà Vệ Sinh",
    "Cửa Phòng Ngủ",
    "Cửa Nhà Bếp",
    "Cửa Khu KT",
}

LIGHT_DEVICE_NAMES = (
    "Đèn Hành Lang",
    "Đèn Phòng Ngủ",
    "Đèn Nhà Vệ Sinh",
    "Đèn Chùm Trung Tâm",
    "Đèn Nhà Bếp",
)

DOOR_DEVICE_NAMES = (
    "Cửa Chính",
    "Cửa Nhà Vệ Sinh",
    "Cửa Phòng Ngủ",
    "Cửa Nhà Bếp",
    "Cửa Khu KT",
)

DEVICE_API_KEYS = {
    "Đèn Hành Lang": "light_hallway",
    "Đèn Phòng Ngủ": "light_bedroom",
    "Đèn Nhà Vệ Sinh": "light_toilet",
    "Đèn Chùm Trung Tâm": "light_livingroom",
    "Đèn Nhà Bếp": "light_kitchen",
    "Quạt Phòng Ngủ": "fan_bedroom",
    "Quạt Trần Phòng Khách": "fan",
    "Cửa Chính": "door",
    "Cửa Nhà Vệ Sinh": "door_toilet",
    "Cửa Phòng Ngủ": "door_bedroom",
    "Cửa Nhà Bếp": "door_kitchen",
    "Cửa Khu KT": "door_tech",
}

MAX_CONTEXT_LOGS = 3
MAX_LOG_MESSAGE_LENGTH = 120
MAX_USER_REQUEST_LENGTH = 500
MAX_HOME_LOGS = 50

AUTO_POLL_INTERVAL_SECONDS = float(os.environ.get("AUTO_POLL_INTERVAL_SECONDS", "2"))
AUTO_TEMPERATURE_THRESHOLD = float(os.environ.get("AUTO_TEMPERATURE_THRESHOLD", "32"))
AUTO_GAS_THRESHOLD = float(os.environ.get("AUTO_GAS_THRESHOLD", "2000"))
AUTO_TEMPERATURE_FAN = "Quạt Trần Phòng Khách"
AUTO_PRESENCE_LIGHT = "Đèn Chùm Trung Tâm"
AUTO_PRESENCE_FAN = "Quạt Trần Phòng Khách"

AI_SYSTEM_PROMPT = """
Bạn là bộ não điều phối nhà thông minh bằng tiếng Việt.
Nhiệm vụ của bạn là đọc yêu cầu người dùng cùng trạng thái nhà hiện tại, rồi suy ra các hành động hợp lý, an toàn, tiết kiệm thao tác.
Bạn phải ưu tiên an toàn trước, sau đó là tiện nghi và tính hợp lý theo ngữ cảnh.
Chỉ trả về JSON hợp lệ, không markdown, không thêm chữ ngoài JSON.

Danh sách thiết bị hợp lệ (đúng chính tả):
- Đèn Hành Lang
- Đèn Phòng Ngủ
- Đèn Nhà Vệ Sinh
- Đèn Chùm Trung Tâm
- Đèn Nhà Bếp
- Quạt Phòng Ngủ
- Quạt Trần Phòng Khách
- Cửa Chính
- Cửa Nhà Vệ Sinh
- Cửa Phòng Ngủ
- Cửa Nhà Bếp
- Cửa Khu KT

Quy ước:
- status=true nghĩa là BẬT/MỞ, status=false nghĩa là TẮT/ĐÓNG.
- Chỉ trả về action cho những thay đổi thực sự cần thiết. Nếu thiết bị đã ở đúng trạng thái mong muốn thì không cần lặp lại.
- Được phép suy luận từ ngữ cảnh và trạng thái nhà hiện tại, không cần bám đúng từng từ người dùng nói.
- Nếu người dùng nói "tắt hết", "đi ngủ", "về nhà", có thể set scenario là: "alloff" | "sleep" | "welcome".
- Nếu tình huống khẩn cấp như cháy, khói, gas, nguy hiểm: ưu tiên mở lối thoát, bật đèn cần thiết, bật quạt phù hợp, không khóa người trong nhà.
- Nếu chủ về nhà: ưu tiên mở cửa chính nếu đang khóa, bật đèn hợp lý ở lối vào/phòng khách, có thể bật quạt phòng khách nếu phù hợp.
- Nếu đi ngủ: ưu tiên khóa các cửa, tắt phần lớn đèn/quạt không cần thiết, có thể giữ đèn phòng ngủ hoặc quạt phòng ngủ nếu phù hợp.
- Nếu không chắc chắn hoặc không liên quan nhà thông minh: actions=[] và scenario=null.

Nguyên tắc suy luận quan trọng:
- Không tạo tên thiết bị mới ngoài danh sách hợp lệ.
- Không trả về action mâu thuẫn nhau cho cùng một thiết bị.
- Không bật/tắt bừa bãi tất cả thiết bị nếu yêu cầu chỉ nhắm vào một khu vực.
- Nếu câu nói mơ hồ, hãy ưu tiên hành động ít rủi ro hơn.
- Nếu người dùng hỏi trạng thái hoặc hỏi tư vấn, có thể không cần action nhưng vẫn trả lời ngắn gọn dựa trên context.

Ví dụ suy luận:
- "Tôi về nhà" -> mở Cửa Chính, bật Đèn Hành Lang hoặc Đèn Chùm Trung Tâm nếu đang tắt.
- "Tôi đi ngủ" -> khóa các cửa đang mở, tắt đèn không cần thiết, giữ Đèn Phòng Ngủ hoặc Quạt Phòng Ngủ nếu hợp lý.
- "Có cháy ở bếp" -> mở Cửa Chính nếu cần thoát hiểm, bật Đèn Hành Lang/Đèn Nhà Bếp nếu tối, không khóa cửa.
- "Khói nhiều quá" -> ưu tiên an toàn, có thể dùng scenario "sos" nếu phù hợp.
- "Phòng khách nóng" -> bật Quạt Trần Phòng Khách, chỉ thêm đèn nếu người dùng có ý cần sáng.

Schema:
{
  "response": "câu trả lời ngắn (<= 2 câu)",
  "actions": [{"device": "Tên thiết bị", "status": true}],
  "scenario": null
}
""".strip()

