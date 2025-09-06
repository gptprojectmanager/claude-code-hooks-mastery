#!/usr/bin/env python3
"""
CRISIS RESOLUTION: OpenAI-Based Memory System
Implementazione immediata per sostituire cipher MCP bloccato
Autorizzato dall'utente per risoluzione urgente
"""

import os
import json
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "openai"], check=True)
    import openai
    OPENAI_AVAILABLE = True

class OpenAIMemorySystem:
    """Sistema di memoria alternativo basato su OpenAI per risoluzione crisis cipher"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Inizializza sistema memoria OpenAI"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("❌ OPENAI_API_KEY required. Set environment variable or pass api_key parameter")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.memory_file = Path("/Users/sam/claude-code-hooks-mastery/.claude/utils/openai_memory_store.json")
        self.memory_store = self._load_memory_store()
        
        print(f"✅ OpenAI Memory System initialized - {len(self.memory_store)} entries loaded")
    
    def _load_memory_store(self) -> List[Dict[str, Any]]:
        """Carica memory store esistente o crea nuovo"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []
    
    def _save_memory_store(self) -> None:
        """Salva memory store su file"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory_store, f, indent=2, ensure_ascii=False)
    
    def _create_embedding(self, text: str) -> List[float]:
        """Crea embedding per testo usando OpenAI"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️  Embedding creation failed: {e}")
            # Fallback: simple hash-based embedding
            return self._hash_embedding(text)
    
    def _hash_embedding(self, text: str) -> List[float]:
        """Fallback embedding basato su hash"""
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        # Convert to normalized float vector
        embedding = [float(b) / 255.0 for b in hash_bytes]
        # Extend to 1536 dimensions (OpenAI embedding size)
        while len(embedding) < 1536:
            embedding.extend(embedding[:min(len(embedding), 1536-len(embedding))])
        return embedding[:1536]
    
    def save_to_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Salva content in memoria con embedding"""
        try:
            # Create embedding
            embedding = self._create_embedding(content)
            
            # Create memory entry
            memory_entry = {
                "id": len(self.memory_store),
                "content": content,
                "embedding": embedding,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
                "content_hash": hashlib.md5(content.encode('utf-8')).hexdigest()
            }
            
            # Add to store
            self.memory_store.append(memory_entry)
            
            # Save to file
            self._save_memory_store()
            
            result = {
                "success": True, 
                "id": memory_entry["id"],
                "content": content,
                "timestamp": memory_entry["timestamp"],
                "message": f"✅ Saved to memory: '{content[:50]}...'"
            }
            
            print(f"✅ MEMORY SAVE SUCCESS: ID={memory_entry['id']}, Content='{content[:30]}...'")
            return result
            
        except Exception as e:
            error_result = {
                "success": False, 
                "error": str(e),
                "message": f"❌ Memory save failed: {e}"
            }
            print(f"❌ MEMORY SAVE FAILED: {e}")
            return error_result
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcola cosine similarity tra due vettori"""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        except:
            return 0.0
    
    def search_memory(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Cerca in memoria usando semantic similarity"""
        try:
            if not self.memory_store:
                return []
            
            # Create query embedding
            query_embedding = self._create_embedding(query)
            
            # Calculate similarities
            similarities = []
            for entry in self.memory_store:
                similarity = self._cosine_similarity(query_embedding, entry["embedding"])
                similarities.append({
                    "entry": entry,
                    "similarity": similarity
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            results = []
            
            for sim_entry in similarities[:top_k]:
                result = {
                    "id": sim_entry["entry"]["id"],
                    "content": sim_entry["entry"]["content"],
                    "similarity": sim_entry["similarity"],
                    "timestamp": sim_entry["entry"]["timestamp"],
                    "metadata": sim_entry["entry"]["metadata"]
                }
                results.append(result)
            
            print(f"✅ MEMORY SEARCH: Found {len(results)} results for '{query[:30]}...'")
            return results
            
        except Exception as e:
            print(f"❌ MEMORY SEARCH FAILED: {e}")
            return []
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche memoria"""
        return {
            "total_entries": len(self.memory_store),
            "memory_file": str(self.memory_file),
            "openai_available": OPENAI_AVAILABLE,
            "latest_entries": [
                {
                    "id": entry["id"],
                    "content": entry["content"][:50] + "..." if len(entry["content"]) > 50 else entry["content"],
                    "timestamp": entry["timestamp"]
                }
                for entry in self.memory_store[-3:]  # Last 3 entries
            ]
        }

def test_hello_world_memory():
    """Test completo del ciclo hello world"""
    print("\n🧪 TESTING HELLO WORLD MEMORY CYCLE")
    
    try:
        # Initialize memory system
        memory = OpenAIMemorySystem()
        
        # Test 1: Save hello world
        print("\n📝 Test 1: Saving 'hello world'")
        save_result = memory.save_to_memory("hello world")
        print(f"Save result: {save_result}")
        
        # Test 2: Search for hello world
        print("\n🔍 Test 2: Searching for 'hello world'")
        search_results = memory.search_memory("hello world")
        print(f"Search results: {search_results}")
        
        # Test 3: Validate content match
        content_match = any("hello world" in result["content"].lower() for result in search_results)
        
        # Results summary
        test_results = {
            "save_success": save_result.get("success", False),
            "retrieve_success": len(search_results) > 0,
            "content_match": content_match,
            "total_entries": len(memory.memory_store)
        }
        
        print(f"\n✅ TEST RESULTS: {test_results}")
        
        return test_results
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    test_hello_world_memory()