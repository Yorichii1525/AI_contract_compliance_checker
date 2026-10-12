# 🚀 AI Compliance Checker - Quick Setup Guide

**Version:** 1.0  
**Date:** November 14, 2025  
**For:** New Users / Team Members

---

## 📦 What You Received

This ZIP package contains the complete AI Compliance Checker application with:
- ✅ All Python source code
- ✅ Sample contracts (PDF & TXT)
- ✅ Configuration files
- ✅ Documentation
- ✅ Knowledge base files

**⚠️ Note:** Virtual environment (`.venv`) is NOT included - you'll create your own.

---

## 🔧 Setup Instructions

### Step 1: Extract ZIP File
```bash
# Extract to your preferred location
# Example: C:\Projects\AI-Compliance-Checker\
```

### Step 2: Install Python (if not installed)
- **Required:** Python 3.9 or higher
- **Download:** https://www.python.org/downloads/
- **Verify installation:**
  ```bash
  python --version
  ```

### Step 3: Create Virtual Environment
```bash
# Navigate to project folder
cd AI-Compliance-Checker

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Windows CMD:
.venv\Scripts\activate.bat

# Linux/Mac:
source .venv/bin/activate
```

### Step 4: Install Dependencies
```bash
# Make sure virtual environment is activated (you should see (.venv) in prompt)
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected installation time:** 2-5 minutes

### Step 5: Configure API Keys

#### Option A: Use Provided .env File (If Included)
The `.env` file already contains your friend's API keys. Just verify:
```bash
# Check if .env exists
dir .env   # Windows
ls .env    # Linux/Mac
```

#### Option B: Create New .env File (If Not Included)
Create a file named `.env` in the project root with:

```env
# Groq API (Required for AI analysis)
GROQ_API_KEY=your_groq_api_key_here

# Google Sheets (Optional - for Google Sheets integration)
GOOGLE_SHEETS_CREDENTIALS_PATH=config/google_credentials.json

# Serper API (Optional - for regulatory updates)
SERPER_API_KEY=your_serper_api_key_here
```

**Get API Keys:**
- **Groq API:** https://console.groq.com/keys (FREE)
- **Serper API:** https://serper.dev/ (FREE tier available)

### Step 6: Verify Google Sheets Credentials (Optional)
If using Google Sheets integration:
```bash
# Check if credentials file exists
dir config\google_credentials.json   # Windows
ls config/google_credentials.json    # Linux/Mac
```

If missing, follow: `GOOGLE_SHEETS_SETUP.md` in the `config` folder

### Step 7: Run the Application
```bash
# Make sure virtual environment is activated
streamlit run app.py
```

The app will open in your browser at: **http://localhost:8501**

---

## ✅ Verification Checklist

After setup, verify everything works:

### 1. Test Sample Contracts
- [ ] Upload `sample_contracts/DPA_Agreement_1.pdf`
- [ ] Click "🚀 Analyze Contract"
- [ ] Verify compliance score appears (should be ~65%)
- [ ] Check all tabs load properly

### 2. Test Google Sheets (if configured)
- [ ] Go to TAB 1 (Contract Analysis)
- [ ] Select "Google Sheets URL" option
- [ ] Enter test spreadsheet URL
- [ ] Click "Extract from Google Sheets"
- [ ] Verify data extraction works

### 3. Test Export Functions
- [ ] After analyzing a contract
- [ ] Go to TAB 5 (Export)
- [ ] Try exporting to JSON, CSV, PDF
- [ ] Verify files are created in `reports/` folder

---

## 🐛 Troubleshooting

### Issue: "0% Compliance Score" or No Results

**Possible Causes:**
1. **Missing Groq API Key**
   ```bash
   # Check .env file
   cat .env   # Linux/Mac
   type .env  # Windows
   
   # Verify GROQ_API_KEY is set and valid
   ```

2. **Knowledge Base Not Loaded**
   ```bash
   # Check if data files exist
   dir data\*.py
   
   # Files should include:
   # - gdpr_requirements.py
   # - hipaa_requirements.py
   # - ccpa_requirements.py
   ```

3. **Dependency Issues**
   ```bash
   # Reinstall dependencies
   pip install --upgrade --force-reinstall -r requirements.txt
   ```

### Issue: "Module Not Found" Error

**Solution:**
```bash
# Make sure virtual environment is activated
# You should see (.venv) in your terminal prompt

# If not activated:
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Then try running again:
streamlit run app.py
```

### Issue: Streamlit Won't Start

**Solution:**
```bash
# Check if port 8501 is already in use
netstat -ano | findstr :8501  # Windows
lsof -i :8501                  # Linux/Mac

# If occupied, use different port:
streamlit run app.py --server.port 8502
```

### Issue: PDF Extraction Fails

**Solution:**
```bash
# Install additional dependencies
pip install pdfplumber pytesseract pillow

# For OCR support, install Tesseract:
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract
```

### Issue: Google Sheets Connection Error

**Solution:**
1. Verify `config/google_credentials.json` exists
2. Check spreadsheet is shared with service account email
3. Verify API is enabled in Google Cloud Console
4. See `GOOGLE_SHEETS_SETUP.md` for detailed setup

---

## 📁 Project Structure

```
AI-Compliance-Checker/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env                      # API keys (configure this!)
├── README.md                 # Project documentation
├── QUICK_START_GUIDE.md      # Quick start instructions
├── config/                   # Configuration files
│   ├── google_credentials.json
│   └── settings.py
├── data/                     # Regulatory knowledge base
│   ├── gdpr_requirements.py
│   ├── hipaa_requirements.py
│   └── ccpa_requirements.py
├── models/                   # Data models
├── services/                 # Core services
│   ├── document_processor.py
│   ├── compliance_checker.py
│   ├── recommendation_engine.py
│   └── export_service.py
├── utils/                    # Utility functions
├── sample_contracts/         # Test contracts
│   ├── DPA_Agreement_1.pdf
│   ├── DPA_Agreement_2.pdf
│   └── ...
├── reports/                  # Generated reports (created automatically)
└── logs/                     # Application logs (created automatically)
```

---

## 🎯 Quick Test Workflow

1. **Start the App:**
   ```bash
   streamlit run app.py
   ```

2. **Upload Sample Contract:**
   - Go to TAB 1 (Contract Analysis)
   - Select "Single File Upload"
   - Choose `sample_contracts/DPA_Agreement_1.pdf`

3. **Analyze:**
   - Click "🚀 Analyze Contract"
   - Wait 10-15 seconds for analysis
   - Compliance score should appear (~65%)

4. **View Results:**
   - TAB 2: Dashboard with charts and metrics
   - TAB 3: Clause-by-clause analysis
   - TAB 4: AI-generated missing clauses
   - TAB 5: Export options

5. **Test Export:**
   - Go to TAB 5
   - Click "Export to PDF"
   - Check `reports/` folder for generated file

---

## 💡 Tips for Best Results

### 1. API Key Management
- Keep `.env` file secure (never commit to Git)
- Use separate API keys for development/production
- Monitor API usage at https://console.groq.com/

### 2. Processing Large Contracts
- Contracts over 50 pages may take 30-60 seconds
- Use "Batch Upload" for multiple files
- Enable logging for debugging: See `utils/logger.py`

### 3. Custom Knowledge Base
- Add new regulations in `data/` folder
- Follow existing format in `gdpr_requirements.py`
- Restart app after changes

### 4. Performance Optimization
- First analysis is slower (model loading)
- Subsequent analyses are faster (~5-10 seconds)
- Use session state for caching

---

## 📞 Support & Resources

### Documentation
- **Full README:** See `README.md` in project root
- **Quick Start:** See `QUICK_START_GUIDE.md`
- **Google Sheets:** See `GOOGLE_SHEETS_QUICK_START.md`
- **API Reference:** See `API_QUICK_REFERENCE.md`

### Sample Contracts Included
1. **DPA_Agreement_1.pdf** - 65% GDPR compliant
2. **DPA_Agreement_2.pdf** - 40% GDPR compliant
3. **data_processing_agreement_sample.pdf** - Full GDPR+HIPAA
4. **saas_service_agreement_sample.pdf** - SaaS licensing
5. **vendor_service_contract_sample.pdf** - HIPAA vendor contract

### Expected Compliance Scores
- DPA Agreement 1: ~65%
- DPA Agreement 2: ~40%
- GDPR-compliant DPA: 70-85%
- HIPAA BAA: 60-75%
- Generic SaaS: 30-50%

---

## 🔐 Security Notes

### API Keys
- ✅ Keep `.env` file secure
- ✅ Never share API keys publicly
- ✅ Use environment variables for production
- ❌ Don't commit `.env` to Git

### Credentials
- Google credentials are service account keys
- Limit permissions to necessary scopes
- Rotate keys periodically

### Data Privacy
- Contracts are processed locally/via API
- No data is stored by default (unless exported)
- Temporary files cleaned up after processing

---

## 🆘 Still Having Issues?

### Check Logs
```bash
# View application logs
cat logs/app.log           # Linux/Mac
type logs\app.log          # Windows

# Look for ERROR or WARNING messages
```

### Common Error Messages

**"GROQ_API_KEY not found"**
→ Check `.env` file exists and contains valid API key

**"No module named 'streamlit'"**
→ Virtual environment not activated or dependencies not installed

**"0% compliance score"**
→ API key invalid or knowledge base files missing

**"PDF extraction failed"**
→ Install pdfplumber: `pip install pdfplumber`

---

## ✅ Setup Complete!

You're all set! The AI Compliance Checker should now be running successfully.

**Next Steps:**
1. Test with provided sample contracts
2. Upload your own contracts for analysis
3. Explore all features (tabs 1-5)
4. Export reports and share with team

**Need Help?** Check the documentation files or review error logs.

---

**Happy Analyzing! 🎉**
