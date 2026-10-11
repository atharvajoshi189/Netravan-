import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from src.alerts.deviation_engine import DeviationAlertEngine
from src.alerts.sms_notifier import SMSNotifier
from src.db.schema import get_connection, init_db, seed_sample_stations


class TestSMSNotifier(unittest.TestCase):
    def test_dry_run_logs_formatted_sms(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            log_file = os.path.join(tmp_dir, "sms_notifications.log")
            alert = {
                "alert_type": "VILLAGE_DISPERSAL",
                "sms_alert_type": "village_proximity",
                "tiger_id": "BAJIRAO",
                "village_name": "Kohka Village",
                "distance_km": 1.4,
                "station_id": "PTR_STN_18",
                "station_range_name": "Kohka_Fringe",
                "timestamp": "2026-08-17 08:30:00",
            }

            with patch("src.alerts.sms_notifier.SMS_LOG_FILE", log_file):
                notifier = SMSNotifier("9999999999", "/tmp/unused-gammu.cfg", dry_run=True)
                try:
                    self.assertTrue(notifier.send_alert_sms(alert))
                finally:
                    notifier.close()

            with open(log_file, "r", encoding="utf-8") as handle:
                log_text = handle.read()

            self.assertIn("dry run", log_text.lower())
            self.assertIn("BAJIRAO", log_text)
            self.assertIn("Kohka Village", log_text)
            self.assertIn("PTR_STN_18", log_text)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_live_mode_uses_gammu_state_machine(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            config_file = os.path.join(tmp_dir, "gammurc")
            with open(config_file, "w", encoding="utf-8") as handle:
                handle.write("[gammu]\nport = dummy\nconnection = at\n")

            log_file = os.path.join(tmp_dir, "sms_notifications.log")
            fake_state_machine = MagicMock()
            fake_gammu = MagicMock()
            fake_gammu.StateMachine.return_value = fake_state_machine

            alert = {
                "alert_type": "VILLAGE_DISPERSAL",
                "sms_alert_type": "village_proximity",
                "tiger_id": "SWASTIK",
                "village_name": "Turia Village",
                "distance_km": 2.1,
                "station_id": "PTR_STN_01",
                "station_range_name": "Turia",
                "timestamp": "2026-08-17 09:15:00",
            }

            with patch("src.alerts.sms_notifier.gammu", fake_gammu), patch("src.alerts.sms_notifier.SMS_LOG_FILE", log_file):
                notifier = SMSNotifier("919999999999", config_file, dry_run=False)
                try:
                    self.assertTrue(notifier.send_alert_sms(alert))
                finally:
                    notifier.close()

            fake_gammu.StateMachine.assert_called_once()
            fake_state_machine.ReadConfig.assert_called_once_with(Filename=config_file)
            fake_state_machine.Init.assert_called_once()
            fake_state_machine.SendSMS.assert_called_once()

            sent_message = fake_state_machine.SendSMS.call_args.args[0]
            self.assertIn("SWASTIK", sent_message["Text"])
            self.assertIn("Turia Village", sent_message["Text"])
            self.assertEqual(sent_message["Number"], "919999999999")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_engine_triggers_sms_callback_for_village_alert(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmp_dir, "tigertrace.db")
            init_db(db_path)
            seed_sample_stations(db_path)
            conn = get_connection(db_path)

            sms_callback = Mock(return_value=True)
            engine = DeviationAlertEngine(
                conn,
                on_alert_raised=sms_callback,
                sms_enabled_alert_types=("village_proximity",),
            )

            batch_sightings = [
                {
                    "sighting_id": 101,
                    "tiger_id": "BAJIRAO",
                    "station_id": "PTR_STN_18",
                    "timestamp": "2026-08-17 10:00:00",
                }
            ]

            alerts = engine.evaluate_batch_alerts(batch_sightings)

            self.assertTrue(any(alert.get("sms_alert_type") == "village_proximity" for alert in alerts))
            self.assertGreaterEqual(sms_callback.call_count, 1)

            village_names = [call.args[0].get("village_name") for call in sms_callback.call_args_list]
            self.assertIn("Kohka Village", village_names)
            self.assertIn("PTR_STN_18", [call.args[0].get("station_id") for call in sms_callback.call_args_list])

            conn.close()
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()