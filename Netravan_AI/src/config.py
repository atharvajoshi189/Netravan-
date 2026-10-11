import os


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _repo_data_path(*parts):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, *parts)


ALERT_PHONE_NUMBER = os.getenv("ALERT_PHONE_NUMBER", "").strip()
GAMMU_CONFIG_PATH = os.getenv("GAMMU_CONFIG_PATH", os.path.join(os.path.expanduser("~"), ".gammurc"))
SMS_DRY_RUN = _env_bool("SMS_DRY_RUN", True)
SMS_ENABLED_ALERT_TYPES = tuple(
    item.strip().lower()
    for item in os.getenv("SMS_ENABLED_ALERT_TYPES", "village_proximity").split(",")
    if item.strip()
)
SMS_RETRY_ATTEMPTS = max(1, int(os.getenv("SMS_RETRY_ATTEMPTS", "3")))
SMS_LOG_FILE = os.getenv(
    "SMS_LOG_FILE",
    _repo_data_path("data", "outputs", "sms_logs", "sms_notifications.log"),
)

SMS_ALERT_TYPE_ALIASES = {
    "VILLAGE_DISPERSAL": "village_proximity",
    "village_proximity": "village_proximity",
}

# Re-ID Similarity Matching & Enrollment Thresholds
REID_HIGH_CONFIDENCE_THRESHOLD = float(os.getenv("REID_HIGH_CONFIDENCE_THRESHOLD", "0.50"))
REID_LOW_CONFIDENCE_THRESHOLD = float(os.getenv("REID_LOW_CONFIDENCE_THRESHOLD", "0.35"))
REID_DUPLICATE_CHECK_THRESHOLD = float(os.getenv("REID_DUPLICATE_CHECK_THRESHOLD", "0.30"))
REID_MODEL_VERSION = os.getenv("REID_MODEL_VERSION", "hotspotter_sift_v1+resnet50_v1")