# /Users/astrodingra/Downloads/neura-os/agents/memory_core.py

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict, Any

# --- Configuration Constants (Defined OUTSIDE the class) ---
MEMORY_FILE = "neura_memory.faiss"
METADATA_FILE = "neura_metadata.txt"
MODEL_NAME = 'all-MiniLM-L6-v2'  # A fast, small embedding model
# -----------------------------------------------------------

class MemoryCore:
    """Manages the Vector Database (FAISS) and file knowledge persistence."""
    
    def __init__(self):
        print(f"[MEMORY] Initializing Embedding Model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Load or create FAISS index and metadata
        self.index = self._load_or_create_index()
        self.metadata: Dict[int, Dict[str, Any]] = {} 
        self._load_metadata()

    
    def _load_or_create_index(self):
        """Loads FAISS index from disk or creates a new one."""
        if os.path.exists(MEMORY_FILE):
            print(f"[MEMORY] Loading index from {MEMORY_FILE}...")
            return faiss.read_index(MEMORY_FILE)
        else:
            print("[MEMORY] Creating new FAISS index...")
            return faiss.IndexFlatIP(self.dimension)

    
    def _save_index(self):
        """Saves the current FAISS index to disk."""
        faiss.write_index(self.index, MEMORY_FILE)
        self._save_metadata()

    def _load_metadata(self):
        """Loads path metadata from a text file."""
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f:
                for line in f:
                    try:
                        idx_str, path, summary = line.strip().split('|', 2)
                        self.metadata[int(idx_str)] = {'path': path, 'summary': summary}
                    except ValueError:
                        continue
        print(f"[MEMORY] Loaded {len(self.metadata)} metadata entries.")


    def _save_metadata(self):
        """Saves path metadata to a text file."""
        with open(METADATA_FILE, 'w') as f:
            for idx, data in self.metadata.items():
                f.write(f"{idx}|{os.path.abspath(data['path'])}|{data['summary']}\n")


    def add_document(self, file_path: str, content_summary: str):
        """Encodes text, adds vector to index, and saves metadata."""
        abs_path = os.path.abspath(file_path)
        
        # Check if file is already indexed by checking the metadata paths
        for data in self.metadata.values():
            if data['path'] == abs_path:
                return

        text_to_embed = f"Path: {abs_path}. Content Summary: {content_summary}"
        
        vector = self.model.encode([text_to_embed]).astype('float32')
        
        new_id = self.index.ntotal 
        self.index.add(vector)

        self.metadata[new_id] = {'path': abs_path, 'summary': content_summary}
        
        self._save_index()
        print(f"[MEMORY] Added document for '{file_path}' (Vector ID: {new_id}).")


    def pre_index_files(self):
        """Indexes known files if they are not already in memory."""
        known_files = [
            'meeting_notes_2025.txt', 
            'neura_log.txt'
        ]
        
        print("[INIT] Checking files for pre-indexing...")
        for file_path in known_files:
            if os.path.exists(file_path):
                abs_path = os.path.abspath(file_path)
                
                # Check if file is already indexed
                is_indexed = any(data['path'] == abs_path for data in self.metadata.values())
                
                if not is_indexed:
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read(250)
                        
                        summary = f"Content Snippet: '{content.strip()}...'"
                        
                        self.add_document(abs_path, summary)
                        print(f"[MEMORY] Pre-indexed file: {file_path}")
                    except Exception as e:
                        print(f"[MEMORY] Error reading {file_path}: {e}")
            
    
    def semantic_search(self, query: str, k: int = 3) -> List[dict]:
        """Searches the index for the top 'k' most relevant vectors."""
        
        if self.index.ntotal == 0:
            return [{"warning": "No documents indexed in Neura's long-term memory."}]
            
        print(f"[MEMORY] Searching index for '{query}'...")
        
        query_vector = self.model.encode([query]).astype('float32')
        
        D, I = self.index.search(query_vector, k)
        
        results = []
        for rank, index_id in enumerate(I[0]):
            if index_id >= 0 and index_id in self.metadata:
                results.append({
                    'rank': rank + 1,
                    'path': self.metadata[index_id]['path'],
                    'summary': self.metadata[index_id]['summary'],
                    'score': float(D[0][rank])
                })
                
        return results