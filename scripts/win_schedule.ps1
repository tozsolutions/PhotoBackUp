Param(
    [string]$BackupRoot = "C:\\Backups\\PhotoBackUp",
    [string]$ApiKey = "",
    [string]$At = "17:55"
)

$env:PHOTO_BACKUP_ROOT = $BackupRoot
if ($ApiKey -ne "") { $env:PHOTO_BACKUP_API_KEY = $ApiKey }

$Action = New-ScheduledTaskAction -Execute "python" -Argument "-m photobackup.server"
$Trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date $At)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName "PhotoBackUpServer" -Settings $Settings -Description "Start PhotoBackUp server before daily backups" -Force
Write-Host "Scheduled 'PhotoBackUpServer' at $At with root $BackupRoot"