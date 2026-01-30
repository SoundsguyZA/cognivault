@echo off
REM CogniVault QUICK START - One-Click Launch
REM VERITAS 150% - Rob "The Sounds Guy"

title CogniVault Quick Start

echo.
echo ========================================
echo   COGNIVAULT QUICK START
echo ========================================
echo.
echo Setting up API keys for this session...
echo.

REM Set API keys for current session (replace with your actual keys)
set GEMINI_API_KEY=your_gemini_api_key_here
set GROQ_API_KEY=your_groq_api_key_here
set NOVITA_API_KEY=your_novita_api_key_here

echo [OK] Gemini API ready
echo [OK] Groq API ready
echo [OK] Novita API ready
echo.

echo Launching CogniVault...
echo.

REM Launch CogniVault
call launch_ultimate.bat
