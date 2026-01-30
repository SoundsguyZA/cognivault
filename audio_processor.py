#!/usr/bin/env python3
"""
Audio Processor for CogniVault
Handles audio transcription using Whisper (local, no API required)
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import json
import shutil

class AudioProcessor:
    def __init__(self, audio_storage_path: Path):
        """Initialize audio processor with storage path"""
        self.audio_storage_path = audio_storage_path
        self.audio_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Check if Whisper is available
        self.whisper_available = self.check_whisper_installation()
        
        # Supported audio formats
        self.supported_formats = {'.mp3', '.wav', '.opus', '.flac', '.m4a', '.aac', '.ogg'}
    
    def check_whisper_installation(self) -> bool:
        """Check if Whisper is installed and available"""
        try:
            # Try to import whisper
            import whisper
            return True
        except ImportError:
            print("Whisper not found. Install with: pip install openai-whisper")
            return False
    
    def install_whisper(self) -> bool:
        """Install Whisper if not available"""
        try:
            import subprocess
            import sys
            
            print("Installing Whisper...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper"])
            
            # Try importing again
            import whisper
            self.whisper_available = True
            print("Whisper installed successfully!")
            return True
        except Exception as e:
            print(f"Failed to install Whisper: {e}")
            return False
    
    def transcribe_audio(self, audio_file_path: Path) -> Optional[str]:
        """Transcribe audio file to text using Whisper"""
        if not audio_file_path.exists():
            print(f"Audio file not found: {audio_file_path}")
            return None
        
        if audio_file_path.suffix.lower() not in self.supported_formats:
            print(f"Unsupported audio format: {audio_file_path.suffix}")
            return None
        
        if not self.whisper_available:
            print("Whisper not available. Attempting to install...")
            if not self.install_whisper():
                return self.fallback_transcription(audio_file_path)
        
        try:
            import whisper
            
            # Load the tiny model (75MB) for speed and efficiency
            print("Loading Whisper model (this may take a moment on first run)...")
            model = whisper.load_model("tiny")
            
            print(f"Transcribing: {audio_file_path.name}")
            result = model.transcribe(str(audio_file_path))
            
            transcript = result["text"].strip()
            
            # Save audio file to storage
            self.save_audio_file(audio_file_path)
            
            print(f"Transcription complete: {len(transcript)} characters")
            return transcript
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return self.fallback_transcription(audio_file_path)
    
    def fallback_transcription(self, audio_file_path: Path) -> str:
        """Fallback transcription when Whisper is not available"""
        # Create a basic metadata description
        file_info = self.get_audio_metadata(audio_file_path)
        
        fallback_text = f"""
        Audio file: {audio_file_path.name}
        Format: {audio_file_path.suffix.upper()}
        Size: {self.format_file_size(audio_file_path.stat().st_size)}
        
        [AUDIO TRANSCRIPTION NOT AVAILABLE - WHISPER NOT INSTALLED]
        
        This audio file has been indexed but could not be transcribed.
        To enable transcription, install Whisper: pip install openai-whisper
        
        File metadata: {json.dumps(file_info, indent=2)}
        """
        
        # Still save the audio file
        self.save_audio_file(audio_file_path)
        
        return fallback_text.strip()
    
    def get_audio_metadata(self, audio_file_path: Path) -> Dict[str, Any]:
        """Extract basic audio metadata"""
        try:
            # Try using ffprobe if available
            if shutil.which('ffprobe'):
                return self.get_metadata_with_ffprobe(audio_file_path)
            else:
                return self.get_basic_metadata(audio_file_path)
        except Exception as e:
            print(f"Error getting audio metadata: {e}")
            return self.get_basic_metadata(audio_file_path)
    
    def get_metadata_with_ffprobe(self, audio_file_path: Path) -> Dict[str, Any]:
        """Get detailed metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(audio_file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extract useful information
                metadata = {
                    'filename': audio_file_path.name,
                    'format': audio_file_path.suffix.upper(),
                    'size_bytes': audio_file_path.stat().st_size
                }
                
                if 'format' in data:
                    format_info = data['format']
                    metadata['duration'] = float(format_info.get('duration', 0))
                    metadata['bit_rate'] = format_info.get('bit_rate')
                    metadata['format_name'] = format_info.get('format_name')
                
                if 'streams' in data and data['streams']:
                    stream = data['streams'][0]  # First audio stream
                    metadata['codec'] = stream.get('codec_name')
                    metadata['sample_rate'] = stream.get('sample_rate')
                    metadata['channels'] = stream.get('channels')
                
                return metadata
        except Exception as e:
            print(f"ffprobe error: {e}")
        
        return self.get_basic_metadata(audio_file_path)
    
    def get_basic_metadata(self, audio_file_path: Path) -> Dict[str, Any]:
        """Get basic file metadata without external tools"""
        stat = audio_file_path.stat()
        
        return {
            'filename': audio_file_path.name,
            'format': audio_file_path.suffix.upper(),
            'size_bytes': stat.st_size,
            'size_formatted': self.format_file_size(stat.st_size),
            'modified': stat.st_mtime,
            'duration': 'Unknown (install ffmpeg for duration detection)'
        }
    
    def save_audio_file(self, source_path: Path) -> Path:
        """Save audio file to storage directory"""
        try:
            # Create unique filename to avoid conflicts
            timestamp = int(source_path.stat().st_mtime)
            safe_name = self.sanitize_filename(source_path.name)
            target_name = f"{timestamp}_{safe_name}"
            target_path = self.audio_storage_path / target_name
            
            # Copy file if it doesn't already exist
            if not target_path.exists():
                shutil.copy2(source_path, target_path)
                print(f"Audio saved to: {target_path}")
            
            return target_path
        except Exception as e:
            print(f"Error saving audio file: {e}")
            return source_path
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        # Remove or replace problematic characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_name = re.sub(r'_{2,}', '_', safe_name)  # Replace multiple underscores
        return safe_name.strip('_')
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def get_supported_formats(self) -> set:
        """Get list of supported audio formats"""
        return self.supported_formats.copy()
    
    def is_supported_format(self, file_path: Path) -> bool:
        """Check if file format is supported"""
        return file_path.suffix.lower() in self.supported_formats
    
    def batch_transcribe(self, audio_files: list) -> Dict[str, Optional[str]]:
        """Transcribe multiple audio files"""
        results = {}
        
        for audio_file in audio_files:
            if isinstance(audio_file, str):
                audio_file = Path(audio_file)
            
            print(f"Processing {audio_file.name}...")
            transcript = self.transcribe_audio(audio_file)
            results[str(audio_file)] = transcript
        
        return results
    
    def get_audio_info(self, audio_file_path: Path) -> Dict[str, Any]:
        """Get comprehensive audio file information"""
        if not audio_file_path.exists():
            return {}
        
        info = {
            'filename': audio_file_path.name,
            'path': str(audio_file_path),
            'supported': self.is_supported_format(audio_file_path),
            'metadata': self.get_audio_metadata(audio_file_path)
        }
        
        return info