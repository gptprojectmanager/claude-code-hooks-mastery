#!/usr/bin/env python3
"""
Safe liteLLM Wrapper
Replaces direct Gemini CLI calls with Smart API Router through liteLLM proxy
"""

import subprocess
import sys
import os
import json
import hashlib
import time
import requests
from pathlib import Path

class SafeLiteLLMWrapper:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.pre_hash = None
        self.post_hash = None
        self.litellm_url = "http://localhost:4001/v1/chat/completions"
        
    def _calculate_directory_hash(self) -> str:
        """Calculate hash of all files in directory for change detection"""
        hasher = hashlib.sha256()
        
        for file_path in sorted(self.base_path.rglob('*')):
            if file_path.is_file() and not str(file_path).startswith('.git'):
                try:
                    with open(file_path, 'rb') as f:
                        hasher.update(f.read())
                    hasher.update(str(file_path).encode())
                except (PermissionError, UnicodeDecodeError):
                    continue
                    
        return hasher.hexdigest()
    
    def _create_git_backup(self) -> bool:
        """Create git backup before analysis"""
        try:
            # Check if in git repo
            subprocess.run(["git", "status"], 
                         cwd=self.base_path, 
                         capture_output=True, 
                         check=True)
            
            # Create backup commit
            subprocess.run(["git", "add", "-A"], 
                         cwd=self.base_path, 
                         capture_output=True)
            
            backup_msg = f"Safe liteLLM analysis backup - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            result = subprocess.run(["git", "commit", "-m", backup_msg], 
                                  cwd=self.base_path, 
                                  capture_output=True)
            
            print(f"✓ Git backup created: {backup_msg}")
            return True
            
        except subprocess.CalledProcessError:
            print("⚠ Warning: Could not create git backup")
            return False
    
    def _rollback_changes(self):
        """Rollback any file modifications"""
        try:
            subprocess.run(["git", "checkout", "--", "."], 
                         cwd=self.base_path, 
                         check=True)
            subprocess.run(["git", "clean", "-fd"], 
                         cwd=self.base_path, 
                         check=True)
            print("✓ Rolled back all changes")
        except subprocess.CalledProcessError:
            print("✗ Failed to rollback changes")
    
    def _validate_safe_prompt(self, prompt: str) -> bool:
        """Validate that prompt is safe (read-only)"""
        dangerous_keywords = [
            "fix", "implement", "create", "update", "edit", "write", 
            "save", "delete", "remove", "refactor", "optimize", 
            "improve", "add", "install", "configure", "generate"
        ]
        
        safe_prefixes = [
            "ANALYZE ONLY - DO NOT MODIFY",
            "DESCRIBE ONLY", 
            "ASSESS ONLY",
            "EXPLAIN ONLY"
        ]
        
        prompt_lower = prompt.lower()
        
        # Check for safe prefix first
        has_safe_prefix = any(prefix.lower() in prompt_lower for prefix in safe_prefixes)
        if not has_safe_prefix:
            print(f"✗ Prompt missing safe prefix. Use: {safe_prefixes[0]}")
            return False
        
        # Remove safe prefix from checking to avoid false positives
        prompt_to_check = prompt_lower
        for prefix in safe_prefixes:
            prompt_to_check = prompt_to_check.replace(prefix.lower(), "")
        
        # Check for dangerous keywords in remaining text
        dangerous_found = [kw for kw in dangerous_keywords if kw in prompt_to_check]
        if dangerous_found:
            print(f"✗ Dangerous keywords found: {dangerous_found}")
            return False
            
        return True
    
    def _prepare_codebase_context(self) -> str:
        """Prepare codebase context for analysis"""
        context_files = []
        
        # Collect key files for context
        for pattern in ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs", "*.md"]:
            for file_path in self.base_path.rglob(pattern):
                if file_path.is_file() and not any(ignore in str(file_path) for ignore in ['.git', 'node_modules', '__pycache__', '.venv']):
                    try:
                        rel_path = file_path.relative_to(self.base_path)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if len(content) < 10000:  # Only include smaller files
                                context_files.append(f"## {rel_path}\n```\n{content}\n```\n")
                    except (UnicodeDecodeError, PermissionError):
                        continue
        
        return "\n".join(context_files[:50])  # Limit to 50 files to avoid token limit
    
    def safe_analyze(self, prompt: str, timeout: int = 300) -> dict:
        """
        Safely execute analysis through liteLLM proxy with comprehensive safeguards
        """
        result = {
            "success": False,
            "output": "",
            "error": "",
            "safety_checks": {
                "prompt_validated": False,
                "backup_created": False,
                "no_modifications": False
            }
        }
        
        # Safety Check 1: Validate prompt
        if not self._validate_safe_prompt(prompt):
            result["error"] = "Unsafe prompt detected"
            return result
        result["safety_checks"]["prompt_validated"] = True
        
        # Safety Check 2: Create backup
        backup_created = self._create_git_backup()
        result["safety_checks"]["backup_created"] = backup_created
        
        # Safety Check 3: Pre-analysis hash
        print("📊 Computing pre-analysis hash...")
        self.pre_hash = self._calculate_directory_hash()
        
        try:
            # Prepare codebase context
            print("📁 Preparing codebase context...")
            codebase_context = self._prepare_codebase_context()
            
            # Construct full prompt with context
            full_prompt = f"{prompt}\n\n# Codebase Context:\n{codebase_context}"
            
            # Execute through liteLLM proxy
            print("🤖 Running analysis through Smart API Router...")
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy_key"
            }
            
            data = {
                "model": "gemini-pro",  # Use liteLLM alias
                "messages": [
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }
            
            response = requests.post(
                self.litellm_url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                result["output"] = content
                result["success"] = True
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                result["error"] = error_data.get("error", {}).get("message", response.text)
            
        except requests.exceptions.Timeout:
            result["error"] = f"liteLLM proxy timed out after {timeout} seconds"
        except requests.exceptions.RequestException as e:
            result["error"] = f"liteLLM proxy request failed: {e}"
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"
        
        # Safety Check 4: Post-analysis verification
        print("🔍 Verifying no modifications...")
        self.post_hash = self._calculate_directory_hash()
        
        if self.pre_hash != self.post_hash:
            print("🚨 FILES WERE MODIFIED! Rolling back...")
            self._rollback_changes()
            result["error"] = "Analysis process modified files - changes rolled back"
            result["success"] = False
        else:
            print("✓ No file modifications detected")
            result["safety_checks"]["no_modifications"] = True
        
        return result

def main():
    if len(sys.argv) < 3:
        print("Usage: safe-litellm-wrapper.py <base_path> <prompt>")
        sys.exit(1)
    
    base_path = sys.argv[1]
    prompt = sys.argv[2]
    
    wrapper = SafeLiteLLMWrapper(base_path)
    result = wrapper.safe_analyze(prompt)
    
    if result["success"]:
        print("\n" + "="*50)
        print("SMART API ROUTER ANALYSIS RESULT:")
        print("="*50)
        print(result["output"])
        print("\n" + "="*50)
        print(f"JSON OUTPUT: {json.dumps(result, indent=2)}")
    else:
        print(f"\n✗ Analysis failed: {result['error']}")
        print(f"Safety checks: {result['safety_checks']}")
        sys.exit(1)

if __name__ == "__main__":
    main()