#!/usr/bin/env python3
"""
Mene Portal Integration for CogniVault
Connects CogniVault to Mene LTM and Bonny's memories
VERITAS BUILD - Complete Memory System Integration
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import streamlit as st

class MenePortalIntegration:
    def __init__(self, cognivault_instance):
        """Initialize Mene Portal integration"""
        self.cv = cognivault_instance
        self.mene_config = self.load_mene_config()
        self.bonny_memories = self.load_bonny_memories()
        
    def load_mene_config(self) -> Dict[str, Any]:
        """Load Mene portal configuration"""
        return {
            'local_api_port': 3001,
            'api_endpoints': {
                'query': '/api/query',
                'memories': '/api/memories',
                'context': '/api/context',
                'bonny': '/api/bonny'
            },
            'memory_types': [
                'personal_memories',
                'technical_knowledge', 
                'conversations',
                'bonny_interactions',
                'system_logs'
            ]
        }
    
    def load_bonny_memories(self) -> Dict[str, Any]:
        """Load Bonny's memory data"""
        # This would typically load from your AI Drive
        bonny_data = {
            'personality_traits': [
                'Analytical problem solver',
                'Direct communication style',
                'Technical expertise focus',
                'Solution-oriented thinking'
            ],
            'interaction_patterns': {
                'prefers_technical_details': True,
                'responds_to_direct_questions': True,
                'appreciates_context_awareness': True,
                'values_memory_continuity': True
            },
            'memory_categories': [
                'technical_solutions',
                'project_discussions',
                'problem_resolutions',
                'system_configurations'
            ]
        }
        
        return bonny_data
    
    def test_mene_portal_connection(self) -> Dict[str, Any]:
        """Test connection to Mene Portal"""
        try:
            # Try to connect to local Mene Portal API
            response = requests.get(
                f'http://localhost:{self.mene_config["local_api_port"]}/api/health',
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'service': 'mene_portal',
                    'status': 'connected',
                    'port': self.mene_config["local_api_port"]
                }
            else:
                return {
                    'success': False,
                    'error': f'Mene Portal not responding (HTTP {response.status_code})'
                }
        
        except requests.ConnectionError:
            return {
                'success': False,
                'error': 'Mene Portal not running. Start the portal first.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)}'
            }
    
    def query_with_mene_context(self, query: str, include_bonny: bool = True, 
                               include_ltm: bool = True) -> Dict[str, Any]:
        """Query with Mene Portal and LTM context"""
        
        # Get CogniVault context
        cv_context = ""
        if self.cv:
            search_results = self.cv.vector_store.search(query, top_k=3)
            cv_context = self.format_cv_context(search_results)
        
        # Get Mene Portal context if available
        mene_context = ""
        if include_ltm:
            portal_test = self.test_mene_portal_connection()
            if portal_test['success']:
                mene_context = self.get_mene_context(query)
        
        # Get Bonny context if requested
        bonny_context = ""
        if include_bonny:
            bonny_context = self.get_bonny_context(query)
        
        # Combine all contexts
        combined_context = self.combine_contexts(cv_context, mene_context, bonny_context)
        
        return {
            'success': True,
            'query': query,
            'cognivault_context': cv_context,
            'mene_context': mene_context,
            'bonny_context': bonny_context,
            'combined_context': combined_context,
            'context_sources': {
                'cognivault': bool(cv_context),
                'mene_portal': bool(mene_context),
                'bonny_memories': bool(bonny_context)
            }
        }
    
    def get_mene_context(self, query: str) -> str:
        """Get context from Mene Portal"""
        try:
            response = requests.post(
                f'http://localhost:{self.mene_config["local_api_port"]}/api/context',
                json={'query': query, 'limit': 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                context_parts = []
                context_parts.append("=== MENE PORTAL CONTEXT ===")
                
                for item in data.get('context', []):
                    context_parts.append(f"[{item.get('type', 'MEMORY')}] {item.get('timestamp', '')}")
                    context_parts.append(item.get('content', ''))
                    context_parts.append("---")
                
                return "\n".join(context_parts)
            
            return ""
        
        except Exception as e:
            print(f"Error getting Mene context: {e}")
            return ""
    
    def get_bonny_context(self, query: str) -> str:
        """Get Bonny-specific context based on query"""
        context_parts = []
        context_parts.append("=== BONNY'S MEMORY CONTEXT ===")
        
        # Add personality context
        context_parts.append("Bonny's Characteristics:")
        for trait in self.bonny_memories['personality_traits']:
            context_parts.append(f"  • {trait}")
        
        # Add interaction preferences
        context_parts.append("\nInteraction Patterns:")
        patterns = self.bonny_memories['interaction_patterns']
        for pattern, value in patterns.items():
            context_parts.append(f"  • {pattern.replace('_', ' ').title()}: {value}")
        
        # Add relevant memory categories
        query_lower = query.lower()
        relevant_categories = []
        
        for category in self.bonny_memories['memory_categories']:
            if any(word in query_lower for word in category.split('_')):
                relevant_categories.append(category)
        
        if relevant_categories:
            context_parts.append("\nRelevant Memory Categories:")
            for category in relevant_categories:
                context_parts.append(f"  • {category.replace('_', ' ').title()}")
        
        context_parts.append("---")
        return "\n".join(context_parts)
    
    def format_cv_context(self, search_results: List[Dict]) -> str:
        """Format CogniVault search results as context"""
        if not search_results:
            return ""
        
        context_parts = []
        context_parts.append("=== COGNIVAULT KNOWLEDGE BASE ===")
        
        for result in search_results:
            context_parts.append(f"[{result['type'].upper()}] {result['filename']} (Relevance: {result['score']:.3f})")
            
            if result['type'] == 'document':
                context_parts.append(result['content'][:400] + "...")
            elif result['type'] == 'audio':
                context_parts.append("Transcript: " + result.get('transcript', '')[:400] + "...")
            elif result['type'] == 'image':
                context_parts.append("Image metadata: " + str(result.get('metadata', {}))[:200])
            
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def combine_contexts(self, cv_context: str, mene_context: str, bonny_context: str) -> str:
        """Combine all context sources"""
        contexts = []
        
        if cv_context:
            contexts.append(cv_context)
        
        if mene_context:
            contexts.append(mene_context)
        
        if bonny_context:
            contexts.append(bonny_context)
        
        if not contexts:
            return "No relevant context found."
        
        combined = "\n\n".join(contexts)
        
        # Add summary header
        summary = "=== INTEGRATED CONTEXT SUMMARY ===\n"
        summary += f"Sources: {len(contexts)} context sources\n"
        summary += f"Total length: {len(combined)} characters\n"
        summary += "=" * 50 + "\n\n"
        
        return summary + combined
    
    def sync_with_mene_portal(self) -> Dict[str, Any]:
        """Sync CogniVault data with Mene Portal"""
        portal_test = self.test_mene_portal_connection()
        
        if not portal_test['success']:
            return {
                'success': False,
                'error': 'Mene Portal not available',
                'details': portal_test
            }
        
        try:
            # Get CogniVault statistics
            cv_stats = self.cv.vector_store.get_detailed_statistics()
            
            # Prepare sync data
            sync_data = {
                'timestamp': datetime.now().isoformat(),
                'source': 'cognivault',
                'statistics': cv_stats,
                'capabilities': [
                    'document_search',
                    'audio_transcription',
                    'image_analysis',
                    'whatsapp_processing'
                ]
            }
            
            # Send to Mene Portal
            response = requests.post(
                f'http://localhost:{self.mene_config["local_api_port"]}/api/sync',
                json=sync_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'synced_items': cv_stats.get('total_documents', 0) + cv_stats.get('total_audio', 0) + cv_stats.get('total_images', 0),
                    'sync_timestamp': sync_data['timestamp']
                }
            else:
                return {
                    'success': False,
                    'error': f'Sync failed with HTTP {response.status_code}',
                    'response': response.text
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Sync error: {str(e)}'
            }
    
    def export_for_mene_portal(self) -> Dict[str, Any]:
        """Export CogniVault data in Mene Portal format"""
        try:
            # Get all data from CogniVault
            export_data = self.cv.vector_store.export_data()
            
            # Transform for Mene Portal format
            mene_format = {
                'export_info': {
                    'source': 'cognivault',
                    'timestamp': datetime.now().isoformat(),
                    'format_version': '1.0'
                },
                'memories': [],
                'knowledge_items': [],
                'media_items': []
            }
            
            # Transform documents
            for doc in export_data.get('documents', []):
                mene_format['knowledge_items'].append({
                    'id': f"cv_doc_{doc['id']}",
                    'type': 'document',
                    'title': doc['filename'],
                    'content': doc['content'],
                    'timestamp': doc['timestamp'],
                    'source': 'cognivault_document',
                    'searchable': True
                })
            
            # Transform audio files
            for audio in export_data.get('audio_files', []):
                mene_format['media_items'].append({
                    'id': f"cv_audio_{audio['id']}",
                    'type': 'audio',
                    'title': audio['filename'],
                    'transcript': audio['transcript'],
                    'timestamp': audio['timestamp'],
                    'source': 'cognivault_audio',
                    'searchable': True
                })
            
            # Transform images
            for image in export_data.get('images', []):
                mene_format['media_items'].append({
                    'id': f"cv_image_{image['id']}",
                    'type': 'image',
                    'title': image['filename'],
                    'description': image['description'],
                    'metadata': json.loads(image['metadata']) if image['metadata'] else {},
                    'timestamp': image['timestamp'],
                    'source': 'cognivault_image',
                    'searchable': True
                })
            
            return {
                'success': True,
                'export_data': mene_format,
                'item_counts': {
                    'knowledge_items': len(mene_format['knowledge_items']),
                    'media_items': len(mene_format['media_items']),
                    'total': len(mene_format['knowledge_items']) + len(mene_format['media_items'])
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Export error: {str(e)}'
            }
    
    def create_mene_portal_interface(self):
        """Create Streamlit interface for Mene Portal integration"""
        st.header("🧠 Mene Portal Integration")
        
        # Connection status
        portal_status = self.test_mene_portal_connection()
        
        if portal_status['success']:
            st.success(f"✅ Connected to Mene Portal (Port {portal_status['port']})")
        else:
            st.error(f"❌ Mene Portal not available: {portal_status['error']}")
            st.info("💡 Start Mene Portal to enable integration features")
        
        # Integration features
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Query with Full Context")
            
            query = st.text_input("Ask a question with full context:")
            
            include_bonny = st.checkbox("Include Bonny's Memory", value=True)
            include_ltm = st.checkbox("Include Mene LTM", value=True)
            
            if st.button("Query with Context") and query:
                with st.spinner("Gathering context from all sources..."):
                    result = self.query_with_mene_context(query, include_bonny, include_ltm)
                
                if result['success']:
                    st.subheader("Context Sources:")
                    sources = result['context_sources']
                    
                    if sources['cognivault']:
                        st.write("✅ CogniVault Knowledge Base")
                    if sources['mene_portal']:
                        st.write("✅ Mene Portal LTM")
                    if sources['bonny_memories']:
                        st.write("✅ Bonny's Memories")
                    
                    with st.expander("View Combined Context"):
                        st.text_area("Full Context:", result['combined_context'], height=400)
        
        with col2:
            st.subheader("Portal Management")
            
            if st.button("🔄 Sync with Portal"):
                if portal_status['success']:
                    with st.spinner("Syncing with Mene Portal..."):
                        sync_result = self.sync_with_mene_portal()
                    
                    if sync_result['success']:
                        st.success(f"✅ Synced {sync_result['synced_items']} items")
                    else:
                        st.error(f"❌ Sync failed: {sync_result['error']}")
                else:
                    st.error("Portal not available for sync")
            
            if st.button("📤 Export for Portal"):
                with st.spinner("Preparing export..."):
                    export_result = self.export_for_mene_portal()
                
                if export_result['success']:
                    st.success(f"✅ Export ready: {export_result['item_counts']['total']} items")
                    
                    # Offer download
                    export_json = json.dumps(export_result['export_data'], indent=2)
                    st.download_button(
                        label="📥 Download Export",
                        data=export_json,
                        file_name=f"cognivault_mene_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                else:
                    st.error(f"❌ Export failed: {export_result['error']}")
        
        # Bonny's Memory Interface
        st.subheader("🤖 Bonny's Memory Interface")
        
        with st.expander("Bonny's Characteristics"):
            st.write("**Personality Traits:**")
            for trait in self.bonny_memories['personality_traits']:
                st.write(f"• {trait}")
            
            st.write("**Interaction Patterns:**")
            for pattern, value in self.bonny_memories['interaction_patterns'].items():
                st.write(f"• {pattern.replace('_', ' ').title()}: {value}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations"""
        return {
            'mene_portal': self.test_mene_portal_connection(),
            'bonny_memories': {
                'success': True,
                'loaded_traits': len(self.bonny_memories['personality_traits']),
                'interaction_patterns': len(self.bonny_memories['interaction_patterns'])
            },
            'cognivault': {
                'success': self.cv is not None,
                'statistics': self.cv.vector_store.get_statistics() if self.cv else {}
            }
        }