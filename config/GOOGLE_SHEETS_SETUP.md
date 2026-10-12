# Google Sheets Integration Setup

This guide explains how to set up Google Sheets integration for the AI Compliance Checker.

## Prerequisites

- Google Cloud Platform account
- Google Sheets API enabled
- Service account with appropriate permissions

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

### 2. Enable Google Sheets API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click "Enable"

### 3. Create Service Account Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `compliance-checker-sheets`
   - Description: `Service account for AI Compliance Checker Google Sheets integration`
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

### 4. Generate and Download Credentials

1. Click on the newly created service account
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Click "Create" - the credentials file will download automatically

### 5. Install Credentials

1. Rename the downloaded file to `google_credentials.json`
2. Place it in the `App/config/` directory
3. **Important**: Never commit this file to version control!

### 6. Share Google Sheets with Service Account

For each Google Sheet you want to analyze:

1. Open the Google Sheet
2. Click the "Share" button
3. Add the service account email (found in the credentials JSON file, looks like: `compliance-checker-sheets@your-project.iam.gserviceaccount.com`)
4. Grant "Viewer" access
5. Click "Send"

## Usage

Once configured, you can use Google Sheets integration in the app:

1. Select "Google Sheets URL" as the upload method
2. Paste the Google Sheets URL
3. (Optional) Specify sheet name and cell range
4. Click "Process Google Sheet"

## Troubleshooting

### Authentication Error

**Problem**: "Google API credentials not found"

**Solution**: Ensure `google_credentials.json` is in the `App/config/` directory

### Permission Denied

**Problem**: "The caller does not have permission"

**Solution**: Share the Google Sheet with the service account email

### Sheet Not Found

**Problem**: "Sheet not found or not accessible"

**Solution**: 
- Verify the URL is correct
- Ensure the sheet is shared with the service account
- Check that the sheet name (if specified) exists

### No Data Found

**Problem**: "No data found in the specified range"

**Solution**:
- Verify the cell range is correct
- Ensure the cells contain data
- Try leaving the range empty to read all data

## Security Notes

- The `google_credentials.json` file contains sensitive information
- Add it to `.gitignore` to prevent accidental commits
- Only share credentials with authorized team members
- Regularly rotate service account keys
- Use least-privilege access (Viewer role is sufficient)

## Required Python Packages

The following packages are required for Google Sheets integration:

```
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.111.0
```

These are already included in `requirements.txt`.
