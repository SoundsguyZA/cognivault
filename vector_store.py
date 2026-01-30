#!/usr/bin/env python3
"""
Vector Store for CogniVault
Local TF-IDF based search engine with no external dependencies
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

class VectorStore:
    def __init__(self, db_path: Path):
        """Initialize the vector store with SQLite backend"""
        self.db_path = db_path
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.db_file = self.db_path / "cognivault.db"
        self.vectorizer_file = self.db_path / "tfidf_vectorizer.pkl"
        self.vectors_file = self.db_path / "document_vectors.pkl"
        
        self.vectorizer = None
        self.document_vectors = None
        
        self.init_database()
        self.load_vectorizer()
    
    def init_database(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_path TEXT,
                    file_hash TEXT UNIQUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    type TEXT DEFAULT 'document'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audio_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    transcript TEXT NOT NULL,
                    file_path TEXT,
                    file_hash TEXT UNIQUE,
                    duration REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    description TEXT,
                    metadata TEXT,
                    file_path TEXT,
                    file_hash TEXT UNIQUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def load_vectorizer(self):
        """Load existing vectorizer and vectors or create new ones"""
        if self.vectorizer_file.exists() and self.vectors_file.exists():
            try:
                with open(self.vectorizer_file, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                with open(self.vectors_file, 'rb') as f:
                    self.document_vectors = pickle.load(f)
            except Exception as e:
                print(f"Error loading vectorizer: {e}")
                self.vectorizer = None
                self.document_vectors = None
    
    def save_vectorizer(self):
        """Save vectorizer and vectors to disk"""
        if self.vectorizer is not None:
            with open(self.vectorizer_file, 'wb') as f:
                pickle.dump(self.vectorizer, f)
        if self.document_vectors is not None:
            with open(self.vectors_file, 'wb') as f:
                pickle.dump(self.document_vectors, f)
    
    def get_file_hash(self, file_path: Path) -> str:
        """Generate SHA-256 hash of file content"""
        if not file_path.exists():
            return hashlib.sha256(str(file_path).encode()).hexdigest()
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def add_document(self, content: str, filename: str, file_path: Path = None) -> bool:
        """Add a document to the vector store"""
        if not content.strip():
            return False
        
        file_hash = self.get_file_hash(file_path) if file_path else hashlib.sha256(content.encode()).hexdigest()
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO documents 
                    (filename, content, file_path, file_hash, type)
                    VALUES (?, ?, ?, ?, 'document')
                """, (filename, content, str(file_path) if file_path else None, file_hash))
                conn.commit()
            
            # Rebuild vectors after adding document
            self.rebuild_corpus()
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
    def add_audio(self, transcript: str, filename: str, file_path: Path = None, duration: float = None) -> bool:
        """Add an audio file transcript to the vector store"""
        if not transcript.strip():
            return False
        
        file_hash = self.get_file_hash(file_path) if file_path else hashlib.sha256(transcript.encode()).hexdigest()
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO audio_files 
                    (filename, transcript, file_path, file_hash, duration)
                    VALUES (?, ?, ?, ?, ?)
                """, (filename, transcript, str(file_path) if file_path else None, file_hash, duration))
                conn.commit()
            
            # Also add to documents for search
            self.add_document(transcript, f"[AUDIO] {filename}", file_path)
            return True
        except Exception as e:
            print(f"Error adding audio: {e}")
            return False
    
    def add_image(self, metadata: Dict[str, Any], filename: str, file_path: Path = None) -> bool:
        """Add an image with metadata to the vector store"""
        description = self.extract_image_description(metadata)
        file_hash = self.get_file_hash(file_path) if file_path else hashlib.sha256(json.dumps(metadata).encode()).hexdigest()
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO images 
                    (filename, description, metadata, file_path, file_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (filename, description, json.dumps(metadata), str(file_path) if file_path else None, file_hash))
                conn.commit()
            
            # Also add description to documents for search
            if description:
                self.add_document(description, f"[IMAGE] {filename}", file_path)
            return True
        except Exception as e:
            print(f"Error adding image: {e}")
            return False
    
    def extract_image_description(self, metadata: Dict[str, Any]) -> str:
        """Extract searchable description from image metadata"""
        description_parts = []
        
        if 'filename' in metadata:
            description_parts.append(f"Image filename: {metadata['filename']}")
        
        if 'dimensions' in metadata:
            description_parts.append(f"Dimensions: {metadata['dimensions']}")
        
        if 'format' in metadata:
            description_parts.append(f"Format: {metadata['format']}")
        
        if 'size' in metadata:
            description_parts.append(f"File size: {metadata['size']} bytes")
        
        # Add any EXIF data if available
        if 'exif' in metadata:
            for key, value in metadata['exif'].items():
                if key in ['Make', 'Model', 'DateTime', 'Software']:
                    description_parts.append(f"{key}: {value}")
        
        return " | ".join(description_parts)
    
    def rebuild_corpus(self):
        """Rebuild TF-IDF vectors from all documents"""
        print("Rebuilding search corpus...")
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("SELECT content FROM documents")
            documents = [row[0] for row in cursor.fetchall()]
        
        if not documents:
            self.vectorizer = None
            self.document_vectors = None
            return
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        
        # Fit and transform documents
        self.document_vectors = self.vectorizer.fit_transform(documents)
        
        # Save to disk
        self.save_vectorizer()
        print(f"Corpus rebuilt with {len(documents)} documents")
    
    def search(self, query: str, include_documents: bool = True, include_audio: bool = True, 
               include_images: bool = True, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search the vector store using TF-IDF similarity"""
        if not query.strip():
            return []
        
        if self.vectorizer is None or self.document_vectors is None:
            self.rebuild_corpus()
            if self.vectorizer is None:
                return []
        
        # Transform query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Get top documents
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        with sqlite3.connect(self.db_file) as conn:
            for idx in top_indices:
                if similarities[idx] < 0.01:  # Minimum similarity threshold
                    break
                
                cursor = conn.execute("""
                    SELECT filename, content, file_path, timestamp, type
                    FROM documents 
                    LIMIT 1 OFFSET ?
                """, (int(idx),))
                
                row = cursor.fetchone()
                if row:
                    result = {
                        'filename': row[0],
                        'content': row[1],
                        'file_path': row[2],
                        'timestamp': row[3],
                        'type': row[4],
                        'score': float(similarities[idx])
                    }
                    
                    # Add additional data for audio files
                    if result['filename'].startswith('[AUDIO]'):
                        result['type'] = 'audio'
                        audio_data = self.get_audio_by_filename(result['filename'].replace('[AUDIO] ', ''))
                        if audio_data:
                            result['transcript'] = audio_data['transcript']
                            result['duration'] = audio_data.get('duration')
                    
                    # Add additional data for images
                    elif result['filename'].startswith('[IMAGE]'):
                        result['type'] = 'image'
                        image_data = self.get_image_by_filename(result['filename'].replace('[IMAGE] ', ''))
                        if image_data:
                            result['metadata'] = json.loads(image_data['metadata'])
                    
                    results.append(result)
        
        # Filter by type preferences
        filtered_results = []
        for result in results:
            if (result['type'] == 'document' and include_documents) or \
               (result['type'] == 'audio' and include_audio) or \
               (result['type'] == 'image' and include_images):
                filtered_results.append(result)
        
        return filtered_results[:top_k]
    
    def get_audio_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get audio file data by filename"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("""
                SELECT filename, transcript, file_path, duration, timestamp
                FROM audio_files 
                WHERE filename = ?
            """, (filename,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'filename': row[0],
                    'transcript': row[1],
                    'file_path': row[2],
                    'duration': row[3],
                    'timestamp': row[4]
                }
        return None
    
    def get_image_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get image data by filename"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("""
                SELECT filename, description, metadata, file_path, timestamp
                FROM images 
                WHERE filename = ?
            """, (filename,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'filename': row[0],
                    'description': row[1],
                    'metadata': row[2],
                    'file_path': row[3],
                    'timestamp': row[4]
                }
        return None
    
    def get_audio_files(self) -> List[Dict[str, Any]]:
        """Get all audio files"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("""
                SELECT filename, transcript, file_path, duration, timestamp
                FROM audio_files 
                ORDER BY timestamp DESC
            """)
            
            return [{
                'filename': row[0],
                'transcript': row[1],
                'file_path': row[2],
                'duration': row[3],
                'timestamp': row[4]
            } for row in cursor.fetchall()]
    
    def get_images(self) -> List[Dict[str, Any]]:
        """Get all images"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("""
                SELECT filename, description, metadata, file_path, timestamp
                FROM images 
                ORDER BY timestamp DESC
            """)
            
            return [{
                'filename': row[0],
                'description': row[1],
                'metadata': json.loads(row[2]) if row[2] else {},
                'file_path': row[2],
                'timestamp': row[4]
            } for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, int]:
        """Get basic system statistics"""
        with sqlite3.connect(self.db_file) as conn:
            doc_count = conn.execute("SELECT COUNT(*) FROM documents WHERE type = 'document'").fetchone()[0]
            audio_count = conn.execute("SELECT COUNT(*) FROM audio_files").fetchone()[0]
            image_count = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]
            
            return {
                'documents': doc_count,
                'audio_files': audio_count,
                'images': image_count
            }
    
    def get_detailed_statistics(self) -> Dict[str, Any]:
        """Get detailed system statistics"""
        basic_stats = self.get_statistics()
        
        # Calculate storage usage
        total_size = 0
        if self.db_file.exists():
            total_size += self.db_file.stat().st_size
        if self.vectorizer_file.exists():
            total_size += self.vectorizer_file.stat().st_size
        if self.vectors_file.exists():
            total_size += self.vectors_file.stat().st_size
        
        # File type distribution
        file_types = {}
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("SELECT filename FROM documents")
            for row in cursor.fetchall():
                ext = Path(row[0]).suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
        
        # Recent activity
        recent_activity = []
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("""
                SELECT filename, timestamp, 'document' as type FROM documents
                UNION ALL
                SELECT filename, timestamp, 'audio' as type FROM audio_files
                UNION ALL
                SELECT filename, timestamp, 'image' as type FROM images
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            recent_activity = [{
                'filename': row[0],
                'timestamp': row[1],
                'type': row[2]
            } for row in cursor.fetchall()]
        
        return {
            'total_documents': basic_stats['documents'],
            'total_audio': basic_stats['audio_files'],
            'total_images': basic_stats['images'],
            'storage_used': total_size,
            'file_types': file_types,
            'recent_activity': recent_activity
        }
    
    def export_data(self) -> Dict[str, Any]:
        """Export all data for backup"""
        with sqlite3.connect(self.db_file) as conn:
            documents = []
            cursor = conn.execute("SELECT * FROM documents")
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                documents.append(dict(zip(columns, row)))
            
            audio_files = []
            cursor = conn.execute("SELECT * FROM audio_files")
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                audio_files.append(dict(zip(columns, row)))
            
            images = []
            cursor = conn.execute("SELECT * FROM images")
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                images.append(dict(zip(columns, row)))
        
        return {
            'export_timestamp': datetime.now().isoformat(),
            'documents': documents,
            'audio_files': audio_files,
            'images': images,
            'statistics': self.get_detailed_statistics()
        }