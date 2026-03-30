#!/usr/bin/env python3
"""
CogniVault Integrated - Complete RAG System with API Bridges
VERITAS BUILD - The ULTIMATE Knowledge Management System
Rob "The Sounds Guy" Barenbrug

Integrates:
- Local RAG with TF-IDF search
- Grok, Claude, OpenAI, Local Gemma API bridges  
- WhatsApp chat processing
- Mene Portal integration
- Bonny's memory system
"""

import streamlit as st
import os
import tempfile
import zipfile
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from datetime import datetime
import hashlib

# Import all modules
from vector_store import VectorStore
from document_processor import DocumentProcessor
from audio_processor import AudioProcessor
from image_processor import ImageProcessor
from zip_processor import ZipProcessor
from utils import setup_directories, get_file_hash, format_file_size

# Import new integrated modules
from api_bridge import APIBridge
from whatsapp_processor import WhatsAppProcessor
from mene_portal_integration import MenePortalIntegration
from local_gemma_setup import LocalGemmaSetup

# Page configuration
st.set_page_config(
    page_title="CogniVault Integrated - VERITAS BUILD",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CogniVaultIntegrated:
    def __init__(self):
        """Initialize the integrated CogniVault system"""
        self.setup_system()
        
    def setup_system(self):
        """Setup the complete integrated system"""
        self.base_dir = Path.home() / "cognivault_data"
        setup_directories(self.base_dir)
        
        # Initialize core processors
        self.vector_store = VectorStore(self.base_dir / "vector_db")
        self.doc_processor = DocumentProcessor()
        self.audio_processor = AudioProcessor(self.base_dir / "audio")
        self.image_processor = ImageProcessor(self.base_dir / "images")
        self.zip_processor = ZipProcessor()
        
        # Initialize integrated modules
        self.api_bridge = APIBridge(self)
        self.whatsapp_processor = WhatsAppProcessor(self)
        self.mene_integration = MenePortalIntegration(self)
        self.gemma_setup = LocalGemmaSetup()
        
    def main_interface(self):
        """Main integrated Streamlit interface"""
        st.title("🧠 CogniVault Integrated")
        st.subheader("VERITAS BUILD - Ultimate Knowledge Management System")
        
        # Sidebar with system status
        with st.sidebar:
            self.render_system_status()
            
        # Main navigation tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📂 Upload & Process", 
            "🔍 AI Search", 
            "💬 WhatsApp Chat",
            "🧠 Mene Portal",
            "🤖 Local Gemma",
            "🎵 Audio Library", 
            "🖼️ Image Gallery", 
            "📈 Analytics"
        ])
        
        with tab1:
            self.upload_interface()
            
        with tab2:
            self.ai_search_interface()
            
        with tab3:
            self.whatsapp_interface()
            
        with tab4:
            self.mene_portal_interface()
            
        with tab5:
            self.local_gemma_interface()
            
        with tab6:
            self.audio_library()
            
        with tab7:
            self.image_gallery()
            
        with tab8:
            self.analytics_dashboard()
    
    def render_system_status(self):
        """Render system status in sidebar"""
        st.header("System Status")

        # Core system stats
        stats = self.vector_store.get_statistics()
        st.metric("Documents", stats.get('documents', 0))
        st.metric("Audio Files", stats.get('audio_files', 0))
        st.metric("Images", stats.get('images', 0))

        st.divider()

        # Provider config
        st.subheader("AI Provider")
        from api_bridge import KNOWN_PROVIDERS

        provider_name = st.selectbox(
            "Provider",
            list(KNOWN_PROVIDERS.keys()),
            index=list(KNOWN_PROVIDERS.keys()).index(st.session_state.get('provider_name', 'Groq')),
            key="provider_select"
        )
        st.session_state['provider_name'] = provider_name

        if provider_name == "Custom":
            base_url = st.text_input("Base URL", value=st.session_state.get('provider_base_url', ''), placeholder="https://...")
        else:
            base_url = KNOWN_PROVIDERS[provider_name]
            st.caption(f"`{base_url}`")
        st.session_state['provider_base_url'] = base_url

        api_key = st.text_input(
            "API Key", type="password",
            value=st.session_state.get('provider_api_key', ''),
            placeholder="Your key..."
        )
        st.session_state['provider_api_key'] = api_key

        model = st.text_input(
            "Model", value=st.session_state.get('provider_model', ''),
            placeholder="e.g. llama-3.3-70b-versatile"
        )
        st.session_state['provider_model'] = model

        st.divider()
        st.subheader("Audio Transcription")
        groq_whisper_key = st.text_input(
            "Groq Key (Whisper)", type="password",
            value=st.session_state.get('groq_whisper_key', ''),
            placeholder="gsk_... (Groq only)"
        )
        st.session_state['groq_whisper_key'] = groq_whisper_key

        st.divider()

        # API Service Status
        st.subheader("AI Services")
        services = self.api_bridge.get_available_services()
        
        for service in services:
            if service['available']:
                st.success(f"✅ {service['name'].title()}")
            else:
                st.error(f"❌ {service['name'].title()}")
        
        st.divider()
        
        # Quick Actions
        st.header("Quick Actions")
        if st.button("🔄 Rebuild Index"):
            self.vector_store.rebuild_corpus()
            st.success("Index rebuilt!")
            st.rerun()
            
        if st.button("📊 Export Data"):
            self.export_system_data()
        
        if st.button("🧹 Clean Temp Files"):
            from utils import cleanup_temp_files
            cleanup_temp_files(self.base_dir / "temp")
            st.success("Temp files cleaned!")
    
    def upload_interface(self):
        """Enhanced upload interface"""
        st.header("📂 Upload & Process Files")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "Drop your files here (supports ALL formats including WhatsApp exports)",
                accept_multiple_files=True,
                help="Supports: Documents (PDF, DOCX, TXT, JSON), Audio (MP3, WAV, OPUS), Images (JPG, PNG), Archives (ZIP with WhatsApp exports)"
            )
            
            # Processing options
            st.subheader("Processing Options")
            
            col_a, col_b = st.columns(2)
            with col_a:
                auto_whatsapp = st.checkbox("Auto-detect WhatsApp exports", value=True)
                transcribe_audio = st.checkbox("Transcribe audio files", value=True)
            
            with col_b:
                analyze_images = st.checkbox("Analyze image metadata", value=True)
                extract_archives = st.checkbox("Auto-extract ZIP files", value=True)
            
            if uploaded_files:
                st.subheader(f"Processing {len(uploaded_files)} files...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                processing_results = []
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing: {uploaded_file.name}")
                    
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = Path(tmp_file.name)
                    
                    try:
                        result = self.process_single_file_enhanced(
                            tmp_path, 
                            uploaded_file.name,
                            auto_whatsapp=auto_whatsapp,
                            transcribe_audio=transcribe_audio,
                            analyze_images=analyze_images,
                            extract_archives=extract_archives
                        )
                        processing_results.append(result)
                        
                        # Show result
                        with results_container:
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                            else:
                                st.error(f"❌ {result['message']}")
                    
                    except Exception as e:
                        processing_results.append({
                            'success': False,
                            'message': f"Failed to process {uploaded_file.name}: {str(e)}"
                        })
                        
                        with results_container:
                            st.error(f"❌ Failed: {uploaded_file.name}")
                    
                    finally:
                        # Cleanup temp file
                        if tmp_path.exists():
                            tmp_path.unlink()
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("Processing complete!")
                
                # Show summary
                successful = sum(1 for r in processing_results if r['success'])
                st.info(f"Summary: {successful}/{len(processing_results)} files processed successfully")
                
                if successful > 0:
                    st.balloons()
        
        with col2:
            st.subheader("Supported Formats")
            st.markdown("""
            **Archives:**
            - ZIP files (WhatsApp exports)
            - TAR files (auto-extracts)
            
            **Documents:**
            - PDF, DOCX, TXT, MD
            - JSON, HTML, RTF
            
            **Audio:**
            - MP3, WAV, OPUS, FLAC
            - M4A, AAC, OGG
            
            **Images:**
            - JPG, PNG, WebP, BMP
            - GIF, TIFF (with EXIF)
            
            **Special:**
            - WhatsApp chat exports
            - ChatGPT conversation logs
            - Mixed media archives
            """)
    
    def process_single_file_enhanced(self, file_path: Path, original_name: str, **options) -> Dict[str, Any]:
        """Enhanced file processing with all integrations"""
        file_extension = file_path.suffix.lower()
        
        # Check for WhatsApp export
        if options.get('auto_whatsapp', True) and file_extension == '.zip':
            if 'whatsapp' in original_name.lower() or self.is_whatsapp_export(file_path):
                result = self.whatsapp_processor.process_whatsapp_export(file_path)
                if result['success']:
                    return {
                        'success': True,
                        'type': 'whatsapp_export',
                        'message': f"WhatsApp export: {result['chat_files_processed']} chats, {result['media_files_processed']} media files"
                    }
                else:
                    return {'success': False, 'message': f"WhatsApp processing failed: {result.get('error', 'Unknown error')}"}
        
        # Regular ZIP processing
        if options.get('extract_archives', True) and file_extension == '.zip':
            extracted_files = self.zip_processor.extract_zip(file_path)
            processed_count = 0
            
            for extracted_file in extracted_files:
                sub_result = self.process_single_file(extracted_file, extracted_file.name)
                if sub_result:
                    processed_count += 1
            
            return {
                'success': processed_count > 0,
                'type': 'archive',
                'message': f"ZIP archive: extracted and processed {processed_count} files"
            }
        
        # Regular file processing
        if file_extension in ['.txt', '.md', '.json', '.pdf', '.docx', '.html', '.rtf']:
            content = self.doc_processor.process_document(file_path)
            if content:
                success = self.vector_store.add_document(content, original_name, file_path)
                return {
                    'success': success,
                    'type': 'document',
                    'message': f"Document processed: {original_name}"
                }
        
        elif options.get('transcribe_audio', True) and file_extension in ['.mp3', '.wav', '.opus', '.flac', '.m4a', '.aac', '.ogg']:
            transcript = self.audio_processor.transcribe_audio(file_path)
            if transcript:
                success = self.vector_store.add_audio(transcript, original_name, file_path)
                return {
                    'success': success,
                    'type': 'audio',
                    'message': f"Audio transcribed: {original_name}"
                }
        
        elif options.get('analyze_images', True) and file_extension in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff']:
            metadata = self.image_processor.analyze_image(file_path)
            if metadata:
                success = self.vector_store.add_image(metadata, original_name, file_path)
                return {
                    'success': success,
                    'type': 'image',
                    'message': f"Image analyzed: {original_name}"
                }
        
        return {'success': False, 'message': f"Unsupported or empty file: {original_name}"}
    
    def is_whatsapp_export(self, zip_path: Path) -> bool:
        """Check if ZIP file is a WhatsApp export"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                files = zip_ref.namelist()
                
                # Look for typical WhatsApp files
                for file in files:
                    if file.endswith('_chat.txt') or 'WhatsApp Chat' in file or file.endswith('.opus'):
                        return True
            
            return False
        except:
            return False
    
    def process_single_file(self, file_path: Path, original_name: str):
        """Original single file processing method"""
        file_extension = file_path.suffix.lower()
        
        if file_extension in ['.txt', '.md', '.json', '.pdf', '.docx']:
            content = self.doc_processor.process_document(file_path)
            if content:
                return self.vector_store.add_document(content, original_name, file_path)
        
        elif file_extension in ['.mp3', '.wav', '.opus', '.flac', '.m4a']:
            transcript = self.audio_processor.transcribe_audio(file_path)
            if transcript:
                return self.vector_store.add_audio(transcript, original_name, file_path)
        
        elif file_extension in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
            metadata = self.image_processor.analyze_image(file_path)
            if metadata:
                return self.vector_store.add_image(metadata, original_name, file_path)
        
        return False
    
    def ai_search_interface(self):
        """AI-powered search interface with multiple models"""
        st.header("🔍 AI-Powered Search")
        
        # Search input
        search_query = st.text_input("Ask anything about your knowledge base:", 
                                   placeholder="Find documents about machine learning, or ask 'What did Rob say about audio processing?'")
        
        # AI Service selection
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            available_services = [s for s in self.api_bridge.get_available_services() if s['available']]
            service_names = [s['name'] for s in available_services]
            
            if service_names:
                selected_service = st.selectbox("AI Service:", service_names, index=0)
            else:
                st.error("No AI services available. Check your API keys or install local Gemma.")
                selected_service = None
        
        with col2:
            include_search = st.checkbox("Include KB Search", value=True)
            search_limit = st.number_input("Search Results", 1, 10, 5)
        
        with col3:
            if st.button("🔍 AI Search") and search_query and selected_service:
                self.perform_ai_search(search_query, selected_service, include_search, search_limit)
        
        # Regular search results
        if search_query and include_search:
            st.subheader("📚 Knowledge Base Results:")
            
            with st.spinner("Searching knowledge base..."):
                search_results = self.vector_store.search(query=search_query, top_k=search_limit)
            
            if search_results:
                for i, result in enumerate(search_results, 1):
                    with st.expander(f"{i}. {result['filename']} (Score: {result['score']:.3f})"):
                        st.write(f"**Type:** {result['type']}")
                        st.write(f"**Added:** {result['timestamp']}")
                        
                        if result['type'] == 'document':
                            st.text_area("Content Preview:", result['content'][:500] + "...", height=100)
                        elif result['type'] == 'audio':
                            st.text_area("Transcript Preview:", result.get('transcript', '')[:500] + "...", height=100)
                        elif result['type'] == 'image':
                            col_a, col_b = st.columns([1, 2])
                            with col_a:
                                try:
                                    st.image(str(result['file_path']), width=150)
                                except:
                                    st.write("Image not found")
                            with col_b:
                                st.json(result.get('metadata', {}))
            else:
                st.info("No results found in knowledge base.")
    
    def perform_ai_search(self, query: str, service: str, include_search: bool, search_limit: int):
        """Perform AI search with selected service"""
        with st.spinner(f"Querying {service.title()} with your knowledge base..."):
            result = self.api_bridge.query_with_context(
                query=query,
                service=service,
                include_search=include_search,
                search_limit=search_limit
            )
        
        if result['success']:
            st.subheader(f"🤖 {service.title()} Response:")
            st.write(result['response'])
            
            if result.get('context_used'):
                with st.expander("📖 Context Used"):
                    st.info("This response was enhanced with your personal knowledge base.")
        else:
            st.error(f"AI query failed: {result['error']}")
    
    def whatsapp_interface(self):
        """WhatsApp processing interface"""
        st.header("💬 WhatsApp Chat Processing")
        
        st.info("Upload WhatsApp chat export ZIP files to automatically process chats and media files.")
        
        # Upload specifically for WhatsApp
        whatsapp_file = st.file_uploader(
            "Upload WhatsApp Export ZIP",
            type=['zip'],
            help="Export your WhatsApp chat (Settings > Chats > Export Chat > Include Media)"
        )
        
        if whatsapp_file and st.button("Process WhatsApp Export"):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_file.write(whatsapp_file.read())
                tmp_path = Path(tmp_file.name)
            
            try:
                with st.spinner("Processing WhatsApp export..."):
                    result = self.whatsapp_processor.process_whatsapp_export(tmp_path)
                
                if result['success']:
                    st.success("✅ WhatsApp export processed successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Chat Files", result['chat_files_processed'])
                    with col2:
                        st.metric("Media Files", result['media_files_processed'])
                    with col3:
                        st.metric("Items Indexed", result['total_indexed'])
                    
                    # Show chat details
                    if result.get('chat_data'):
                        st.subheader("📱 Processed Chats:")
                        for chat in result['chat_data']:
                            with st.expander(f"💬 {chat['chat_name']}"):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**Messages:** {chat['message_count']}")
                                    st.write(f"**Date Range:** {chat['date_range']}")
                                with col_b:
                                    st.write(f"**Participants:** {', '.join(chat['participants'])}")
                                
                                if chat.get('statistics'):
                                    st.json(chat['statistics'])
                    
                    st.balloons()
                else:
                    st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
    
    def mene_portal_interface(self):
        """Mene Portal integration interface"""
        self.mene_integration.create_mene_portal_interface()
    
    def local_gemma_interface(self):
        """Local Gemma setup and management interface"""
        st.header("🤖 Local Gemma Setup")
        
        # Status check
        status = self.gemma_setup.create_status_report()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Current Status")
            
            if status.get('installation', {}).get('installed'):
                st.success("✅ Ollama installed")
                st.write(f"Version: {status['installation'].get('version', 'Unknown')}")
            else:
                st.error("❌ Ollama not installed")
            
            if status.get('api', {}).get('running'):
                st.success("✅ API running")
                models = status['api'].get('models', [])
                st.write(f"Models: {len(models)}")
            else:
                st.error("❌ API not running")
            
            if status.get('models', {}).get('success'):
                gemma_models = status['models'].get('gemma_models', [])
                if gemma_models:
                    st.success(f"✅ {len(gemma_models)} Gemma model(s) installed")
                    for model in gemma_models:
                        st.write(f"  • {model['name']}")
                else:
                    st.warning("⚠️ No Gemma models installed")
        
        with col2:
            st.subheader("Setup Actions")
            
            if st.button("🔧 Complete Setup"):
                with st.spinner("Running complete setup..."):
                    setup_result = self.gemma_setup.complete_setup()
                
                if setup_result['success']:
                    st.success("✅ Setup completed successfully!")
                    st.json(setup_result['final_test'])
                else:
                    st.error(f"❌ Setup failed: {setup_result['error']}")
                    with st.expander("Setup Details"):
                        st.json(setup_result)
            
            if st.button("🔄 Refresh Status"):
                st.rerun()
            
            if st.button("📋 Get Instructions"):
                instructions = self.gemma_setup.get_setup_instructions()
                st.subheader(f"Setup Instructions for {instructions['system'].title()}")
                for step in instructions['steps']:
                    st.write(step)
        
        # Test interface
        if status.get('models', {}).get('gemma_models'):
            st.subheader("🧪 Test Gemma")
            
            test_query = st.text_input("Test query:", "Hello! How are you?")
            
            if st.button("Test Gemma") and test_query:
                with st.spinner("Testing Gemma..."):
                    model_name = status['models']['gemma_models'][0]['name']
                    test_result = self.gemma_setup.test_gemma_model(model_name)
                
                if test_result['success']:
                    st.success("✅ Gemma is working!")
                    st.write("**Response:**")
                    st.write(test_result['response'])
                    
                    st.write("**Performance:**")
                    st.write(f"Load time: {test_result.get('load_duration', 0) / 1000000:.2f}ms")
                    st.write(f"Response time: {test_result.get('prompt_eval_duration', 0) / 1000000:.2f}ms")
                else:
                    st.error(f"❌ Test failed: {test_result['error']}")
    
    def audio_library(self):
        """Audio library interface"""
        st.header("🎵 Audio Library")
        
        audio_files = self.vector_store.get_audio_files()
        
        if audio_files:
            for audio in audio_files:
                with st.expander(f"🎵 {audio['filename']}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        if audio['file_path'] and Path(audio['file_path']).exists():
                            st.audio(str(audio['file_path']))
                        st.write(f"**Duration:** {audio.get('duration', 'Unknown')}")
                        st.write(f"**Added:** {audio['timestamp']}")
                    
                    with col2:
                        st.text_area("Transcript:", audio['transcript'], height=200, key=f"transcript_{audio['filename']}")
        else:
            st.info("No audio files in library. Upload some audio files to get started!")
    
    def image_gallery(self):
        """Image gallery interface"""
        st.header("🖼️ Image Gallery")
        
        images = self.vector_store.get_images()
        
        if images:
            cols = st.columns(3)
            for i, img in enumerate(images):
                with cols[i % 3]:
                    if img['file_path'] and Path(img['file_path']).exists():
                        st.image(str(img['file_path']), caption=img['filename'])
                    with st.expander("Details"):
                        st.json(img['metadata'])
        else:
            st.info("No images in gallery. Upload some images to get started!")
    
    def analytics_dashboard(self):
        """Analytics and system statistics"""
        st.header("📈 System Analytics")
        
        stats = self.vector_store.get_detailed_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Documents", stats.get('total_documents', 0))
        with col2:
            st.metric("Total Audio Files", stats.get('total_audio', 0))
        with col3:
            st.metric("Total Images", stats.get('total_images', 0))
        with col4:
            st.metric("Storage Used", format_file_size(stats.get('storage_used', 0)))
        
        # Integration status
        st.subheader("🔗 Integration Status")
        integration_status = self.mene_integration.get_integration_status()
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if integration_status['mene_portal']['success']:
                st.success("✅ Mene Portal")
            else:
                st.error("❌ Mene Portal")
        
        with col_b:
            if integration_status['bonny_memories']['success']:
                st.success("✅ Bonny's Memories")
            else:
                st.error("❌ Bonny's Memories")
        
        with col_c:
            if integration_status['cognivault']['success']:
                st.success("✅ CogniVault Core")
            else:
                st.error("❌ CogniVault Core")
        
        # File type distribution
        if stats.get('file_types'):
            st.subheader("📊 File Type Distribution")
            df = pd.DataFrame(list(stats['file_types'].items()), columns=['Type', 'Count'])
            st.bar_chart(df.set_index('Type'))
        
        # Recent activity
        if stats.get('recent_activity'):
            st.subheader("⚡ Recent Activity")
            df = pd.DataFrame(stats['recent_activity'])
            st.dataframe(df, use_container_width=True)
    
    def export_system_data(self):
        """Export complete system data"""
        export_data = self.vector_store.export_data()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cognivault_integrated_export_{timestamp}.json"
        
        st.download_button(
            label="📥 Download Complete Export",
            data=json.dumps(export_data, indent=2),
            file_name=filename,
            mime="application/json"
        )

def main():
    """Main application entry point"""
    app = CogniVaultIntegrated()
    app.main_interface()

if __name__ == "__main__":
    main()