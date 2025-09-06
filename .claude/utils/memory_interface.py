#!/usr/bin/env python3
"""
INTERFACCIA SEMPLICE MEMORIA - Sostituzione cipher MCP
Utilizzo immediato per salvare/recuperare memoria
"""

import sys
import json
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from openai_memory_system import OpenAIMemorySystem

def save_memory(content: str, metadata: dict = None):
    """Salva contenuto in memoria"""
    try:
        memory = OpenAIMemorySystem()
        result = memory.save_to_memory(content, metadata)
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        error = {"success": False, "error": str(e)}
        print(json.dumps(error, indent=2))
        return error

def search_memory(query: str, top_k: int = 5):
    """Cerca in memoria"""
    try:
        memory = OpenAIMemorySystem()
        results = memory.search_memory(query, top_k)
        print(json.dumps(results, indent=2))
        return results
    except Exception as e:
        error = {"error": str(e)}
        print(json.dumps(error, indent=2))
        return error

def memory_stats():
    """Statistiche memoria"""
    try:
        memory = OpenAIMemorySystem()
        stats = memory.get_memory_stats()
        print(json.dumps(stats, indent=2))
        return stats
    except Exception as e:
        error = {"error": str(e)}
        print(json.dumps(error, indent=2))
        return error

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python memory_interface.py save '<content>' [metadata_json]")
        print("  python memory_interface.py search '<query>' [top_k]")
        print("  python memory_interface.py stats")
        print("")
        print("Examples:")
        print("  python memory_interface.py save 'hello world'")
        print("  python memory_interface.py search 'hello'")
        print("  python memory_interface.py stats")
        return
    
    command = sys.argv[1]
    
    if command == "save":
        if len(sys.argv) < 3:
            print("Error: Content required for save command")
            return
        content = sys.argv[2]
        metadata = None
        if len(sys.argv) > 3:
            try:
                metadata = json.loads(sys.argv[3])
            except json.JSONDecodeError:
                print("Warning: Invalid metadata JSON, ignoring")
        save_memory(content, metadata)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("Error: Query required for search command")
            return
        query = sys.argv[2]
        top_k = 5
        if len(sys.argv) > 3:
            try:
                top_k = int(sys.argv[3])
            except ValueError:
                print("Warning: Invalid top_k, using default 5")
        search_memory(query, top_k)
    
    elif command == "stats":
        memory_stats()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()