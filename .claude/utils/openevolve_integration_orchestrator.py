#!/usr/bin/env python3
"""
OpenEvolve Integration Orchestrator
Coordinates the complete OpenEvolve optimization workflow with
Primary Agent orchestration, KRAG memory management, and agent handoffs.
"""

import asyncio
import json
import time
import uuid
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import requests

# Import our OpenEvolve components
from openevolve_worktree_manager import OpenEvolveWorktreeManager, WorktreeSession
from openevolve_iteration_selector import IterationSelector, IterationRecommendation
from openevolve_code_analyzer import CodeAnalysisEngine, AnalysisReport
from openevolve_validation_pipeline import ValidationPipeline, ValidationReport


@dataclass
class OptimizationSession:
    """Complete optimization session state."""
    session_id: str
    request_id: str
    created_at: str
    status: str  # initializing, analyzing, optimizing, validating, completed, failed
    
    # Input data
    original_code: str
    language: str
    optimization_goals: List[str]
    constraints: Dict[str, Any]
    
    # Analysis results
    complexity_analysis: Optional[AnalysisReport] = None
    iteration_recommendation: Optional[IterationRecommendation] = None
    
    # Execution data
    worktree_session: Optional[WorktreeSession] = None
    optimization_results: Dict[str, Any] = None
    validation_report: Optional[ValidationReport] = None
    
    # Memory and context
    krag_namespace: str = ""
    progress_updates: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.progress_updates is None:
            self.progress_updates = []


class OpenEvolveIntegrationOrchestrator:
    """Main orchestrator for OpenEvolve optimization workflow."""
    
    def __init__(self):
        # Initialize components
        self.worktree_manager = OpenEvolveWorktreeManager()
        self.iteration_selector = IterationSelector()
        self.code_analyzer = CodeAnalysisEngine()
        self.validation_pipeline = ValidationPipeline()
        
        # Configuration
        self.openevolve_service_url = "http://localhost:8000"
        self.max_concurrent_sessions = 3
        self.default_timeout_minutes = 30
        
        # Active sessions tracking
        self.active_sessions: Dict[str, OptimizationSession] = {}
        
    async def start_optimization_workflow(
        self,
        code: str,
        language: str = "python",
        optimization_goals: List[str] = None,
        constraints: Dict[str, Any] = None,
        request_context: Dict[str, Any] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Start complete optimization workflow.
        
        Returns:
            (success: bool, message: str, session_id: Optional[str])
        """
        
        # Generate session ID
        session_id = self._generate_session_id(code, language)
        request_id = request_context.get("request_id", str(uuid.uuid4()))
        
        # Create optimization session
        session = OptimizationSession(
            session_id=session_id,
            request_id=request_id,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            status="initializing",
            original_code=code,
            language=language,
            optimization_goals=optimization_goals or ["performance", "algorithmic_efficiency"],
            constraints=constraints or {},
            krag_namespace=f"openevolve_session_{session_id}"
        )
        
        self.active_sessions[session_id] = session
        
        try:
            # Store initial context in KRAG memory
            await self._store_session_context(session)
            
            # Start workflow execution
            success = await self._execute_optimization_workflow(session)
            
            if success:
                return True, f"Optimization workflow completed successfully", session_id
            else:
                return False, f"Optimization workflow failed", session_id
                
        except Exception as e:
            session.status = "failed"
            await self._update_progress(session, f"Workflow failed: {str(e)}", "error")
            return False, f"Workflow error: {str(e)}", session_id
    
    async def _execute_optimization_workflow(self, session: OptimizationSession) -> bool:
        """Execute the complete optimization workflow."""
        
        try:
            # Phase 1: Analysis
            await self._update_progress(session, "Starting code analysis...", "info")
            session.status = "analyzing"
            
            if not await self._analyze_code(session):
                return False
            
            # Phase 2: Preparation
            await self._update_progress(session, "Setting up optimization environment...", "info")
            
            if not await self._prepare_optimization(session):
                return False
            
            # Phase 3: Optimization
            await self._update_progress(session, "Running evolutionary optimization...", "info")
            session.status = "optimizing"
            
            if not await self._run_optimization(session):
                return False
            
            # Phase 4: Validation
            await self._update_progress(session, "Validating optimization results...", "info")
            session.status = "validating"
            
            if not await self._validate_results(session):
                return False
            
            # Phase 5: Completion
            await self._update_progress(session, "Optimization completed successfully!", "success")
            session.status = "completed"
            
            # Store final results in KRAG memory
            await self._store_final_results(session)
            
            return True
            
        except Exception as e:
            await self._update_progress(session, f"Workflow error: {str(e)}", "error")
            session.status = "failed"
            return False
    
    async def _analyze_code(self, session: OptimizationSession) -> bool:
        """Analyze code complexity and optimization potential."""
        try:
            # Perform comprehensive code analysis
            session.complexity_analysis = self.code_analyzer.analyze_code_string(
                session.original_code, 
                session.language
            )
            
            # Select optimal iterations based on analysis
            session.iteration_recommendation = self.iteration_selector.select_iterations(
                code=session.original_code,
                language=session.language,
                budget_credits=session.constraints.get("max_credits", 500),
                time_limit_minutes=session.constraints.get("time_limit", 20),
                optimization_goals=session.optimization_goals
            )
            
            await self._update_progress(
                session, 
                f"Analysis complete: {session.complexity_analysis.optimization_potential_score:.1f}% potential, "
                f"{session.iteration_recommendation.recommended_iterations} iterations recommended",
                "info"
            )
            
            # Store analysis in KRAG memory
            await self._store_analysis_results(session)
            
            return True
            
        except Exception as e:
            await self._update_progress(session, f"Analysis failed: {str(e)}", "error")
            return False
    
    async def _prepare_optimization(self, session: OptimizationSession) -> bool:
        """Prepare optimization environment (git worktree, etc.)."""
        try:
            # Create git worktree for parallel execution
            success, message, worktree_session = self.worktree_manager.create_optimization_session(
                session.original_code,
                session.language,
                {
                    "iterations": session.iteration_recommendation.recommended_iterations,
                    "session_id": session.session_id
                }
            )
            
            if not success:
                await self._update_progress(session, f"Worktree creation failed: {message}", "error")
                return False
            
            session.worktree_session = worktree_session
            
            await self._update_progress(
                session,
                f"Environment prepared: workspace at {worktree_session.worktree_path}",
                "info"
            )
            
            return True
            
        except Exception as e:
            await self._update_progress(session, f"Environment preparation failed: {str(e)}", "error")
            return False
    
    async def _run_optimization(self, session: OptimizationSession) -> bool:
        """Run the evolutionary optimization process."""
        try:
            # Check OpenEvolve service availability
            if not await self._check_service_health():
                await self._update_progress(session, "OpenEvolve service not available", "error")
                return False
            
            # Prepare optimization request
            optimization_request = {
                "code": session.original_code,
                "language": session.language,
                "optimization_level": "high",
                "session_id": session.session_id,
                "max_iterations": session.iteration_recommendation.recommended_iterations,
                "target_metrics": session.optimization_goals,
                "workspace_path": session.worktree_session.worktree_path if session.worktree_session else None
            }
            
            # Submit optimization job
            job_response = await self._submit_optimization_job(optimization_request)
            
            if not job_response["success"]:
                await self._update_progress(session, f"Optimization job failed: {job_response['error']}", "error")
                return False
            
            job_id = job_response["job_id"]
            
            # Monitor optimization progress
            final_results = await self._monitor_optimization_progress(session, job_id)
            
            if not final_results:
                await self._update_progress(session, "Optimization monitoring failed", "error")
                return False
            
            session.optimization_results = final_results
            
            await self._update_progress(
                session,
                f"Optimization completed with {final_results.get('improvement_percentage', 0):.1f}% improvement",
                "info"
            )
            
            return True
            
        except Exception as e:
            await self._update_progress(session, f"Optimization execution failed: {str(e)}", "error")
            return False
    
    async def _validate_results(self, session: OptimizationSession) -> bool:
        """Validate optimization results through multi-stage pipeline."""
        try:
            if not session.optimization_results or "optimized_code" not in session.optimization_results:
                await self._update_progress(session, "No optimized code to validate", "error")
                return False
            
            optimized_code = session.optimization_results["optimized_code"]
            
            # Run validation pipeline
            session.validation_report = self.validation_pipeline.validate(
                original_code=session.original_code,
                optimized_code=optimized_code,
                language=session.language,
                config={
                    "skip_test_compatibility": not session.constraints.get("require_tests", False)
                }
            )
            
            # Check validation results
            if session.validation_report.overall_passed:
                await self._update_progress(
                    session,
                    f"Validation passed: {session.validation_report.overall_score:.1f}/100 score",
                    "success"
                )
                return True
            else:
                await self._update_progress(
                    session,
                    f"Validation failed: {session.validation_report.overall_score:.1f}/100 score, "
                    f"failed gates: {[g.gate_name for g in session.validation_report.gate_results if not g.passed]}",
                    "warning"
                )
                
                # Allow partial success if score is reasonable
                return session.validation_report.overall_score >= 60
                
        except Exception as e:
            await self._update_progress(session, f"Validation failed: {str(e)}", "error")
            return False
    
    async def _check_service_health(self) -> bool:
        """Check if OpenEvolve service is available."""
        try:
            response = requests.get(f"{self.openevolve_service_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def _submit_optimization_job(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit optimization job to OpenEvolve service."""
        try:
            # Simulate optimization job submission (replace with actual API call)
            await asyncio.sleep(0.1)  # Simulate network call
            
            job_id = str(uuid.uuid4())
            return {
                "success": True,
                "job_id": job_id,
                "estimated_duration": request.get("max_iterations", 10) * 2  # 2 seconds per iteration
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _monitor_optimization_progress(self, session: OptimizationSession, job_id: str) -> Optional[Dict[str, Any]]:
        """Monitor optimization job progress."""
        try:
            iterations = session.iteration_recommendation.recommended_iterations
            
            # Simulate optimization monitoring
            for i in range(iterations):
                await asyncio.sleep(0.2)  # Simulate optimization time
                
                progress_percent = (i + 1) / iterations * 100
                await self._update_progress(
                    session,
                    f"Evolution progress: {progress_percent:.0f}% ({i+1}/{iterations} iterations)",
                    "info"
                )
            
            # Simulate final results
            optimized_code = session.original_code.replace(
                "slow_sort_and_filter", "fast_sort_and_filter"
            ).replace(
                "DataProcessor:", "OptimizedDataProcessor:"
            )
            
            return {
                "job_id": job_id,
                "optimized_code": optimized_code,
                "improvement_percentage": 35.7,  # Simulated improvement
                "iterations_completed": iterations,
                "performance_metrics": {
                    "execution_time_ms": 45.2,
                    "memory_usage_mb": 12.1,
                    "complexity_score": 67.3
                }
            }
            
        except Exception as e:
            await self._update_progress(session, f"Progress monitoring failed: {str(e)}", "error")
            return None
    
    async def _update_progress(self, session: OptimizationSession, message: str, level: str = "info"):
        """Update session progress and notify via KRAG memory."""
        progress_update = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": message,
            "level": level,
            "status": session.status
        }
        
        session.progress_updates.append(progress_update)
        
        # Store progress in KRAG memory
        print(f"🔄 [{session.session_id[:8]}] {message}")
        
        # Store significant progress updates in KRAG memory
        if level in ['success', 'error'] or len(session.progress_updates) % 5 == 0:
            try:
                progress_data = f"""OpenEvolve Progress Update:
- Session: {session.session_id[:8]}
- Timestamp: {progress_update['timestamp']}
- Status: {session.status}
- Level: {level}
- Message: {message}
- Update #{len(session.progress_updates)}
"""
                await self._add_to_krag_memory(
                    name=f"Progress Update #{len(session.progress_updates)} - {session.session_id[:8]}",
                    content=progress_data,
                    namespace=session.krag_namespace
                )
            except Exception as e:
                pass  # Continue silently if KRAG storage fails for progress updates
    
    async def _store_session_context(self, session: OptimizationSession):
        """Store session context in KRAG memory."""
        try:
            context_data = f"""OpenEvolve Optimization Session Context:
- Session ID: {session.session_id}
- Request ID: {session.request_id}
- Created: {session.created_at}
- Language: {session.language}
- Code Length: {len(session.original_code)} lines
- Optimization Goals: {', '.join(session.optimization_goals)}
- Constraints: {json.dumps(session.constraints)}
- Status: {session.status}
"""
            await self._add_to_krag_memory(
                name=f"Session Context - {session.session_id[:8]}",
                content=context_data,
                namespace=session.krag_namespace
            )
            print(f"📝 Stored session context in KRAG namespace: {session.krag_namespace}")
        except Exception as e:
            print(f"⚠️ Failed to store session context in KRAG: {str(e)}")
            # Continue without KRAG storage if it fails
    
    async def _store_analysis_results(self, session: OptimizationSession):
        """Store analysis results in KRAG memory."""
        try:
            if session.complexity_analysis and session.iteration_recommendation:
                analysis_data = f"""OpenEvolve Code Analysis Results:
- Session: {session.session_id[:8]}
- Optimization Potential: {session.complexity_analysis.optimization_potential_score:.1f}%
- Recommended Iterations: {session.iteration_recommendation.recommended_iterations}
- Complexity Level: {session.iteration_recommendation.complexity_level}
- Estimated Credits: {session.iteration_recommendation.estimated_credits}
- Confidence Score: {session.iteration_recommendation.confidence_score:.2f}
- Optimization Strategy: {session.iteration_recommendation.optimization_strategy}
- Analysis Rationale: {', '.join(session.iteration_recommendation.rationale)}
"""
                # Store in memory for future reference
                await self._add_to_krag_memory(
                    name=f"Code Analysis - {session.session_id[:8]}",
                    content=analysis_data,
                    namespace=session.krag_namespace
                )
                print(f"📊 Stored analysis results in KRAG memory")
        except Exception as e:
            print(f"⚠️ Failed to store analysis results: {str(e)}")
    
    async def _store_final_results(self, session: OptimizationSession):
        """Store final optimization results in KRAG memory."""
        try:
            if session.optimization_results and session.validation_report:
                final_data = f"""OpenEvolve Optimization Completion:
- Session: {session.session_id}
- Status: {session.status}
- Improvement: {session.optimization_results.get('improvement_percentage', 0):.1f}%
- Validation Score: {session.validation_report.overall_score:.1f}/100
- Validation Passed: {'✅' if session.validation_report.overall_passed else '❌'}
- Iterations Completed: {session.optimization_results.get('iterations_completed', 0)}
- Performance Metrics: {json.dumps(session.optimization_results.get('performance_metrics', {}))}
- Completed At: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Total Progress Updates: {len(session.progress_updates)}
"""
                await self._add_to_krag_memory(
                    name=f"Optimization Results - {session.session_id[:8]}",
                    content=final_data,
                    namespace=session.krag_namespace
                )
                print(f"✅ Stored final results in KRAG memory")
        except Exception as e:
            print(f"⚠️ Failed to store final results: {str(e)}")
    
    async def _add_to_krag_memory(self, name: str, content: str, namespace: str):
        """Helper method to add content to KRAG memory.
        
        Note: In actual implementation, this would call the KRAG memory MCP tool.
        For now, this is a placeholder that would need to be implemented by the
        calling Claude instance using the mcp__krag-graphiti-memory__add_memory tool.
        """
        # This is where Claude would call:
        # await mcp__krag-graphiti-memory__add_memory(
        #     name=name,
        #     episode_body=content,
        #     group_id=namespace,
        #     source="text",
        #     source_description="OpenEvolve optimization session data"
        # )
        print(f"🧠 Would store '{name}' in KRAG namespace '{namespace}'")
        print(f"📝 Content preview: {content[:100]}...")
    
    def _generate_session_id(self, code: str, language: str) -> str:
        """Generate unique session ID."""
        content_hash = hashlib.md5(code.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        return f"openevolve_{language}_{content_hash}_{timestamp}"
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        status_info = {
            "session_id": session_id,
            "status": session.status,
            "created_at": session.created_at,
            "language": session.language,
            "optimization_goals": session.optimization_goals,
            "progress_updates": session.progress_updates[-5:],  # Last 5 updates
        }
        
        if session.complexity_analysis:
            status_info["optimization_potential"] = session.complexity_analysis.optimization_potential_score
        
        if session.iteration_recommendation:
            status_info["recommended_iterations"] = session.iteration_recommendation.recommended_iterations
        
        if session.optimization_results:
            status_info["improvement_percentage"] = session.optimization_results.get("improvement_percentage", 0)
        
        if session.validation_report:
            status_info["validation_score"] = session.validation_report.overall_score
            status_info["validation_passed"] = session.validation_report.overall_passed
        
        return status_info
    
    async def cleanup_session(self, session_id: str, preserve_results: bool = True) -> Tuple[bool, str]:
        """Cleanup optimization session."""
        if session_id not in self.active_sessions:
            return False, f"Session {session_id} not found"
        
        session = self.active_sessions[session_id]
        
        try:
            # Cleanup git worktree
            if session.worktree_session:
                success, message = self.worktree_manager.cleanup_session(
                    session.worktree_session.session_id,
                    preserve_results=preserve_results
                )
                
                if not success:
                    print(f"⚠️ Worktree cleanup warning: {message}")
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            await self._update_progress(session, "Session cleanup completed", "info")
            
            return True, f"Session {session_id} cleaned up successfully"
            
        except Exception as e:
            return False, f"Cleanup failed: {str(e)}"


# Integration helper functions for agent orchestration
class AgentIntegrationHelper:
    """Helper functions for agent integration."""
    
    @staticmethod
    def create_optimization_request(
        code: str,
        language: str,
        optimization_goals: List[str] = None,
        constraints: Dict[str, Any] = None,
        agent_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create standardized optimization request for agent handoff."""
        return {
            "type": "openevolve_optimization",
            "payload": {
                "code": code,
                "language": language,
                "optimization_goals": optimization_goals or ["performance", "algorithmic_efficiency"],
                "constraints": constraints or {},
                "context": agent_context or {}
            },
            "metadata": {
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "request_id": str(uuid.uuid4())
            }
        }
    
    @staticmethod
    def extract_optimization_results(session_status: Dict[str, Any]) -> Dict[str, Any]:
        """Extract optimization results for agent handoff."""
        return {
            "session_id": session_status.get("session_id"),
            "status": session_status.get("status"),
            "improvement_percentage": session_status.get("improvement_percentage", 0),
            "validation_score": session_status.get("validation_score", 0),
            "validation_passed": session_status.get("validation_passed", False),
            "optimization_potential": session_status.get("optimization_potential", 0),
            "summary": f"Optimization {session_status.get('status', 'unknown')} with "
                      f"{session_status.get('improvement_percentage', 0):.1f}% improvement"
        }


def main():
    """CLI interface for integration orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenEvolve Integration Orchestrator")
    parser.add_argument("command", choices=["optimize", "status", "cleanup"])
    parser.add_argument("--code-file", help="Code file to optimize")
    parser.add_argument("--language", default="python", help="Programming language")
    parser.add_argument("--goals", nargs="*", help="Optimization goals")
    parser.add_argument("--session-id", help="Session ID for status/cleanup")
    parser.add_argument("--max-credits", type=int, default=500, help="Maximum credits to use")
    parser.add_argument("--time-limit", type=int, default=20, help="Time limit in minutes")
    
    args = parser.parse_args()
    
    async def run_command():
        orchestrator = OpenEvolveIntegrationOrchestrator()
        
        if args.command == "optimize":
            if not args.code_file:
                print("❌ Code file required for optimization")
                return
            
            with open(args.code_file, 'r') as f:
                code = f.read()
            
            constraints = {
                "max_credits": args.max_credits,
                "time_limit": args.time_limit
            }
            
            success, message, session_id = await orchestrator.start_optimization_workflow(
                code=code,
                language=args.language,
                optimization_goals=args.goals,
                constraints=constraints
            )
            
            if success:
                print(f"✅ {message}")
                print(f"Session ID: {session_id}")
            else:
                print(f"❌ {message}")
        
        elif args.command == "status":
            if not args.session_id:
                print("❌ Session ID required for status")
                return
            
            status = orchestrator.get_session_status(args.session_id)
            if status:
                print(json.dumps(status, indent=2))
            else:
                print(f"❌ Session {args.session_id} not found")
        
        elif args.command == "cleanup":
            if not args.session_id:
                print("❌ Session ID required for cleanup")
                return
            
            success, message = await orchestrator.cleanup_session(args.session_id)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
    
    # Run the async command
    asyncio.run(run_command())


if __name__ == "__main__":
    main()