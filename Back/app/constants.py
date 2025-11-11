"""애플리케이션 전역 상수 정의"""

# ==========================================================
# 알림 설정 기본값
# ==========================================================
DEFAULT_NOTIFICATION_HOUR = 7
DEFAULT_NOTIFICATION_MINUTE = 0
DEFAULT_NOTIFICATION_DAYS = [0, 1, 2, 3, 4]  # 월요일(0) ~ 금요일(4)
DEFAULT_NOTIFICATION_ALLOWED = False
DEFAULT_NOTIFICATION_TIME_ENABLED = False
DEFAULT_NOTIFICATION_PROMPTED = False

# ==========================================================
# 닉네임 생성 관련
# ==========================================================
MAX_NICKNAME_LENGTH = 30
MAX_NICKNAME_SUFFIX_ATTEMPTS = 100
FALLBACK_NICKNAME_HEX_LENGTH = 6
