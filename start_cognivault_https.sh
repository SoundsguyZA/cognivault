#!/bin/bash
# CogniVault HTTPS Launcher for Linux/Mac
# Built by VERITAS for Rob "The Sounds Guy"

echo ""
echo "========================================"
echo "  CogniVault HTTPS Launcher"
echo "  Built by VERITAS - Living in Truth"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ ERROR: Python not found!"
        echo "   Please install Python first"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check if we're in the right directory
if [ ! -f "cognivault_https_fix.py" ]; then
    echo "❌ ERROR: cognivault_https_fix.py not found!"
    echo "   Make sure you're in the correct directory"
    exit 1
fi

echo "Step 1: Setting up SSL certificates..."
$PYTHON_CMD cognivault_https_fix.py

echo ""
echo "Step 2: Starting HTTPS server..."
if [ -f "https_runner.py" ]; then
    $PYTHON_CMD https_runner.py
else
    echo "❌ ERROR: https_runner.py not created!"
    echo "   Something went wrong with the setup"
    exit 1
fi