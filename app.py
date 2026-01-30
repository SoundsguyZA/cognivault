#!/usr/bin/env python3
"""
CogniVault - Production RAG System
VERITAS BUILD - Truth-Based Local Knowledge Management
Rob "The Sounds Guy" Barenbrug

A complete RAG system that runs 100% local with no corporate dependencies.
Processes documents, images, audio, and ZIP archives.
Uses TF-IDF for embeddings and Whisper for audio transcription.
"""

import streamlit as st
import os
import tempfile
import zipfile
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
import hashlib

# Import our local modules
from vector_store import VectorStore
from document_processor import DocumentProcessor
from audio_processor import AudioProcessor
from image_processor import ImageProcessor
from zip_processor import ZipProcessor
from utils import setup_directories, get_file_hash, format_file_size

# Page configuration
st.set_page_config(
    page_title="CogniVault - Local RAG System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CogniVault:
    def __init__(self):
        """Initialize the CogniVault system"""
        self.setup_system()
        
    def setup_system(self):
        """Setup the system directories and components"""
        self.base_dir = Path.home() / "cognivault_data"
        setup_directories(self.base_dir)
        
        # Initialize processors
        self.vector_store = VectorStore(self.base_dir / "vector_db")
        self.doc_processor = DocumentProcessor()
        self.audio_processor = AudioProcessor(self.base_dir / "audio")
        self.image_processor = ImageProcessor(self.base_dir / "images")
        self.zip_processor = ZipProcessor()
        
    def main_interface(self):
        """Main Streamlit interface"""
        st.title("🧠 CogniVault - Local RAG System")
        st.subheader("VERITAS BUILD - Truth-Based Knowledge Management")
        
        # Sidebar
        with st.sidebar:
            st.header("System Status")
            stats = self.vector_store.get_statistics()
            st.metric("Documents Indexed", stats.get('documents', 0))
            st.metric("Audio Files", stats.get('audio_files', 0))
            st.metric("Images", stats.get('images', 0))
            
            st.header("Actions")
            if st.button("🔄 Rebuild Index"):
                self.vector_store.rebuild_corpus()
                st.success("Index rebuilt successfully!")
                st.rerun()
                
            if st.button("📊 Export Data"):
                self.export_system_data()
                
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📂 Upload & Process", 
            "🔍 Search", 
            "🎵 Audio Library", 
            "🖼️ Image Gallery", 
            "📈 Analytics"
        ])
        
        with tab1:
            self.upload_interface()
            
        with tab2:
            self.search_interface()
            
        with tab3:
            self.audio_library()
            
        with tab4:
            self.image_gallery()
            
        with tab5:
            self.analytics_dashboard()
    
    def upload_interface(self):
        """File upload and processing interface"""
        st.header("Upload & Process Files")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "Drop your files here (supports ZIP, audio, documents, images)",
                accept_multiple_files=True,
                type=['zip', 'txt', 'md', 'json', 'pdf', 'docx', 
                      'mp3', 'wav', 'opus', 'flac', 'm4a',
                      'jpg', 'jpeg', 'png', 'webp', 'bmp']
            )
            
            if uploaded_files:
                st.subheader(f"Processing {len(uploaded_files)} files...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing: {uploaded_file.name}")
                    
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = Path(tmp_file.name)
                    
                    try:
                        self.process_single_file(tmp_path, uploaded_file.name)
                        st.success(f"✅ Processed: {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"❌ Failed to process {uploaded_file.name}: {str(e)}")
                    finally:
                        # Cleanup temp file
                        if tmp_path.exists():
                            tmp_path.unlink()
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("Processing complete!")
                st.balloons()
        
        with col2:
            st.subheader("Supported Formats")
            st.markdown("""
            **Archives:**
            - ZIP files (auto-extracts)
            
            **Documents:**
            - TXT, MD, JSON
            - PDF, DOCX
            
            **Audio:**
            - MP3, WAV, OPUS
            - FLAC, M4A
            
            **Images:**
            - JPG, PNG, WebP
            - BMP, JPEG
            """)
    
    def process_single_file(self, file_path: Path, original_name: str):
        """Process a single file based on its type"""
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.zip':
            # Process ZIP file
            extracted_files = self.zip_processor.extract_zip(file_path)
            for extracted_file in extracted_files:
                self.process_single_file(extracted_file, extracted_file.name)
        
        elif file_extension in ['.txt', '.md', '.json', '.pdf', '.docx']:
            # Process document
            content = self.doc_processor.process_document(file_path)
            if content:
                self.vector_store.add_document(content, original_name, file_path)
        
        elif file_extension in ['.mp3', '.wav', '.opus', '.flac', '.m4a']:
            # Process audio
            transcript = self.audio_processor.transcribe_audio(file_path)
            if transcript:
                self.vector_store.add_audio(transcript, original_name, file_path)
        
        elif file_extension in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
            # Process image
            metadata = self.image_processor.analyze_image(file_path)
            if metadata:
                self.vector_store.add_image(metadata, original_name, file_path)
    
    def search_interface(self):
        """Search interface for the knowledge base"""
        st.header("🔍 Search Your Knowledge Base")
        
        search_query = st.text_input("Enter your search query:", placeholder="Search documents, audio transcripts, images...")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            search_documents = st.checkbox("📄 Documents", value=True)
        with col2:
            search_audio = st.checkbox("🎵 Audio", value=True)
        with col3:
            search_images = st.checkbox("🖼️ Images", value=True)
        
        if search_query:
            with st.spinner("Searching..."):
                results = self.vector_store.search(
                    query=search_query,
                    include_documents=search_documents,
                    include_audio=search_audio,
                    include_images=search_images,
                    top_k=10
                )
            
            if results:
                st.subheader(f"Found {len(results)} results:")
                
                for i, result in enumerate(results, 1):
                    with st.expander(f"{i}. {result['filename']} (Score: {result['score']:.3f})"):
                        st.write(f"**Type:** {result['type']}")
                        st.write(f"**Added:** {result['timestamp']}")
                        
                        if result['type'] == 'document':
                            st.text_area("Content Preview:", result['content'][:500] + "...", height=150)
                        elif result['type'] == 'audio':
                            st.text_area("Transcript Preview:", result['transcript'][:500] + "...", height=150)
                            if st.button(f"🎵 Play Audio {i}", key=f"play_{i}"):
                                st.audio(str(result['file_path']))
                        elif result['type'] == 'image':
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.image(str(result['file_path']), width=200)
                            with col2:
                                st.json(result['metadata'])
            else:
                st.info("No results found. Try a different search query.")
    
    def audio_library(self):
        """Audio library interface"""
        st.header("🎵 Audio Library")
        
        audio_files = self.vector_store.get_audio_files()
        
        if audio_files:
            for audio in audio_files:
                with st.expander(f"🎵 {audio['filename']}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.audio(str(audio['file_path']))
                        st.write(f"**Duration:** {audio.get('duration', 'Unknown')}")
                        st.write(f"**Added:** {audio['timestamp']}")
                    
                    with col2:
                        st.text_area("Transcript:", audio['transcript'], height=200)
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
        
        # File type distribution
        if stats.get('file_types'):
            st.subheader("File Type Distribution")
            df = pd.DataFrame(list(stats['file_types'].items()), columns=['Type', 'Count'])
            st.bar_chart(df.set_index('Type'))
        
        # Recent activity
        if stats.get('recent_activity'):
            st.subheader("Recent Activity")
            df = pd.DataFrame(stats['recent_activity'])
            st.dataframe(df)
    
    def export_system_data(self):
        """Export system data for backup"""
        export_data = self.vector_store.export_data()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cognivault_export_{timestamp}.json"
        
        st.download_button(
            label="📥 Download Export",
            data=json.dumps(export_data, indent=2),
            file_name=filename,
            mime="application/json"
        )

def main():
    """Main application entry point"""
    app = CogniVault()
    app.main_interface()

if __name__ == "__main__":
    main()