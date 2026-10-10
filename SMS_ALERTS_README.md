# SMS Alerts For TigerTrace_AI

This feature sends an offline SMS immediately when the alert engine raises a village-proximity alert. It is designed for a Linux field laptop with a USB GSM modem and SIM card attached.

## What This Uses

- `python-gammu` for modem control in live mode.
- A Gammu configuration file, usually `~/.gammurc`.
- A configurable phone number for the first deployment.
- A dry-run mode for testing without hardware.

The code only triggers SMS for the alert routing type `village_proximity` for now. In the current alert engine, the database alert row remains `VILLAGE_DISPERSAL`, but the SMS hook maps that event to `village_proximity` so the transport layer stays decoupled from the storage schema.

## Linux Install Steps

On Ubuntu or Debian-based field laptops:

```bash
sudo apt update
sudo apt install gammu gammu-smsd python3-pip
pip install python-gammu
```

If you use a different distribution, install the equivalent Gammu packages from your package manager.

## Gammu Config

Create `~/.gammurc` for direct modem access through python-gammu.

Example:

```ini
[gammu]
port = /dev/ttyUSB0
connection = at115200
name = TigerTrace field modem
```

Find the real modem device with `dmesg | tail`, `ls /dev/ttyUSB*`, or your distro's serial device tools. Some modems appear as `/dev/ttyACM0` instead.

Test the modem before using TigerTrace_AI:

```bash
gammu --identify -c ~/.gammurc
```

If you prefer Gammu-SMSD queue-based delivery, you can also run SMSD as a service and point it at the same modem config. The application code here still uses the python-gammu send path because it gives immediate delivery feedback and keeps the hook simple.

## Environment Variables

Set these in your shell, `.env`, or launch script:

```bash
export ALERT_PHONE_NUMBER="919999999999"
export GAMMU_CONFIG_PATH="$HOME/.gammurc"
export SMS_DRY_RUN="true"
```

Optional:

```bash
export SMS_ENABLED_ALERT_TYPES="village_proximity"
export SMS_RETRY_ATTEMPTS="3"
```

## How To Use It In Code

```python
from src.pipeline import TigerTracePipeline

pipeline = TigerTracePipeline(
    enable_sms_alerts=True,
    alert_phone_number="919999999999",
    gammu_config_path="/home/field/.gammurc",
    sms_dry_run=True,
)
```

If `enable_sms_alerts=True`, the pipeline passes an `on_alert_raised` callback into the deviation engine. The SMS is sent immediately when a village-proximity alert is inserted into SQLite.

## Dry-Run Mode

Keep `SMS_DRY_RUN=true` until the modem is physically attached and verified. In dry-run mode:

- No SMS is transmitted.
- The formatted message is written to the SMS log file.
- You can validate the full alert flow without hardware.

The default is dry-run, so the system stays safe on a laptop that does not yet have a modem configured.

## Log File

SMS activity is written to:

`TigerTrace_AI/data/outputs/sms_logs/sms_notifications.log`

This includes dry-run messages, retries, success, and failure details.

## Testing Without Hardware

Run the test file:

```bash
python -m unittest tests.test_sms_notifier
```

Or run the whole suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests mock the Gammu backend and verify that:

- The notifier formats the SMS text correctly.
- The Gammu state machine is called in live mode.
- The deviation engine calls the SMS callback when a village-proximity alert is generated.

## Flip To Live Mode

When the modem is verified:

1. Set `SMS_DRY_RUN=false`.
2. Confirm `ALERT_PHONE_NUMBER` is correct.
3. Confirm `GAMMU_CONFIG_PATH` points to the modem config file.
4. Run the pipeline on a controlled test alert first.

Example:

```bash
export SMS_DRY_RUN="false"
python run_demo.py
```

## Assumptions

- The current SQLite schema already stores alerts in the `alerts` table, which is enough for persistence.
- The existing alert row type for village proximity is `VILLAGE_DISPERSAL`, so the SMS layer adds a separate routing label instead of changing the database schema.
- The first rollout is one phone number only.