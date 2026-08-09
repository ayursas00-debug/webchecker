# Estonian Visa Checker

Automatically monitors the Estonian embassy website for D-visa availability at the Embassy in New Delhi.

## Features

- ✅ Runs automatically from 10 AM to 5 PM every day
- ✅ Checks every 1 minute during working hours
- ✅ Sends push notifications via ntfy.sh
- ✅ Automatic daily scheduling with Windows Task Scheduler

## Setup Instructions

### 1. Install Dependencies (One-time setup)

```powershell
pip install playwright requests
playwright install chromium
```

### 2. Test the Script Manually

```powershell
python check_continuous.py
```

The script will:
- Wait until 10 AM if started before working hours
- Run checks from 10 AM to 5 PM
- Stop at 5 PM and wait until next day
- Send notifications to: https://ntfy.sh/webchecker

### 3. Setup Automatic Daily Scheduling

Run the PowerShell setup script (may require Administrator privileges):

```powershell
powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1
```

This creates a Windows Task that:
- Starts automatically at 9:55 AM every day
- Runs the visa checker from 10 AM to 5 PM
- Restarts automatically even after system reboots

### 4. Subscribe to Notifications

Visit or subscribe to: **https://ntfy.sh/webchecker**

You'll receive notifications for:
- 🤖 Bot start (10 AM)
- 🎉 D-visa found (3 urgent alerts)
- 📅 Day ended (5 PM)
- ⏹️ Bot stopped (if manually stopped)

## Manual Controls

### Start the checker manually:
```powershell
python check_continuous.py
```

### Start the scheduled task immediately:
```powershell
Start-ScheduledTask -TaskName "EstoniaVisaChecker"
```

### Stop the scheduled task:
```powershell
Stop-ScheduledTask -TaskName "EstoniaVisaChecker"
```

### Remove the scheduled task:
```powershell
Unregister-ScheduledTask -TaskName "EstoniaVisaChecker" -Confirm:$false
```

### View all scheduled tasks:
```powershell
taskschd.msc
```

## Configuration

Edit `check_continuous.py` to customize:

```python
# Target embassy
TARGET_OFFICE_TEXT = "New Delhi"

# Check interval (seconds)
CHECK_INTERVAL = 60  # 1 minute

# Working hours
START_HOUR = 10  # 10 AM
END_HOUR = 17    # 5 PM

# Notification URL
NTFY_URL = "https://ntfy.sh/webchecker"
```

## Files

- `check_once.py` - Single check script (for testing)
- `check_continuous.py` - Main monitoring script with scheduling
- `start_checker.bat` - Windows batch file to start manually
- `setup_scheduler.ps1` - PowerShell script to setup Task Scheduler
- `README.md` - This file

## Troubleshooting

### Script doesn't start automatically
- Check Task Scheduler: `taskschd.msc`
- Verify the task "EstoniaVisaChecker" exists and is enabled
- Check task history for errors

### Not receiving notifications
- Visit https://ntfy.sh/webchecker to verify subscription
- Check if the script is running during working hours
- Verify internet connection

### Python not found
- Ensure Python is installed and in PATH
- Run: `python --version` to verify

## Notes

- The script automatically handles time outside working hours
- You can leave it running 24/7 - it will wait until 10 AM to start checking
- The script is safe to run continuously and will restart each day
- All timestamps are in your local system time
