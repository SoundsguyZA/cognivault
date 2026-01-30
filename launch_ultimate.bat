@echo off
REM CogniVault Ultimate Launcher - PYTHON 3.13 FORCED
REM VERITAS 150% BUILD - Rob "The Sounds Guy"
REM Auto-configured with API keys

echo.
echo ========================================
echo    COGNIVAULT ULTIMATE LAUNCHER
echo    Python 3.13 Forced Edition
echo ========================================
echo.

REM Force Python 3.13 detection
set PYTHON_CMD=
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.13 --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=py -3.13
        echo [OK] Python 3.13 via py launcher
        goto :python_found
    )
)

where python3.13 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3.13
    echo [OK] Python 3.13 via python3.13
    goto :python_found
)

if exist "C:\Python313\python.exe" (
    set PYTHON_CMD=C:\Python313\python.exe
    echo [OK] Python 3.13 at C:\Python313
    goto :python_found
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
    echo [OK] Python 3.13 in AppData
    goto :python_found
)

echo [ERROR] Python 3.13 NOT FOUND!
echo.
echo You have Python 3.14 which is incompatible.
echo Please install Python 3.13 from: https://www.python.org/downloads/
echo.
pause
exit /b 1

:python_found
%PYTHON_CMD% --version
echo.

REM Install/update dependencies
echo Checking dependencies...
%PYTHON_CMD% -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies (first run - ~2 min)...
    %PYTHON_CMD% -m pip install --quiet --upgrade pip
    %PYTHON_CMD% -m pip install --quiet -r requirements_integrated.txt
    if errorlevel 1 (
        echo [ERROR] Dependency install failed
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies ready
)
echo.

REM Check API keys
echo Checking API configuration...
if defined GEMINI_API_KEY (
    echo   [OK] Gemini API configured
) else (
    echo   [WARN] Gemini API not set
)
if defined GROQ_API_KEY (
    echo   [OK] Groq API configured
) else (
    echo   [WARN] Groq API not set
)
if defined NOVITA_API_KEY (
    echo   [OK] Novita API configured
) else (
    echo   [WARN] Novita API not set
)
echo.

REM Launch options
echo Deployment Mode:
echo   1. HTTP Local (localhost:8501) - RECOMMENDED
echo   2. HTTP Network (0.0.0.0:8501) - LAN access
echo.
set /p CHOICE="Select [1-2] (default 1): "
if "%CHOICE%"=="" set CHOICE=1

echo.
echo ========================================
echo   LAUNCHING COGNIVAULT...
echo ========================================
echo.

if "%CHOICE%"=="1" (
    echo [Mode] Local Only
    echo [URL]  http://localhost:8501
    echo [Python] %PYTHON_CMD%
    echo.
    echo Browser opening in 3 seconds...
    timeout /t 3 /nobreak >nul
    start http://localhost:8501
    %PYTHON_CMD% -m streamlit run app_integrated.py --server.port 8501 --server.headless true
) else (
    echo [Mode] Network Access
    echo [URL]  http://localhost:8501
    echo [Python] %PYTHON_CMD%
    echo.
    %PYTHON_CMD% -m streamlit run app_integrated.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
)

:end
echo.
echo ========================================
echo   CogniVault stopped
echo ========================================
pause
