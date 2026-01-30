#!/usr/bin/env python3
"""
ChatGPT/Genspark Log Processor for CogniVault
Handles ChatGPT and Genspark export ZIP files and extracts conversation data
VERITAS BUILD - Universal AI Chat Log Processor
"""

import json
import os
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil
from datetime import datetime

class ChatGPTProcessor:
    def __init__(self, cognivault_instance):
        """Initialize ChatGPT processor with reference to main CogniVault instance"""
        self.cv = cognivault_instance
        
        # Detection patterns for different export types
        self.export_patterns = {
            'chatgpt': ['conversations.json', 'chat.html', 'message_'],
            'genspark': ['user_data.json', 'conversations/', 'genspark_'],
            'generic_json': ['.json']
        }
    
    def process_chat_export(self, zip_path: Path) -> Dict[str, Any]:
        """
        Process ChatGPT or Genspark export ZIP file
        Auto-detects export type and extracts all conversations
        """
        print(f"Processing chat export: {zip_path.name}")
        
        # Create temporary directory for extraction
        temp_dir = Path(tempfile.mkdtemp(prefix="chatgpt_export_"))
        
        try:
            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            print(f"Extracted to: {temp_dir}")
            
            # Detect export type
            export_type = self.detect_export_type(temp_dir)
            print(f"Detected export type: {export_type}")
            
            # Process based on type
            if export_type == 'chatgpt':
                return self.process_chatgpt_export(temp_dir)
            elif export_type == 'genspark':
                return self.process_genspark_export(temp_dir)
            elif export_type == 'generic_json':
                return self.process_generic_json_export(temp_dir)
            else:
                return {
                    'success': False,
                    'error': f'Unknown export type: {export_type}',
                    'conversations_processed': 0
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'conversations_processed': 0
            }
        
        finally:
            # Cleanup
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def detect_export_type(self, directory: Path) -> str:
        """Auto-detect export type from directory contents"""
        all_files = []
        for root, dirs, files in os.walk(directory):
            all_files.extend(files)
        
        file_names = ' '.join(all_files).lower()
        
        # Check for ChatGPT patterns
        if any(pattern in file_names for pattern in self.export_patterns['chatgpt']):
            return 'chatgpt'
        
        # Check for Genspark patterns
        if any(pattern in file_names for pattern in self.export_patterns['genspark']):
            return 'genspark'
        
        # Check for generic JSON
        if any(f.endswith('.json') for f in all_files):
            return 'generic_json'
        
        return 'unknown'
    
    def process_chatgpt_export(self, directory: Path) -> Dict[str, Any]:
        """Process ChatGPT export (conversations.json format)"""
        conversations_file = None
        
        # Find conversations.json
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file == 'conversations.json':
                    conversations_file = Path(root) / file
                    break
            if conversations_file:
                break
        
        if not conversations_file:
            return {
                'success': False,
                'error': 'conversations.json not found in export',
                'conversations_processed': 0
            }
        
        print(f"Found conversations file: {conversations_file}")
        
        try:
            with open(conversations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversations = []
            total_messages = 0
            
            # Process each conversation
            for conv in data:
                conv_data = self.parse_chatgpt_conversation(conv)
                if conv_data:
                    conversations.append(conv_data)
                    total_messages += conv_data['message_count']
                    
                    # Index in vector store
                    self.index_conversation(conv_data)
            
            return {
                'success': True,
                'export_type': 'chatgpt',
                'conversations_processed': len(conversations),
                'total_messages': total_messages,
                'conversations': conversations
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Error parsing ChatGPT export: {str(e)}',
                'conversations_processed': 0
            }
    
    def parse_chatgpt_conversation(self, conv_data: Dict) -> Optional[Dict[str, Any]]:
        """Parse a single ChatGPT conversation"""
        try:
            conv_id = conv_data.get('id', 'unknown')
            title = conv_data.get('title', 'Untitled Conversation')
            create_time = conv_data.get('create_time', 0)
            update_time = conv_data.get('update_time', 0)
            
            # Extract messages
            messages = []
            mapping = conv_data.get('mapping', {})
            
            for node_id, node in mapping.items():
                message = node.get('message')
                if message and message.get('content'):
                    content = message.get('content', {})
                    
                    # Handle different content types
                    text_parts = []
                    if isinstance(content, dict):
                        parts = content.get('parts', [])
                        for part in parts:
                            if isinstance(part, str):
                                text_parts.append(part)
                            elif isinstance(part, dict):
                                text_parts.append(str(part))
                    elif isinstance(content, str):
                        text_parts.append(content)
                    
                    if text_parts:
                        messages.append({
                            'role': message.get('author', {}).get('role', 'unknown'),
                            'content': '\n'.join(text_parts),
                            'timestamp': message.get('create_time', 0)
                        })
            
            if not messages:
                return None
            
            return {
                'conversation_id': conv_id,
                'title': title,
                'create_time': datetime.fromtimestamp(create_time).isoformat() if create_time else None,
                'update_time': datetime.fromtimestamp(update_time).isoformat() if update_time else None,
                'message_count': len(messages),
                'messages': messages,
                'source': 'chatgpt'
            }
        
        except Exception as e:
            print(f"Error parsing conversation: {e}")
            return None
    
    def process_genspark_export(self, directory: Path) -> Dict[str, Any]:
        """Process Genspark export (similar structure to ChatGPT)"""
        # Genspark uses similar JSON structure - reuse ChatGPT parser
        return self.process_chatgpt_export(directory)
    
    def process_generic_json_export(self, directory: Path) -> Dict[str, Any]:
        """Process generic JSON conversation exports"""
        conversations = []
        total_messages = 0
        
        # Find all JSON files
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    json_file = Path(root) / file
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Try to extract conversation-like structure
                        conv_data = self.parse_generic_json(data, json_file.stem)
                        if conv_data:
                            conversations.append(conv_data)
                            total_messages += conv_data['message_count']
                            self.index_conversation(conv_data)
                    
                    except Exception as e:
                        print(f"Error processing {json_file.name}: {e}")
        
        return {
            'success': True,
            'export_type': 'generic_json',
            'conversations_processed': len(conversations),
            'total_messages': total_messages,
            'conversations': conversations
        }
    
    def parse_generic_json(self, data: Any, filename: str) -> Optional[Dict[str, Any]]:
        """Attempt to parse generic JSON into conversation format"""
        try:
            messages = []
            
            # Handle list of messages
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Extract message-like fields
                        content = item.get('content') or item.get('text') or item.get('message') or str(item)
                        messages.append({
                            'role': item.get('role') or item.get('author') or 'user',
                            'content': content,
                            'timestamp': item.get('timestamp') or item.get('time') or 0
                        })
            
            # Handle dict with messages array
            elif isinstance(data, dict):
                messages_arr = data.get('messages') or data.get('conversation') or data.get('chat')
                if messages_arr and isinstance(messages_arr, list):
                    for msg in messages_arr:
                        if isinstance(msg, dict):
                            content = msg.get('content') or msg.get('text') or msg.get('message') or str(msg)
                            messages.append({
                                'role': msg.get('role') or msg.get('author') or 'user',
                                'content': content,
                                'timestamp': msg.get('timestamp') or msg.get('time') or 0
                            })
            
            if not messages:
                return None
            
            return {
                'conversation_id': filename,
                'title': filename,
                'message_count': len(messages),
                'messages': messages,
                'source': 'generic_json'
            }
        
        except Exception as e:
            print(f"Error parsing generic JSON: {e}")
            return None
    
    def index_conversation(self, conv_data: Dict[str, Any]):
        """Index conversation in CogniVault vector store"""
        try:
            # Build full conversation text
            conversation_text = f"Conversation: {conv_data['title']}\n\n"
            
            for msg in conv_data['messages']:
                role = msg['role'].upper()
                content = msg['content']
                conversation_text += f"{role}: {content}\n\n"
            
            # Add to vector store
            self.cv.vector_store.add_document(
                content=conversation_text,
                filename=f"Chat_{conv_data['source']}_{conv_data['conversation_id']}",
                file_path=None,
                metadata={
                    'type': 'chat_log',
                    'source': conv_data['source'],
                    'conversation_id': conv_data['conversation_id'],
                    'title': conv_data['title'],
                    'message_count': conv_data['message_count']
                }
            )
            
            print(f"Indexed conversation: {conv_data['title']} ({conv_data['message_count']} messages)")
        
        except Exception as e:
            print(f"Error indexing conversation: {e}")
