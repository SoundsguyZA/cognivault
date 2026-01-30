#!/usr/bin/env python3
"""
Image Processor for CogniVault - FIXED VERSION
Handles image analysis and metadata extraction

FIXES:
- Properly serialize EXIF IFDRational objects to floats
- Better error handling for corrupted EXIF data
- Safe JSON serialization for all EXIF types
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib
from datetime import datetime

class ImageProcessor:
    def __init__(self, image_storage_path: Path):
        """Initialize image processor"""
        self.image_storage_path = image_storage_path
        self.image_storage_path.mkdir(parents=True, exist_ok=True)
        
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
        
        # Check available image processing libraries
        self.tools_available = self.check_available_tools()
    
    def check_available_tools(self) -> Dict[str, bool]:
        """Check which image processing tools are available"""
        tools = {}
        
        # Check for Pillow (PIL)
        try:
            from PIL import Image, ExifTags
            tools['pillow'] = True
        except ImportError:
            tools['pillow'] = False
        
        # Check for opencv
        try:
            import cv2
            tools['opencv'] = True
        except ImportError:
            tools['opencv'] = False
        
        return tools
    
    def analyze_image(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze image and extract metadata"""
        if not image_path.exists():
            print(f"Image file not found: {image_path}")
            return None
        
        if not self.is_supported_format(image_path):
            print(f"Unsupported image format: {image_path.suffix}")
            return None
        
        try:
            # Get basic file information
            metadata = self.get_basic_metadata(image_path)
            
            # Try to get detailed image analysis
            if self.tools_available['pillow']:
                image_data = self.analyze_with_pillow(image_path)
                metadata.update(image_data)
            elif self.tools_available['opencv']:
                image_data = self.analyze_with_opencv(image_path)
                metadata.update(image_data)
            else:
                # Install Pillow and try again
                if self.install_pillow():
                    image_data = self.analyze_with_pillow(image_path)
                    metadata.update(image_data)
            
            # Save image to storage
            saved_path = self.save_image_file(image_path)
            metadata['stored_path'] = str(saved_path)
            
            return metadata
        
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return self.get_basic_metadata(image_path)
    
    def is_supported_format(self, file_path: Path) -> bool:
        """Check if file format is supported"""
        return file_path.suffix.lower() in self.supported_formats
    
    def get_basic_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file metadata"""
        stat = file_path.stat()
        
        return {
            'filename': file_path.name,
            'file_path': str(file_path),
            'file_size': stat.st_size,
            'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'file_hash': self.calculate_file_hash(file_path)
        }
    
    def analyze_with_pillow(self, image_path: Path) -> Dict[str, Any]:
        """Analyze image using Pillow (PIL)"""
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                analysis = {
                    'dimensions': f"{img.width}x{img.height}",
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'aspect_ratio': round(img.width / img.height, 2),
                    'pixel_count': img.width * img.height
                }
                
                # Extract EXIF data (FIXED VERSION)
                exif_data = self.extract_exif_data(img)
                if exif_data:
                    analysis['exif'] = exif_data
                
                # Color information
                if img.mode == 'P':
                    analysis['colors'] = len(img.getpalette()) // 3
                else:
                    analysis['colors'] = self.estimate_color_count(img)
                
                # Image statistics
                try:
                    extrema = img.getextrema()
                    analysis['pixel_range'] = extrema
                except:
                    pass
            
            return analysis
        
        except Exception as e:
            print(f"Error analyzing with Pillow: {e}")
            return {}
    
    def analyze_with_opencv(self, image_path: Path) -> Dict[str, Any]:
        """Analyze image using OpenCV"""
        try:
            import cv2
            import numpy as np
            
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                return {}
            
            height, width, channels = img.shape
            
            analysis = {
                'dimensions': f"{width}x{height}",
                'width': width,
                'height': height,
                'channels': channels,
                'aspect_ratio': round(width / height, 2),
                'pixel_count': width * height
            }
            
            # Basic color analysis
            analysis['mean_color'] = {
                'blue': float(np.mean(img[:, :, 0])),
                'green': float(np.mean(img[:, :, 1])),
                'red': float(np.mean(img[:, :, 2]))
            }
            
            # Brightness analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            analysis['brightness'] = float(np.mean(gray))
            analysis['contrast'] = float(np.std(gray))
            
            return analysis
        
        except Exception as e:
            print(f"Error analyzing with OpenCV: {e}")
            return {}
    
    def extract_exif_data(self, pil_image) -> Dict[str, Any]:
        """Extract EXIF data from PIL image - FIXED VERSION"""
        try:
            from PIL import ExifTags
            from PIL.TiffImagePlugin import IFDRational
            
            exif_dict = {}
            exif = pil_image._getexif()
            
            if exif is not None:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    
                    # FIXED: Convert value to JSON-serializable format
                    try:
                        # Handle IFDRational objects
                        if isinstance(value, IFDRational):
                            value = float(value)
                        
                        # Handle bytes
                        elif isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8')
                            except:
                                value = str(value)
                        
                        # Handle tuples (convert to list)
                        elif isinstance(value, tuple):
                            # Check if tuple contains IFDRational objects
                            value = [float(v) if isinstance(v, IFDRational) else v for v in value]
                        
                        # Handle other non-serializable types
                        elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            value = str(value)
                        
                        # Test JSON serialization
                        json.dumps({tag: value})
                        exif_dict[tag] = value
                    
                    except (TypeError, ValueError) as e:
                        # If still can't serialize, convert to string
                        print(f"⚠️ EXIF tag {tag} value not serializable, converting to string")
                        exif_dict[tag] = str(value)
            
            return exif_dict
        
        except Exception as e:
            print(f"Error extracting EXIF: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def estimate_color_count(self, pil_image) -> int:
        """Estimate the number of unique colors in image"""
        try:
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # For large images, sample to avoid memory issues
            max_size = 100
            if pil_image.width > max_size or pil_image.height > max_size:
                pil_image.thumbnail((max_size, max_size))
            
            # Get colors
            colors = pil_image.getcolors(maxcolors=256*256)
            
            if colors:
                return len(colors)
            else:
                return 256*256  # Too many to count
        
        except Exception as e:
            print(f"Error estimating colors: {e}")
            return 0
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return ""
    
    def save_image_file(self, source_path: Path) -> Path:
        """Save image file to storage"""
        try:
            # Generate unique filename using hash
            file_hash = self.calculate_file_hash(source_path)
            stored_filename = f"{file_hash}{source_path.suffix}"
            stored_path = self.image_storage_path / stored_filename
            
            # Copy file if not already exists
            if not stored_path.exists():
                import shutil
                shutil.copy2(source_path, stored_path)
            
            return stored_path
        
        except Exception as e:
            print(f"Error saving image: {e}")
            return source_path
    
    def install_pillow(self) -> bool:
        """Try to install Pillow"""
        try:
            import subprocess
            import sys
            
            print("Installing Pillow (PIL)...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "--quiet"])
            
            # Re-check tools
            self.tools_available = self.check_available_tools()
            return self.tools_available['pillow']
        
        except Exception as e:
            print(f"Could not install Pillow: {e}")
            return False
    
    def process_image(self, file_path: Path) -> Dict[str, Any]:
        """Main entry point for image processing"""
        metadata = self.analyze_image(file_path)
        
        if metadata:
            return {
                'success': True,
                'metadata': metadata,
                'filename': file_path.name,
                'file_type': 'image'
            }
        else:
            return {
                'success': False,
                'error': 'Failed to analyze image',
                'filename': file_path.name,
                'file_type': 'image'
            }
