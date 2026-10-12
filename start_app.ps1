# Quick start script for AI-Powered Regulatory Compliance Checker
# This PowerShell script starts the Streamlit application

Write-Host "========================================"
Write-Host "AI-Powered Regulatory Compliance Checker"
Write-Host "========================================"
Write-Host ""
Write-Host "Starting the application..."
Write-Host ""
Write-Host "The app will open automatically in your browser at:"
Write-Host "http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the application"
Write-Host ""
Write-Host "========================================"
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Start Streamlit
streamlit run app.py
