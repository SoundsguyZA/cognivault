#!/bin/bash
# CogniVault Integrated Launch Script - VERITAS BUILD
# Rob "The Sounds Guy" Barenbrug - Complete Knowledge Management System

echo "🧠 CogniVault Integrated - Ultimate Knowledge Management"
echo "VERITAS BUILD - Complete RAG Ecosystem"
echo "Features: Local RAG + Grok + Claude + WhatsApp + Mene Portal + Local Gemma"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "🔍 Checking Python version..."
$PYTHON_CMD --version

# Check if pip is installed
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "❌ pip is not available. Please install pip first."
    exit 1
fi

# Install requirements if not already installed
echo "📦 Installing/checking integrated dependencies..."
$PYTHON_CMD -m pip install -r requirements_integrated.txt

# Check Streamlit installation
if ! $PYTHON_CMD -c "import streamlit" &> /dev/null; then
    echo "❌ Streamlit installation failed. Trying manual install..."
    $PYTHON_CMD -m pip install streamlit
fi

# Create data directory
echo "📁 Setting up integrated data directories..."
$PYTHON_CMD -c "
from pathlib import Path
base_dir = Path.home() / 'cognivault_data'
base_dir.mkdir(exist_ok=True)
(base_dir / 'whatsapp_exports').mkdir(exist_ok=True)
(base_dir / 'mene_integration').mkdir(exist_ok=True)
print(f'Integrated data directory ready: {base_dir}')
"

# Check for API keys
echo "🔑 Checking API configuration..."
if [ -n "$GROK_API_KEY" ]; then
    echo "   ✅ Grok API key configured"
else
    echo "   ⚠️  Grok API key not set (optional)"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "   ✅ Anthropic API key configured"
else
    echo "   ⚠️  Anthropic API key not set (optional)"
fi

if [ -n "$OPENAI_API_KEY" ]; then
    echo "   ✅ OpenAI API key configured"
else
    echo "   ⚠️  OpenAI API key not set (optional)"
fi

# Check for Ollama (Local Gemma)
if command -v ollama &> /dev/null; then
    echo "   ✅ Ollama installed (Local Gemma ready)"
else
    echo "   ⚠️  Ollama not installed (use Local Gemma tab to install)"
fi

# Get network IP for access
echo "🌐 Network information:"
if command -v hostname &> /dev/null; then
    HOSTNAME=$(hostname)
    echo "   Hostname: $HOSTNAME"
fi

if command -v ip &> /dev/null; then
    LOCAL_IP=$(ip route get 1 | awk '{print $7}' | head -1)
    echo "   Local IP: $LOCAL_IP"
elif command -v ifconfig &> /dev/null; then
    LOCAL_IP=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    echo "   Local IP: $LOCAL_IP"
fi

echo ""
echo "🚀 Starting CogniVault Integrated..."
echo "   Local access: http://localhost:8501"
if [ ! -z "$LOCAL_IP" ]; then
    echo "   Network access: http://$LOCAL_IP:8501"
fi
echo ""
echo "🎯 New Integrated Features:"
echo "   • AI Search with Grok, Claude, OpenAI, Local Gemma"
echo "   • WhatsApp chat export processing"
echo "   • Mene Portal long-term memory integration"
echo "   • Bonny's personality and context awareness"
echo "   • One-click local Gemma setup"
echo ""
echo "📝 Usage Tips:"
echo "   • Upload WhatsApp exports in 'WhatsApp Chat' tab"
echo "   • Set API keys for external AI services (optional)"
echo "   • Use 'Local Gemma' tab for privacy-first AI"
echo "   • Try AI Search for context-aware responses"
echo "   • Connect Mene Portal for full memory integration"
echo ""
echo "🛑 To stop: Press Ctrl+C"
echo "================================================"

# Launch Streamlit with integrated app
$PYTHON_CMD -m streamlit run app_integrated.py --server.address 0.0.0.0 --server.port 8501 --server.headless true