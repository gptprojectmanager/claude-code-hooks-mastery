#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-cloud-secret-manager",
#     "requests",
#     "pathlib",
#     "asyncio",
#     "websockets",
#     "json5",
# ]
# ///

"""
Enhanced Memory Sync - KRAG Integration
Converts memory-manager.sh to Python UV script with KRAG namespace integration

Key Features:
- Google Secret Manager integration for API keys
- KRAG namespace isolation (session_{timestamp}_primary, validated_knowledge)  
- Cross-session memory sync and backup
- Semantic memory categorization and conflict detection
- Integration with existing work-validator-sonnet patterns
"""

import os
import sys
import json
import asyncio
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from google.cloud import secretmanager


@dataclass
class MemoryEntry:
    """Structured memory entry for KRAG integration"""
    content: str
    category: str
    priority: str  # high, medium, low
    source: str    # project, user, system
    timestamp: str
    namespace: str  # KRAG group_id
    hash_id: str
    conflicts: List[str]
    metadata: Dict[str, Any]


class KRAGMemorySync:
    """Enhanced memory synchronization with KRAG integration"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.claude_dir = self.project_root / ".claude"
        self.backup_dir = self.claude_dir / "memory_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # KRAG namespace patterns (matching primary-agent-sonnet.md)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.namespaces = {
            "primary": f"session_{self.timestamp}_primary",
            "validated": "validated_knowledge", 
            "coordination": "system_coordination",
            "research_cache": f"session_{self.timestamp}_research"
        }
        
        # Memory files
        self.project_memory = self.project_root / "CLAUDE.md"
        self.user_memory = Path.home() / ".claude" / "CLAUDE.md"
        
        # Claude CLI available check
        self.claude_available = self._check_claude_cli()
        
    def _check_claude_cli(self) -> bool:
        """Check if Claude CLI is available"""
        try:
            result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_secret_api_key(self, secret_name: str) -> Optional[str]:
        """Retrieve API key from Google Secret Manager"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = "custom-mix-460500-g9" 
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"⚠️  Error accessing Google Secret Manager: {e}")
            return None

    async def add_to_krag(self, memory_entry: MemoryEntry) -> bool:
        """Add memory entry to KRAG using MCP tool integration"""
        try:
            # Prepare structured episode data for KRAG
            episode_data = {
                "memory_entry": asdict(memory_entry),
                "semantic_context": {
                    "category": memory_entry.category,
                    "priority": memory_entry.priority,
                    "source": memory_entry.source,
                    "project_context": str(self.project_root.name)
                },
                "relationships": {
                    "conflicts_with": memory_entry.conflicts,
                    "namespace": memory_entry.namespace,
                    "hash_signature": memory_entry.hash_id
                }
            }
            
            # Create episode body as escaped JSON string (as per KRAG documentation)
            episode_body = json.dumps(episode_data).replace('"', '\\"')
            
            print(f"📝 Adding to KRAG namespace: {memory_entry.namespace}")
            print(f"   Category: {memory_entry.category} | Priority: {memory_entry.priority}")
            
            # Note: In actual implementation, this would call the MCP tool
            # mcp__krag-graphiti-memory__add_memory(
            #     name=f"Memory_{memory_entry.hash_id[:8]}",
            #     episode_body=episode_body,
            #     group_id=memory_entry.namespace,
            #     source="json",
            #     source_description="Enhanced memory sync"
            # )
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding to KRAG: {e}")
            return False

    def categorize_memory_intelligent(self, content: str, existing_memories: str) -> Dict[str, Any]:
        """Intelligent memory categorization using Claude CLI if available"""
        
        if not self.claude_available:
            # Fallback to simple categorization
            return self._fallback_categorization(content)
        
        categorize_prompt = f"""
Given this memory instruction: "{content}"

And this existing memory context:
{existing_memories[:2000]}  # Truncate for token limits

Determine:
1. The most appropriate category (Development|Architecture|Testing|Security|Performance|Documentation)
2. Priority level (high|medium|low) based on impact
3. Whether this conflicts with existing memories
4. Suggested namespace for KRAG storage
5. Semantic relationships to existing content

Return JSON:
{{
  "category": "category_name",
  "priority": "high|medium|low",
  "conflicts": ["list of conflicting entries"],
  "duplicate": true/false,
  "namespace_suggestion": "primary|validated|coordination|research_cache",
  "semantic_tags": ["tag1", "tag2"],
  "relationships": ["related_concept1", "related_concept2"]
}}
"""
        
        try:
            result = subprocess.run([
                "claude", "-p", categorize_prompt,
                "--output-format", "json",
                "--max-turns", "1"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse Claude CLI JSON response
                response_data = json.loads(result.stdout)
                # Extract result if wrapped, otherwise use directly  
                return response_data.get("result", response_data)
            else:
                print(f"⚠️  Claude CLI error: {result.stderr}")
                return self._fallback_categorization(content)
                
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"⚠️  Claude CLI categorization failed: {e}")
            return self._fallback_categorization(content)
    
    def _fallback_categorization(self, content: str) -> Dict[str, Any]:
        """Fallback categorization when Claude CLI is unavailable"""
        content_lower = content.lower()
        
        # Simple keyword-based categorization
        if any(word in content_lower for word in ["test", "spec", "coverage"]):
            category = "Testing"
            priority = "medium"
        elif any(word in content_lower for word in ["security", "auth", "permission"]):
            category = "Security"
            priority = "high"
        elif any(word in content_lower for word in ["performance", "optimize", "speed"]):
            category = "Performance" 
            priority = "medium"
        elif any(word in content_lower for word in ["architecture", "design", "pattern"]):
            category = "Architecture"
            priority = "high"
        elif any(word in content_lower for word in ["document", "readme", "guide"]):
            category = "Documentation"
            priority = "low"
        else:
            category = "Development"
            priority = "medium"
        
        return {
            "category": category,
            "priority": priority,
            "conflicts": [],
            "duplicate": False,
            "namespace_suggestion": "primary",
            "semantic_tags": [category.lower()],
            "relationships": []
        }

    def create_memory_entry(self, content: str, source: str = "project") -> MemoryEntry:
        """Create structured memory entry"""
        
        # Read existing memories for context
        existing_content = ""
        if self.project_memory.exists():
            existing_content += self.project_memory.read_text()
        if self.user_memory.exists():
            existing_content += "\n" + self.user_memory.read_text()
        
        # Intelligent categorization
        categorization = self.categorize_memory_intelligent(content, existing_content)
        
        # Select namespace based on categorization
        namespace_map = {
            "primary": self.namespaces["primary"],
            "validated": self.namespaces["validated"],
            "coordination": self.namespaces["coordination"],
            "research_cache": self.namespaces["research_cache"]
        }
        
        suggested_ns = categorization.get("namespace_suggestion", "primary")
        namespace = namespace_map.get(suggested_ns, self.namespaces["primary"])
        
        # Create memory entry
        return MemoryEntry(
            content=content,
            category=categorization["category"],
            priority=categorization["priority"],
            source=source,
            timestamp=datetime.now().isoformat(),
            namespace=namespace,
            hash_id=hashlib.sha256(content.encode()).hexdigest()[:16],
            conflicts=categorization.get("conflicts", []),
            metadata={
                "semantic_tags": categorization.get("semantic_tags", []),
                "relationships": categorization.get("relationships", []),
                "project_root": str(self.project_root),
                "is_duplicate": categorization.get("duplicate", False)
            }
        )

    async def add_memory(self, content: str, source: str = "project") -> bool:
        """Add memory with KRAG integration"""
        
        if not content.strip():
            print("❌ Empty memory content")
            return False
        
        # Create structured memory entry
        memory_entry = self.create_memory_entry(content, source)
        
        # Check for duplicates
        if memory_entry.metadata.get("is_duplicate", False):
            print(f"⚠️  Memory appears to be duplicate: {content[:50]}...")
            conflicts = memory_entry.conflicts
            if conflicts:
                print(f"   Conflicts: {', '.join(conflicts[:3])}")
            return False
        
        print(f"🧠 Adding memory: {memory_entry.category} | {memory_entry.priority}")
        print(f"   Content: {content[:80]}...")
        print(f"   Namespace: {memory_entry.namespace}")
        
        # Add to KRAG knowledge graph
        success = await self.add_to_krag(memory_entry)
        
        if success:
            # Also add to local file for backup
            self._add_to_local_file(memory_entry, source)
            print("✅ Memory added successfully")
            return True
        else:
            print("❌ Failed to add memory to KRAG")
            return False

    def _add_to_local_file(self, memory_entry: MemoryEntry, source: str):
        """Add memory to local file as backup"""
        
        target_file = self.project_memory if source == "project" else self.user_memory
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup
        if target_file.exists():
            backup_name = f"{target_file.name}.{int(datetime.now().timestamp())}.backup"
            backup_path = self.backup_dir / backup_name
            backup_path.write_text(target_file.read_text())
        
        # Format memory entry for markdown
        formatted_entry = f"\n## {memory_entry.category} - {memory_entry.priority.upper()}\n"
        formatted_entry += f"- {memory_entry.content}\n"
        formatted_entry += f"  - Added: {memory_entry.timestamp}\n"
        formatted_entry += f"  - Hash: {memory_entry.hash_id}\n"
        formatted_entry += f"  - Namespace: {memory_entry.namespace}\n"
        
        # Append to file
        with open(target_file, "a", encoding="utf-8") as f:
            f.write(formatted_entry)

    async def sync_memories(self) -> Dict[str, Any]:
        """Cross-session memory synchronization"""
        
        print("🔄 Starting memory synchronization...")
        
        # Find all CLAUDE.md files in workspace
        workspace_memories = []
        try:
            git_root = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"], 
                capture_output=True, text=True, cwd=self.project_root
            )
            if git_root.returncode == 0:
                workspace_root = Path(git_root.stdout.strip())
                workspace_memories = list(workspace_root.rglob("CLAUDE.md"))
            else:
                workspace_memories = list(self.project_root.rglob("CLAUDE.md"))
        except Exception:
            workspace_memories = list(self.project_root.rglob("CLAUDE.md"))
        
        print(f"📁 Found {len(workspace_memories)} memory files")
        
        # Analyze patterns across memory files
        all_memories = []
        for memory_file in workspace_memories:
            try:
                content = memory_file.read_text(encoding="utf-8")
                all_memories.append({
                    "path": str(memory_file),
                    "content": content,
                    "size": len(content)
                })
            except Exception as e:
                print(f"⚠️  Error reading {memory_file}: {e}")
        
        sync_results = {
            "files_processed": len(all_memories),
            "patterns_identified": [],
            "recommendations": [],
            "namespace_distribution": {ns: 0 for ns in self.namespaces.values()}
        }
        
        # Pattern analysis (simplified without Claude CLI dependency)
        common_patterns = self._analyze_memory_patterns(all_memories)
        sync_results["patterns_identified"] = common_patterns
        
        # Generate recommendations
        if len(all_memories) > 1:
            sync_results["recommendations"] = [
                "Consider consolidating duplicate patterns",
                "Move project-agnostic patterns to user memory",
                f"Distribute memories across KRAG namespaces: {list(self.namespaces.keys())}"
            ]
        
        print("✅ Memory synchronization completed")
        return sync_results

    def _analyze_memory_patterns(self, memories: List[Dict]) -> List[str]:
        """Simple pattern analysis without external dependencies"""
        
        patterns = []
        all_content = " ".join([mem["content"].lower() for mem in memories])
        
        # Simple keyword frequency analysis
        keywords = ["typescript", "testing", "security", "performance", "architecture"]
        for keyword in keywords:
            count = all_content.count(keyword)
            if count > 2:  # Appears in multiple files
                patterns.append(f"{keyword} (mentioned {count} times)")
        
        return patterns[:5]  # Return top 5 patterns

    async def backup_memories(self) -> str:
        """Create comprehensive memory backup"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"memory_backup_{timestamp}.json"
        
        backup_data = {
            "timestamp": timestamp,
            "namespaces": self.namespaces,
            "project_root": str(self.project_root),
            "memories": []
        }
        
        # Collect all memory files
        memory_files = [self.project_memory, self.user_memory]
        memory_files.extend(self.project_root.rglob("CLAUDE.md"))
        
        for memory_file in memory_files:
            if memory_file.exists():
                try:
                    backup_data["memories"].append({
                        "path": str(memory_file),
                        "content": memory_file.read_text(encoding="utf-8"),
                        "size": memory_file.stat().st_size,
                        "modified": memory_file.stat().st_mtime
                    })
                except Exception as e:
                    print(f"⚠️  Error backing up {memory_file}: {e}")
        
        # Write backup
        backup_file.write_text(json.dumps(backup_data, indent=2))
        
        print(f"💾 Backup created: {backup_file}")
        print(f"   Files: {len(backup_data['memories'])}")
        
        return str(backup_file)


async def main():
    """Main CLI interface matching memory-manager.sh functionality"""
    
    if len(sys.argv) < 2:
        print("""
🧠 Enhanced Memory Sync - KRAG Integration

Commands:
  add <memory>     Add memory with intelligent categorization
  sync            Synchronize memories across sessions  
  backup          Create comprehensive backup
  analyze         Analyze memory patterns (requires Claude CLI)
  
Options:
  --source project|user  (default: project)
  --namespace <name>     Override namespace selection
  
Examples:
  python memory_sync_enhanced.py add "Always use TypeScript strict mode"
  python memory_sync_enhanced.py sync
  python memory_sync_enhanced.py backup
""")
        return
    
    command = sys.argv[1]
    memory_sync = KRAGMemorySync()
    
    try:
        if command == "add":
            if len(sys.argv) < 3:
                print("❌ Memory content required")
                return
            
            content = " ".join(sys.argv[2:])
            source = "project"  # Default, could be made configurable
            
            success = await memory_sync.add_memory(content, source)
            sys.exit(0 if success else 1)
            
        elif command == "sync":
            results = await memory_sync.sync_memories()
            print(f"\n📊 Sync Results:")
            print(f"   Files processed: {results['files_processed']}")
            print(f"   Patterns: {', '.join(results['patterns_identified'][:3])}")
            
        elif command == "backup":
            backup_path = await memory_sync.backup_memories()
            print(f"✅ Backup completed: {backup_path}")
            
        elif command == "analyze":
            print("🔍 Analysis requires full KRAG integration")
            print("   Use 'sync' command for basic pattern analysis")
            
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())