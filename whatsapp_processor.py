#!/usr/bin/env python3
"""
WhatsApp Chat Processor for CogniVault - FIXED VERSION
Handles WhatsApp export ZIP files and extracts all content
VERITAS BUILD - Complete WhatsApp Chat Analysis

FIXES:
- Improved datetime pattern matching (handles more formats)
- Better encoding detection
- More flexible message parsing
- Handles large exports (1GB+)
"""

import json
import re
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import tempfile
import shutil
import chardet  # For better encoding detection

class WhatsAppProcessor:
    def __init__(self, cognivault_instance):
        """Initialize WhatsApp processor with CogniVault instance"""
        self.cv = cognivault_instance
        
        # WhatsApp file patterns
        self.chat_file_patterns = [
            r'.*\.txt$',  # WhatsApp chat export
            r'_chat\.txt$',  # Specific chat export format
            r'WhatsApp Chat.*\.txt$'  # Standard naming
        ]
        
        # Media patterns in WhatsApp exports
        self.media_patterns = {
            'audio': [r'.*\.(opus|m4a|mp3|wav|aac)$'],
            'image': [r'.*\.(jpg|jpeg|png|webp|gif)$'],
            'video': [r'.*\.(mp4|3gp|mov|avi)$'],
            'document': [r'.*\.(pdf|doc|docx|txt|ppt|pptx|xls|xlsx)$']
        }
        
        # IMPROVED: More flexible message parsing patterns
        self.message_patterns = {
            # Match various datetime formats (international support)
            'datetime': r'(\[?\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}[,\s]+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\]?)',
            'sender': r'([^:]+):',
            'system': r'<This message was deleted>|changed their phone number|changed to|left|added|created group|changed the subject|changed this group\'s icon',
            'media': r'<Media omitted>|<attached:|audio omitted|image omitted|video omitted|document omitted|\.(?:opus|jpg|jpeg|png|mp4|pdf|docx?)\s*\(file attached\)'
        }
    
    def process_whatsapp_export(self, zip_path: Path) -> Dict[str, Any]:
        """Process complete WhatsApp export ZIP file"""
        print(f"Processing WhatsApp export: {zip_path.name}")
        
        # Extract ZIP to temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="whatsapp_export_"))
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find and process chat files
            chat_results = []
            media_results = []
            
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    if self.is_chat_file(file_path):
                        print(f"Found chat file: {file_path.name}")
                        chat_data = self.process_chat_file(file_path)
                        if chat_data:
                            chat_results.append(chat_data)
                            print(f"  → Processed {chat_data['message_count']} messages from {chat_data['chat_name']}")
                    
                    elif self.is_media_file(file_path):
                        media_data = self.process_media_file(file_path)
                        if media_data:
                            media_results.append(media_data)
            
            # Index processed content in CogniVault
            total_indexed = 0
            
            # Index chat content
            for chat_data in chat_results:
                success = self.cv.vector_store.add_document(
                    content=chat_data['searchable_content'],
                    filename=f"WhatsApp_{chat_data['chat_name']}_{chat_data['date_range']}.txt",
                    file_path=None
                )
                if success:
                    total_indexed += 1
            
            # Process media files
            for media_data in media_results:
                if media_data['type'] == 'audio':
                    transcript = self.cv.audio_processor.transcribe_audio(media_data['path'])
                    if transcript:
                        self.cv.vector_store.add_audio(
                            transcript=transcript,
                            filename=media_data['filename'],
                            file_path=media_data['path']
                        )
                        total_indexed += 1
                
                elif media_data['type'] == 'image':
                    metadata = self.cv.image_processor.analyze_image(media_data['path'])
                    if metadata:
                        self.cv.vector_store.add_image(
                            metadata=metadata,
                            filename=media_data['filename'],
                            file_path=media_data['path']
                        )
                        total_indexed += 1
            
            return {
                'success': True,
                'chats_processed': len(chat_results),
                'media_processed': len(media_results),
                'total_indexed': total_indexed,
                'chat_details': chat_results
            }
        
        finally:
            # Cleanup temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def is_chat_file(self, file_path: Path) -> bool:
        """Check if file is a WhatsApp chat export"""
        filename = file_path.name.lower()
        
        for pattern in self.chat_file_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                # Additional check: file should contain chat-like content
                try:
                    with open(file_path, 'rb') as f:
                        sample = f.read(1024).decode('utf-8', errors='ignore')
                        # Look for datetime patterns in first 1KB
                        if re.search(self.message_patterns['datetime'], sample):
                            return True
                except:
                    pass
        
        return False
    
    def is_media_file(self, file_path: Path) -> bool:
        """Check if file is WhatsApp media"""
        filename = file_path.name.lower()
        
        for media_type, patterns in self.media_patterns.items():
            for pattern in patterns:
                if re.match(pattern, filename, re.IGNORECASE):
                    return True
        
        return False
    
    def get_media_type(self, file_path: Path) -> Optional[str]:
        """Get media type of file"""
        filename = file_path.name.lower()
        
        for media_type, patterns in self.media_patterns.items():
            for pattern in patterns:
                if re.match(pattern, filename, re.IGNORECASE):
                    return media_type
        
        return None
    
    def process_chat_file(self, chat_file: Path) -> Optional[Dict[str, Any]]:
        """Process individual chat file"""
        try:
            # IMPROVED: Better encoding detection
            content = None
            
            # First, try auto-detection with chardet
            with open(chat_file, 'rb') as f:
                raw_data = f.read()
            
            # Detect encoding
            detected = chardet.detect(raw_data)
            detected_encoding = detected.get('encoding', 'utf-8')
            
            # Try detected encoding first, then fallback encodings
            encodings = [detected_encoding, 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    content = raw_data.decode(encoding)
                    print(f"Successfully decoded with {encoding}")
                    break
                except (UnicodeDecodeError, AttributeError):
                    continue
            
            if not content:
                print(f"Could not read chat file: {chat_file}")
                return None
            
            # Parse chat content
            messages = self.parse_chat_messages(content)
            
            if not messages:
                print(f"⚠️ WARNING: No messages found in: {chat_file.name}")
                print(f"   File size: {len(content)} characters")
                print(f"   First 200 chars: {content[:200]}")
                return None
            
            # Extract chat metadata
            chat_name = self.extract_chat_name(chat_file.name, messages)
            date_range = self.get_date_range(messages)
            participants = self.get_participants(messages)
            
            # Create searchable content
            searchable_content = self.create_searchable_content(messages, chat_name, participants)
            
            # Generate statistics
            stats = self.generate_chat_statistics(messages)
            
            return {
                'filename': chat_file.name,
                'chat_name': chat_name,
                'date_range': date_range,
                'participants': participants,
                'message_count': len(messages),
                'searchable_content': searchable_content,
                'statistics': stats,
                'first_message': messages[0]['datetime'] if messages else None,
                'last_message': messages[-1]['datetime'] if messages else None
            }
        
        except Exception as e:
            print(f"Error processing chat file {chat_file}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_chat_messages(self, content: str) -> List[Dict[str, Any]]:
        """Parse WhatsApp chat messages from text content - IMPROVED"""
        messages = []
        lines = content.split('\n')
        
        current_message = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # IMPROVED: More flexible datetime matching
            # Try multiple datetime patterns
            datetime_match = None
            datetime_patterns = [
                # Standard formats
                r'(\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)',
                # With brackets (iOS style)
                r'\[(\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\]',
                # With dashes
                r'(\d{1,2}-\d{1,2}-\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)',
                # With dots
                r'(\d{1,2}\.\d{1,2}\.\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)',
            ]
            
            for pattern in datetime_patterns:
                match = re.match(pattern, line)
                if match:
                    datetime_match = match
                    break
            
            if datetime_match:
                # Save previous message if exists
                if current_message:
                    messages.append(current_message)
                
                # Start new message
                datetime_str = datetime_match.group(1)
                remaining_line = line[len(datetime_match.group(0)):].strip()
                
                # Remove common separators
                for separator in ['-', '—', '–', ':']:
                    if remaining_line.startswith(separator):
                        remaining_line = remaining_line[1:].strip()
                        break
                
                # Extract sender and content
                sender_match = re.match(r'([^:]+):\s*(.*)$', remaining_line)
                
                if sender_match:
                    sender = sender_match.group(1).strip()
                    message_content = sender_match.group(2).strip()
                else:
                    sender = "System"
                    message_content = remaining_line
                
                current_message = {
                    'datetime': self.parse_datetime(datetime_str),
                    'datetime_str': datetime_str,
                    'sender': sender,
                    'content': message_content,
                    'is_system': self.is_system_message(message_content),
                    'is_media': self.is_media_message(message_content)
                }
            
            elif current_message:
                # Continue previous message (multi-line messages)
                current_message['content'] += '\n' + line
        
        # Add last message
        if current_message:
            messages.append(current_message)
        
        print(f"Parsed {len(messages)} messages from {len(lines)} lines")
        return messages
    
    def parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse WhatsApp datetime string - IMPROVED"""
        # Common WhatsApp datetime formats
        formats = [
            # With comma and space
            '%d/%m/%Y, %H:%M:%S',
            '%d/%m/%Y, %H:%M',
            '%m/%d/%Y, %H:%M:%S',
            '%m/%d/%Y, %H:%M',
            '%d/%m/%y, %H:%M:%S',
            '%d/%m/%y, %H:%M',
            '%m/%d/%y, %H:%M:%S',
            '%m/%d/%y, %H:%M',
            # Without comma
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            # With dashes
            '%d-%m-%Y, %H:%M:%S',
            '%d-%m-%Y, %H:%M',
            '%d-%m-%Y %H:%M:%S',
            '%d-%m-%Y %H:%M',
            # With dots
            '%d.%m.%Y, %H:%M:%S',
            '%d.%m.%Y, %H:%M',
            '%d.%m.%Y %H:%M:%S',
            '%d.%m.%Y %H:%M',
        ]
        
        # Clean datetime string
        cleaned = datetime_str.strip().replace('  ', ' ')
        
        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        
        # If still can't parse, try removing commas
        cleaned_no_comma = cleaned.replace(',', '')
        for fmt in formats:
            try:
                return datetime.strptime(cleaned_no_comma, fmt)
            except ValueError:
                continue
        
        print(f"⚠️ Could not parse datetime: '{datetime_str}'")
        return None
    
    def is_system_message(self, content: str) -> bool:
        """Check if message is a system message"""
        return bool(re.search(self.message_patterns['system'], content, re.IGNORECASE))
    
    def is_media_message(self, content: str) -> bool:
        """Check if message contains media"""
        return bool(re.search(self.message_patterns['media'], content, re.IGNORECASE))
    
    def extract_chat_name(self, filename: str, messages: List[Dict]) -> str:
        """Extract chat name from filename or content"""
        # Try to extract from filename
        name_from_file = filename.replace('.txt', '').replace('_', ' ')
        
        # Remove common prefixes
        prefixes = ['WhatsApp Chat with ', 'Chat with ', 'WhatsApp ', 'chat ']
        for prefix in prefixes:
            if name_from_file.lower().startswith(prefix.lower()):
                name_from_file = name_from_file[len(prefix):]
                break
        
        return name_from_file or "Unknown Chat"
    
    def get_date_range(self, messages: List[Dict]) -> str:
        """Get date range of chat"""
        if not messages:
            return "Unknown"
        
        first_date = messages[0].get('datetime')
        last_date = messages[-1].get('datetime')
        
        if first_date and last_date:
            return f"{first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}"
        
        return "Unknown"
    
    def get_participants(self, messages: List[Dict]) -> List[str]:
        """Get list of participants"""
        participants = set()
        
        for msg in messages:
            sender = msg.get('sender', '')
            if sender and sender != "System":
                participants.add(sender)
        
        return sorted(list(participants))
    
    def create_searchable_content(self, messages: List[Dict], chat_name: str, participants: List[str]) -> str:
        """Create searchable text content from messages"""
        content_parts = [
            f"WhatsApp Chat: {chat_name}",
            f"Participants: {', '.join(participants)}",
            f"Total Messages: {len(messages)}",
            "\n--- Messages ---\n"
        ]
        
        for msg in messages:
            if msg.get('content') and not msg.get('is_system'):
                content_parts.append(
                    f"{msg['sender']}: {msg['content']}"
                )
        
        return '\n'.join(content_parts)
    
    def generate_chat_statistics(self, messages: List[Dict]) -> Dict[str, Any]:
        """Generate chat statistics"""
        total_messages = len(messages)
        sender_counts = {}
        media_count = 0
        system_count = 0
        
        for msg in messages:
            sender = msg.get('sender', 'Unknown')
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
            
            if msg.get('is_media'):
                media_count += 1
            if msg.get('is_system'):
                system_count += 1
        
        return {
            'total_messages': total_messages,
            'message_counts_by_sender': sender_counts,
            'media_messages': media_count,
            'system_messages': system_count
        }
    
    def process_media_file(self, media_file: Path) -> Optional[Dict[str, Any]]:
        """Process individual media file"""
        try:
            media_type = self.get_media_type(media_file)
            
            return {
                'type': media_type,
                'filename': media_file.name,
                'path': str(media_file),
                'size': media_file.stat().st_size
            }
        
        except Exception as e:
            print(f"Error processing media file {media_file}: {e}")
            return None
