# Google Service Account Credentials Template

⚠️ **DO NOT COMMIT THE ACTUAL CREDENTIALS FILE!**

This directory should contain your Google service account JSON file:
- **Filename**: `google_credentials.json`
- **How to get it**: Follow the setup guide in `../GOOGLE_SHEETS_SETUP_CHECKLIST.md`

## Quick Setup:

1. Go to https://console.cloud.google.com
2. Select project: `august-will-477705-i7`
3. Enable **Google Sheets API** and **Google Drive API**
4. Create **Service Account**
5. Download JSON key
6. Save it here as: `google_credentials.json`

## What the JSON file contains:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  ...
}
```

## Security:
✅ The actual `google_credentials.json` is ignored by `.gitignore`  
✅ Never commit files containing `private_key` or secrets  
✅ Share the setup instructions, not the actual credentials
