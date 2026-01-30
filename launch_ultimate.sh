#!/bin/bash
# CogniVault Ultimate Launcher
# VERITAS 150% BUILD - Production Ready
# Rob "The Sounds Guy" Barenbrug

echo "🔷 COGNIVAULT ULTIMATE LAUNCHER"
echo "================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="Windows"
else
    OS="Unknown"
fi

echo "✅ Detected OS: $OS"
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
else
    echo "❌ ERROR: Python not found!"
    echo "   Please install Python 3.8+ from python.org"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"
echo ""

# Check if requirements are installed
echo "🔍 Checking dependencies..."
if $PYTHON_CMD -c "import streamlit" &> /dev/null; then
    echo "✅ Dependencies installed"
else
    echo "📦 Installing dependencies..."
    $PYTHON_CMD -m pip install -q -r requirements_integrated.txt
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies installed successfully"
    else
        echo "❌ Failed to install dependencies"
        echo "   Try manually: pip install -r requirements_integrated.txt"
        exit 1
    fi
fi
echo ""

# Check for API keys (optional)
echo "🔑 Checking API keys..."
API_KEYS_SET=0
if [ ! -z "$GROK_API_KEY" ]; then
    echo "  ✅ Grok API key detected"
    API_KEYS_SET=$((API_KEYS_SET + 1))
fi
if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo "  ✅ Claude API key detected"
    API_KEYS_SET=$((API_KEYS_SET + 1))
fi
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "  ✅ OpenAI API key detected"
    API_KEYS_SET=$((API_KEYS_SET + 1))
fi

if [ $API_KEYS_SET -eq 0 ]; then
    echo "  ⚠️  No API keys set (Local Gemma will work)"
    echo "     To set keys: export GROK_API_KEY='your-key'"
else
    echo "  ✅ $API_KEYS_SET AI service(s) configured"
fi
echo ""

# Check for Ollama (Local Gemma)
echo "🤖 Checking Local AI..."
if command -v ollama &> /dev/null; then
    echo "  ✅ Ollama installed"
    if ollama list | grep -q "gemma2:2b"; then
        echo "  ✅ Gemma2:2b model ready"
    else
        echo "  ⚠️  Gemma2:2b not installed (use 'Local Gemma' tab in app)"
    fi
else
    echo "  ⚠️  Ollama not installed (use 'Local Gemma' tab in app)"
fi
echo ""

# Ask user for deployment mode
echo "🚀 Choose deployment mode:"
echo "  1) HTTP - Local only (localhost:8501)"
echo "  2) HTTP - Network access (0.0.0.0:8501)"
echo "  3) HTTPS - Secure with SSL (localhost:8502)"
echo "  4) HTTPS - Network secure (0.0.0.0:8502)"
echo ""
read -p "Enter choice [1-4] (default: 1): " CHOICE
CHOICE=${CHOICE:-1}

echo ""
echo "🔷 LAUNCHING COGNIVAULT ULTIMATE..."
echo "================================"
echo ""

case $CHOICE in
    1)
        echo "📍 Mode: HTTP Local Only"
        echo "🌐 Access: http://localhost:8501"
        echo ""
        $PYTHON_CMD -m streamlit run app_integrated.py --server.port 8501
        ;;
    2)
        echo "📍 Mode: HTTP Network Access"
        echo "🌐 Access: http://localhost:8501"
        echo "🌐 Network: http://$(hostname -I | awk '{print $1}'):8501"
        echo ""
        $PYTHON_CMD -m streamlit run app_integrated.py \
            --server.address 0.0.0.0 \
            --server.port 8501
        ;;
    3)
        echo "📍 Mode: HTTPS Local Only"
        echo "🌐 Access: https://localhost:8502"
        echo "⚠️  Accept self-signed certificate warning in browser"
        echo ""
        if [ -f "cognivault_https_fix.py" ]; then
            $PYTHON_CMD cognivault_https_fix.py --port 8502 --host localhost
        else
            echo "❌ HTTPS script not found! Using HTTP fallback..."
            $PYTHON_CMD -m streamlit run app_integrated.py --server.port 8501
        fi
        ;;
    4)
        echo "📍 Mode: HTTPS Network Secure"
        echo "🌐 Access: https://localhost:8502"
        echo "🌐 Network: https://$(hostname -I | awk '{print $1}'):8502"
        echo "⚠️  Accept self-signed certificate warning in browser"
        echo ""
        if [ -f "cognivault_https_fix.py" ]; then
            $PYTHON_CMD cognivault_https_fix.py --port 8502 --host 0.0.0.0
        else
            echo "❌ HTTPS script not found! Using HTTP fallback..."
            $PYTHON_CMD -m streamlit run app_integrated.py \
                --server.address 0.0.0.0 \
                --server.port 8501
        fi
        ;;
    *)
        echo "❌ Invalid choice. Using default (HTTP Local)"
        $PYTHON_CMD -m streamlit run app_integrated.py --server.port 8501
        ;;
esac

# If we reach here, the app has stopped
echo ""
echo "🔷 CogniVault Ultimate stopped"
echo "================================"
