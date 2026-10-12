@echo off
REM Quick start script for AI-Powered Regulatory Compliance Checker
REM This script starts the Streamlit application

echo ========================================
echo AI-Powered Regulatory Compliance Checker
echo ========================================
echo.
echo Starting the application...
echo.
echo The app will open automatically in your browser at:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.
echo ========================================

cd /d "%~dp0"
streamlit run app.py

pause
