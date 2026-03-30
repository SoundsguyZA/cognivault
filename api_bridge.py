#!/usr/bin/env python3
"""
CogniVault API Bridge - Groq Cloud + Local Gemma
VERITAS BUILD
"""

import requests
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import streamlit as st
from datetime import datetime


def get_groq_key() -> str:
    """Get Groq API key from session state, falling back to env var."""
    return st.session_state.get('groq_api_key', '') or os.getenv('GROQ_API_KEY', '')


class APIBridge:
    def __init__(self, cognivault_instance):
        self.cv = cognivault_instance

    def get_available_services(self) -> List[Dict[str, Any]]:
        """Get list of available AI services."""
        services = []

        groq_key = get_groq_key()
        services.append({
            'name': 'groq',
            'available': bool(groq_key),
            'error': None if groq_key else 'No Groq API key set',
        })

        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=3)
            models = response.json().get('models', []) if response.status_code == 200 else []
            gemma_available = any('gemma' in m.get('name', '').lower() for m in models)
            services.append({
                'name': 'local_gemma',
                'available': gemma_available,
                'error': None if gemma_available else 'Ollama not running or no Gemma model',
            })
        except Exception:
            services.append({'name': 'local_gemma', 'available': False, 'error': 'Ollama not running'})

        return services

    def query_with_context(self, query: str, service: str = 'groq',
                           include_search: bool = True, search_limit: int = 5) -> Dict[str, Any]:
        """Query AI service with CogniVault context."""
        context = ""
        if include_search and self.cv:
            search_results = self.cv.vector_store.search(query, top_k=search_limit)
            parts = []
            for r in search_results:
                parts.append(f"[{r['type'].upper()}] {r['filename']}")
                if r['type'] == 'document':
                    parts.append(r['content'][:500] + "...")
                elif r['type'] == 'audio':
                    parts.append("Transcript: " + r.get('transcript', '')[:500] + "...")
                elif r['type'] == 'image':
                    parts.append("Image metadata: " + str(r.get('metadata', {})))
                parts.append("---")
            context = "\n".join(parts)

        if context:
            full_prompt = f"""Based on the following context from the user's knowledge base, answer the question.

CONTEXT:
{context}

QUESTION: {query}

Answer based on the context. If it's not relevant, say so."""
        else:
            full_prompt = query

        if service == 'groq':
            return self.query_groq(full_prompt)
        elif service == 'local_gemma':
            return self.query_local_gemma(full_prompt)
        else:
            return {'success': False, 'error': f'Unknown service: {service}'}

    def query_groq(self, prompt: str, model: str = 'llama-3.3-70b-versatile') -> Dict[str, Any]:
        """Query Groq Cloud LLM."""
        api_key = get_groq_key()
        if not api_key:
            return {'success': False, 'error': 'No Groq API key. Add it in the sidebar.'}

        try:
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 2000},
                timeout=60
            )
            if response.status_code == 200:
                return {
                    'success': True,
                    'service': 'groq',
                    'response': response.json()['choices'][0]['message']['content'],
                    'context_used': bool(self.cv)
                }
            return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def transcribe_audio_groq(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio using Groq Whisper."""
        api_key = get_groq_key()
        if not api_key:
            return {'success': False, 'error': 'No Groq API key. Add it in the sidebar.'}

        try:
            with open(audio_file_path, 'rb') as f:
                response = requests.post(
                    'https://api.groq.com/openai/v1/audio/transcriptions',
                    headers={'Authorization': f'Bearer {api_key}'},
                    files={'file': f},
                    data={'model': 'whisper-large-v3'},
                    timeout=120
                )
            if response.status_code == 200:
                return {'success': True, 'transcript': response.json().get('text', '')}
            return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def query_local_gemma(self, prompt: str) -> Dict[str, Any]:
        """Query local Gemma via Ollama."""
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={'model': 'gemma2:2b', 'prompt': prompt, 'stream': False},
                timeout=60
            )
            if response.status_code == 200:
                return {
                    'success': True,
                    'service': 'local_gemma',
                    'response': response.json().get('response', ''),
                    'context_used': bool(self.cv)
                }
            return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
