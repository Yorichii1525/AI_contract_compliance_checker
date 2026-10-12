# Google Sheets Upload Guide for Contract.xlsx

## ✅ Conversion Complete

Your CSV file has been successfully converted to Excel format:
- **Source:** `config/Contract.csv` (10.1 KB, 114 rows)
- **Output:** `config/Contract.xlsx` (11.5 KB, 114 rows)
- **Format:** Excel (.xlsx) with professional formatting
- **Status:** ✅ Ready for Google Sheets upload

## 📊 File Details

### Excel Formatting Applied:
- ✅ **Header Row:** Blue background, white text, bold, centered
- ✅ **Column Widths:** Optimized for readability
  - SectionNumber: 15 characters
  - Topic: 30 characters
  - Details: 60 characters (main content)
  - RelevantArticle: 20 characters
- ✅ **Cell Formatting:** Borders, text wrapping, top-aligned
- ✅ **Frozen Header:** Top row stays visible when scrolling
- ✅ **Clean Data:** NaN values converted to empty strings

### Google Sheets Compatibility:
- ✅ **Rows:** 114 (limit: 10,000,000 cells)
- ✅ **Columns:** 4 (limit: 18,278 columns)
- ✅ **Total Cells:** 456 (well within limits)
- ✅ **File Format:** .xlsx (native Google Sheets support)
- ✅ **Character Encoding:** UTF-8
- ✅ **Special Characters:** None in column names

## 📤 Upload Methods

### Method 1: Direct Upload to Google Drive (Recommended)

1. **Go to Google Drive:**
   ```
   https://drive.google.com
   ```

2. **Upload File:**
   - Click "New" button → "File upload"
   - Navigate to: `E:\323103310024\Updated Infosys\jaggu-proj\config\Contract.xlsx`
   - Select and upload

3. **Convert to Google Sheets:**
   - Right-click the uploaded file
   - Select "Open with" → "Google Sheets"
   - Google Sheets will open with your data
   - File → "Save as Google Sheets" (to create native Sheets file)

### Method 2: Import in Google Sheets

1. **Open Google Sheets:**
   ```
   https://sheets.google.com
   ```

2. **Import File:**
   - Click "Blank" to create new spreadsheet
   - File → Import → Upload
   - Drag `Contract.xlsx` or browse to select
   - Import location: "Replace spreadsheet"
   - Click "Import data"

3. **Verify Import:**
   - Check all 114 rows are imported
   - Verify formatting is preserved
   - Column headers should be visible

### Method 3: Using Google Sheets API (Programmatic)

Your project already has Google Sheets integration! Use the services:

```python
from services.google_sheets_writer import GoogleSheetsWriter

# Initialize writer
writer = GoogleSheetsWriter()

# Create new spreadsheet
spreadsheet_id = writer.create_new_spreadsheet("Contract Data - GDPR")

# Get spreadsheet URL
print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
```

## 🔧 Google Sheets Service Status

Your project has THREE Google Sheets services:

### 1. `google_sheets_service.py` (Reader)
- ✅ **Status:** Active and working
- ✅ **Credentials:** Found at `config/google_credentials.json`
- ✅ **Connection Test:** Successful
- **Purpose:** Extract contract text FROM Google Sheets
- **Scope:** `spreadsheets.readonly`

### 2. `google_sheets_writer.py` (Writer)
- ✅ **Status:** Available
- **Purpose:** Write compliance reports TO Google Sheets
- **Scope:** `spreadsheets` (full read/write)
- **Features:**
  - Create new spreadsheets
  - Write compliance reports
  - Write missing requirements
  - Append notifications
  - Auto-formatting

### 3. `google_sheets_compliance_sync.py` (Sync)
- **Purpose:** Real-time compliance monitoring
- **Features:** Bidirectional sync with Google Sheets

## 📋 After Upload: Using Google Sheets

### Share with Service Account (Important!)

After uploading to Google Sheets, you need to share it with your service account:

1. **Get Service Account Email:**
   - Open `config/google_credentials.json`
   - Find the `"client_email"` field
   - Copy the email (looks like: `yourproject@yourproject.iam.gserviceaccount.com`)

2. **Share the Sheet:**
   - In Google Sheets, click "Share" button
   - Paste the service account email
   - Set permission to "Editor" (if you want to write) or "Viewer" (if read-only)
   - Uncheck "Notify people"
   - Click "Share"

### Use in Your App

Once uploaded and shared, you can access it programmatically:

```python
from services.google_sheets_service import GoogleSheetsService

# Initialize service
sheets_service = GoogleSheetsService()

# Get the sheet URL from Google Drive
url = "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit"

# Extract text
contract_text = sheets_service.extract_text_from_sheet(url)

print(f"Extracted {len(contract_text)} characters")
```

## 🔐 Google API Setup (If Not Done)

If you don't have `config/google_credentials.json`:

1. **Google Cloud Console:**
   - Go to: https://console.cloud.google.com
   - Create new project or select existing

2. **Enable APIs:**
   - Navigate to "APIs & Services" → "Library"
   - Search and enable:
     - Google Sheets API
     - Google Drive API

3. **Create Service Account:**
   - "APIs & Services" → "Credentials"
   - "Create Credentials" → "Service Account"
   - Fill in details and create

4. **Download Credentials:**
   - Click on created service account
   - "Keys" tab → "Add Key" → "Create new key"
   - Choose JSON format
   - Download and save as `config/google_credentials.json`

5. **Set Permissions:**
   - In service account details, grant roles:
     - Google Sheets API: Editor
     - Google Drive API: Editor (if needed)

## 📝 Data Structure in Excel

The Contract.xlsx contains GDPR DPA (Data Processing Agreement) clauses:

```
SectionNumber | Topic                  | Details                              | RelevantArticle
1.            | DEFINITIONS            |                                      |
1.1           | Personal Data          | Personal Data means any info...      |
1.2           | Processing             | Processing means any operation...    |
...
17.           | AUDIT RIGHTS           |                                      | 
17.3          | Notice                 | Reasonable notice shall be...        |
```

**Total Sections:** 17 major sections
**Total Clauses:** 114 detailed clauses
**GDPR Coverage:** Articles 5-39, Chapter V

## 🎯 Next Steps

1. **Upload to Google Drive** using Method 1 or 2 above
2. **Share with service account** (copy email from credentials)
3. **Test API access** using the code examples
4. **Integrate with app** for contract analysis

## 🔗 Useful Links

- **Google Drive:** https://drive.google.com
- **Google Sheets:** https://sheets.google.com
- **Google Cloud Console:** https://console.cloud.google.com
- **API Documentation:** https://developers.google.com/sheets/api

## ⚙️ Troubleshooting

### Issue: "Permission Denied" Error
**Solution:** Share the spreadsheet with your service account email

### Issue: "File Not Found" Error
**Solution:** Check spreadsheet ID in URL is correct

### Issue: "Authentication Error"
**Solution:** 
- Verify `google_credentials.json` exists in config folder
- Check credentials are valid (not expired)
- Ensure Google Sheets API is enabled

### Issue: "Invalid URL" Error
**Solution:** URL must be in format:
```
https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
```

## 📞 Support

If you encounter issues:
1. Check logs in `logs/` folder
2. Verify credentials setup
3. Test connection: `python convert_contract_to_excel.py`
4. Check service status in output

---

**Generated:** November 13, 2025
**File Location:** `E:\323103310024\Updated Infosys\jaggu-proj\config\Contract.xlsx`
**Size:** 11.5 KB (11,482 bytes)
**Status:** ✅ Ready for Google Sheets
