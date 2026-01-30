"""
CogniVault Memory Bridge
Connects local TF-IDF search with Aluna-Memory (Mem0) semantic storage

Author: Rob "The Sounds Guy" Barenbrug
Built by: VERITAS - 150% Production Standard
Date: 2026-01-30
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib


class MemoryBridge:
    """Bridge between CogniVault and Aluna-Memory"""
    
    def __init__(self, aluna_url: Optional[str] = None):
        """
        Initialize Memory Bridge
        
        Args:
            aluna_url: URL of Aluna-Memory service
                      Default: http://aluna-memory:8000 (Docker)
                      or http://localhost:50003 (local dev)
        """
        self.aluna_url = aluna_url or os.getenv(
            'ALUNA_MEMORY_URL', 
            'http://localhost:50003'
        )
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CogniVault-Memory-Bridge/1.0'
        })
        self._connected = False
        self._check_connection()
    
    def _check_connection(self):
        """Internal connection check on init"""
        try:
            self._connected = self.health_check()
        except:
            self._connected = False
    
    def is_connected(self) -> bool:
        """Check if bridge is connected to Aluna-Memory"""
        return self._connected
    
    def health_check(self) -> bool:
        """Check if Aluna-Memory is accessible"""
        try:
            response = self.session.get(
                f"{self.aluna_url}/health",
                timeout=5
            )
            self._connected = response.status_code == 200
            return self._connected
        except Exception as e:
            print(f"Aluna-Memory health check failed: {e}")
            self._connected = False
            return False
    
    def add_document_memory(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_type: str,
        user_id: str = "default_user"
    ) -> Optional[str]:
        """
        Add document to long-term memory
        
        Args:
            content: Document text content
            metadata: Document metadata (author, date, source, etc.)
            doc_type: Type of document (whatsapp, chatgpt, audio, pdf, etc.)
            user_id: User identifier for memory isolation
            
        Returns:
            Memory ID if successful, None otherwise
        """
        if not self._connected:
            print("⚠ Memory Bridge not connected - skipping")
            return None
        
        try:
            # Generate unique document ID
            doc_id = hashlib.sha256(
                f"{content[:100]}{metadata.get('timestamp', '')}".encode()
            ).hexdigest()[:16]
            
            # Format for Mem0
            memory_data = {
                "messages": [
                    {
                        "role": "system",
                        "content": f"Storing {doc_type} document"
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "user_id": user_id,
                "metadata": {
                    **metadata,
                    "doc_type": doc_type,
                    "doc_id": doc_id,
                    "source": "cognivault",
                    "indexed_at": datetime.utcnow().isoformat()
                }
            }
            
            # Send to Aluna-Memory
            response = self.session.post(
                f"{self.aluna_url}/v1/memories",
                json=memory_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                memory_id = result.get('id') or result.get('memory_id')
                print(f"✓ Added to memory: {memory_id}")
                return memory_id
            else:
                print(f"✗ Failed to add memory: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Error adding document to memory: {e}")
            return None
    
    def search_memories(
        self,
        query: str,
        user_id: str = "default_user",
        limit: int = 10,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories semantically
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum results
            doc_type: Filter by document type
            
        Returns:
            List of matching memories with metadata
        """
        if not self._connected:
            print("⚠ Memory Bridge not connected")
            return []
        
        try:
            # Build search request
            search_data = {
                "query": query,
                "user_id": user_id,
                "limit": limit
            }
            
            if doc_type:
                search_data["filters"] = {
                    "doc_type": doc_type
                }
            
            # Query Aluna-Memory
            response = self.session.post(
                f"{self.aluna_url}/v1/memories/search",
                json=search_data,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                memories = results.get('memories', [])
                print(f"✓ Found {len(memories)} memories")
                return memories
            else:
                print(f"✗ Search failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Error searching memories: {e}")
            return []
    
    def get_context(
        self,
        query: str,
        user_id: str = "default_user",
        max_tokens: int = 2000
    ) -> str:
        """
        Get relevant context for a query
        
        Args:
            query: Query to get context for
            user_id: User identifier
            max_tokens: Maximum context length
            
        Returns:
            Formatted context string
        """
        if not self._connected:
            return ""
        
        try:
            memories = self.search_memories(query, user_id, limit=5)
            
            if not memories:
                return ""
            
            # Format context
            context_parts = []
            total_length = 0
            
            for memory in memories:
                content = memory.get('content', '')
                metadata = memory.get('metadata', {})
                
                # Format memory entry
                entry = f"[{metadata.get('doc_type', 'unknown')}] {content}"
                
                if total_length + len(entry) > max_tokens:
                    break
                
                context_parts.append(entry)
                total_length += len(entry)
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"✗ Error getting context: {e}")
            return ""
    
    def add_conversation_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str = "default_user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add conversation to memory
        
        Args:
            messages: List of {role, content} messages
            user_id: User identifier
            metadata: Additional metadata
            
        Returns:
            Memory ID if successful
        """
        if not self._connected:
            print("⚠ Memory Bridge not connected")
            return None
        
        try:
            memory_data = {
                "messages": messages,
                "user_id": user_id,
                "metadata": {
                    **(metadata or {}),
                    "doc_type": "conversation",
                    "source": "cognivault",
                    "indexed_at": datetime.utcnow().isoformat()
                }
            }
            
            response = self.session.post(
                f"{self.aluna_url}/v1/memories",
                json=memory_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                memory_id = result.get('id') or result.get('memory_id')
                print(f"✓ Conversation stored: {memory_id}")
                return memory_id
            else:
                print(f"✗ Failed to store conversation: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Error storing conversation: {e}")
            return None
    
    def get_all_memories(
        self,
        user_id: str = "default_user",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all memories for a user"""
        if not self._connected:
            return []
        
        try:
            response = self.session.get(
                f"{self.aluna_url}/v1/memories",
                params={"user_id": user_id, "limit": limit},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('memories', [])
            else:
                return []
                
        except Exception as e:
            print(f"✗ Error getting memories: {e}")
            return []
    
    def delete_memory(
        self,
        memory_id: str
    ) -> bool:
        """Delete a specific memory"""
        if not self._connected:
            return False
        
        try:
            response = self.session.delete(
                f"{self.aluna_url}/v1/memories/{memory_id}",
                timeout=10
            )
            return response.status_code == 200
            
        except Exception as e:
            print(f"✗ Error deleting memory: {e}")
            return False


# Singleton instance
_bridge_instance: Optional[MemoryBridge] = None


def get_memory_bridge() -> MemoryBridge:
    """Get or create singleton Memory Bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = MemoryBridge()
    return _bridge_instance
