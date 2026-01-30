#!/usr/bin/env python3
"""
Intelligent ZIP Detection for CogniVault
Auto-detects export types: WhatsApp, ChatGPT, Genspark, Generic
VERITAS BUILD
"""

import zipfile
from pathlib import Path
from typing import Dict, Optional

class ZipDetector:
    """Intelligent ZIP file type detector"""
    
    @staticmethod
    def detect_export_type(zip_path: Path) -> Dict[str, any]:
        """
        Detect what type of export this ZIP contains
        Returns: {'type': str, 'confidence': float, 'indicators': list}
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                file_list = zf.namelist()
                file_names_lower = [f.lower() for f in file_list]
                
                # WhatsApp detection
                whatsapp_score = 0
                whatsapp_indicators = []
                
                for fname in file_names_lower:
                    if 'whatsapp chat' in fname and fname.endswith('.txt'):
                        whatsapp_score += 10
                        whatsapp_indicators.append('whatsapp_chat_txt')
                    if fname.endswith('.opus') or fname.endswith('-wa'):
                        whatsapp_score += 2
                        whatsapp_indicators.append('whatsapp_media')
                
                # ChatGPT detection
                chatgpt_score = 0
                chatgpt_indicators = []
                
                if 'conversations.json' in file_names_lower:
                    chatgpt_score += 15
                    chatgpt_indicators.append('conversations_json')
                if 'chat.html' in file_names_lower:
                    chatgpt_score += 5
                    chatgpt_indicators.append('chat_html')
                for fname in file_names_lower:
                    if fname.startswith('message_') and fname.endswith('.json'):
                        chatgpt_score += 2
                        chatgpt_indicators.append('message_json')
                        break
                
                # Genspark detection
                genspark_score = 0
                genspark_indicators = []
                
                if 'user_data.json' in file_names_lower:
                    genspark_score += 10
                    genspark_indicators.append('user_data_json')
                if any('genspark' in f for f in file_names_lower):
                    genspark_score += 5
                    genspark_indicators.append('genspark_naming')
                
                # Determine type
                scores = {
                    'whatsapp': (whatsapp_score, whatsapp_indicators),
                    'chatgpt': (chatgpt_score, chatgpt_indicators),
                    'genspark': (genspark_score, genspark_indicators)
                }
                
                best_type = max(scores, key=lambda k: scores[k][0])
                best_score, best_indicators = scores[best_type]
                
                if best_score >= 5:
                    confidence = min(best_score / 15.0, 1.0)
                    return {
                        'type': best_type,
                        'confidence': confidence,
                        'indicators': best_indicators
                    }
                else:
                    # Generic archive
                    return {
                        'type': 'generic',
                        'confidence': 0.5,
                        'indicators': ['no_specific_patterns']
                    }
        
        except Exception as e:
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'indicators': [f'error: {str(e)}']
            }
