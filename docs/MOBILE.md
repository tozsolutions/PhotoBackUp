# Mobile Setup (Android & iOS)

This guide shows practical, no-root ways to trigger daily uploads at 18:00 only on your home Wi‑Fi SSIDs (e.g., `TOZ 2.4G` or `TOZ 5G`). The server must be reachable on your LAN (Windows PC running `photobackup-server`).

Server endpoint:
- URL: `http://<PC-IP>:8080/upload`
- Header (optional): `x-api-key: <YOUR_KEY>` if you set `PHOTO_BACKUP_API_KEY`
- Form field: `file` (multipart) per uploaded file

## iOS (Shortcuts)
Constraints: iOS cannot access call logs or SMS, and background triggers have limits. We focus on Photos/Videos.

Steps:
1. Open Shortcuts → Automation → New Personal Automation → Time of Day → 18:00 → Daily.
2. Add Action: If → Condition: Network Name equals `TOZ 2.4G` OR `TOZ 5G`.
3. In the If branch:
   - Action: Find Photos → Filter: Date is Today, Include Videos if desired.
   - Action: Repeat with Each → Repeat Item is a photo/video.
   - Action: Get Contents of URL → Method: POST → URL: `http://<PC-IP>:8080/upload` → Request Body: Form
     - Add new field “file” → File → pick “Repeat Item”.
     - Optional: Add header `x-api-key` with your key.
4. Disable “Ask Before Running”.

Result: At 18:00, if connected to your home Wi‑Fi, latest photos/videos from that day are sent to the PC. iOS will still ask for permission the first runs for Photos access and network.

Notes:
- For Messages/WhatsApp/Telegram content, Apple does not expose an automatic export API.
- For Mail backup, set up IMAP backup on the PC (see Windows guide) instead.

## Android (Tasker or Automate)
We recommend Tasker for flexible automation.

Profile:
- Time: 18:00 (1 minute window)
- State: WiFi Connected → SSID `TOZ 2.4G` or `TOZ 5G`

Task:
1. Variable Set `%BACKUP_URL` to `http://<PC-IP>:8080/upload`
2. Select Files:
   - Use `Files → List Files` in `/sdcard/DCIM/Camera` (and other directories), filter by “Modified within 1 day”.
3. For Each file in list:
   - HTTP Request → Method POST → URL `%BACKUP_URL` → Multipart form: Name `file`, File `%file`
   - Header `x-api-key` if used

SMS/Call Log:
- Use “SMS Backup & Restore” app:
  - Schedule daily backup at 18:05 to create XML files (SMS + Call logs) in a known folder.
  - Add a Tasker File Observer for that folder and POST newly created files to `%BACKUP_URL`.

Messaging Apps:
- WhatsApp/Telegram/Signal restrict automatic access. If the app creates daily local backups (e.g., WhatsApp Databases), you can POST those files if accessible via Storage Access Framework permissions. Otherwise, manual exports are required.

Security:
- Configure `PHOTO_BACKUP_API_KEY` on the server and send it in `x-api-key`.
- Restrict automations to your home SSIDs.