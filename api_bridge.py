#!/usr/bin/env python3
"""
CogniVault API Bridge - Provider-Agnostic OpenAI-Compatible
VERITAS BUILD
"""

import requests
import os
from typing import Dict, List, Any
import streamlit as st

# Known provider base URLs for convenience
KNOWN_PROVIDERS = {
    "Groq": "https://api.groq.com/openai/v1",
    "OpenRouter": "https://openrouter.ai/api/v1",
    "Novita": "https://api.novita.ai/v3/openai",
    "HuggingFace": "https://api-inference.huggingface.co/v1",
    "Ollama (local)": "http://localhost:11434/v1",
    "Custom": "",
}

# Groq Whisper is separate — most providers don't do audio transcription
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


def get_provider_config() -> Dict[str, str]:
    """Get active provider config from session state."""
    return {
        'base_url': st.session_state.get('provider_base_url', ''),
        'api_key': st.session_state.get('provider_api_key', ''),
        'model': st.session_state.get('provider_model', ''),
    }


def get_groq_key() -> str:
    """Groq key specifically for Whisper transcription."""
    return st.session_state.get('groq_whisper_key', '') or os.getenv('GROQ_API_KEY', '')


class APIBridge:
    def __init__(self, cognivault_instance):
        self.cv = cognivault_instance

    def get_available_services(self) -> List[Dict[str, Any]]:
        """Check what's available."""
        services = []
        cfg = get_provider_config()

        services.append({
            'name': f"LLM ({st.session_state.get('provider_name', 'not set')})",
            'available': bool(cfg['base_url'] and cfg['api_key'] and cfg['model']),
            'error': None if (cfg['base_url'] and cfg['api_key'] and cfg['model'])
                     else 'Set provider, API key and model in sidebar',
        })

        groq_key = get_groq_key()
        services.append({
            'name': 'Groq Whisper (audio)',
            'available': bool(groq_key),
            'error': None if groq_key else 'Add Groq key for audio transcription',
        })

        return services

    def query_with_context(self, query: str, service: str = 'llm',
                           include_search: bool = True, search_limit: int = 5) -> Dict[str, Any]:
        """Query AI with optional RAG context."""
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

        return self.query_llm(full_prompt)

    def query_llm(self, prompt: str) -> Dict[str, Any]:
        """Query any OpenAI-compatible provider."""
        cfg = get_provider_config()

        if not cfg['base_url']:
            return {'success': False, 'error': 'No provider base URL set. Check sidebar.'}
        if not cfg['api_key']:
            return {'success': False, 'error': 'No API key set. Check sidebar.'}
        if not cfg['model']:
            return {'success': False, 'error': 'No model set. Check sidebar.'}

        url = cfg['base_url'].rstrip('/') + '/chat/completions'
        headers = {
            'Authorization': f'Bearer {cfg["api_key"]}',
            'Content-Type': 'application/json',
        }
        # OpenRouter requires these headers
        if 'openrouter' in cfg['base_url']:
            headers['HTTP-Referer'] = 'https://cognivault.app'
            headers['X-Title'] = 'CogniVault'

        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    'model': cfg['model'],
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 2000,
                },
                timeout=60
            )
            if response.status_code == 200:
                return {
                    'success': True,
                    'service': st.session_state.get('provider_name', 'llm'),
                    'response': response.json()['choices'][0]['message']['content'],
                    'context_used': bool(self.cv),
                }
            return {'success': False, 'error': f'HTTP {response.status_code}: {response.text[:200]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def transcribe_audio_groq(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio using Groq Whisper."""
        api_key = get_groq_key()
        if not api_key:
            return {'success': False, 'error': 'No Groq key for Whisper. Add it in sidebar.'}

        try:
            with open(audio_file_path, 'rb') as f:
                response = requests.post(
                    GROQ_WHISPER_URL,
                    headers={'Authorization': f'Bearer {api_key}'},
                    files={'file': f},
                    data={'model': 'whisper-large-v3'},
                    timeout=120
                )
            if response.status_code == 200:
                return {'success': True, 'transcript': response.json().get('text', '')}
            return {'success': False, 'error': f'HTTP {response.status_code}: {response.text[:200]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
