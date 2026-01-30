#!/usr/bin/env python3
"""
ZIP Processor for CogniVault
Handles ZIP file extraction and processing
"""

import zipfile
import tarfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import os

class ZipProcessor:
    def __init__(self):
        """Initialize ZIP processor"""
        self.supported_archives = {'.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2'}
        
        # Supported content types we'll extract
        self.supported_content = {
            'documents': {'.txt', '.md', '.json', '.pdf', '.docx', '.html', '.rtf'},
            'images': {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'},
            'audio': {'.mp3', '.wav', '.opus', '.flac', '.m4a', '.aac', '.ogg'},
            'archives': {'.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2'}
        }
        
        # Security settings
        self.max_file_size = 100 * 1024 * 1024  # 100MB per file
        self.max_total_size = 500 * 1024 * 1024  # 500MB total extraction
        self.max_files = 1000  # Maximum files to extract
    
    def extract_zip(self, archive_path: Path, temp_dir: Path = None) -> List[Path]:
        """Extract ZIP/archive file and return list of extracted files"""
        if not archive_path.exists():
            print(f"Archive file not found: {archive_path}")
            return []
        
        if not self.is_supported_archive(archive_path):
            print(f"Unsupported archive format: {archive_path.suffix}")
            return []
        
        # Create temporary directory for extraction
        if temp_dir is None:
            temp_dir = Path(tempfile.mkdtemp(prefix="cognivault_extract_"))
        
        try:
            print(f"Extracting archive: {archive_path.name}")
            
            if archive_path.suffix.lower() == '.zip':
                extracted_files = self.extract_zip_file(archive_path, temp_dir)
            elif archive_path.suffix.lower() in {'.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2'}:
                extracted_files = self.extract_tar_file(archive_path, temp_dir)
            else:
                print(f"Archive type not implemented: {archive_path.suffix}")
                return []
            
            # Filter and validate extracted files
            valid_files = self.filter_extracted_files(extracted_files)
            
            print(f"Successfully extracted {len(valid_files)} files from {archive_path.name}")
            return valid_files
        
        except Exception as e:
            print(f"Error extracting archive: {e}")
            return []
    
    def extract_zip_file(self, zip_path: Path, extract_dir: Path) -> List[Path]:
        """Extract ZIP file using zipfile module"""
        extracted_files = []
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Check archive safety
            if not self.is_safe_archive(zip_ref):
                raise Exception("Archive contains potentially unsafe files")
            
            total_size = 0
            file_count = 0
            
            for member in zip_ref.namelist():
                if file_count >= self.max_files:
                    print(f"Warning: Stopped extraction at {self.max_files} files limit")
                    break
                
                # Skip directories
                if member.endswith('/'):
                    continue
                
                # Check file size
                file_info = zip_ref.getinfo(member)
                if file_info.file_size > self.max_file_size:
                    print(f"Skipping large file: {member} ({file_info.file_size} bytes)")
                    continue
                
                total_size += file_info.file_size
                if total_size > self.max_total_size:
                    print(f"Warning: Stopped extraction at {self.max_total_size} bytes limit")
                    break
                
                try:
                    # Extract file
                    zip_ref.extract(member, extract_dir)
                    extracted_path = extract_dir / member
                    
                    if extracted_path.exists() and extracted_path.is_file():
                        extracted_files.append(extracted_path)
                        file_count += 1
                
                except Exception as e:
                    print(f"Error extracting {member}: {e}")
                    continue
        
        return extracted_files
    
    def extract_tar_file(self, tar_path: Path, extract_dir: Path) -> List[Path]:
        """Extract TAR file using tarfile module"""
        extracted_files = []
        
        # Determine compression mode
        if tar_path.suffix.lower() in {'.tar.gz', '.tgz'}:
            mode = 'r:gz'
        elif tar_path.suffix.lower() in {'.tar.bz2', '.tbz2'}:
            mode = 'r:bz2'
        else:
            mode = 'r'
        
        with tarfile.open(tar_path, mode) as tar_ref:
            total_size = 0
            file_count = 0
            
            for member in tar_ref.getmembers():
                if file_count >= self.max_files:
                    print(f"Warning: Stopped extraction at {self.max_files} files limit")
                    break
                
                # Skip directories and special files
                if not member.isfile():
                    continue
                
                # Check file size
                if member.size > self.max_file_size:
                    print(f"Skipping large file: {member.name} ({member.size} bytes)")
                    continue
                
                total_size += member.size
                if total_size > self.max_total_size:
                    print(f"Warning: Stopped extraction at {self.max_total_size} bytes limit")
                    break
                
                # Security check - prevent path traversal
                if not self.is_safe_path(member.name):
                    print(f"Skipping unsafe path: {member.name}")
                    continue
                
                try:
                    # Extract file
                    tar_ref.extract(member, extract_dir)
                    extracted_path = extract_dir / member.name
                    
                    if extracted_path.exists() and extracted_path.is_file():
                        extracted_files.append(extracted_path)
                        file_count += 1
                
                except Exception as e:
                    print(f"Error extracting {member.name}: {e}")
                    continue
        
        return extracted_files
    
    def is_safe_archive(self, zip_ref: zipfile.ZipFile) -> bool:
        """Check if ZIP archive is safe to extract"""
        for member in zip_ref.namelist():
            if not self.is_safe_path(member):
                return False
        return True
    
    def is_safe_path(self, path: str) -> bool:
        """Check if file path is safe (no path traversal)"""
        # Normalize path
        normalized = os.path.normpath(path)
        
        # Check for path traversal attempts
        if normalized.startswith('..') or '/../' in normalized:
            return False
        
        # Check for absolute paths
        if os.path.isabs(normalized):
            return False
        
        return True
    
    def filter_extracted_files(self, files: List[Path]) -> List[Path]:
        """Filter extracted files to only include supported types"""
        valid_files = []
        
        for file_path in files:
            if not file_path.exists() or not file_path.is_file():
                continue
            
            # Check if file type is supported
            if self.is_supported_content(file_path):
                valid_files.append(file_path)
            else:
                print(f"Skipping unsupported file: {file_path.name}")
        
        return valid_files
    
    def is_supported_content(self, file_path: Path) -> bool:
        """Check if file is a supported content type"""
        file_ext = file_path.suffix.lower()
        
        for content_type, extensions in self.supported_content.items():
            if file_ext in extensions:
                return True
        
        return False
    
    def get_content_type(self, file_path: Path) -> Optional[str]:
        """Get content type of file"""
        file_ext = file_path.suffix.lower()
        
        for content_type, extensions in self.supported_content.items():
            if file_ext in extensions:
                return content_type
        
        return None
    
    def is_supported_archive(self, file_path: Path) -> bool:
        """Check if archive format is supported"""
        return file_path.suffix.lower() in self.supported_archives
    
    def get_archive_info(self, archive_path: Path) -> Dict[str, Any]:
        """Get information about archive contents"""
        if not archive_path.exists():
            return {}
        
        if not self.is_supported_archive(archive_path):
            return {'error': 'Unsupported archive format'}
        
        try:
            info = {
                'filename': archive_path.name,
                'size': archive_path.stat().st_size,
                'format': archive_path.suffix.lower(),
                'files': [],
                'content_types': {}
            }
            
            if archive_path.suffix.lower() == '.zip':
                info.update(self.get_zip_info(archive_path))
            elif archive_path.suffix.lower() in {'.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2'}:
                info.update(self.get_tar_info(archive_path))
            
            return info
        
        except Exception as e:
            return {'error': f'Error reading archive: {e}'}
    
    def get_zip_info(self, zip_path: Path) -> Dict[str, Any]:
        """Get information about ZIP file contents"""
        files = []
        content_types = {}
        total_size = 0
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith('/'):
                    continue
                
                file_info = zip_ref.getinfo(member)
                file_path = Path(member)
                content_type = self.get_content_type(file_path)
                
                files.append({
                    'name': member,
                    'size': file_info.file_size,
                    'content_type': content_type,
                    'supported': content_type is not None
                })
                
                total_size += file_info.file_size
                
                if content_type:
                    content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            'file_count': len(files),
            'total_size': total_size,
            'files': files,
            'content_types': content_types
        }
    
    def get_tar_info(self, tar_path: Path) -> Dict[str, Any]:
        """Get information about TAR file contents"""
        files = []
        content_types = {}
        total_size = 0
        
        # Determine compression mode
        if tar_path.suffix.lower() in {'.tar.gz', '.tgz'}:
            mode = 'r:gz'
        elif tar_path.suffix.lower() in {'.tar.bz2', '.tbz2'}:
            mode = 'r:bz2'
        else:
            mode = 'r'
        
        with tarfile.open(tar_path, mode) as tar_ref:
            for member in tar_ref.getmembers():
                if not member.isfile():
                    continue
                
                file_path = Path(member.name)
                content_type = self.get_content_type(file_path)
                
                files.append({
                    'name': member.name,
                    'size': member.size,
                    'content_type': content_type,
                    'supported': content_type is not None
                })
                
                total_size += member.size
                
                if content_type:
                    content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            'file_count': len(files),
            'total_size': total_size,
            'files': files,
            'content_types': content_types
        }
    
    def cleanup_temp_files(self, temp_dir: Path):
        """Clean up temporary extraction directory"""
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Error cleaning up temp directory: {e}")
    
    def batch_extract(self, archive_files: List[Path]) -> Dict[str, List[Path]]:
        """Extract multiple archive files"""
        results = {}
        
        for archive_file in archive_files:
            print(f"Processing archive: {archive_file.name}")
            
            # Create unique temp directory for each archive
            temp_dir = Path(tempfile.mkdtemp(prefix=f"cognivault_{archive_file.stem}_"))
            
            try:
                extracted_files = self.extract_zip(archive_file, temp_dir)
                results[str(archive_file)] = extracted_files
            except Exception as e:
                print(f"Error processing {archive_file.name}: {e}")
                results[str(archive_file)] = []
        
        return results
    
    def get_supported_formats(self) -> Dict[str, set]:
        """Get supported archive and content formats"""
        return {
            'archives': self.supported_archives.copy(),
            'content': {k: v.copy() for k, v in self.supported_content.items()}
        }