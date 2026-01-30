#!/usr/bin/env python3
"""
Utility functions for CogniVault
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import subprocess
import sys

def setup_directories(base_dir: Path) -> Dict[str, Path]:
    """Setup required directories for CogniVault"""
    directories = {
        'base': base_dir,
        'vector_db': base_dir / "vector_db",
        'audio': base_dir / "audio",
        'images': base_dir / "images",
        'documents': base_dir / "documents",
        'temp': base_dir / "temp",
        'exports': base_dir / "exports"
    }
    
    # Create all directories
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Directory ready: {name} -> {path}")
    
    return directories

def get_file_hash(file_path: Path) -> str:
    """Generate SHA-256 hash of file content"""
    if not file_path.exists():
        return hashlib.sha256(str(file_path).encode()).hexdigest()
    
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"Error hashing file {file_path}: {e}")
        return hashlib.sha256(str(file_path).encode()).hexdigest()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace problematic characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = re.sub(r'_{2,}', '_', safe_name)  # Replace multiple underscores
    safe_name = safe_name.strip('_')
    
    # Ensure filename isn't too long
    if len(safe_name) > 200:
        name_part = safe_name[:150]
        ext_part = safe_name[-50:] if '.' in safe_name[-50:] else ''
        safe_name = name_part + '_' + ext_part
    
    return safe_name

def check_system_dependencies() -> Dict[str, bool]:
    """Check if system dependencies are available"""
    dependencies = {}
    
    # Check Python packages
    python_packages = [
        'streamlit',
        'scikit-learn',
        'numpy',
        'pandas',
        'sqlite3'  # Built-in
    ]
    
    for package in python_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
            dependencies[package] = True
        except ImportError:
            dependencies[package] = False
    
    # Check optional packages
    optional_packages = [
        'whisper',
        'PIL',
        'cv2',
        'pdfplumber',
        'docx',
        'bs4'
    ]
    
    for package in optional_packages:
        try:
            if package == 'PIL':
                from PIL import Image
            elif package == 'cv2':
                import cv2
            elif package == 'bs4':
                from bs4 import BeautifulSoup
            else:
                __import__(package)
            dependencies[f"{package}_optional"] = True
        except ImportError:
            dependencies[f"{package}_optional"] = False
    
    # Check system tools
    system_tools = ['ffmpeg', 'ffprobe', 'pandoc']
    
    for tool in system_tools:
        dependencies[f"{tool}_system"] = check_command_available(tool)
    
    return dependencies

def check_command_available(command: str) -> bool:
    """Check if a system command is available"""
    import shutil
    return shutil.which(command) is not None

def install_package(package_name: str) -> bool:
    """Install Python package using pip"""
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_name}: {e}")
        return False

def install_required_packages() -> Dict[str, bool]:
    """Install required packages for CogniVault"""
    required_packages = {
        'streamlit': 'streamlit',
        'scikit-learn': 'scikit-learn',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'whisper': 'openai-whisper',
        'PIL': 'Pillow',
        'pdfplumber': 'pdfplumber',
        'docx': 'python-docx',
        'bs4': 'beautifulsoup4'
    }
    
    installation_results = {}
    
    for module_name, package_name in required_packages.items():
        try:
            if module_name == 'PIL':
                from PIL import Image
            elif module_name == 'bs4':
                from bs4 import BeautifulSoup
            else:
                __import__(module_name)
            installation_results[package_name] = True
            print(f"✅ {package_name} already installed")
        except ImportError:
            success = install_package(package_name)
            installation_results[package_name] = success
    
    return installation_results

def create_system_info() -> Dict[str, Any]:
    """Create system information summary"""
    import platform
    import psutil
    
    try:
        system_info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version()
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'percentage': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'used': psutil.disk_usage('/').used,
                'percentage': psutil.disk_usage('/').percent
            },
            'dependencies': check_system_dependencies()
        }
    except ImportError:
        # Fallback if psutil is not available
        system_info = {
            'platform': {
                'system': platform.system(),
                'python_version': platform.python_version()
            },
            'dependencies': check_system_dependencies()
        }
    
    return system_info

def validate_file_path(file_path: Path, check_exists: bool = True) -> bool:
    """Validate file path for security and existence"""
    try:
        # Convert to Path object if string
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # Resolve path to detect traversal attempts
        resolved_path = file_path.resolve()
        
        # Check for path traversal (basic check)
        if '..' in str(file_path):
            print(f"Potential path traversal detected: {file_path}")
            return False
        
        # Check if file exists (if required)
        if check_exists and not resolved_path.exists():
            print(f"File does not exist: {resolved_path}")
            return False
        
        return True
    
    except Exception as e:
        print(f"Error validating path {file_path}: {e}")
        return False

def safe_json_load(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load JSON file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return None

def safe_json_save(data: Dict[str, Any], file_path: Path) -> bool:
    """Safely save data to JSON file"""
    try:
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {e}")
        return False

def cleanup_temp_files(temp_dir: Path, max_age_hours: int = 24):
    """Clean up temporary files older than specified hours"""
    import time
    
    if not temp_dir.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    cleaned_count = 0
    for file_path in temp_dir.rglob('*'):
        try:
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    cleaned_count += 1
        except Exception as e:
            print(f"Error cleaning temp file {file_path}: {e}")
    
    # Remove empty directories
    try:
        for dir_path in temp_dir.rglob('*'):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()
    except Exception as e:
        print(f"Error cleaning empty directories: {e}")
    
    if cleaned_count > 0:
        print(f"Cleaned up {cleaned_count} temporary files")

def get_mime_type(file_path: Path) -> str:
    """Get MIME type of file"""
    import mimetypes
    
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'

def is_text_file(file_path: Path) -> bool:
    """Check if file is likely a text file"""
    text_extensions = {
        '.txt', '.md', '.json', '.csv', '.xml', '.html', '.htm', 
        '.css', '.js', '.py', '.java', '.cpp', '.c', '.h', '.yaml', '.yml'
    }
    
    if file_path.suffix.lower() in text_extensions:
        return True
    
    # Check MIME type
    mime_type = get_mime_type(file_path)
    return mime_type.startswith('text/')

def get_file_type_category(file_path: Path) -> str:
    """Categorize file type"""
    extension = file_path.suffix.lower()
    
    categories = {
        'document': {'.txt', '.md', '.pdf', '.docx', '.doc', '.rtf', '.odt'},
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'},
        'audio': {'.mp3', '.wav', '.opus', '.flac', '.m4a', '.aac', '.ogg'},
        'video': {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'},
        'archive': {'.zip', '.tar', '.gz', '.bz2', '.rar', '.7z'},
        'code': {'.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h'},
        'data': {'.json', '.xml', '.csv', '.tsv', '.sql', '.yaml', '.yml'}
    }
    
    for category, extensions in categories.items():
        if extension in extensions:
            return category
    
    return 'other'

def create_backup(source_dir: Path, backup_dir: Path) -> bool:
    """Create backup of directory"""
    try:
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        shutil.copytree(source_dir, backup_path)
        print(f"Backup created: {backup_path}")
        return True
    
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def estimate_processing_time(file_path: Path) -> float:
    """Estimate processing time for file (in seconds)"""
    if not file_path.exists():
        return 0.0
    
    file_size = file_path.stat().st_size
    file_type = get_file_type_category(file_path)
    
    # Base processing speeds (bytes per second, roughly estimated)
    speeds = {
        'document': 1024 * 1024 * 10,  # 10MB/s
        'image': 1024 * 1024 * 5,     # 5MB/s
        'audio': 1024 * 1024 * 2,     # 2MB/s (transcription is slow)
        'archive': 1024 * 1024 * 20,  # 20MB/s
        'other': 1024 * 1024 * 5      # 5MB/s
    }
    
    speed = speeds.get(file_type, speeds['other'])
    estimated_time = file_size / speed
    
    # Add some overhead
    return max(1.0, estimated_time * 1.5)

def generate_system_report() -> Dict[str, Any]:
    """Generate comprehensive system report"""
    report = {
        'timestamp': import_datetime().datetime.now().isoformat(),
        'system_info': create_system_info(),
        'dependencies': check_system_dependencies(),
        'cognivault_version': '1.0.0',
        'features': {
            'local_processing': True,
            'whisper_transcription': check_system_dependencies().get('whisper_optional', False),
            'pdf_processing': check_system_dependencies().get('pdfplumber_optional', False),
            'image_analysis': check_system_dependencies().get('PIL_optional', False),
            'zip_processing': True,
            'tfidf_search': True
        }
    }
    
    return report

def import_datetime():
    """Import datetime module (for compatibility with different environments)"""
    import datetime
    return datetime