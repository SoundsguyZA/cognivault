#!/usr/bin/env python3
"""
CogniVault API Bridge - Connect to External AI Services
VERITAS BUILD - Grok, Claude, Gemma Integration
"""

import requests
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import streamlit as st
from datetime import datetime

class APIBridge:
    def __init__(self, cognivault_instance):
        """Initialize API bridge with CogniVault instance"""
        self.cv = cognivault_instance
        self.api_configs = self.load_api_configs()
        
    def load_api_configs(self) -> Dict[str, Dict]:
        """Load API configurations"""
        return {
            'grok': {
                'base_url': 'https://api.x.ai/v1',
                'model': 'grok-beta',
                'api_key_env': 'GROK_API_KEY',
                'headers_template': {
                    'Authorization': 'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
            },
            'openai': {
                'base_url': 'https://api.openai.com/v1',
                'model': 'gpt-4',
                'api_key_env': 'OPENAI_API_KEY',
                'headers_template': {
                    'Authorization': 'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
            },
            'anthropic': {
                'base_url': 'https://api.anthropic.com/v1',
                'model': 'claude-3-5-sonnet-20241022',
                'api_key_env': 'ANTHROPIC_API_KEY',
                'headers_template': {
                    'x-api-key': '{api_key}',
                    'Content-Type': 'application/json',
                    'anthropic-version': '2023-06-01'
                }
            },
            'local_gemma': {
                'base_url': 'http://localhost:11434/api',
                'model': 'gemma2:2b',
                'api_key_env': None,
                'headers_template': {
                    'Content-Type': 'application/json'
                }
            }
        }
    
    def test_api_connection(self, service: str) -> Dict[str, Any]:
        """Test connection to specific API service"""
        if service not in self.api_configs:
            return {'success': False, 'error': f'Unknown service: {service}'}
        
        config = self.api_configs[service]
        
        # Check API key if required
        if config['api_key_env']:
            api_key = os.getenv(config['api_key_env'])
            if not api_key:
                return {
                    'success': False, 
                    'error': f'API key not found in environment: {config["api_key_env"]}'
                }
        
        try:
            if service == 'grok':
                return self.test_grok_connection()
            elif service == 'anthropic':
                return self.test_anthropic_connection()
            elif service == 'openai':
                return self.test_openai_connection()
            elif service == 'local_gemma':
                return self.test_local_gemma_connection()
            else:
                return {'success': False, 'error': 'Service test not implemented'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_grok_connection(self) -> Dict[str, Any]:
        """Test Grok API connection"""
        api_key = os.getenv('GROK_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'GROK_API_KEY not set'}
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messages': [{'role': 'user', 'content': 'Test connection'}],
            'model': 'grok-beta',
            'max_tokens': 10
        }
        
        try:
            response = requests.post(
                'https://api.x.ai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True, 'service': 'grok', 'model': 'grok-beta'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_local_gemma_connection(self) -> Dict[str, Any]:
        """Test local Ollama/Gemma connection"""
        try:
            # Test if Ollama is running
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                gemma_models = [m for m in models if 'gemma' in m.get('name', '').lower()]
                
                if gemma_models:
                    return {
                        'success': True, 
                        'service': 'local_gemma',
                        'available_models': [m['name'] for m in gemma_models]
                    }
                else:
                    return {'success': False, 'error': 'No Gemma models found. Run: ollama pull gemma2:2b'}
            else:
                return {'success': False, 'error': 'Ollama not responding'}
        
        except requests.ConnectionError:
            return {'success': False, 'error': 'Ollama not running. Install from https://ollama.ai'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_anthropic_connection(self) -> Dict[str, Any]:
        """Test Anthropic Claude connection"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'ANTHROPIC_API_KEY not set'}
        
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 10,
            'messages': [{'role': 'user', 'content': 'Test'}]
        }
        
        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True, 'service': 'anthropic', 'model': 'claude-3-5-sonnet-20241022'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_openai_connection(self) -> Dict[str, Any]:
        """Test OpenAI connection"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'OPENAI_API_KEY not set'}
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4',
            'messages': [{'role': 'user', 'content': 'Test'}],
            'max_tokens': 10
        }
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True, 'service': 'openai', 'model': 'gpt-4'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def query_with_context(self, query: str, service: str = 'local_gemma', 
                          include_search: bool = True, search_limit: int = 5) -> Dict[str, Any]:
        """Query AI service with CogniVault context"""
        
        # Get relevant context from CogniVault
        context = ""
        if include_search and self.cv:
            search_results = self.cv.vector_store.search(query, top_k=search_limit)
            
            context_parts = []
            for result in search_results:
                context_parts.append(f"[{result['type'].upper()}] {result['filename']}")
                if result['type'] == 'document':
                    context_parts.append(result['content'][:500] + "...")
                elif result['type'] == 'audio':
                    context_parts.append("Transcript: " + result.get('transcript', '')[:500] + "...")
                elif result['type'] == 'image':
                    context_parts.append("Image metadata: " + str(result.get('metadata', {})))
                context_parts.append("---")
            
            context = "\n".join(context_parts)
        
        # Build prompt with context
        if context:
            full_prompt = f"""Based on the following context from the user's knowledge base, please answer the question.

CONTEXT:
{context}

QUESTION: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain relevant information, say so clearly."""
        else:
            full_prompt = query
        
        # Query the selected service
        if service == 'local_gemma':
            return self.query_local_gemma(full_prompt)
        elif service == 'grok':
            return self.query_grok(full_prompt)
        elif service == 'anthropic':
            return self.query_anthropic(full_prompt)
        elif service == 'openai':
            return self.query_openai(full_prompt)
        else:
            return {'success': False, 'error': f'Unknown service: {service}'}
    
    def query_local_gemma(self, prompt: str) -> Dict[str, Any]:
        """Query local Gemma via Ollama"""
        try:
            payload = {
                'model': 'gemma2:2b',
                'prompt': prompt,
                'stream': False
            }
            
            response = requests.post(
                'http://localhost:11434/api/generate',
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'service': 'local_gemma',
                    'response': result.get('response', ''),
                    'context_used': True if self.cv else False
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def query_grok(self, prompt: str) -> Dict[str, Any]:
        """Query Grok API"""
        api_key = os.getenv('GROK_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'GROK_API_KEY not set'}
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messages': [{'role': 'user', 'content': prompt}],
            'model': 'grok-beta',
            'max_tokens': 2000
        }
        
        try:
            response = requests.post(
                'https://api.x.ai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'service': 'grok',
                    'response': result['choices'][0]['message']['content'],
                    'context_used': True if self.cv else False
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def query_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Query Anthropic Claude"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'ANTHROPIC_API_KEY not set'}
        
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 2000,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'service': 'anthropic',
                    'response': result['content'][0]['text'],
                    'context_used': True if self.cv else False
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        
        except Exception e:
            return {'success': False, 'error': str(e)}
    
    def query_openai(self, prompt: str) -> Dict[str, Any]:
        """Query OpenAI GPT"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'OPENAI_API_KEY not set'}
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 2000
        }
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'service': 'openai',
                    'response': result['choices'][0]['message']['content'],
                    'context_used': True if self.cv else False
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_available_services(self) -> List[Dict[str, Any]]:
        """Get list of available AI services"""
        services = []
        
        for service_name in self.api_configs.keys():
            test_result = self.test_api_connection(service_name)
            services.append({
                'name': service_name,
                'available': test_result['success'],
                'error': test_result.get('error', None),
                'config': self.api_configs[service_name]
            })
        
        return services