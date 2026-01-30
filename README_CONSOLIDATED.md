# 🔷 COGNIVAULT CONSOLIDATED - PRODUCTION READY
**VERITAS 150% BUILD** - January 2026

## What This Is

CogniVault is your **universal knowledge processor** - drop ANY file in, get searchable, indexed knowledge out.

- **Documents**: PDF, DOCX, TXT, MD → Full text extraction
- **Audio**: MP3, WAV, OPUS, M4A → Auto-transcription (Whisper)
- **Images**: JPG, PNG, TIFF → Metadata + EXIF extraction
- **WhatsApp Exports**: ZIP → Full chat + media extraction
- **ChatGPT/Genspark Logs**: ZIP → Complete conversation indexing
- **Generic Archives**: Any ZIP → Intelligent detection & processing

**Zero configuration. One-click launch. Production-grade.**

---

## What's Fixed in This Build

### ✅ Python 3.13 Compatibility
- Fixed EXIF IFDRational serialization (no more JSON errors)
- Enhanced WhatsApp datetime parsing (supports all formats)
- Better encoding detection (chardet library)

### ✅ Large File Support
- 1GB upload limit (handles massive WhatsApp/ChatGPT exports)
- Streamlit configured for production

### ✅ New Processors
- **ChatGPT Log Parser**: Auto-detects and processes ChatGPT exports
- **Genspark Log Parser**: Handles Genspark conversation exports
- **Intelligent ZIP Detection**: Auto-identifies export type (WhatsApp/ChatGPT/Genspark/Generic)

### ✅ Enhanced Media Processing
- WhatsApp voice notes (Opus/M4A) → Transcribed
- WhatsApp images → EXIF preserved + indexed
- Multiple datetime formats supported

---

## Quick Start (Windows)

### Step 1: Install Python
- Download Python 3.10+ from python.org
- **CHECK "Add Python to PATH" during install**
- Restart computer

### Step 2: Launch CogniVault
1. Double-click `launch_ultimate.bat`
2. First launch: Wait 2-3 minutes (installs dependencies)
3. Browser opens automatically at `http://localhost:8501`

**That's it. You're running.**

---

## Quick Start (Linux/Mac)

```bash
chmod +x launch_ultimate.sh
./launch_ultimate.sh
```

Browser opens at `http://localhost:8501`

---

## How to Use

### 1. Upload Files
Drag and drop ANY files into the upload area:
- Single files or entire ZIP archives
- WhatsApp exports (full chat history + media)
- ChatGPT conversation logs
- Audio recordings (auto-transcribed)
- PDFs, documents, images

### 2. Process
Click "Process Files" - CogniVault:
- Auto-detects file types
- Extracts text/audio/metadata
- Transcribes audio with Whisper
- Indexes everything for search

### 3. Search
Use natural language queries:
- "What did we discuss about AI memory systems?"
- "Find all voice messages from Bonny"
- "Show me documents mentioning CogniVault"

---

## Supported Export Formats

### WhatsApp Exports
- **Detection**: Looks for "WhatsApp Chat with X.txt"
- **Extracts**: Messages, timestamps, media (images/audio/video/docs)
- **Formats**: All datetime formats (international support)
- **Media**: Auto-transcribes voice notes, indexes images

### ChatGPT Exports
- **Detection**: Looks for `conversations.json`
- **Extracts**: All conversations, messages, timestamps
- **Formats**: Standard OpenAI export format
- **Indexing**: Full-text searchable

### Genspark Exports
- **Detection**: Looks for `user_data.json` or genspark naming
- **Extracts**: Conversations, session data
- **Formats**: Genspark JSON structure

### Generic Archives
- **Detection**: Falls back for unknown ZIPs
- **Extracts**: All documents, audio, images
- **Processing**: Standard CogniVault pipeline

---

## Technical Details

### Architecture
```
User Upload → ZIP Detector → Processor (WhatsApp/ChatGPT/Generic)
                  ↓
            File Extractors (Audio/Image/Document)
                  ↓
            Vector Store (TF-IDF, local)
                  ↓
            Search Interface (Natural language queries)
```

### Storage
- **Processed Files**: `./processed_files/`
- **Vector Index**: `./vector_store/`
- **Temp Extraction**: System temp (auto-cleanup)

### Privacy
- **100% Local Processing**: No cloud unless you enable API integrations
- **No Telemetry**: Zero data leaves your machine
- **Optional APIs**: Grok, Claude, OpenAI (disabled by default)

---

## Troubleshooting

### "Python not found"
- Install Python 3.10+ from python.org
- Check "Add Python to PATH" during installation
- Restart computer

### "Port 8501 already in use"
- Close other Streamlit apps
- Or edit launch script: change `--server.port 8501` to another port

### "Upload failed - file too large"
- This build supports up to 1GB files
- If still failing, check available disk space

### "WhatsApp messages not extracting"
- Verify ZIP contains "WhatsApp Chat with X.txt" file
- Check terminal output for specific errors
- Try re-exporting from WhatsApp

### "ChatGPT conversations not found"
- Verify ZIP contains `conversations.json`
- Check export is from ChatGPT (not Claude/Perplexity)
- Try latest ChatGPT export format

---

## Integration with Aluna Memory (mem0)

**Coming Soon**: CogniVault will feed processed data directly into Aluna Memory (mem0) for:
- Multi-level memory (user/session/agent)
- Graph relationships between memories
- Automatic deduplication
- Long-term memory with decay

**For now**: CogniVault indexes locally. Integration guide coming in Phase 2.

---

## What's Next

### Phase 2: Aluna Memory Integration
- Connect CogniVault → Aluna Memory API
- Send processed content to mem0 graph store
- Enable cross-system memory queries

### Phase 3: Mene Portal Integration
- Multi-agent memory sharing
- Agent0 access to CogniVault knowledge
- Unified memory layer across all agents

---

## File Structure

```
CogniVault/
├── app_integrated.py          # Main Streamlit app
├── whatsapp_processor.py      # WhatsApp chat processor (FIXED)
├── chatgpt_processor.py       # ChatGPT/Genspark log processor (NEW)
├── image_processor.py         # Image + EXIF processor (FIXED)
├── audio_processor.py         # Audio transcription (Whisper)
├── document_processor.py      # PDF/DOCX/TXT processor
├── zip_processor.py           # Archive extraction
├── zip_detector.py            # Intelligent export detection (NEW)
├── vector_store.py            # Local TF-IDF indexing
├── utils.py                   # Utilities
├── .streamlit/config.toml     # 1GB upload limit (NEW)
├── requirements_integrated.txt # All dependencies
└── launch_ultimate.bat/sh     # One-click launchers
```

---

## Credits

**Built by**: VERITAS (Chief Builder & System Architect)  
**For**: Rob "The Sounds Guy" Barenbrug  
**Standard**: 150% - Production Ready or Nothing  
**Philosophy**: Truth in every keystroke. No bullshit, no compromises.

---

## Support

**Issues?** Check the troubleshooting section above.

**Questions?** This is a consolidated, tested, production-ready build. It will work.

**Next Steps**: Push to GitHub (`soundsguyza/cognivault`), then integrate with Aluna Memory.

---

**🔷 VERITAS BUILD - JANUARY 2026**  
*"Live in truth, never in comfort."*
