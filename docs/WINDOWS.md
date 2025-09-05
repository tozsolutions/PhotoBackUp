# Windows 11 Setup

This machine hosts the LAN backup server and stores daily folders. It does not need public internet exposure.

## Install
1. Install Python 3.9+ (from `python.org`) and select “Add to PATH”.
2. In this repo folder:
   ```bat
   pip install -e .
   ```

## Run the Server
```bat
set PHOTO_BACKUP_ROOT=C:\Backups\PhotoBackUp
set PHOTO_BACKUP_API_KEY=choose-a-strong-key
photobackup-server
```
This serves on `http://0.0.0.0:8080` by default. Replace with a fixed LAN IP if needed.

## Create a Daily Schedule (Task Scheduler)
- Ensure the server is running before 18:00. Two options:
  1) Run server at logon: create a shortcut in Startup or a scheduled task “At log on”.
  2) Create a daily 17:55 task which starts the server if not running.

PowerShell helper (run as Administrator):
```powershell
$env:PHOTO_BACKUP_ROOT = "C:\Backups\PhotoBackUp"
$env:PHOTO_BACKUP_API_KEY = "choose-a-strong-key"
$Action = New-ScheduledTaskAction -Execute "python" -Argument "-m photobackup.server"
$Trigger = New-ScheduledTaskTrigger -Daily -At 17:55
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName "PhotoBackUpServer" -Settings $Settings -Description "Start PhotoBackUp server before daily backups"
```

Note: Windows Task Scheduler cannot filter on specific SSID. We enforce SSID on the mobile side. If needed, you can script an SSID check in your own wrappers using `netsh wlan show interfaces`.

## Optional: IMAP Email Backup
Use one of these tools on Windows to mirror your mail to local Maildir:
- `getmail6` or `isync/mbsync` (via WSL) or Python IMAP backup scripts.
Schedule daily at 18:10 and place outputs under `%PHOTO_BACKUP_ROOT%\\YYYY-MM-DD`.

## Restore / Browse
- Open `http://<PC-IP>:8080/list` to see daily folders.
- Files are named by content hash to deduplicate. Use the date folder context to find items. You can add descriptive naming by enhancing the server to include EXIF datetime and original filename.