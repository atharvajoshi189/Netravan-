import logging
import os
import time

from ..config import SMS_LOG_FILE, SMS_RETRY_ATTEMPTS

try:
    import gammu  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    gammu = None


class SMSNotifier:
    def __init__(self, phone_number: str, gammu_config_path: str, dry_run: bool = False):
        self.phone_number = phone_number.strip()
        self.gammu_config_path = os.path.expanduser(gammu_config_path.strip()) if gammu_config_path else ""
        self.dry_run = dry_run
        self.retry_attempts = SMS_RETRY_ATTEMPTS
        self.logger = self._build_logger()

    def _build_logger(self):
        logger = logging.getLogger("TigerTraceAI.SMSNotifier")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        log_path = os.path.abspath(SMS_LOG_FILE)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        has_file_handler = False
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler) and getattr(handler, "baseFilename", None) == log_path:
                has_file_handler = True
                break

        if not has_file_handler:
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def _format_message(self, alert: dict) -> str:
        tiger_id = alert.get("tiger_id") or "UNKNOWN_TIGER"
        village_name = alert.get("village_name") or "unknown village"
        distance_km = alert.get("distance_km")
        station_id = alert.get("station_id") or "unknown station"
        station_range = alert.get("station_range_name") or alert.get("range_name")
        timestamp = alert.get("timestamp") or alert.get("detected_at") or "unknown time"

        distance_part = f"{float(distance_km):.1f} km" if isinstance(distance_km, (int, float)) else "nearby"
        station_part = f" {station_range}" if station_range else ""
        message = (
            f"TigerTrace AI ALERT: {tiger_id} near {village_name} ({distance_part}). "
            f"Station {station_id}{station_part}. Time {timestamp}"
        )
        return message[:159]

    def _send_via_gammu(self, message_text: str) -> None:
        if gammu is None:
            raise RuntimeError("python-gammu is not installed")

        state_machine = gammu.StateMachine()
        if self.gammu_config_path:
            state_machine.ReadConfig(Filename=self.gammu_config_path)
        else:
            state_machine.ReadConfig()

        state_machine.Init()
        sms_message = {
            "Text": message_text,
            "SMSC": {"Location": 1},
            "Number": self.phone_number,
        }
        state_machine.SendSMS(sms_message)

    def send_alert_sms(self, alert: dict) -> bool:
        message_text = self._format_message(alert)

        if not self.phone_number:
            self.logger.error("SMS send skipped: ALERT_PHONE_NUMBER is empty. Alert=%s", message_text)
            return False

        if self.dry_run:
            self.logger.info("SMS dry run to %s | %s", self.phone_number, message_text)
            return True

        for attempt in range(1, self.retry_attempts + 1):
            try:
                self._send_via_gammu(message_text)
                self.logger.info("SMS sent to %s on attempt %d | %s", self.phone_number, attempt, message_text)
                return True
            except Exception as exc:
                self.logger.warning(
                    "SMS send attempt %d/%d failed for %s: %s",
                    attempt,
                    self.retry_attempts,
                    self.phone_number,
                    exc,
                )
                if attempt < self.retry_attempts:
                    time.sleep(min(2 ** (attempt - 1), 5))

        self.logger.error("SMS send failed after %d attempts for %s | %s", self.retry_attempts, self.phone_number, message_text)
        return False

    def close(self):
        for handler in list(self.logger.handlers):
            try:
                handler.flush()
            except Exception:
                pass
            try:
                handler.close()
            except Exception:
                pass
            try:
                self.logger.removeHandler(handler)
            except Exception:
                pass