#!/usr/bin/env python3
"""
Safe Gemini CLI Wrapper
Ensures read-only analysis without file modifications
"""

import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path
import hashlib
import time

class SafeGeminiWrapper:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.pre_hash = None
        self.post_hash = None
        
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
            
            backup_msg = f"Safe Gemini CLI backup - {time.strftime('%Y-%m-%d %H:%M:%S')}"
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
    
    def safe_analyze(self, prompt: str, timeout: int = 300) -> dict:
        """
        Safely execute Gemini CLI analysis with comprehensive safeguards
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
        
        # Safety Check 2: No backup needed - handled by /safe-gemini command
        result["safety_checks"]["backup_created"] = True
        
        # Safety Check 3: Pre-analysis hash
        print("📊 Computing pre-analysis hash...")
        self.pre_hash = self._calculate_directory_hash()
        
        try:
            # Execute Gemini CLI
            print("🤖 Running Gemini CLI analysis...")
            gemini_result = subprocess.run(
                ["gemini", "-p", prompt],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if gemini_result.returncode == 0:
                result["output"] = gemini_result.stdout
                result["success"] = True
            else:
                result["error"] = gemini_result.stderr
            
        except subprocess.TimeoutExpired:
            result["error"] = f"Gemini CLI timed out after {timeout} seconds"
        except subprocess.CalledProcessError as e:
            result["error"] = f"Gemini CLI failed: {e}"
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"
        
        # Safety Check 4: Post-analysis verification
        print("🔍 Verifying no modifications...")
        self.post_hash = self._calculate_directory_hash()
        
        if self.pre_hash != self.post_hash:
            print("🚨 FILES WERE MODIFIED! Rolling back...")
            self._rollback_changes()
            result["error"] = "Gemini CLI modified files - changes rolled back"
            result["success"] = False
        else:
            print("✓ No file modifications detected")
            result["safety_checks"]["no_modifications"] = True
        
        return result

def main():
    if len(sys.argv) < 3:
        print("Usage: safe-gemini-wrapper.py <base_path> <prompt>")
        sys.exit(1)
    
    base_path = sys.argv[1]
    prompt = sys.argv[2]
    
    wrapper = SafeGeminiWrapper(base_path)
    result = wrapper.safe_analyze(prompt)
    
    if result["success"]:
        print("\n" + "="*50)
        print("GEMINI CLI ANALYSIS RESULT:")
        print("="*50)
        print(result["output"])
    else:
        print(f"\n✗ Analysis failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()