#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"  
# dependencies = [
#     "asyncio",
#     "aiohttp", 
#     "python-dotenv",
#     "typing-extensions",
#     "pydantic>=2.0",
#     "numpy",
#     "scikit-learn",
# ]
# ///

"""
Primary Agent GitHub Controller - Enterprise Multi-Agent Orchestration

Advanced coordination layer for GitHub operations with:
- HANDOFF_TOKEN system with semantic validation
- KRAG-based context assembly and agent coordination
- Quality gates with semantic scoring thresholds  
- Multi-agent workflow orchestration with conflict resolution
- Circuit breaker patterns for resilience
- Saga pattern for transaction-like rollback capabilities
- Performance monitoring and observability integration

Architecture Patterns:
- Orchestrator: Central coordination hub
- Command: Structured operation delegation
- Circuit Breaker: Error resilience
- Saga: Transaction coordination with rollback
"""

import asyncio
import json
import os
import sys
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import re
import time
from contextlib import asynccontextmanager

try:
    import aiohttp
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"Missing dependencies: {e}")
    sys.exit(1)

# Add project paths for existing integrations
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "utils"))

try:
    # Existing integrations
    from github_service import GitHubService, GitHubConfig, GitHubAPIError
    from event_bus import GitHubEventBus, GitHubEvent, EventType, EventMetadata
    from constants import ensure_session_log_dir, get_session_log_dir
    from observability_sender import send_observability_event
except ImportError as e:
    print(f"Integration module import error: {e}")
    # Fallback implementations for development
    def ensure_session_log_dir(session_id: str) -> Path:
        log_dir = Path("logs") / session_id
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def send_observability_event(event_type: str, payload: Dict[str, Any], **kwargs) -> bool:
        return True


# ============================================================================
# CORE DATA STRUCTURES AND ENUMS
# ============================================================================

class AgentCapability(Enum):
    """Agent capability categories for intelligent routing."""
    GITHUB_OPERATIONS = "github_operations"
    CODE_ANALYSIS = "code_analysis"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ARCHITECTURE_DESIGN = "architecture_design"
    DATABASE_OPERATIONS = "database_operations"
    DEVOPS_AUTOMATION = "devops_automation"
    AI_ML_INTEGRATION = "ai_ml_integration"
    UI_UX_DESIGN = "ui_ux_design"
    TESTING_VALIDATION = "testing_validation"


class OperationType(Enum):
    """GitHub operation types for agent delegation."""
    REPOSITORY_ANALYSIS = "repository_analysis"
    PULL_REQUEST_CREATION = "pull_request_creation"
    ISSUE_MANAGEMENT = "issue_management"
    WORKFLOW_AUTOMATION = "workflow_automation"
    SECURITY_SCANNING = "security_scanning"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    CODE_REVIEW = "code_review"
    DEPLOYMENT_COORDINATION = "deployment_coordination"
    INCIDENT_RESPONSE = "incident_response"


class QualityGateType(Enum):
    """Quality gate types for validation pipeline."""
    PLANNING = "planning_gate"
    SECURITY = "security_gate"
    PERFORMANCE = "performance_gate"
    ARCHITECTURE = "architecture_gate"
    TESTING = "testing_gate"
    COMPLIANCE = "compliance_gate"
    DEPLOYMENT = "deployment_gate"


class HandoffTokenStatus(Enum):
    """HANDOFF_TOKEN lifecycle status."""
    CREATED = "created"
    VALIDATED = "validated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    ROLLBACK_INITIATED = "rollback_initiated"
    ROLLBACK_COMPLETED = "rollback_completed"


class CircuitBreakerState(Enum):
    """Circuit breaker states for resilience."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class AgentDefinition:
    """Agent definition with capabilities and routing information."""
    agent_name: str
    capabilities: List[AgentCapability]
    operation_types: List[OperationType]
    tools_available: List[str]
    max_concurrent_tasks: int = 3
    performance_score: float = 1.0
    priority: int = 1  # 1=highest, 5=lowest
    specialization_domains: List[str] = field(default_factory=list)
    integration_dependencies: List[str] = field(default_factory=list)


@dataclass 
class HandoffToken:
    """KRAG-based agent coordination token with semantic validation."""
    token_id: str
    source_agent: str
    target_agent: str
    operation_type: OperationType
    context_vector: Optional[List[float]]
    semantic_context: Dict[str, Any]
    validation_criteria: List[str]
    status: HandoffTokenStatus
    created_at: datetime
    expires_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    rollback_data: Optional[Dict[str, Any]] = None
    quality_gates: List[QualityGateType] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries and not self.is_expired()
    
    def to_krag_entity(self) -> Dict[str, Any]:
        """Convert to KRAG entity format for storage."""
        return {
            "entity_type": "handoff_token",
            "token_id": self.token_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "operation_type": self.operation_type.value,
            "context_vector": self.context_vector,
            "semantic_context": self.semantic_context,
            "validation_criteria": self.validation_criteria,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "rollback_data": self.rollback_data,
            "quality_gates": [gate.value for gate in self.quality_gates],
            "dependencies": self.dependencies
        }


@dataclass
class QualityGate:
    """Semantic quality gate with KRAG graph enforcement."""
    gate_type: QualityGateType
    validation_criteria: List[str]
    threshold_score: float = 0.80
    status: str = "pending"  # pending, passed, failed
    validation_results: Dict[str, Any] = field(default_factory=dict)
    failure_reasons: List[str] = field(default_factory=list)
    blocking_dependencies: List[QualityGateType] = field(default_factory=list)
    semantic_validator: Optional[Callable] = None


@dataclass
class CircuitBreaker:
    """Circuit breaker for agent resilience."""
    agent_name: str
    failure_threshold: int = 5
    timeout_seconds: int = 60
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    success_threshold: int = 3  # For half-open state
    consecutive_successes: int = 0


@dataclass
class AgentWorkflowSaga:
    """Saga pattern for transaction-like coordination."""
    saga_id: str
    workflow_name: str
    participating_agents: List[str]
    operations: List[Dict[str, Any]]
    completed_operations: List[Dict[str, Any]] = field(default_factory=list)
    rollback_operations: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "in_progress"  # in_progress, completed, rolling_back, failed
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# AGENT CAPABILITY MATRIX AND ROUTING
# ============================================================================

class AgentCapabilityMatrix:
    """Agent capability matrix for intelligent operation routing."""
    
    def __init__(self):
        self.agents = self._initialize_agent_definitions()
        self.capability_index = self._build_capability_index()
    
    def _initialize_agent_definitions(self) -> Dict[str, AgentDefinition]:
        """Initialize comprehensive agent definitions."""
        return {
            # Core Development Team
            "planner": AgentDefinition(
                agent_name="planner",
                capabilities=[AgentCapability.ARCHITECTURE_DESIGN],
                operation_types=[OperationType.REPOSITORY_ANALYSIS],
                tools_available=["shrimp-task-manager", "krag-graphiti-memory"],
                specialization_domains=["project-management", "system-design"]
            ),
            
            "coder": AgentDefinition(
                agent_name="coder",
                capabilities=[AgentCapability.CODE_ANALYSIS, AgentCapability.GITHUB_OPERATIONS],
                operation_types=[OperationType.PULL_REQUEST_CREATION, OperationType.CODE_REVIEW],
                tools_available=["Read", "Write", "Bash", "git-mcp"],
                specialization_domains=["full-stack-development", "clean-code"]
            ),
            
            "code-reviewer": AgentDefinition(
                agent_name="code-reviewer", 
                capabilities=[AgentCapability.CODE_ANALYSIS, AgentCapability.SECURITY_AUDIT],
                operation_types=[OperationType.CODE_REVIEW, OperationType.SECURITY_SCANNING],
                tools_available=["git-mcp", "context7"],
                specialization_domains=["code-quality", "security-analysis"]
            ),
            
            # Architecture & Design Specialists
            "backend-architect": AgentDefinition(
                agent_name="backend-architect",
                capabilities=[AgentCapability.ARCHITECTURE_DESIGN, AgentCapability.DATABASE_OPERATIONS],
                operation_types=[OperationType.REPOSITORY_ANALYSIS, OperationType.PERFORMANCE_ANALYSIS],
                tools_available=["context7", "krag-graphiti-memory", "git-mcp"],
                specialization_domains=["api-design", "microservices", "scalability"]
            ),
            
            "cloud-architect": AgentDefinition(
                agent_name="cloud-architect",
                capabilities=[AgentCapability.DEVOPS_AUTOMATION, AgentCapability.ARCHITECTURE_DESIGN],
                operation_types=[OperationType.WORKFLOW_AUTOMATION, OperationType.DEPLOYMENT_COORDINATION],
                tools_available=["Bash", "context7", "git-mcp"],
                specialization_domains=["infrastructure-as-code", "cost-optimization"]
            ),
            
            "security-specialist": AgentDefinition(
                agent_name="security-specialist",
                capabilities=[AgentCapability.SECURITY_AUDIT],
                operation_types=[OperationType.SECURITY_SCANNING, OperationType.INCIDENT_RESPONSE],
                tools_available=["git-mcp", "context7"],
                specialization_domains=["vulnerability-assessment", "compliance"]
            ),
            
            # Language & Technology Experts
            "python-pro": AgentDefinition(
                agent_name="python-pro",
                capabilities=[AgentCapability.CODE_ANALYSIS, AgentCapability.PERFORMANCE_OPTIMIZATION],
                operation_types=[OperationType.CODE_REVIEW, OperationType.PERFORMANCE_ANALYSIS],
                tools_available=["Read", "Write", "Bash", "context7"],
                specialization_domains=["python", "performance-tuning"]
            ),
            
            "ai-engineer": AgentDefinition(
                agent_name="ai-engineer",
                capabilities=[AgentCapability.AI_ML_INTEGRATION, AgentCapability.CODE_ANALYSIS],
                operation_types=[OperationType.REPOSITORY_ANALYSIS, OperationType.PERFORMANCE_ANALYSIS],
                tools_available=["context7", "krag-graphiti-memory", "git-mcp"],
                specialization_domains=["llm-applications", "rag-systems", "ml-pipelines"]
            ),
            
            # DevOps & Operations Team  
            "devops-troubleshooter": AgentDefinition(
                agent_name="devops-troubleshooter",
                capabilities=[AgentCapability.DEVOPS_AUTOMATION],
                operation_types=[OperationType.INCIDENT_RESPONSE, OperationType.DEPLOYMENT_COORDINATION],
                tools_available=["Bash", "git-mcp"],
                specialization_domains=["incident-response", "production-debugging"]
            ),
            
            # Quality & Validation Framework
            "work-validator": AgentDefinition(
                agent_name="work-validator",
                capabilities=[AgentCapability.TESTING_VALIDATION],
                operation_types=[OperationType.CODE_REVIEW],
                tools_available=["context7", "git-mcp", "krag-graphiti-memory"],
                specialization_domains=["quality-assurance", "deliverable-validation"]
            )
        }
    
    def _build_capability_index(self) -> Dict[AgentCapability, List[str]]:
        """Build reverse index of capabilities to agents."""
        index = {}
        for capability in AgentCapability:
            index[capability] = []
            
        for agent_name, agent_def in self.agents.items():
            for capability in agent_def.capabilities:
                index[capability].append(agent_name)
                
        return index
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[AgentDefinition]:
        """Get agents that have specific capability."""
        agent_names = self.capability_index.get(capability, [])
        return [self.agents[name] for name in agent_names]
    
    def get_optimal_agent(self, operation_type: OperationType, 
                         required_capabilities: List[AgentCapability],
                         context_hint: str = "") -> Optional[AgentDefinition]:
        """Get optimal agent for operation with capability matching."""
        candidates = []
        
        # Find agents that support the operation type
        for agent_def in self.agents.values():
            if operation_type in agent_def.operation_types:
                # Check capability overlap
                capability_match = len(set(required_capabilities) & set(agent_def.capabilities))
                if capability_match > 0:
                    # Calculate domain specialization match
                    domain_match = 0
                    if context_hint:
                        for domain in agent_def.specialization_domains:
                            if domain.lower() in context_hint.lower():
                                domain_match += 1
                    
                    score = (capability_match * 2) + domain_match + agent_def.performance_score
                    candidates.append((agent_def, score))
        
        if not candidates:
            return None
            
        # Return highest scoring agent
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]


# ============================================================================
# SEMANTIC CONTEXT ENGINE
# ============================================================================

class SemanticContextEngine:
    """Semantic context assembly and validation engine."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.context_cache = {}
        
    def create_context_vector(self, text: str) -> List[float]:
        """Create semantic vector representation of text."""
        try:
            # Use TF-IDF for now - can be enhanced with embeddings
            vector_matrix = self.vectorizer.fit_transform([text])
            return vector_matrix.toarray()[0].tolist()
        except Exception as e:
            logging.warning(f"Vector creation failed: {e}")
            return [0.0] * 100  # Fallback zero vector
    
    def calculate_semantic_similarity(self, vector1: List[float], 
                                    vector2: List[float]) -> float:
        """Calculate semantic similarity between vectors."""
        try:
            v1 = np.array(vector1).reshape(1, -1)
            v2 = np.array(vector2).reshape(1, -1)
            similarity = cosine_similarity(v1, v2)[0][0]
            return float(similarity)
        except Exception as e:
            logging.warning(f"Similarity calculation failed: {e}")
            return 0.0
    
    def assemble_agent_context(self, operation: Dict[str, Any], 
                             agent_name: str,
                             krag_namespace: str) -> Dict[str, Any]:
        """Assemble JIT context for agent from KRAG semantic search."""
        # Simulate KRAG context assembly - would use real MCP tool in production
        base_context = {
            "operation_type": operation.get("operation_type", "unknown"),
            "target_agent": agent_name,
            "semantic_query": self._build_semantic_query(operation, agent_name),
            "namespace": krag_namespace,
            "assembled_at": datetime.utcnow().isoformat(),
        }
        
        # Add agent-specific context patterns
        if "github" in operation.get("operation_type", ""):
            base_context["github_patterns"] = self._get_github_patterns()
        
        if "security" in agent_name:
            base_context["security_patterns"] = self._get_security_patterns()
            
        return base_context
    
    def _build_semantic_query(self, operation: Dict[str, Any], agent_name: str) -> str:
        """Build semantic query for KRAG context retrieval."""
        query_parts = [
            operation.get("operation_type", ""),
            agent_name.replace("-", " "),
            operation.get("description", "")
        ]
        return " ".join(filter(None, query_parts))
    
    def _get_github_patterns(self) -> Dict[str, Any]:
        """Get GitHub operation patterns from knowledge."""
        return {
            "api_patterns": ["rest_api", "graphql", "webhooks"],
            "workflow_patterns": ["ci_cd", "automated_testing", "deployment"],
            "collaboration_patterns": ["pull_request", "issue_tracking", "code_review"]
        }
    
    def _get_security_patterns(self) -> Dict[str, Any]:
        """Get security patterns from knowledge."""
        return {
            "vulnerability_types": ["xss", "sql_injection", "csrf", "dependency_vulnerabilities"],
            "compliance_frameworks": ["owasp", "pci_dss", "gdpr"],
            "security_tools": ["static_analysis", "dependency_scan", "secret_detection"]
        }
    
    def validate_context_coherence(self, context: Dict[str, Any], 
                                  validation_criteria: List[str]) -> Tuple[bool, float, List[str]]:
        """Validate context coherence against criteria."""
        issues = []
        coherence_scores = []
        
        context_text = json.dumps(context)
        context_vector = self.create_context_vector(context_text)
        
        for criterion in validation_criteria:
            criterion_vector = self.create_context_vector(criterion)
            similarity = self.calculate_semantic_similarity(context_vector, criterion_vector)
            coherence_scores.append(similarity)
            
            if similarity < 0.3:  # Threshold for coherence
                issues.append(f"Low coherence for criterion: {criterion}")
        
        avg_score = np.mean(coherence_scores) if coherence_scores else 0.0
        is_coherent = avg_score >= 0.5 and len(issues) == 0
        
        return is_coherent, avg_score, issues


# ============================================================================
# QUALITY GATES ENGINE
# ============================================================================

class QualityGatesEngine:
    """Quality gates engine with KRAG graph enforcement."""
    
    def __init__(self, semantic_engine: SemanticContextEngine):
        self.semantic_engine = semantic_engine
        self.gates = self._initialize_quality_gates()
        self.gate_dependencies = self._build_gate_dependencies()
    
    def _initialize_quality_gates(self) -> Dict[QualityGateType, QualityGate]:
        """Initialize quality gates with validation criteria."""
        return {
            QualityGateType.PLANNING: QualityGate(
                gate_type=QualityGateType.PLANNING,
                validation_criteria=[
                    "requirements clearly defined",
                    "success criteria measurable",
                    "dependencies identified",
                    "risk assessment completed"
                ],
                threshold_score=0.80
            ),
            
            QualityGateType.SECURITY: QualityGate(
                gate_type=QualityGateType.SECURITY,
                validation_criteria=[
                    "security scan completed",
                    "vulnerabilities addressed",
                    "authentication mechanisms secure",
                    "data protection measures implemented"
                ],
                threshold_score=0.90,
                blocking_dependencies=[QualityGateType.PLANNING]
            ),
            
            QualityGateType.ARCHITECTURE: QualityGate(
                gate_type=QualityGateType.ARCHITECTURE,
                validation_criteria=[
                    "architecture patterns followed",
                    "scalability considerations addressed",
                    "integration points defined",
                    "performance requirements met"
                ],
                threshold_score=0.85,
                blocking_dependencies=[QualityGateType.PLANNING]
            ),
            
            QualityGateType.TESTING: QualityGate(
                gate_type=QualityGateType.TESTING,
                validation_criteria=[
                    "unit tests coverage >= 80%",
                    "integration tests passing",
                    "performance tests completed",
                    "edge cases covered"
                ],
                threshold_score=0.80,
                blocking_dependencies=[QualityGateType.ARCHITECTURE]
            ),
            
            QualityGateType.PERFORMANCE: QualityGate(
                gate_type=QualityGateType.PERFORMANCE,
                validation_criteria=[
                    "response time within limits",
                    "memory usage optimized",
                    "scalability requirements met",
                    "load testing completed"
                ],
                threshold_score=0.80,
                blocking_dependencies=[QualityGateType.ARCHITECTURE]
            ),
            
            QualityGateType.COMPLIANCE: QualityGate(
                gate_type=QualityGateType.COMPLIANCE,
                validation_criteria=[
                    "regulatory requirements met",
                    "code standards followed",
                    "documentation complete",
                    "audit trail maintained"
                ],
                threshold_score=0.85,
                blocking_dependencies=[QualityGateType.SECURITY, QualityGateType.TESTING]
            ),
            
            QualityGateType.DEPLOYMENT: QualityGate(
                gate_type=QualityGateType.DEPLOYMENT,
                validation_criteria=[
                    "deployment scripts tested",
                    "rollback procedures defined",
                    "monitoring configured",
                    "production readiness verified"
                ],
                threshold_score=0.90,
                blocking_dependencies=[QualityGateType.COMPLIANCE, QualityGateType.PERFORMANCE]
            )
        }
    
    def _build_gate_dependencies(self) -> Dict[QualityGateType, Set[QualityGateType]]:
        """Build gate dependency graph."""
        dependencies = {}
        for gate_type, gate in self.gates.items():
            dependencies[gate_type] = set(gate.blocking_dependencies)
        return dependencies
    
    async def validate_gate(self, gate_type: QualityGateType, 
                           deliverable: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """Validate specific quality gate."""
        gate = self.gates.get(gate_type)
        if not gate:
            return False, 0.0, [f"Unknown gate type: {gate_type}"]
        
        # Check dependencies first
        dependency_issues = await self._check_gate_dependencies(gate_type)
        if dependency_issues:
            return False, 0.0, dependency_issues
        
        # Semantic validation of deliverable against criteria
        deliverable_text = json.dumps(deliverable)
        is_coherent, coherence_score, issues = self.semantic_engine.validate_context_coherence(
            {"deliverable": deliverable_text}, 
            gate.validation_criteria
        )
        
        # Update gate status
        if coherence_score >= gate.threshold_score and is_coherent:
            gate.status = "passed"
            gate.validation_results = {
                "score": coherence_score,
                "passed_at": datetime.utcnow().isoformat()
            }
            return True, coherence_score, []
        else:
            gate.status = "failed" 
            gate.failure_reasons = issues
            gate.validation_results = {
                "score": coherence_score,
                "failed_at": datetime.utcnow().isoformat(),
                "issues": issues
            }
            return False, coherence_score, issues
    
    async def _check_gate_dependencies(self, gate_type: QualityGateType) -> List[str]:
        """Check if gate dependencies are satisfied."""
        issues = []
        dependencies = self.gate_dependencies.get(gate_type, set())
        
        for dep_gate_type in dependencies:
            dep_gate = self.gates.get(dep_gate_type)
            if not dep_gate or dep_gate.status != "passed":
                issues.append(f"Dependency gate {dep_gate_type.value} not passed")
        
        return issues
    
    def get_next_gates(self, current_gates: List[QualityGateType]) -> List[QualityGateType]:
        """Get next gates that can be processed based on current state."""
        passed_gates = set(current_gates)
        next_gates = []
        
        for gate_type, dependencies in self.gate_dependencies.items():
            if gate_type not in passed_gates:
                if dependencies.issubset(passed_gates):
                    next_gates.append(gate_type)
        
        return next_gates
    
    def validate_gate_sequence(self, gate_sequence: List[QualityGateType]) -> Tuple[bool, List[str]]:
        """Validate that gate sequence respects dependencies."""
        issues = []
        processed = set()
        
        for gate_type in gate_sequence:
            dependencies = self.gate_dependencies.get(gate_type, set())
            missing_deps = dependencies - processed
            
            if missing_deps:
                issues.append(f"Gate {gate_type.value} missing dependencies: {[dep.value for dep in missing_deps]}")
            
            processed.add(gate_type)
        
        return len(issues) == 0, issues


# ============================================================================
# CIRCUIT BREAKER FOR AGENT RESILIENCE
# ============================================================================

class CircuitBreakerManager:
    """Circuit breaker manager for agent resilience."""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, agent_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for agent."""
        if agent_name not in self.breakers:
            self.breakers[agent_name] = CircuitBreaker(agent_name=agent_name)
        return self.breakers[agent_name]
    
    async def call_through_breaker(self, agent_name: str, 
                                  operation: Callable, 
                                  *args, **kwargs) -> Any:
        """Execute operation through circuit breaker."""
        breaker = self.get_breaker(agent_name)
        
        if breaker.state == CircuitBreakerState.OPEN:
            if await self._should_attempt_reset(breaker):
                breaker.state = CircuitBreakerState.HALF_OPEN
                breaker.consecutive_successes = 0
            else:
                raise Exception(f"Circuit breaker OPEN for agent {agent_name}")
        
        try:
            result = await operation(*args, **kwargs)
            await self._on_success(breaker)
            return result
        except Exception as e:
            await self._on_failure(breaker)
            raise e
    
    async def _should_attempt_reset(self, breaker: CircuitBreaker) -> bool:
        """Check if circuit breaker should attempt reset."""
        if breaker.last_failure_time is None:
            return True
            
        time_since_failure = datetime.utcnow() - breaker.last_failure_time
        return time_since_failure.total_seconds() > breaker.timeout_seconds
    
    async def _on_success(self, breaker: CircuitBreaker) -> None:
        """Handle successful operation."""
        if breaker.state == CircuitBreakerState.HALF_OPEN:
            breaker.consecutive_successes += 1
            if breaker.consecutive_successes >= breaker.success_threshold:
                breaker.state = CircuitBreakerState.CLOSED
                breaker.failure_count = 0
                breaker.consecutive_successes = 0
        elif breaker.state == CircuitBreakerState.CLOSED:
            breaker.failure_count = max(0, breaker.failure_count - 1)
    
    async def _on_failure(self, breaker: CircuitBreaker) -> None:
        """Handle failed operation."""
        breaker.failure_count += 1
        breaker.last_failure_time = datetime.utcnow()
        breaker.consecutive_successes = 0
        
        if breaker.failure_count >= breaker.failure_threshold:
            breaker.state = CircuitBreakerState.OPEN
    
    def get_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers."""
        return {
            name: {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
            }
            for name, breaker in self.breakers.items()
        }


# ============================================================================
# SAGA PATTERN FOR TRANSACTION COORDINATION
# ============================================================================

class SagaOrchestrator:
    """Saga orchestrator for transaction-like multi-agent coordination."""
    
    def __init__(self):
        self.active_sagas: Dict[str, AgentWorkflowSaga] = {}
        self.completed_sagas: List[AgentWorkflowSaga] = []
    
    async def start_saga(self, workflow_name: str, 
                        participating_agents: List[str],
                        operations: List[Dict[str, Any]]) -> str:
        """Start new workflow saga."""
        saga_id = str(uuid.uuid4())
        
        saga = AgentWorkflowSaga(
            saga_id=saga_id,
            workflow_name=workflow_name,
            participating_agents=participating_agents,
            operations=operations
        )
        
        self.active_sagas[saga_id] = saga
        logging.info(f"Started saga {saga_id} for workflow {workflow_name}")
        
        return saga_id
    
    async def execute_saga(self, saga_id: str, 
                          operation_executor: Callable) -> bool:
        """Execute saga operations with rollback support."""
        saga = self.active_sagas.get(saga_id)
        if not saga:
            logging.error(f"Saga {saga_id} not found")
            return False
        
        try:
            for i, operation in enumerate(saga.operations):
                logging.info(f"Executing operation {i+1}/{len(saga.operations)} for saga {saga_id}")
                
                try:
                    result = await operation_executor(operation)
                    saga.completed_operations.append({
                        **operation,
                        "result": result,
                        "completed_at": datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logging.error(f"Operation {i+1} failed in saga {saga_id}: {e}")
                    saga.status = "rolling_back"
                    await self._rollback_saga(saga, operation_executor)
                    return False
            
            saga.status = "completed"
            self.completed_sagas.append(saga)
            del self.active_sagas[saga_id]
            
            logging.info(f"Saga {saga_id} completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Saga {saga_id} execution failed: {e}")
            saga.status = "failed"
            await self._rollback_saga(saga, operation_executor)
            return False
    
    async def _rollback_saga(self, saga: AgentWorkflowSaga, 
                           operation_executor: Callable) -> None:
        """Rollback completed operations in reverse order."""
        logging.info(f"Rolling back saga {saga.saga_id}")
        
        # Execute rollback operations in reverse order
        for operation in reversed(saga.completed_operations):
            if "rollback_operation" in operation:
                try:
                    rollback_op = operation["rollback_operation"]
                    await operation_executor(rollback_op)
                    saga.rollback_operations.append({
                        **rollback_op,
                        "rolled_back_at": datetime.utcnow().isoformat()
                    })
                    logging.info(f"Rolled back operation for saga {saga.saga_id}")
                except Exception as e:
                    logging.error(f"Rollback failed for saga {saga.saga_id}: {e}")
        
        saga.status = "rollback_completed"
        self.completed_sagas.append(saga)
        
        if saga.saga_id in self.active_sagas:
            del self.active_sagas[saga.saga_id]
    
    def get_saga_status(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """Get saga status."""
        saga = self.active_sagas.get(saga_id)
        if not saga:
            # Check completed sagas
            for completed_saga in self.completed_sagas:
                if completed_saga.saga_id == saga_id:
                    saga = completed_saga
                    break
        
        if not saga:
            return None
        
        return {
            "saga_id": saga.saga_id,
            "workflow_name": saga.workflow_name,
            "status": saga.status,
            "participating_agents": saga.participating_agents,
            "operations_completed": len(saga.completed_operations),
            "operations_total": len(saga.operations),
            "created_at": saga.created_at.isoformat()
        }
    
    def get_all_saga_status(self) -> Dict[str, Any]:
        """Get status of all sagas."""
        return {
            "active_sagas": len(self.active_sagas),
            "completed_sagas": len(self.completed_sagas),
            "sagas": {
                saga_id: self.get_saga_status(saga_id) 
                for saga_id in self.active_sagas.keys()
            }
        }


# ============================================================================
# HANDOFF TOKEN MANAGER
# ============================================================================

class HandoffTokenManager:
    """KRAG-based HANDOFF_TOKEN system for agent coordination."""
    
    def __init__(self, semantic_engine: SemanticContextEngine):
        self.semantic_engine = semantic_engine
        self.active_tokens: Dict[str, HandoffToken] = {}
        self.token_history: List[HandoffToken] = []
        self.krag_namespace = "system_coordination"
    
    async def create_handoff_token(self, 
                                  source_agent: str,
                                  target_agent: str,
                                  operation_type: OperationType,
                                  semantic_context: Dict[str, Any],
                                  validation_criteria: List[str],
                                  quality_gates: List[QualityGateType] = None,
                                  dependencies: List[str] = None) -> str:
        """Create new HANDOFF_TOKEN with semantic validation."""
        token_id = f"HANDOFF_{operation_type.value.upper()}_{str(uuid.uuid4())[:8]}"
        
        # Create context vector for semantic validation
        context_text = json.dumps(semantic_context)
        context_vector = self.semantic_engine.create_context_vector(context_text)
        
        token = HandoffToken(
            token_id=token_id,
            source_agent=source_agent,
            target_agent=target_agent,
            operation_type=operation_type,
            context_vector=context_vector,
            semantic_context=semantic_context,
            validation_criteria=validation_criteria,
            status=HandoffTokenStatus.CREATED,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            quality_gates=quality_gates or [],
            dependencies=dependencies or []
        )
        
        self.active_tokens[token_id] = token
        
        # Store in KRAG (simulated - would use real MCP tool)
        await self._store_token_in_krag(token)
        
        logging.info(f"Created HANDOFF_TOKEN {token_id} from {source_agent} to {target_agent}")
        return token_id
    
    async def validate_token(self, token_id: str) -> Tuple[bool, float, List[str]]:
        """Validate HANDOFF_TOKEN semantics and status."""
        token = self.active_tokens.get(token_id)
        if not token:
            return False, 0.0, [f"Token {token_id} not found"]
        
        if token.is_expired():
            token.status = HandoffTokenStatus.EXPIRED
            return False, 0.0, [f"Token {token_id} expired"]
        
        # Semantic coherence validation
        context_text = json.dumps(token.semantic_context)
        is_coherent, coherence_score, issues = self.semantic_engine.validate_context_coherence(
            {"context": context_text},
            token.validation_criteria
        )
        
        if is_coherent and coherence_score >= 0.7:
            token.status = HandoffTokenStatus.VALIDATED
            await self._update_token_in_krag(token)
            return True, coherence_score, []
        else:
            validation_issues = [f"Token {token_id} semantic validation failed"] + issues
            return False, coherence_score, validation_issues
    
    async def start_token_execution(self, token_id: str) -> bool:
        """Mark token as in progress."""
        token = self.active_tokens.get(token_id)
        if not token or token.status != HandoffTokenStatus.VALIDATED:
            return False
        
        token.status = HandoffTokenStatus.IN_PROGRESS
        await self._update_token_in_krag(token)
        logging.info(f"Started execution for token {token_id}")
        return True
    
    async def complete_token(self, token_id: str, 
                           result: Dict[str, Any]) -> bool:
        """Complete HANDOFF_TOKEN with result."""
        token = self.active_tokens.get(token_id)
        if not token:
            return False
        
        token.status = HandoffTokenStatus.COMPLETED
        token.semantic_context["result"] = result
        token.semantic_context["completed_at"] = datetime.utcnow().isoformat()
        
        # Move to history
        self.token_history.append(token)
        del self.active_tokens[token_id]
        
        await self._update_token_in_krag(token)
        logging.info(f"Completed token {token_id}")
        return True
    
    async def fail_token(self, token_id: str, 
                        error: str,
                        retry: bool = True) -> bool:
        """Fail HANDOFF_TOKEN with optional retry."""
        token = self.active_tokens.get(token_id)
        if not token:
            return False
        
        token.retry_count += 1
        
        if retry and token.can_retry():
            token.status = HandoffTokenStatus.CREATED
            token.semantic_context["last_error"] = error
            token.semantic_context["retry_attempt"] = token.retry_count
            logging.warning(f"Token {token_id} failed, retrying (attempt {token.retry_count})")
            return True
        else:
            token.status = HandoffTokenStatus.FAILED
            token.semantic_context["failure_reason"] = error
            token.semantic_context["failed_at"] = datetime.utcnow().isoformat()
            
            # Move to history
            self.token_history.append(token)
            del self.active_tokens[token_id]
            
            await self._update_token_in_krag(token)
            logging.error(f"Token {token_id} failed permanently: {error}")
            return False
    
    async def _store_token_in_krag(self, token: HandoffToken) -> bool:
        """Store token in KRAG memory (simulated)."""
        try:
            # Would use real KRAG MCP tool: mcp__krag-graphiti-memory__add_memory
            entity_data = token.to_krag_entity()
            logging.debug(f"Would store token {token.token_id} in KRAG namespace {self.krag_namespace}")
            return True
        except Exception as e:
            logging.error(f"Failed to store token in KRAG: {e}")
            return False
    
    async def _update_token_in_krag(self, token: HandoffToken) -> bool:
        """Update token in KRAG memory (simulated)."""
        try:
            # Would update existing entity in KRAG
            logging.debug(f"Would update token {token.token_id} in KRAG")
            return True
        except Exception as e:
            logging.error(f"Failed to update token in KRAG: {e}")
            return False
    
    def get_token_status(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get token status."""
        token = self.active_tokens.get(token_id)
        if not token:
            # Check history
            for hist_token in self.token_history:
                if hist_token.token_id == token_id:
                    token = hist_token
                    break
        
        if not token:
            return None
        
        return {
            "token_id": token.token_id,
            "source_agent": token.source_agent,
            "target_agent": token.target_agent,
            "operation_type": token.operation_type.value,
            "status": token.status.value,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "retry_count": token.retry_count,
            "is_expired": token.is_expired()
        }
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens."""
        expired_count = 0
        expired_tokens = []
        
        for token_id, token in self.active_tokens.items():
            if token.is_expired():
                token.status = HandoffTokenStatus.EXPIRED
                expired_tokens.append(token_id)
                expired_count += 1
        
        for token_id in expired_tokens:
            token = self.active_tokens.pop(token_id)
            self.token_history.append(token)
            await self._update_token_in_krag(token)
        
        if expired_count > 0:
            logging.info(f"Cleaned up {expired_count} expired tokens")
        
        return expired_count


# ============================================================================
# PRIMARY AGENT GITHUB CONTROLLER - MAIN ORCHESTRATOR
# ============================================================================

class PrimaryAgentGitHubController:
    """
    Enterprise Primary Agent GitHub Controller.
    
    Central orchestration layer for multi-agent GitHub operations with:
    - HANDOFF_TOKEN system for agent coordination
    - Quality gates with semantic validation  
    - Circuit breaker resilience patterns
    - Saga transaction coordination
    - KRAG memory integration
    - Performance monitoring and observability
    """
    
    def __init__(self, session_id: str = None):
        # Core configuration
        self.session_id = session_id or os.getenv('CLAUDE_SESSION_ID', 'default-session')
        self.krag_primary_namespace = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_primary"
        
        # Initialize core components
        self.capability_matrix = AgentCapabilityMatrix()
        self.semantic_engine = SemanticContextEngine()
        self.quality_gates = QualityGatesEngine(self.semantic_engine)
        self.circuit_breakers = CircuitBreakerManager()
        self.saga_orchestrator = SagaOrchestrator()
        self.token_manager = HandoffTokenManager(self.semantic_engine)
        
        # GitHub integrations
        self.github_config = GitHubConfig()
        self.github_service: Optional[GitHubService] = None
        self.event_bus: Optional[GitHubEventBus] = None
        
        # Performance metrics
        self.metrics = {
            'operations_delegated': 0,
            'operations_completed': 0,
            'operations_failed': 0,
            'avg_operation_time': 0.0,
            'quality_gate_failures': 0,
            'token_validations': 0,
            'circuit_breaker_trips': 0
        }
        
        # Configuration
        self.max_concurrent_operations = int(os.getenv('MAX_CONCURRENT_OPERATIONS', '5'))
        self.enable_monitoring = os.getenv('GITHUB_ORCHESTRATOR_MONITORING', 'true').lower() == 'true'
        
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Setup comprehensive logging."""
        log_dir = ensure_session_log_dir(self.session_id)
        log_file = log_dir / "primary_agent_github.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized Primary Agent GitHub Controller for session {self.session_id}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_services()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup_services()
    
    async def _initialize_services(self) -> None:
        """Initialize GitHub services and event bus."""
        try:
            self.github_service = GitHubService(self.github_config)
            await self.github_service.__aenter__()
            
            self.event_bus = GitHubEventBus(
                krag_namespace=f"{self.krag_primary_namespace}_events",
                session_id=self.session_id
            )
            
            # Test GitHub authentication
            auth_success = await self.github_service.authenticate_token()
            if not auth_success:
                self.logger.warning("GitHub authentication failed - some operations may be limited")
            
            self.logger.info("GitHub services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    async def _cleanup_services(self) -> None:
        """Cleanup services on shutdown."""
        try:
            if self.github_service:
                await self.github_service.__aexit__(None, None, None)
            
            # Cleanup expired tokens
            await self.token_manager.cleanup_expired_tokens()
            
            self.logger.info("Services cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    # ========================================================================
    # CORE ORCHESTRATION METHODS
    # ========================================================================
    
    async def delegate_github_task(self, 
                                  agent_name: str,
                                  operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate GitHub operation to specialist agent with full orchestration.
        
        Args:
            agent_name: Target agent for delegation
            operation: Operation specification with type, parameters, context
            
        Returns:
            Dict containing operation result, quality metrics, and status
        """
        operation_start = time.time()
        
        try:
            # Step 1: Validate agent permissions and capabilities
            if not await self.validate_permissions(agent_name, operation.get("operation_type", "")):
                return {
                    "success": False,
                    "error": f"Agent {agent_name} lacks permissions for operation",
                    "error_type": "permission_denied"
                }
            
            # Step 2: Create operation context and HANDOFF_TOKEN
            operation_type = OperationType(operation.get("operation_type", "repository_analysis"))
            context = await self._assemble_operation_context(operation, agent_name)
            
            validation_criteria = operation.get("validation_criteria", [
                "operation parameters valid",
                "GitHub API requirements met",
                "agent capabilities matched"
            ])
            
            # Step 3: Create HANDOFF_TOKEN with semantic validation
            token_id = await self.token_manager.create_handoff_token(
                source_agent="primary-agent",
                target_agent=agent_name,
                operation_type=operation_type,
                semantic_context=context,
                validation_criteria=validation_criteria,
                quality_gates=operation.get("quality_gates", []),
                dependencies=operation.get("dependencies", [])
            )
            
            # Step 4: Validate token semantics
            is_valid, coherence_score, issues = await self.token_manager.validate_token(token_id)
            if not is_valid:
                self.metrics['token_validations'] += 1
                return {
                    "success": False,
                    "error": f"Token validation failed: {issues}",
                    "error_type": "token_validation_failed",
                    "coherence_score": coherence_score
                }
            
            # Step 5: Execute through circuit breaker
            try:
                result = await self.circuit_breakers.call_through_breaker(
                    agent_name=agent_name,
                    operation=self._execute_agent_operation,
                    token_id=token_id,
                    context=context
                )
                
                # Step 6: Complete token and update metrics
                await self.token_manager.complete_token(token_id, result)
                self.metrics['operations_completed'] += 1
                
                operation_time = time.time() - operation_start
                self._update_avg_operation_time(operation_time)
                
                # Step 7: Send success event
                if self.event_bus:
                    await self.event_bus.publish_event(
                        event_type=EventType.AGENT_TASK_COMPLETED.value,
                        payload={
                            "agent_name": agent_name,
                            "operation_type": operation_type.value,
                            "token_id": token_id,
                            "duration": operation_time,
                            "result_summary": result.get("summary", "")
                        },
                        agent_context="primary-agent"
                    )
                
                return {
                    "success": True,
                    "result": result,
                    "token_id": token_id,
                    "coherence_score": coherence_score,
                    "operation_time": operation_time,
                    "agent_name": agent_name
                }
                
            except Exception as e:
                # Handle circuit breaker and other execution failures
                await self.token_manager.fail_token(token_id, str(e))
                self.metrics['operations_failed'] += 1
                
                if "Circuit breaker OPEN" in str(e):
                    self.metrics['circuit_breaker_trips'] += 1
                
                # Send failure event
                if self.event_bus:
                    await self.event_bus.publish_event(
                        event_type=EventType.SYSTEM_ERROR.value,
                        payload={
                            "agent_name": agent_name,
                            "operation_type": operation_type.value,
                            "token_id": token_id,
                            "error": str(e),
                            "error_type": "execution_failure"
                        },
                        agent_context="primary-agent"
                    )
                
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "execution_failure",
                    "token_id": token_id,
                    "agent_name": agent_name
                }
        
        except Exception as e:
            self.logger.error(f"Critical error in delegate_github_task: {e}")
            self.metrics['operations_failed'] += 1
            
            return {
                "success": False,
                "error": str(e),
                "error_type": "critical_failure"
            }
        finally:
            self.metrics['operations_delegated'] += 1
    
    async def validate_permissions(self, agent_name: str, operation_type: str) -> bool:
        """
        Validate agent permissions for GitHub operation.
        
        Args:
            agent_name: Agent requesting permission
            operation_type: Type of operation to validate
            
        Returns:
            bool: True if agent has permissions
        """
        try:
            # Get agent definition
            agent_def = self.capability_matrix.agents.get(agent_name)
            if not agent_def:
                self.logger.warning(f"Unknown agent: {agent_name}")
                return False
            
            # Check operation type mapping
            try:
                op_type = OperationType(operation_type)
                if op_type not in agent_def.operation_types:
                    self.logger.warning(f"Agent {agent_name} not authorized for {operation_type}")
                    return False
            except ValueError:
                self.logger.warning(f"Unknown operation type: {operation_type}")
                return False
            
            # Check GitHub service requirements
            if op_type in [OperationType.PULL_REQUEST_CREATION, 
                          OperationType.ISSUE_MANAGEMENT,
                          OperationType.WORKFLOW_AUTOMATION]:
                if not self.github_service:
                    self.logger.error("GitHub service not available")
                    return False
                
                # Verify GitHub authentication
                auth_success = await self.github_service.authenticate_token()
                if not auth_success:
                    self.logger.error("GitHub authentication failed")
                    return False
            
            # Check tool availability
            required_tools = self._get_required_tools_for_operation(op_type)
            missing_tools = set(required_tools) - set(agent_def.tools_available)
            if missing_tools:
                self.logger.warning(f"Agent {agent_name} missing required tools: {missing_tools}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Permission validation error: {e}")
            return False
    
    async def aggregate_results(self, multi_agent_ops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from multiple agent operations using Saga pattern.
        
        Args:
            multi_agent_ops: List of agent operations to coordinate
            
        Returns:
            Dict containing aggregated results and coordination status
        """
        if not multi_agent_ops:
            return {"success": False, "error": "No operations provided"}
        
        try:
            # Step 1: Create workflow saga
            participating_agents = list(set(op.get("agent_name", "unknown") for op in multi_agent_ops))
            saga_id = await self.saga_orchestrator.start_saga(
                workflow_name="multi_agent_github_coordination",
                participating_agents=participating_agents,
                operations=multi_agent_ops
            )
            
            # Step 2: Execute saga with coordination
            async def execute_coordinated_operation(operation: Dict[str, Any]) -> Dict[str, Any]:
                """Execute single operation within saga context."""
                agent_name = operation.get("agent_name")
                if not agent_name:
                    raise ValueError("Operation missing agent_name")
                
                # Add rollback operation for saga
                operation["rollback_operation"] = {
                    "operation_type": "rollback_github_operation", 
                    "agent_name": agent_name,
                    "original_operation": operation
                }
                
                # Execute through main delegation
                result = await self.delegate_github_task(agent_name, operation)
                if not result.get("success", False):
                    raise Exception(result.get("error", "Operation failed"))
                
                return result
            
            # Step 3: Execute saga
            success = await self.saga_orchestrator.execute_saga(saga_id, execute_coordinated_operation)
            
            if success:
                saga_status = self.saga_orchestrator.get_saga_status(saga_id)
                return {
                    "success": True,
                    "saga_id": saga_id,
                    "participating_agents": participating_agents,
                    "operations_completed": len(multi_agent_ops),
                    "saga_status": saga_status,
                    "coordination_type": "saga_pattern"
                }
            else:
                saga_status = self.saga_orchestrator.get_saga_status(saga_id)
                return {
                    "success": False,
                    "error": "Multi-agent coordination failed",
                    "saga_id": saga_id,
                    "saga_status": saga_status,
                    "coordination_type": "saga_pattern"
                }
        
        except Exception as e:
            self.logger.error(f"Multi-agent aggregation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "coordination_failure"
            }
    
    async def enforce_quality_gates(self, deliverable: Dict[str, Any]) -> bool:
        """
        Enforce quality gates with semantic validation.
        
        Args:
            deliverable: Deliverable to validate against quality gates
            
        Returns:
            bool: True if all quality gates pass
        """
        try:
            # Determine required quality gates based on deliverable type
            required_gates = self._determine_required_gates(deliverable)
            
            if not required_gates:
                self.logger.info("No quality gates required for deliverable")
                return True
            
            # Validate gate sequence
            is_valid_sequence, sequence_issues = self.quality_gates.validate_gate_sequence(required_gates)
            if not is_valid_sequence:
                self.logger.error(f"Invalid gate sequence: {sequence_issues}")
                self.metrics['quality_gate_failures'] += 1
                return False
            
            # Execute gates in dependency order
            passed_gates = []
            
            for gate_type in required_gates:
                self.logger.info(f"Validating quality gate: {gate_type.value}")
                
                passed, score, issues = await self.quality_gates.validate_gate(gate_type, deliverable)
                
                if passed:
                    passed_gates.append(gate_type)
                    self.logger.info(f"Quality gate {gate_type.value} PASSED (score: {score:.2f})")
                else:
                    self.logger.error(f"Quality gate {gate_type.value} FAILED (score: {score:.2f}): {issues}")
                    self.metrics['quality_gate_failures'] += 1
                    
                    # Send failure event
                    if self.event_bus:
                        await self.event_bus.publish_event(
                            event_type=EventType.SYSTEM_WARNING.value,
                            payload={
                                "gate_type": gate_type.value,
                                "score": score,
                                "issues": issues,
                                "deliverable_type": deliverable.get("type", "unknown")
                            },
                            agent_context="quality-gates-engine"
                        )
                    
                    return False
            
            self.logger.info(f"All quality gates passed: {[gate.value for gate in passed_gates]}")
            
            # Send success event
            if self.event_bus:
                await self.event_bus.publish_event(
                    event_type=EventType.SYSTEM_WARNING.value,  # Using WARNING for info events
                    payload={
                        "message": "All quality gates passed",
                        "passed_gates": [gate.value for gate in passed_gates],
                        "deliverable_type": deliverable.get("type", "unknown")
                    },
                    agent_context="quality-gates-engine"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Quality gate enforcement error: {e}")
            self.metrics['quality_gate_failures'] += 1
            return False
    
    # ========================================================================
    # WORKFLOW ORCHESTRATION AND CONTEXT MANAGEMENT
    # ========================================================================
    
    async def orchestrate_multi_agent_workflow(self,
                                             workflow_name: str,
                                             agents: List[str],
                                             operations: List[Dict[str, Any]],
                                             quality_gates: List[QualityGateType] = None) -> Dict[str, Any]:
        """
        Orchestrate complete multi-agent workflow with quality gates.
        
        Args:
            workflow_name: Name of the workflow
            agents: List of participating agents  
            operations: Sequence of operations to execute
            quality_gates: Quality gates to enforce
            
        Returns:
            Dict containing workflow execution results
        """
        workflow_start = time.time()
        
        try:
            self.logger.info(f"Starting multi-agent workflow: {workflow_name}")
            
            # Step 1: Validate workflow structure
            validation_result = await self._validate_workflow_structure(agents, operations)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Workflow validation failed: {validation_result['issues']}",
                    "workflow_name": workflow_name
                }
            
            # Step 2: Create workflow saga
            saga_id = await self.saga_orchestrator.start_saga(
                workflow_name=workflow_name,
                participating_agents=agents,
                operations=operations
            )
            
            # Step 3: Execute operations with coordination
            operation_results = []
            
            for i, operation in enumerate(operations):
                agent_name = operation.get("agent_name")
                self.logger.info(f"Executing operation {i+1}/{len(operations)}: {agent_name}")
                
                # Execute with timeout and retry
                result = await self._execute_workflow_operation(operation, saga_id)
                
                if not result.get("success", False):
                    self.logger.error(f"Workflow operation failed: {result.get('error')}")
                    # Trigger saga rollback
                    await self.saga_orchestrator._rollback_saga(
                        self.saga_orchestrator.active_sagas.get(saga_id),
                        self._execute_rollback_operation
                    )
                    
                    return {
                        "success": False,
                        "error": f"Workflow failed at operation {i+1}",
                        "failed_operation": operation,
                        "saga_id": saga_id,
                        "workflow_name": workflow_name
                    }
                
                operation_results.append(result)
            
            # Step 4: Enforce quality gates if specified
            if quality_gates:
                workflow_deliverable = {
                    "type": "workflow_output",
                    "workflow_name": workflow_name,
                    "operations": operation_results,
                    "participating_agents": agents
                }
                
                gates_passed = await self.enforce_quality_gates(workflow_deliverable)
                if not gates_passed:
                    return {
                        "success": False,
                        "error": "Quality gates failed",
                        "workflow_name": workflow_name,
                        "saga_id": saga_id,
                        "quality_gates": [gate.value for gate in quality_gates]
                    }
            
            # Step 5: Complete saga and workflow
            saga_success = await self.saga_orchestrator.execute_saga(
                saga_id, 
                lambda op: asyncio.create_future().set_result({"success": True})
            )
            
            workflow_time = time.time() - workflow_start
            
            self.logger.info(f"Workflow {workflow_name} completed successfully in {workflow_time:.2f}s")
            
            # Send completion event
            if self.event_bus:
                await self.event_bus.publish_event(
                    event_type=EventType.AGENT_TASK_COMPLETED.value,
                    payload={
                        "workflow_name": workflow_name,
                        "participating_agents": agents,
                        "operations_count": len(operations),
                        "duration": workflow_time,
                        "saga_id": saga_id
                    },
                    agent_context="workflow-orchestrator"
                )
            
            return {
                "success": True,
                "workflow_name": workflow_name,
                "saga_id": saga_id,
                "operations_completed": len(operations),
                "operation_results": operation_results,
                "duration": workflow_time,
                "participating_agents": agents,
                "quality_gates_enforced": quality_gates is not None
            }
            
        except Exception as e:
            self.logger.error(f"Workflow orchestration error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "workflow_orchestration_failure",
                "workflow_name": workflow_name
            }
    
    async def get_optimal_agent_for_operation(self, 
                                            operation: Dict[str, Any],
                                            context_hint: str = "") -> Optional[str]:
        """Get optimal agent for GitHub operation based on capability matrix."""
        try:
            operation_type = OperationType(operation.get("operation_type", "repository_analysis"))
            required_capabilities = operation.get("required_capabilities", [])
            
            # Convert string capabilities to enum
            capability_enums = []
            for cap_str in required_capabilities:
                try:
                    capability_enums.append(AgentCapability(cap_str))
                except ValueError:
                    self.logger.warning(f"Unknown capability: {cap_str}")
            
            # Get optimal agent
            agent_def = self.capability_matrix.get_optimal_agent(
                operation_type=operation_type,
                required_capabilities=capability_enums,
                context_hint=context_hint
            )
            
            return agent_def.agent_name if agent_def else None
            
        except Exception as e:
            self.logger.error(f"Agent selection error: {e}")
            return None
    
    # ========================================================================
    # MONITORING AND OBSERVABILITY
    # ========================================================================
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get comprehensive orchestration metrics."""
        circuit_breaker_status = self.circuit_breakers.get_breaker_status()
        saga_status = self.saga_orchestrator.get_all_saga_status()
        
        # Calculate derived metrics
        success_rate = (
            self.metrics['operations_completed'] / max(self.metrics['operations_delegated'], 1)
        ) * 100
        
        failure_rate = (
            self.metrics['operations_failed'] / max(self.metrics['operations_delegated'], 1)
        ) * 100
        
        return {
            "session_id": self.session_id,
            "krag_namespace": self.krag_primary_namespace,
            "timestamp": datetime.utcnow().isoformat(),
            
            # Core metrics
            "operations": {
                "delegated": self.metrics['operations_delegated'],
                "completed": self.metrics['operations_completed'], 
                "failed": self.metrics['operations_failed'],
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "avg_operation_time": round(self.metrics['avg_operation_time'], 2)
            },
            
            # Quality and validation
            "quality": {
                "gate_failures": self.metrics['quality_gate_failures'],
                "token_validations": self.metrics['token_validations'],
                "circuit_breaker_trips": self.metrics['circuit_breaker_trips']
            },
            
            # System status
            "system": {
                "active_tokens": len(self.token_manager.active_tokens),
                "active_sagas": saga_status["active_sagas"],
                "completed_sagas": saga_status["completed_sagas"],
                "circuit_breakers": circuit_breaker_status
            },
            
            # Configuration
            "config": {
                "max_concurrent_operations": self.max_concurrent_operations,
                "monitoring_enabled": self.enable_monitoring,
                "github_service_available": self.github_service is not None,
                "event_bus_available": self.event_bus is not None
            }
        }
    
    async def send_monitoring_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Send monitoring event to observability system."""
        if not self.enable_monitoring:
            return True
            
        try:
            return send_observability_event(
                event_type=f"PrimaryAgent.{event_type}",
                payload=payload,
                session_id=self.session_id,
                source_app="primary-agent-github-controller"
            )
        except Exception as e:
            self.logger.debug(f"Monitoring event send failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive system health check."""
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "overall_status": "healthy",
            "components": {}
        }
        
        # Check GitHub service
        if self.github_service:
            try:
                auth_test = await self.github_service.authenticate_token()
                health_status["components"]["github_service"] = {
                    "status": "healthy" if auth_test else "degraded",
                    "authenticated": auth_test
                }
            except Exception as e:
                health_status["components"]["github_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
        else:
            health_status["components"]["github_service"] = {
                "status": "not_initialized",
                "error": "Service not available"
            }
        
        # Check event bus
        health_status["components"]["event_bus"] = {
            "status": "healthy" if self.event_bus else "not_initialized",
            "active": self.event_bus is not None
        }
        
        # Check token manager
        active_tokens = len(self.token_manager.active_tokens)
        expired_count = await self.token_manager.cleanup_expired_tokens()
        
        health_status["components"]["token_manager"] = {
            "status": "healthy",
            "active_tokens": active_tokens,
            "expired_tokens_cleaned": expired_count
        }
        
        # Check circuit breakers
        breaker_status = self.circuit_breakers.get_breaker_status()
        open_breakers = sum(1 for status in breaker_status.values() if status["state"] == "open")
        
        health_status["components"]["circuit_breakers"] = {
            "status": "healthy" if open_breakers == 0 else "degraded",
            "total_breakers": len(breaker_status),
            "open_breakers": open_breakers
        }
        
        # Check saga orchestrator
        saga_status = self.saga_orchestrator.get_all_saga_status()
        health_status["components"]["saga_orchestrator"] = {
            "status": "healthy",
            "active_sagas": saga_status["active_sagas"],
            "completed_sagas": saga_status["completed_sagas"]
        }
        
        return health_status
    
    # ========================================================================
    # INTERNAL HELPER METHODS
    # ========================================================================
    
    async def _assemble_operation_context(self, 
                                        operation: Dict[str, Any], 
                                        agent_name: str) -> Dict[str, Any]:
        """Assemble JIT context for agent operation."""
        return self.semantic_engine.assemble_agent_context(
            operation=operation,
            agent_name=agent_name,
            krag_namespace=self.krag_primary_namespace
        )
    
    async def _execute_agent_operation(self, 
                                     token_id: str,
                                     operation: Dict[str, Any],
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent operation with context."""
        # Start token execution
        await self.token_manager.start_token_execution(token_id)
        
        # Simulate agent execution - in production would delegate to actual agent
        self.logger.info(f"Executing {operation.get('operation_type')} for token {token_id}")
        
        # Add artificial delay to simulate work
        await asyncio.sleep(0.1)
        
        # Generate simulated result based on operation type
        operation_type = operation.get("operation_type", "unknown")
        
        if operation_type == "repository_analysis":
            result = {
                "analysis_type": "repository_structure",
                "files_analyzed": 42,
                "technologies_detected": ["python", "javascript", "docker"],
                "recommendations": ["Add CI/CD pipeline", "Improve test coverage"],
                "security_score": 85
            }
        elif operation_type == "pull_request_creation":
            result = {
                "pr_number": 123,
                "pr_url": "https://github.com/owner/repo/pull/123",
                "status": "open",
                "changes": {"files_modified": 5, "lines_added": 150, "lines_removed": 30}
            }
        else:
            result = {
                "operation_type": operation_type,
                "status": "completed",
                "context_used": bool(context)
            }
        
        # Add execution metadata
        result.update({
            "token_id": token_id,
            "execution_time": 0.1,
            "context_coherence": context.get("semantic_coherence", 0.8)
        })
        
        return result
    
    async def _execute_workflow_operation(self, 
                                        operation: Dict[str, Any], 
                                        saga_id: str) -> Dict[str, Any]:
        """Execute single workflow operation."""
        agent_name = operation.get("agent_name")
        operation_with_saga = {
            **operation,
            "saga_id": saga_id,
            "saga_context": True
        }
        
        return await self.delegate_github_task(agent_name, operation_with_saga)
    
    async def _execute_rollback_operation(self, rollback_op: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rollback operation for saga."""
        self.logger.info(f"Executing rollback for {rollback_op.get('agent_name')}")
        # Simulate rollback execution
        await asyncio.sleep(0.05)
        return {"rollback_success": True}
    
    def _get_required_tools_for_operation(self, operation_type: OperationType) -> List[str]:
        """Get required tools for operation type."""
        tool_mapping = {
            OperationType.REPOSITORY_ANALYSIS: ["git-mcp", "context7"],
            OperationType.PULL_REQUEST_CREATION: ["git-mcp", "Read", "Write"],
            OperationType.ISSUE_MANAGEMENT: ["git-mcp"],
            OperationType.WORKFLOW_AUTOMATION: ["Bash", "git-mcp"],
            OperationType.SECURITY_SCANNING: ["git-mcp", "context7"],
            OperationType.CODE_REVIEW: ["git-mcp", "context7"],
            OperationType.PERFORMANCE_ANALYSIS: ["context7", "Bash"]
        }
        
        return tool_mapping.get(operation_type, ["git-mcp"])
    
    def _determine_required_gates(self, deliverable: Dict[str, Any]) -> List[QualityGateType]:
        """Determine required quality gates based on deliverable."""
        deliverable_type = deliverable.get("type", "")
        
        if "workflow" in deliverable_type:
            return [
                QualityGateType.PLANNING,
                QualityGateType.ARCHITECTURE, 
                QualityGateType.SECURITY,
                QualityGateType.TESTING,
                QualityGateType.COMPLIANCE
            ]
        elif "security" in deliverable_type:
            return [
                QualityGateType.SECURITY,
                QualityGateType.COMPLIANCE
            ]
        elif "performance" in deliverable_type:
            return [
                QualityGateType.ARCHITECTURE,
                QualityGateType.PERFORMANCE,
                QualityGateType.TESTING
            ]
        else:
            return [QualityGateType.PLANNING, QualityGateType.TESTING]
    
    async def _validate_workflow_structure(self, 
                                         agents: List[str], 
                                         operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate workflow structure and agent capabilities."""
        issues = []
        
        # Check agent definitions exist
        for agent_name in agents:
            if agent_name not in self.capability_matrix.agents:
                issues.append(f"Unknown agent: {agent_name}")
        
        # Check operations have required fields
        for i, operation in enumerate(operations):
            if "agent_name" not in operation:
                issues.append(f"Operation {i+1} missing agent_name")
            
            if "operation_type" not in operation:
                issues.append(f"Operation {i+1} missing operation_type")
            
            # Validate operation type
            try:
                OperationType(operation.get("operation_type", ""))
            except ValueError:
                issues.append(f"Operation {i+1} has invalid operation_type")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _update_avg_operation_time(self, new_time: float) -> None:
        """Update rolling average operation time."""
        if self.metrics['operations_completed'] <= 1:
            self.metrics['avg_operation_time'] = new_time
        else:
            # Simple rolling average
            count = self.metrics['operations_completed']
            current_avg = self.metrics['avg_operation_time']
            self.metrics['avg_operation_time'] = ((current_avg * (count - 1)) + new_time) / count


# ============================================================================
# TESTING AND CLI INTERFACE
# ============================================================================

async def test_primary_agent_controller() -> Dict[str, Any]:
    """Comprehensive test suite for Primary Agent GitHub Controller."""
    test_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {}
    }
    
    try:
        async with PrimaryAgentGitHubController() as controller:
            # Test 1: Agent capability matrix
            try:
                agent_def = controller.capability_matrix.get_optimal_agent(
                    OperationType.REPOSITORY_ANALYSIS,
                    [AgentCapability.CODE_ANALYSIS],
                    "python project analysis"
                )
                test_results["tests"]["capability_matrix"] = {
                    "status": "passed" if agent_def else "failed",
                    "selected_agent": agent_def.agent_name if agent_def else None
                }
            except Exception as e:
                test_results["tests"]["capability_matrix"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Test 2: Permission validation
            try:
                has_permission = await controller.validate_permissions(
                    "code-reviewer", 
                    "code_review"
                )
                test_results["tests"]["permission_validation"] = {
                    "status": "passed" if has_permission else "failed",
                    "has_permission": has_permission
                }
            except Exception as e:
                test_results["tests"]["permission_validation"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Test 3: HANDOFF_TOKEN creation and validation
            try:
                token_id = await controller.token_manager.create_handoff_token(
                    source_agent="primary-agent",
                    target_agent="coder",
                    operation_type=OperationType.REPOSITORY_ANALYSIS,
                    semantic_context={"test": "context"},
                    validation_criteria=["test criterion"]
                )
                
                is_valid, score, issues = await controller.token_manager.validate_token(token_id)
                
                test_results["tests"]["handoff_token"] = {
                    "status": "passed" if is_valid else "failed",
                    "token_id": token_id,
                    "validation_score": score,
                    "issues": issues
                }
            except Exception as e:
                test_results["tests"]["handoff_token"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Test 4: Quality gates
            try:
                test_deliverable = {
                    "type": "security_analysis",
                    "content": "security analysis completed with recommendations"
                }
                
                gates_passed = await controller.enforce_quality_gates(test_deliverable)
                
                test_results["tests"]["quality_gates"] = {
                    "status": "passed" if gates_passed else "failed",
                    "gates_passed": gates_passed
                }
            except Exception as e:
                test_results["tests"]["quality_gates"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Test 5: Agent delegation
            try:
                result = await controller.delegate_github_task(
                    agent_name="coder",
                    operation={
                        "operation_type": "repository_analysis",
                        "description": "Analyze repository structure"
                    }
                )
                
                test_results["tests"]["agent_delegation"] = {
                    "status": "passed" if result.get("success") else "failed",
                    "result": result
                }
            except Exception as e:
                test_results["tests"]["agent_delegation"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Test 6: Multi-agent workflow
            try:
                workflow_result = await controller.orchestrate_multi_agent_workflow(
                    workflow_name="test_workflow",
                    agents=["planner", "coder"],
                    operations=[
                        {"agent_name": "planner", "operation_type": "repository_analysis"},
                        {"agent_name": "coder", "operation_type": "code_review"}
                    ]
                )
                
                test_results["tests"]["multi_agent_workflow"] = {
                    "status": "passed" if workflow_result.get("success") else "failed",
                    "workflow_result": workflow_result
                }
            except Exception as e:
                test_results["tests"]["multi_agent_workflow"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Test 7: Health check
            try:
                health = await controller.health_check()
                test_results["tests"]["health_check"] = {
                    "status": "passed",
                    "health": health
                }
            except Exception as e:
                test_results["tests"]["health_check"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Test 8: Metrics collection
            try:
                metrics = controller.get_orchestration_metrics()
                test_results["tests"]["metrics_collection"] = {
                    "status": "passed",
                    "metrics": metrics
                }
            except Exception as e:
                test_results["tests"]["metrics_collection"] = {
                    "status": "failed",
                    "error": str(e)
                }
    
    except Exception as e:
        test_results["overall_error"] = str(e)
    
    # Calculate test summary
    passed_tests = sum(1 for test in test_results["tests"].values() if test.get("status") == "passed")
    total_tests = len(test_results["tests"])
    
    test_results["summary"] = {
        "passed": passed_tests,
        "total": total_tests,
        "success_rate": round((passed_tests / max(total_tests, 1)) * 100, 2),
        "overall_status": "passed" if passed_tests == total_tests else "partial"
    }
    
    return test_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Primary Agent GitHub Controller")
    parser.add_argument("--test", action="store_true", help="Run comprehensive test suite")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--metrics", action="store_true", help="Show orchestration metrics")
    parser.add_argument("--delegate", help="Test agent delegation (format: agent_name:operation_type)")
    
    args = parser.parse_args()
    
    async def main():
        if args.test:
            print("Running Primary Agent GitHub Controller test suite...")
            results = await test_primary_agent_controller()
            print(json.dumps(results, indent=2))
        
        elif args.health:
            async with PrimaryAgentGitHubController() as controller:
                health = await controller.health_check()
                print(json.dumps(health, indent=2))
        
        elif args.metrics:
            async with PrimaryAgentGitHubController() as controller:
                metrics = controller.get_orchestration_metrics()
                print(json.dumps(metrics, indent=2))
        
        elif args.delegate:
            try:
                agent_name, operation_type = args.delegate.split(":", 1)
                async with PrimaryAgentGitHubController() as controller:
                    result = await controller.delegate_github_task(
                        agent_name=agent_name,
                        operation={
                            "operation_type": operation_type,
                            "description": f"Test delegation to {agent_name}"
                        }
                    )
                    print(json.dumps(result, indent=2))
            except ValueError:
                print("Error: Use format agent_name:operation_type")
            except Exception as e:
                print(f"Error: {e}")
        
        else:
            print("Use --test, --health, --metrics, or --delegate agent:operation")
    
    asyncio.run(main())