#!/usr/bin/env python3
"""
Claude Instance Launcher for OpenEvolve
Launches separate Claude Code instances in isolated git worktrees for parallel optimization.

This module implements the official Claude Code workflow for parallel sessions with git worktrees,
following best practices from: https://docs.anthropic.com/en/docs/claude-code/common-workflows

Key Features:
- Official Claude Code CLI integration with `claude --print` 
- CLAUDE.md memory system integration for context sharing
- Git worktree isolation for parallel execution
- Background process management with proper PID tracking
- Comprehensive optimization context transfer via JSON
"""

import os
import json
import subprocess
import signal
import time
import hashlib
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import threading
import shlex


@dataclass
class ClaudeInstanceConfig:
    """Configuration for Claude Code instance following official patterns."""
    instance_id: str
    worktree_path: str
    claude_md_file: str  # CLAUDE.md memory file
    optimization_context_file: str
    command_args: List[str]
    environment: Dict[str, str]
    background_mode: bool = True
    timeout_minutes: int = 30


@dataclass
class RunningInstance:
    """Represents a running Claude Code instance."""
    instance_id: str
    process_id: int
    worktree_path: str
    started_at: str
    status: str  # starting, running, completed, failed, timeout, killed
    optimization_context: Dict[str, Any]
    log_file: str
    claude_md_path: str  # Path to instance-specific CLAUDE.md
    last_heartbeat: Optional[str] = None
    completion_data: Optional[Dict[str, Any]] = None
    config: Optional['ClaudeInstanceConfig'] = None


class ClaudeInstanceLauncher:
    """
    Official Claude Code Instance Launcher for OpenEvolve.
    
    Implements parallel session workflow using:
    - `claude --print` executed in worktree directory
    - CLAUDE.md files for memory and context sharing
    - Git worktrees for complete isolation
    - Background subprocess management
    """
    
    def __init__(self, base_repo_path: str = None):
        """Initialize the Claude instance launcher following official patterns."""
        self.base_repo_path = Path(base_repo_path or os.getcwd())
        self.instances_dir = self.base_repo_path / ".claude" / "instances"
        self.instances_registry_file = self.instances_dir / "registry.json"
        self.max_concurrent_instances = 5
        self.claude_command = "claude"  # Official Claude Code CLI
        
        # Ensure directories exist
        self.instances_dir.mkdir(parents=True, exist_ok=True)
        
        # Active instances tracking
        self.running_instances: Dict[str, RunningInstance] = {}
        self._load_registry()
        
        # Start background monitoring
        self._start_monitoring_thread()
    
    def _generate_instance_id(self, code: str, language: str) -> str:
        """Generate unique instance ID based on content and timestamp."""
        content_hash = hashlib.md5(code.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        return f"claude_{language}_{content_hash}_{timestamp}"
    
    def _load_registry(self) -> None:
        """Load running instances registry from disk."""
        if not self.instances_registry_file.exists():
            return
        
        try:
            with open(self.instances_registry_file, 'r') as f:
                registry_data = json.load(f)
                
            for instance_id, instance_data in registry_data.items():
                # Extract config data first
                config_data = instance_data.get("config", {})
                config = None
                if config_data:
                    try:
                        config = ClaudeInstanceConfig(**config_data)
                    except Exception as e:
                        print(f"Warning: Could not reconstruct config for {instance_id}: {e}")
                
                # Create instance with config
                try:
                    # Remove config from instance_data to avoid duplicate
                    instance_data_copy = instance_data.copy()
                    instance_data_copy.pop("config", None)
                    
                    instance = RunningInstance(**instance_data_copy, config=config)
                    
                    # Check if process is still running
                    if self._is_process_running(instance.process_id):
                        self.running_instances[instance_id] = instance
                    else:
                        # Mark as completed/failed if process not found
                        instance.status = "completed" if instance.status == "running" else "failed"
                        self.running_instances[instance_id] = instance
                        
                except Exception as e:
                    print(f"Warning: Could not reconstruct instance {instance_id}: {e}")
                    
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Could not load instances registry: {e}")
    
    def _save_registry(self) -> None:
        """Save running instances registry to disk."""
        registry_data = {}
        
        for instance_id, instance in self.running_instances.items():
            instance_dict = asdict(instance)
            # Handle config serialization separately if it exists
            if instance.config:
                instance_dict["config"] = asdict(instance.config)
            registry_data[instance_id] = instance_dict
        
        with open(self.instances_registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2)
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            return psutil.pid_exists(pid)
        except:
            try:
                # Fallback method
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    
    def create_claude_md_file(
        self,
        worktree_path: Path,
        instance_id: str,
        code: str,
        language: str,
        optimization_params: Dict[str, Any] = None
    ) -> Path:
        """
        Create instance-specific CLAUDE.md file following official documentation.
        
        Based on: https://docs.anthropic.com/en/docs/claude-code/memory#claude-md-imports
        """
        claude_md_path = worktree_path / "CLAUDE.md"
        
        # Create comprehensive CLAUDE.md content
        claude_md_content = f"""# Claude Code - OpenEvolve Optimization Instance

## Instance Context
This file provides guidance to Claude Code when working with code in this OpenEvolve optimization instance.

**Instance ID**: {instance_id}  
**Language**: {language}  
**Created**: {datetime.now().isoformat()}  
**Mode**: Automated Evolutionary Optimization

## AI Guidance
- Focus on evolutionary code optimization for the provided {language} code
- Apply advanced optimization techniques: algorithmic improvement, performance enhancement, readability
- Maintain code correctness while maximizing optimization potential
- Document all changes with before/after comparisons
- Save final results to `.claude/optimization_results.json`

## Optimization Mission
You are a specialized Claude instance running in parallel optimization mode. Your core mission:

1. **Code Analysis**: Deep analysis of the provided code for optimization opportunities
2. **Evolutionary Optimization**: Apply advanced optimization techniques iteratively
3. **Performance Validation**: Ensure optimizations improve performance without breaking functionality
4. **Results Documentation**: Create comprehensive optimization report with metrics

## Code Context
**Original Code Length**: {len(code.split('\\n'))} lines  
**Optimization Focus**: {', '.join(optimization_params.get('target_metrics', ['performance', 'readability']) if optimization_params else ['performance'])}  
**Complexity Assessment**: {self._assess_code_complexity(code)}

## Execution Protocol
1. Read optimization context from `.claude/optimization_context.json`
2. Analyze code structure and identify key optimization opportunities
3. Apply optimization techniques based on language best practices
4. Test and validate improvements
5. Document results with performance comparisons
6. Save comprehensive results to `.claude/optimization_results.json`

## Memory and Context Management
- Use KRAG memory system for storing optimization insights
- Namespace: `openevolve_optimization_{instance_id}`
- Store significant findings and optimization patterns

## Success Criteria
- Maintain code correctness (all tests pass)
- Achieve measurable performance improvement
- Improve code readability and maintainability
- Document optimization rationale clearly

**START OPTIMIZATION PROCESS IMMEDIATELY**
"""
        
        # Write CLAUDE.md file
        with open(claude_md_path, 'w') as f:
            f.write(claude_md_content)
        
        return claude_md_path
    
    def _assess_code_complexity(self, code: str) -> str:
        """Quick complexity assessment for CLAUDE.md context."""
        lines = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')])
        
        if lines < 20:
            return "Low complexity - focus on micro-optimizations and code clarity"
        elif lines < 100:
            return "Medium complexity - balance algorithmic and structural improvements"
        else:
            return "High complexity - prioritize architectural and algorithmic optimizations"
    
    def prepare_context_file(
        self,
        worktree_path: Path,
        code: str,
        language: str,
        complexity_level: str = "medium",
        optimization_params: Dict[str, Any] = None
    ) -> Path:
        """
        Prepare optimization context file for Claude instance.
        
        This creates the structured context that the CLAUDE.md file references.
        """
        context_file = worktree_path / ".claude" / "optimization_context.json"
        context_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare comprehensive optimization context
        optimization_context = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "language": language,
                "complexity_level": complexity_level,
                "code_length_lines": len(code.split('\n')),
                "worktree_path": str(worktree_path),
                "version": "2.0",
                "claude_code_integration": True
            },
            "code": {
                "content": code,
                "language": language,
                "analysis_hints": {
                    "focus_areas": self._identify_optimization_areas(code, language),
                    "complexity_indicators": self._analyze_complexity_indicators(code),
                    "optimization_potential": self._estimate_optimization_potential(code, language)
                }
            },
            "optimization_parameters": {
                "target_metrics": optimization_params.get("target_metrics", ["performance", "memory", "readability"]) if optimization_params else ["performance"],
                "constraints": optimization_params.get("constraints", {}) if optimization_params else {},
                "iterations": optimization_params.get("iterations", 10) if optimization_params else 10,
                "timeout_minutes": optimization_params.get("timeout_minutes", 20) if optimization_params else 20,
                "preserve_functionality": True,
                "require_tests": optimization_params.get("require_tests", False) if optimization_params else False
            },
            "execution_context": {
                "instance_type": "claude_code_optimization",
                "parallel_execution": True,
                "background_mode": True,
                "krag_namespace": f"openevolve_optimization_{int(time.time())}",
                "claude_md_driven": True,
                "official_workflow": True
            },
            "expected_outputs": {
                "optimization_results_file": ".claude/optimization_results.json",
                "performance_comparison": True,
                "test_validation": True,
                "optimization_summary": True
            }
        }
        
        # Write context file
        with open(context_file, 'w') as f:
            json.dump(optimization_context, f, indent=2)
        
        return context_file
    
    def _identify_optimization_areas(self, code: str, language: str) -> List[str]:
        """Identify potential optimization areas in code."""
        areas = []
        code_lower = code.lower()
        
        # Language-agnostic patterns
        if any(pattern in code_lower for pattern in ['for ', 'while ', 'loop']):
            areas.append("loop_optimization")
        
        if any(pattern in code_lower for pattern in ['sort', 'search', 'find']):
            areas.append("algorithmic_complexity")
        
        if any(pattern in code_lower for pattern in ['list', 'array', 'dict', 'map']):
            areas.append("data_structure_optimization")
        
        # Python-specific patterns
        if language.lower() == "python":
            if any(pattern in code for pattern in ['list(', '[x for x', 'map(', 'filter(']):
                areas.append("pythonic_optimizations")
            
            if 'import' in code_lower and ('pandas' in code_lower or 'numpy' in code_lower):
                areas.append("vectorization")
            
            if any(pattern in code for pattern in ['def ', 'class ', 'lambda']):
                areas.append("functional_optimization")
        
        # JavaScript-specific patterns
        elif language.lower() in ["javascript", "typescript"]:
            if any(pattern in code for pattern in ['forEach', 'map(', 'filter(', 'reduce(']):
                areas.append("functional_programming")
            
            if 'async' in code_lower or 'promise' in code_lower:
                areas.append("async_optimization")
        
        # Default areas if none identified
        return areas if areas else ["general_performance", "code_clarity"]
    
    def _analyze_complexity_indicators(self, code: str) -> Dict[str, Any]:
        """Analyze complexity indicators in the code."""
        lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        return {
            "line_count": len(lines),
            "nested_loops": code.count('for ') + code.count('while '),
            "function_count": code.count('def ') + code.count('function '),
            "class_count": code.count('class '),
            "import_count": code.count('import ') + code.count('require('),
            "complexity_score": min(100, len(lines) * 0.5 + (code.count('for ') + code.count('while ')) * 10),
            "cognitive_complexity": self._estimate_cognitive_complexity(code)
        }
    
    def _estimate_cognitive_complexity(self, code: str) -> int:
        """Estimate cognitive complexity of code."""
        complexity = 0
        
        # Basic control flow
        complexity += code.count('if ') * 1
        complexity += code.count('for ') * 2
        complexity += code.count('while ') * 2
        complexity += code.count('try') * 1
        complexity += code.count('catch') * 2
        
        # Nesting penalty
        nesting_level = 0
        for line in code.split('\n'):
            stripped = line.strip()
            if any(keyword in stripped for keyword in ['if ', 'for ', 'while ', 'try']):
                nesting_level += 1
                complexity += nesting_level
        
        return min(50, complexity)
    
    def _estimate_optimization_potential(self, code: str, language: str) -> Dict[str, Any]:
        """Estimate optimization potential of the code."""
        indicators = self._analyze_complexity_indicators(code)
        
        # Enhanced scoring algorithm
        potential_score = 0
        
        # Size-based potential
        if indicators["line_count"] > 100:
            potential_score += 40
        elif indicators["line_count"] > 50:
            potential_score += 25
        elif indicators["line_count"] > 20:
            potential_score += 15
        
        # Complexity-based potential
        if indicators["nested_loops"] > 3:
            potential_score += 35
        elif indicators["nested_loops"] > 1:
            potential_score += 20
        
        # Cognitive complexity penalty/opportunity
        if indicators["cognitive_complexity"] > 20:
            potential_score += 30
        elif indicators["cognitive_complexity"] > 10:
            potential_score += 15
        
        # Language-specific potential
        if language.lower() == "python":
            # Python has high optimization potential
            potential_score += 10
            
        return {
            "score": min(95, potential_score),
            "confidence": 0.8,
            "primary_opportunities": [
                "algorithmic_improvement", 
                "data_structure_optimization", 
                "code_clarity",
                "performance_enhancement"
            ],
            "estimated_improvement_range": f"{max(10, potential_score//4)}-{min(70, potential_score)}%",
            "optimization_difficulty": "medium" if potential_score < 60 else "high"
        }
    
    def launch_optimization_instance(
        self,
        code: str,
        language: str = "python",
        worktree_path: str = None,
        optimization_params: Dict[str, Any] = None,
        background: bool = True,
        timeout_minutes: int = 30
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Launch a Claude Code instance for optimization using official workflow.
        
        Uses `claude --print` executed in worktree directory with CLAUDE.md memory file.
        
        Args:
            code: Code to optimize
            language: Programming language
            worktree_path: Path to git worktree (if None, uses current directory)
            optimization_params: Optimization parameters
            background: Run in background mode
            timeout_minutes: Instance timeout
            
        Returns:
            (success: bool, message: str, instance_id: Optional[str])
        """
        try:
            # Check concurrent instance limit
            active_count = len([i for i in self.running_instances.values() 
                              if i.status in ['starting', 'running']])
            
            if active_count >= self.max_concurrent_instances:
                return False, f"Maximum concurrent instances ({self.max_concurrent_instances}) reached", None
            
            # Generate instance ID
            instance_id = self._generate_instance_id(code, language)
            
            # Use provided worktree or current directory
            target_worktree_path = Path(worktree_path) if worktree_path else self.base_repo_path
            
            # Ensure worktree path exists
            if not target_worktree_path.exists():
                return False, f"Worktree path does not exist: {target_worktree_path}", None
            
            # Create instance-specific CLAUDE.md file (official pattern)
            claude_md_path = self.create_claude_md_file(
                target_worktree_path,
                instance_id,
                code,
                language,
                optimization_params
            )
            
            # Prepare context file
            context_file = self.prepare_context_file(
                target_worktree_path,
                code,
                language,
                optimization_params.get("complexity_level", "medium") if optimization_params else "medium",
                optimization_params
            )
            
            # Prepare optimization prompt for Claude
            optimization_prompt = f"""I am now in the optimization worktree. I will read my CLAUDE.md file to understand my mission and begin the optimization process immediately.

OPTIMIZATION CONTEXT:
- Instance ID: {instance_id}
- Language: {language}
- Working Directory: {target_worktree_path}
- Context File: {context_file}
- Expected Results File: .claude/optimization_results.json

My mission is to optimize the code provided in the context file using evolutionary techniques, following the instructions in my CLAUDE.md file."""
            
            # Prepare Claude Code command (without --dir, execute in worktree)
            claude_args = [
                self.claude_command,
                "--print", optimization_prompt
            ]
            
            # Setup environment following official patterns
            env = os.environ.copy()
            env.update({
                "CLAUDE_OPTIMIZATION_CONTEXT": str(context_file),
                "CLAUDE_INSTANCE_ID": instance_id,
                "CLAUDE_LANGUAGE": language,
                "CLAUDE_WORKTREE": str(target_worktree_path),
                "CLAUDE_BACKGROUND_MODE": "true" if background else "false",
                "OPENEVOLVE_MODE": "true"
            })
            
            # Setup logging
            log_file = self.instances_dir / f"{instance_id}.log"
            
            # Create instance configuration
            config = ClaudeInstanceConfig(
                instance_id=instance_id,
                worktree_path=str(target_worktree_path),
                claude_md_file=str(claude_md_path),
                optimization_context_file=str(context_file),
                command_args=claude_args,
                environment=env,
                background_mode=background,
                timeout_minutes=timeout_minutes
            )
            
            # Launch process using official Claude Code CLI in worktree directory
            if background:
                with open(log_file, 'w') as log_f:
                    process = subprocess.Popen(
                        claude_args,
                        cwd=target_worktree_path,  # Execute in worktree
                        env=env,
                        stdout=log_f,
                        stderr=subprocess.STDOUT,
                        start_new_session=True  # Detach from parent
                    )
            else:
                process = subprocess.Popen(
                    claude_args,
                    cwd=target_worktree_path,  # Execute in worktree
                    env=env
                )
            
            # Create running instance record
            running_instance = RunningInstance(
                instance_id=instance_id,
                process_id=process.pid,
                worktree_path=str(target_worktree_path),
                started_at=datetime.now().isoformat(),
                status="starting",
                optimization_context=json.loads(context_file.read_text()),
                log_file=str(log_file),
                claude_md_path=str(claude_md_path),
                config=config
            )
            
            # Register instance
            self.running_instances[instance_id] = running_instance
            self._save_registry()
            
            # Short delay to check if process started successfully
            time.sleep(1.0)
            
            if self._is_process_running(process.pid):
                running_instance.status = "running"
                running_instance.last_heartbeat = datetime.now().isoformat()
                self._save_registry()
                
                success_msg = (
                    f"Claude optimization instance launched successfully\n"
                    f"  Instance ID: {instance_id}\n"
                    f"  Process ID: {process.pid}\n"
                    f"  Worktree: {target_worktree_path}\n"
                    f"  CLAUDE.md: {claude_md_path}\n"
                    f"  Background: {background}"
                )
                
                return True, success_msg, instance_id
            else:
                running_instance.status = "failed"
                self._save_registry()
                return False, f"Claude instance failed to start (check log: {log_file})", instance_id
                
        except Exception as e:
            return False, f"Failed to launch Claude instance: {str(e)}", None
    
    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive status information for a Claude instance.
        
        Args:
            instance_id: Instance to check
            
        Returns:
            Status information or None if instance not found
        """
        if instance_id not in self.running_instances:
            return None
        
        instance = self.running_instances[instance_id]
        
        # Update process status
        if instance.status == "running" and not self._is_process_running(instance.process_id):
            instance.status = "completed"
            instance.completion_data = self._collect_completion_data(instance)
            self._save_registry()
        
        status_info = {
            "instance_id": instance_id,
            "status": instance.status,
            "process_id": instance.process_id,
            "started_at": instance.started_at,
            "worktree_path": instance.worktree_path,
            "claude_md_path": instance.claude_md_path,
            "language": instance.optimization_context.get("metadata", {}).get("language", "unknown"),
            "last_heartbeat": instance.last_heartbeat,
            "is_process_running": self._is_process_running(instance.process_id),
            "log_file": instance.log_file,
            "optimization_focus": instance.optimization_context.get("optimization_parameters", {}).get("target_metrics", []),
            "complexity_assessment": instance.optimization_context.get("code", {}).get("analysis_hints", {}).get("optimization_potential", {})
        }
        
        # Add completion data if available
        if instance.completion_data:
            status_info["completion_data"] = instance.completion_data
        
        # Add runtime duration
        if instance.started_at:
            try:
                start_time = datetime.fromisoformat(instance.started_at)
                duration = (datetime.now() - start_time).total_seconds()
                status_info["runtime_seconds"] = duration
                status_info["runtime_formatted"] = f"{duration//60:.0f}m {duration%60:.0f}s"
            except:
                pass
        
        return status_info
    
    def _collect_completion_data(self, instance: RunningInstance) -> Dict[str, Any]:
        """Collect completion data from instance worktree."""
        try:
            worktree_path = Path(instance.worktree_path)
            results_file = worktree_path / ".claude" / "optimization_results.json"
            claude_md_file = Path(instance.claude_md_path)
            
            completion_data = {
                "completed_at": datetime.now().isoformat(),
                "has_results_file": results_file.exists(),
                "claude_md_exists": claude_md_file.exists()
            }
            
            # Check optimization results
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        optimization_results = json.load(f)
                    completion_data["optimization_results"] = optimization_results
                    completion_data["has_valid_results"] = True
                except Exception as e:
                    completion_data["results_error"] = str(e)
                    completion_data["has_valid_results"] = False
            
            # Check for CLAUDE.md updates (instance may have updated it)
            if claude_md_file.exists():
                try:
                    completion_data["claude_md_size"] = claude_md_file.stat().st_size
                    completion_data["claude_md_modified"] = datetime.fromtimestamp(
                        claude_md_file.stat().st_mtime
                    ).isoformat()
                except:
                    pass
            
            # Check for log file size and last lines
            log_file = Path(instance.log_file)
            if log_file.exists():
                try:
                    completion_data["log_size_bytes"] = log_file.stat().st_size
                    # Get last few lines for quick status check
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            completion_data["log_last_lines"] = lines[-5:]  # Last 5 lines
                except:
                    pass
            
            return completion_data
            
        except Exception as e:
            return {"collection_error": str(e)}
    
    def kill_instance(self, instance_id: str, force: bool = False) -> Tuple[bool, str]:
        """
        Terminate a running Claude instance gracefully.
        
        Args:
            instance_id: Instance to terminate
            force: Use SIGKILL instead of SIGTERM
            
        Returns:
            (success: bool, message: str)
        """
        if instance_id not in self.running_instances:
            return False, f"Instance {instance_id} not found"
        
        instance = self.running_instances[instance_id]
        
        if not self._is_process_running(instance.process_id):
            instance.status = "completed"
            self._save_registry()
            return True, f"Instance {instance_id} was already terminated"
        
        try:
            if force:
                os.kill(instance.process_id, signal.SIGKILL)
                instance.status = "killed"
                termination_type = "force kill (SIGKILL)"
            else:
                # Graceful shutdown
                os.kill(instance.process_id, signal.SIGTERM)
                instance.status = "killed"
                termination_type = "graceful termination (SIGTERM)"
                
                # Wait a bit for graceful shutdown
                time.sleep(3)
                if self._is_process_running(instance.process_id):
                    os.kill(instance.process_id, signal.SIGKILL)
                    termination_type = "graceful -> force kill"
            
            instance.completion_data = {
                "terminated_at": datetime.now().isoformat(),
                "termination_reason": "manual_kill",
                "termination_type": termination_type,
                "force_kill": force
            }
            
            self._save_registry()
            
            return True, f"Instance {instance_id} terminated successfully ({termination_type})"
            
        except Exception as e:
            return False, f"Failed to terminate instance {instance_id}: {str(e)}"
    
    def list_instances(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """
        List all instances with optional status filter.
        
        Args:
            status_filter: Filter by status (starting, running, completed, failed, killed)
            
        Returns:
            List of instance status information
        """
        instances = []
        
        for instance_id, instance in self.running_instances.items():
            status_info = self.get_instance_status(instance_id)
            
            if status_filter is None or status_info.get("status") == status_filter:
                instances.append(status_info)
        
        # Sort by started_at, newest first
        instances.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        
        return instances
    
    def cleanup_completed_instances(self, max_age_hours: int = 24) -> List[str]:
        """
        Cleanup completed instances older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age for keeping completed instances
            
        Returns:
            List of cleaned up instance IDs
        """
        cleaned_instances = []
        current_time = datetime.now()
        
        for instance_id, instance in list(self.running_instances.items()):
            if instance.status in ['completed', 'failed', 'killed']:
                try:
                    start_time = datetime.fromisoformat(instance.started_at)
                    age_hours = (current_time - start_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        # Remove from registry
                        del self.running_instances[instance_id]
                        cleaned_instances.append(instance_id)
                        
                        # Optionally clean up files
                        log_file = Path(instance.log_file)
                        if log_file.exists():
                            log_file.unlink()
                        
                        # Note: We keep CLAUDE.md and context files as they might be useful
                        # They can be cleaned up manually if needed
                            
                except Exception as e:
                    print(f"Warning: Failed to cleanup instance {instance_id}: {e}")
        
        if cleaned_instances:
            self._save_registry()
        
        return cleaned_instances
    
    def _start_monitoring_thread(self):
        """Start background monitoring thread for instance health."""
        def monitoring_loop():
            while True:
                try:
                    time.sleep(30)  # Check every 30 seconds
                    self._update_instance_statuses()
                except Exception as e:
                    print(f"Warning: Monitoring thread error: {e}")
                    
        thread = threading.Thread(target=monitoring_loop, daemon=True)
        thread.start()
    
    def _update_instance_statuses(self):
        """Update status of all running instances."""
        current_time = datetime.now()
        updated = False
        
        for instance_id, instance in self.running_instances.items():
            if instance.status in ['starting', 'running']:
                # Check if process is still running
                if not self._is_process_running(instance.process_id):
                    instance.status = "completed"
                    instance.completion_data = self._collect_completion_data(instance)
                    updated = True
                    
                # Check for timeout
                elif instance.status == "running" and instance.config:
                    try:
                        start_time = datetime.fromisoformat(instance.started_at)
                        runtime_minutes = (current_time - start_time).total_seconds() / 60
                        
                        if runtime_minutes > instance.config.timeout_minutes:
                            # Kill timed out instance gracefully
                            try:
                                os.kill(instance.process_id, signal.SIGTERM)
                                time.sleep(3)
                                if self._is_process_running(instance.process_id):
                                    os.kill(instance.process_id, signal.SIGKILL)
                            except:
                                pass
                            
                            instance.status = "timeout"
                            instance.completion_data = {
                                "timeout_at": current_time.isoformat(),
                                "runtime_minutes": runtime_minutes,
                                "timeout_limit": instance.config.timeout_minutes
                            }
                            updated = True
                    except:
                        pass
        
        if updated:
            self._save_registry()
    
    def get_optimization_results(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get optimization results from completed instance.
        
        Args:
            instance_id: Instance to get results from
            
        Returns:
            Optimization results or None if not available
        """
        if instance_id not in self.running_instances:
            return None
        
        instance = self.running_instances[instance_id]
        
        try:
            worktree_path = Path(instance.worktree_path)
            results_file = worktree_path / ".claude" / "optimization_results.json"
            
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                # Add metadata
                results["_metadata"] = {
                    "instance_id": instance_id,
                    "retrieved_at": datetime.now().isoformat(),
                    "worktree_path": str(worktree_path),
                    "claude_md_path": instance.claude_md_path
                }
                
                return results
            
            return None
            
        except Exception as e:
            return {"error": f"Failed to read results: {str(e)}"}
    
    def get_instance_logs(self, instance_id: str, tail_lines: int = 50) -> Optional[str]:
        """
        Get recent log output from instance.
        
        Args:
            instance_id: Instance to get logs from
            tail_lines: Number of lines to return from end of log
            
        Returns:
            Log content or None if not available
        """
        if instance_id not in self.running_instances:
            return None
        
        instance = self.running_instances[instance_id]
        log_file = Path(instance.log_file)
        
        if not log_file.exists():
            return "Log file not found"
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            if tail_lines and len(lines) > tail_lines:
                return ''.join(lines[-tail_lines:])
            else:
                return ''.join(lines)
                
        except Exception as e:
            return f"Error reading log: {str(e)}"


# CLI Interface with enhanced functionality
def main():
    """Enhanced command-line interface for Claude Instance Launcher."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Claude Instance Launcher for OpenEvolve - Official Claude Code Integration",
        epilog="Uses official Claude Code CLI with git worktrees and CLAUDE.md memory files"
    )
    parser.add_argument("command", choices=[
        "launch", "status", "kill", "list", "cleanup", "results", "logs"
    ])
    
    # Launch command arguments
    parser.add_argument("--code-file", help="File containing code to optimize")
    parser.add_argument("--language", default="python", help="Programming language")
    parser.add_argument("--worktree", help="Git worktree path")
    parser.add_argument("--background", action="store_true", default=True, help="Run in background")
    parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in minutes")
    parser.add_argument("--target-metrics", nargs="+", help="Optimization target metrics", 
                       choices=["performance", "memory", "readability", "maintainability"])
    
    # General arguments
    parser.add_argument("--instance-id", help="Instance ID for operations")
    parser.add_argument("--status-filter", help="Filter instances by status",
                       choices=["starting", "running", "completed", "failed", "killed", "timeout"])
    parser.add_argument("--max-age-hours", type=int, default=24, help="Max age for cleanup")
    parser.add_argument("--force", action="store_true", help="Force kill instance")
    parser.add_argument("--tail", type=int, default=50, help="Number of log lines to show")
    
    args = parser.parse_args()
    
    # Handle foreground override
    if args.foreground:
        args.background = False
    
    launcher = ClaudeInstanceLauncher()
    
    if args.command == "launch":
        if not args.code_file:
            print("❌ Error: --code-file required for launch")
            return 1
        
        try:
            with open(args.code_file, 'r') as f:
                code = f.read()
        except Exception as e:
            print(f"❌ Error reading code file: {e}")
            return 1
        
        # Prepare optimization parameters
        optimization_params = {}
        if args.target_metrics:
            optimization_params["target_metrics"] = args.target_metrics
        
        success, message, instance_id = launcher.launch_optimization_instance(
            code=code,
            language=args.language,
            worktree_path=args.worktree,
            optimization_params=optimization_params,
            background=args.background,
            timeout_minutes=args.timeout
        )
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            return 1
    
    elif args.command == "status":
        if not args.instance_id:
            print("❌ Error: --instance-id required for status")
            return 1
        
        status = launcher.get_instance_status(args.instance_id)
        if status:
            print(json.dumps(status, indent=2))
        else:
            print(f"❌ Instance {args.instance_id} not found")
            return 1
    
    elif args.command == "list":
        instances = launcher.list_instances(args.status_filter)
        if instances:
            print(f"Claude Code Instances ({len(instances)}):")
            print("=" * 80)
            for instance in instances:
                status_icon = {
                    "starting": "🚀", "running": "⚡", "completed": "✅",
                    "failed": "❌", "killed": "💀", "timeout": "⏰"
                }.get(instance["status"], "❓")
                
                print(f"{status_icon} {instance['instance_id']}")
                print(f"   Status: {instance['status'].upper()}")
                print(f"   Language: {instance['language']}")
                print(f"   Started: {instance['started_at']}")
                if "runtime_formatted" in instance:
                    print(f"   Runtime: {instance['runtime_formatted']}")
                print(f"   Worktree: {instance['worktree_path']}")
                print(f"   CLAUDE.md: {instance.get('claude_md_path', 'N/A')}")
                if instance.get('optimization_focus'):
                    print(f"   Focus: {', '.join(instance['optimization_focus'])}")
                print(f"   Log: {instance['log_file']}")
                print()
        else:
            status_text = f" with status '{args.status_filter}'" if args.status_filter else ""
            print(f"No Claude instances found{status_text}")
    
    elif args.command == "kill":
        if not args.instance_id:
            print("❌ Error: --instance-id required for kill")
            return 1
        
        success, message = launcher.kill_instance(args.instance_id, args.force)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            return 1
    
    elif args.command == "cleanup":
        cleaned = launcher.cleanup_completed_instances(args.max_age_hours)
        if cleaned:
            print(f"✅ Cleaned up {len(cleaned)} instances:")
            for instance_id in cleaned:
                print(f"  - {instance_id}")
        else:
            print("No instances to clean up")
    
    elif args.command == "results":
        if not args.instance_id:
            print("❌ Error: --instance-id required for results")
            return 1
        
        results = launcher.get_optimization_results(args.instance_id)
        if results:
            if "error" in results:
                print(f"❌ {results['error']}")
                return 1
            else:
                print("🎯 OPTIMIZATION RESULTS")
                print("=" * 50)
                print(json.dumps(results, indent=2))
        else:
            print(f"❌ No results available for instance {args.instance_id}")
            return 1
    
    elif args.command == "logs":
        if not args.instance_id:
            print("❌ Error: --instance-id required for logs")
            return 1
        
        logs = launcher.get_instance_logs(args.instance_id, args.tail)
        if logs:
            print(f"📝 LOGS for {args.instance_id} (last {args.tail} lines)")
            print("=" * 80)
            print(logs)
        else:
            print(f"❌ No logs available for instance {args.instance_id}")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())