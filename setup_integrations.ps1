# =============================================================================
# QUICK START: Multi-Platform Integration Setup
# =============================================================================
# Run this script to set up and test all integrations

Write-Host "`n" -NoNewline
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "🚀 AI-POWERED COMPLIANCE CHECKER - INTEGRATION SETUP" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

# Step 1: Check Python
Write-Host "`n📍 Step 1: Checking Python installation..." -ForegroundColor Yellow
$python_version = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python installed: $python_version" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Step 2: Check if .env exists
Write-Host "`n📍 Step 2: Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ .env file found" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "   Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env and add your API keys!" -ForegroundColor Yellow
    Write-Host "   Required: SLACK_WEBHOOK_URL, EMAIL settings, GOOGLE_SHEETS_SPREADSHEET_ID" -ForegroundColor Yellow
}

# Step 3: Install additional dependencies
Write-Host "`n📍 Step 3: Installing integration dependencies..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Gray

$packages = @(
    "spacy>=3.7.0",
    "openai>=1.0.0",
    "sendgrid>=6.11.0",
    "requests>=2.31.0"
)

foreach ($package in $packages) {
    Write-Host "   Installing $package..." -ForegroundColor Gray
    pip install $package --quiet --disable-pip-version-check
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $package" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Failed to install $package (non-critical)" -ForegroundColor Yellow
    }
}

# Step 4: Download spaCy model (optional but recommended)
Write-Host "`n📍 Step 4: Installing spaCy language model..." -ForegroundColor Yellow
Write-Host "   Downloading en_core_web_sm..." -ForegroundColor Gray
python -m spacy download en_core_web_sm 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ spaCy model installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  spaCy model installation skipped (optional)" -ForegroundColor Yellow
}

# Step 5: Create logs directory
Write-Host "`n📍 Step 5: Setting up directories..." -ForegroundColor Yellow
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "✅ Created logs/ directory" -ForegroundColor Green
} else {
    Write-Host "✅ logs/ directory exists" -ForegroundColor Green
}

# Step 6: Check Google Sheets credentials
Write-Host "`n📍 Step 6: Checking Google Sheets credentials..." -ForegroundColor Yellow
$creds_path = "config/google-sheets-credentials.json"
if (Test-Path $creds_path) {
    Write-Host "✅ Google Sheets credentials found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Google Sheets credentials not found" -ForegroundColor Yellow
    Write-Host "   Download from Google Cloud Console and save to:" -ForegroundColor Yellow
    Write-Host "   $creds_path" -ForegroundColor Gray
}

# Step 7: Run integration tests
Write-Host "`n📍 Step 7: Running integration tests..." -ForegroundColor Yellow
Write-Host "   This will test all configured integrations" -ForegroundColor Gray
Write-Host ""

python test_integrations.py

# Final summary
Write-Host "`n" -NoNewline
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "📚 NEXT STEPS" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

Write-Host "`n1. Configure API Keys:" -ForegroundColor Yellow
Write-Host "   Edit .env file with your actual credentials:" -ForegroundColor Gray
Write-Host "   - SLACK_WEBHOOK_URL (required for Slack alerts)" -ForegroundColor Gray
Write-Host "   - Email settings (SMTP or SendGrid)" -ForegroundColor Gray
Write-Host "   - GOOGLE_SHEETS_SPREADSHEET_ID" -ForegroundColor Gray
Write-Host "   - OPENAI_API_KEY (optional, for AI amendments)" -ForegroundColor Gray

Write-Host "`n2. Set Up Google Sheets:" -ForegroundColor Yellow
Write-Host "   - Create service account in Google Cloud Console" -ForegroundColor Gray
Write-Host "   - Download credentials JSON" -ForegroundColor Gray
Write-Host "   - Save to config/google-sheets-credentials.json" -ForegroundColor Gray
Write-Host "   - Share spreadsheet with service account email" -ForegroundColor Gray

Write-Host "`n3. Run the Application:" -ForegroundColor Yellow
Write-Host "   streamlit run app.py" -ForegroundColor Green

Write-Host "`n4. Test Integrations:" -ForegroundColor Yellow
Write-Host "   python test_integrations.py" -ForegroundColor Green

Write-Host "`n5. Read Documentation:" -ForegroundColor Yellow
Write-Host "   See INTEGRATION_SETUP_GUIDE.md for detailed instructions" -ForegroundColor Gray

Write-Host "`n" -NoNewline
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "✨ Setup complete! Happy compliance checking! ✨" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Cyan
Write-Host ""
