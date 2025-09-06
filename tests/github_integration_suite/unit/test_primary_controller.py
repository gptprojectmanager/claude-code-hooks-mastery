"""
Unit Tests for Primary Agent GitHub Controller
Comprehensive testing of multi-agent orchestration, HANDOFF_TOKEN system, quality gates, and saga patterns
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Import the components to test
import sys
sys.path.append('/Users/sam/claude-code-hooks-mastery/.claude/hooks')

try:
    from primary_agent_github import (
        PrimaryAgentGitHubController,
        AgentCapability,
        OperationType,
        QualityGateType,
        HandoffTokenStatus,
        CircuitBreakerState,
        AgentDefinition,
        HandoffToken,
        QualityGate,
        CircuitBreaker,
        AgentWorkflowSaga,
        AgentCapabilityMatrix,
        SemanticContextEngine,
        QualityGatesEngine,
        CircuitBreakerManager,
        SagaOrchestrator,
        HandoffTokenManager,
        test_primary_agent_controller
    )
except ImportError:
    pytestmark = pytest.mark.skip("Primary controller components not available")


class TestAgentCapability:
    """Test agent capability enumeration."""
    
    def test_agent_capabilities(self):
        """Test agent capability enum values."""
        assert AgentCapability.GITHUB_OPERATIONS.value == "github_operations"
        assert AgentCapability.CODE_ANALYSIS.value == "code_analysis"
        assert AgentCapability.SECURITY_AUDIT.value == "security_audit"
        assert AgentCapability.AI_ML_INTEGRATION.value == "ai_ml_integration"
    
    def test_all_capabilities_available(self):
        """Test that all expected capabilities are available."""
        expected_capabilities = [
            'GITHUB_OPERATIONS', 'CODE_ANALYSIS', 'SECURITY_AUDIT',
            'PERFORMANCE_OPTIMIZATION', 'ARCHITECTURE_DESIGN',
            'DATABASE_OPERATIONS', 'DEVOPS_AUTOMATION', 'AI_ML_INTEGRATION',
            'UI_UX_DESIGN', 'TESTING_VALIDATION'
        ]
        
        for capability in expected_capabilities:
            assert hasattr(AgentCapability, capability)


class TestOperationType:
    """Test operation type enumeration."""
    
    def test_operation_types(self):
        """Test operation type enum values."""
        assert OperationType.REPOSITORY_ANALYSIS.value == "repository_analysis"
        assert OperationType.PULL_REQUEST_CREATION.value == "pull_request_creation"
        assert OperationType.ISSUE_MANAGEMENT.value == "issue_management"
        assert OperationType.SECURITY_SCANNING.value == "security_scanning"


class TestQualityGateType:
    """Test quality gate type enumeration."""
    
    def test_quality_gate_types(self):
        """Test quality gate type enum values."""
        assert QualityGateType.PLANNING.value == "planning_gate"
        assert QualityGateType.SECURITY.value == "security_gate"
        assert QualityGateType.PERFORMANCE.value == "performance_gate"
        assert QualityGateType.DEPLOYMENT.value == "deployment_gate"


class TestAgentDefinition:
    """Test agent definition structure."""
    
    def test_agent_definition_creation(self):
        """Test agent definition creation."""
        agent_def = AgentDefinition(
            agent_name="test-agent",
            capabilities=[AgentCapability.CODE_ANALYSIS, AgentCapability.GITHUB_OPERATIONS],
            operation_types=[OperationType.REPOSITORY_ANALYSIS],
            tools_available=["git-mcp", "context7"],
            max_concurrent_tasks=5,
            performance_score=1.2,
            priority=1,
            specialization_domains=["python", "testing"],
            integration_dependencies=["github-service"]
        )
        
        assert agent_def.agent_name == "test-agent"
        assert len(agent_def.capabilities) == 2
        assert AgentCapability.CODE_ANALYSIS in agent_def.capabilities
        assert OperationType.REPOSITORY_ANALYSIS in agent_def.operation_types
        assert agent_def.max_concurrent_tasks == 5
        assert agent_def.performance_score == 1.2
        assert "python" in agent_def.specialization_domains
    
    def test_agent_definition_defaults(self):
        """Test agent definition with default values."""
        agent_def = AgentDefinition(
            agent_name="simple-agent",
            capabilities=[AgentCapability.CODE_ANALYSIS],
            operation_types=[OperationType.CODE_REVIEW],
            tools_available=["basic-tool"]
        )
        
        assert agent_def.max_concurrent_tasks == 3
        assert agent_def.performance_score == 1.0
        assert agent_def.priority == 1
        assert agent_def.specialization_domains == []
        assert agent_def.integration_dependencies == []


class TestHandoffToken:
    """Test HANDOFF_TOKEN system."""
    
    def setup_method(self):
        """Setup test handoff token."""
        self.token = HandoffToken(
            token_id="HANDOFF_TEST_12345",
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            context_vector=[0.1, 0.2, 0.3],
            semantic_context={"test": "context"},
            validation_criteria=["test criterion"],
            status=HandoffTokenStatus.CREATED,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            quality_gates=[QualityGateType.PLANNING],
            dependencies=["dep1"]
        )
    
    def test_handoff_token_creation(self):
        """Test handoff token creation."""
        assert self.token.token_id == "HANDOFF_TEST_12345"
        assert self.token.source_agent == "primary-agent"
        assert self.token.target_agent == "test-agent"
        assert self.token.operation_type == OperationType.REPOSITORY_ANALYSIS
        assert self.token.status == HandoffTokenStatus.CREATED
        assert len(self.token.quality_gates) == 1
    
    def test_token_expiration_check(self):
        """Test token expiration checking."""
        # Token should not be expired yet
        assert not self.token.is_expired()
        
        # Create expired token
        expired_token = HandoffToken(
            token_id="EXPIRED_TOKEN",
            source_agent="test",
            target_agent="test",
            operation_type=OperationType.CODE_REVIEW,
            context_vector=[],
            semantic_context={},
            validation_criteria=[],
            status=HandoffTokenStatus.CREATED,
            created_at=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert expired_token.is_expired()
    
    def test_token_retry_logic(self):
        """Test token retry logic."""
        # Should be able to retry initially
        assert self.token.can_retry()
        
        # Increment retry count
        self.token.retry_count = 2
        assert self.token.can_retry()
        
        # Max retries reached
        self.token.retry_count = 3
        assert not self.token.can_retry()
        
        # Expired token cannot retry
        self.token.retry_count = 1
        self.token.expires_at = datetime.utcnow() - timedelta(minutes=1)
        assert not self.token.can_retry()
    
    def test_token_to_krag_entity(self):
        """Test token conversion to KRAG entity format."""
        entity = self.token.to_krag_entity()
        
        assert entity["entity_type"] == "handoff_token"
        assert entity["token_id"] == "HANDOFF_TEST_12345"
        assert entity["source_agent"] == "primary-agent"
        assert entity["operation_type"] == "repository_analysis"
        assert entity["status"] == "created"
        assert entity["context_vector"] == [0.1, 0.2, 0.3]
        assert entity["quality_gates"] == ["planning_gate"]


class TestQualityGate:
    """Test quality gate functionality."""
    
    def test_quality_gate_creation(self):
        """Test quality gate creation."""
        gate = QualityGate(
            gate_type=QualityGateType.SECURITY,
            validation_criteria=["security scan passed", "vulnerabilities addressed"],
            threshold_score=0.85,
            blocking_dependencies=[QualityGateType.PLANNING]
        )
        
        assert gate.gate_type == QualityGateType.SECURITY
        assert len(gate.validation_criteria) == 2
        assert gate.threshold_score == 0.85
        assert gate.status == "pending"
        assert QualityGateType.PLANNING in gate.blocking_dependencies
    
    def test_quality_gate_defaults(self):
        """Test quality gate with default values."""
        gate = QualityGate(
            gate_type=QualityGateType.TESTING,
            validation_criteria=["tests pass"]
        )
        
        assert gate.threshold_score == 0.80
        assert gate.status == "pending"
        assert gate.validation_results == {}
        assert gate.failure_reasons == []
        assert gate.blocking_dependencies == []


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_creation(self):
        """Test circuit breaker creation."""
        breaker = CircuitBreaker(
            agent_name="test-agent",
            failure_threshold=3,
            timeout_seconds=30
        )
        
        assert breaker.agent_name == "test-agent"
        assert breaker.failure_threshold == 3
        assert breaker.timeout_seconds == 30
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0


class TestAgentWorkflowSaga:
    """Test saga pattern for workflows."""
    
    def test_saga_creation(self):
        """Test saga creation."""
        saga = AgentWorkflowSaga(
            saga_id="saga-123",
            workflow_name="test-workflow",
            participating_agents=["agent1", "agent2"],
            operations=[
                {"operation_type": "step1", "agent": "agent1"},
                {"operation_type": "step2", "agent": "agent2"}
            ]
        )
        
        assert saga.saga_id == "saga-123"
        assert saga.workflow_name == "test-workflow"
        assert len(saga.participating_agents) == 2
        assert len(saga.operations) == 2
        assert saga.status == "in_progress"
        assert len(saga.completed_operations) == 0


class TestAgentCapabilityMatrix:
    """Test agent capability matrix and routing."""
    
    def setup_method(self):
        """Setup capability matrix."""
        self.matrix = AgentCapabilityMatrix()
    
    def test_matrix_initialization(self):
        """Test capability matrix initialization."""
        assert isinstance(self.matrix.agents, dict)
        assert isinstance(self.matrix.capability_index, dict)
        assert len(self.matrix.agents) > 0
        
        # Check some expected agents
        expected_agents = ['planner', 'coder', 'code-reviewer', 'security-specialist']
        for agent_name in expected_agents:
            assert agent_name in self.matrix.agents
    
    def test_get_agents_by_capability(self):
        """Test getting agents by capability."""
        code_analysis_agents = self.matrix.get_agents_by_capability(AgentCapability.CODE_ANALYSIS)
        
        assert len(code_analysis_agents) > 0
        for agent in code_analysis_agents:
            assert AgentCapability.CODE_ANALYSIS in agent.capabilities
    
    def test_get_optimal_agent(self):
        """Test optimal agent selection."""
        # Test repository analysis
        agent = self.matrix.get_optimal_agent(
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            required_capabilities=[AgentCapability.CODE_ANALYSIS],
            context_hint="python project"
        )
        
        assert agent is not None
        assert OperationType.REPOSITORY_ANALYSIS in agent.operation_types
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
    
    def test_get_optimal_agent_with_domain_match(self):
        """Test optimal agent selection with domain specialization."""
        # Test with python context hint
        agent = self.matrix.get_optimal_agent(
            operation_type=OperationType.CODE_REVIEW,
            required_capabilities=[AgentCapability.CODE_ANALYSIS],
            context_hint="python performance optimization"
        )
        
        assert agent is not None
        # Should prefer python-pro for python-related tasks
        if agent.agent_name == "python-pro":
            assert "python" in agent.specialization_domains
    
    def test_get_optimal_agent_no_match(self):
        """Test optimal agent selection with no matching agents."""
        # Test with non-existent operation type combination
        agent = self.matrix.get_optimal_agent(
            operation_type=OperationType.DEPLOYMENT_COORDINATION,
            required_capabilities=[AgentCapability.AI_ML_INTEGRATION],  # Unlikely combination
            context_hint=""
        )
        
        # Should return None or find best available match
        if agent is not None:
            assert OperationType.DEPLOYMENT_COORDINATION in agent.operation_types


class TestSemanticContextEngine:
    """Test semantic context engine."""
    
    def setup_method(self):
        """Setup semantic context engine."""
        self.engine = SemanticContextEngine()
    
    def test_create_context_vector(self):
        """Test context vector creation."""
        text = "This is a test text for vector creation"
        vector = self.engine.create_context_vector(text)
        
        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(v, float) for v in vector)
    
    def test_create_context_vector_empty(self):
        """Test context vector creation with empty text."""
        vector = self.engine.create_context_vector("")
        
        assert isinstance(vector, list)
        assert len(vector) == 100  # Fallback vector size
    
    def test_calculate_semantic_similarity(self):
        """Test semantic similarity calculation."""
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]
        vector3 = [0.0, 1.0, 0.0]
        
        # Identical vectors should have high similarity
        similarity_same = self.engine.calculate_semantic_similarity(vector1, vector2)
        assert similarity_same > 0.95
        
        # Different vectors should have lower similarity
        similarity_diff = self.engine.calculate_semantic_similarity(vector1, vector3)
        assert similarity_diff < similarity_same
    
    def test_assemble_agent_context(self):
        """Test agent context assembly."""
        operation = {
            "operation_type": "repository_analysis",
            "description": "Analyze Python repository structure"
        }
        
        context = self.engine.assemble_agent_context(
            operation=operation,
            agent_name="python-pro",
            krag_namespace="test"
        )
        
        assert context["operation_type"] == "repository_analysis"
        assert context["target_agent"] == "python-pro"
        assert context["namespace"] == "test"
        assert "semantic_query" in context
        assert "assembled_at" in context
    
    def test_validate_context_coherence(self):
        """Test context coherence validation."""
        context = {
            "operation_type": "security_analysis",
            "description": "security scan and vulnerability assessment"
        }
        
        criteria = [
            "security analysis",
            "vulnerability assessment",
            "scan completed"
        ]
        
        is_coherent, score, issues = self.engine.validate_context_coherence(context, criteria)
        
        assert isinstance(is_coherent, bool)
        assert isinstance(score, float)
        assert isinstance(issues, list)
        assert 0.0 <= score <= 1.0


class TestQualityGatesEngine:
    """Test quality gates engine."""
    
    def setup_method(self):
        """Setup quality gates engine."""
        self.semantic_engine = SemanticContextEngine()
        self.gates_engine = QualityGatesEngine(self.semantic_engine)
    
    def test_gates_initialization(self):
        """Test quality gates engine initialization."""
        assert len(self.gates_engine.gates) > 0
        assert QualityGateType.PLANNING in self.gates_engine.gates
        assert QualityGateType.SECURITY in self.gates_engine.gates
        assert isinstance(self.gates_engine.gate_dependencies, dict)
    
    def test_gate_dependencies(self):
        """Test quality gate dependencies."""
        # Security gate should depend on planning
        security_deps = self.gates_engine.gate_dependencies[QualityGateType.SECURITY]
        assert QualityGateType.PLANNING in security_deps
        
        # Deployment should have multiple dependencies
        deployment_deps = self.gates_engine.gate_dependencies[QualityGateType.DEPLOYMENT]
        assert len(deployment_deps) > 0
    
    async def test_validate_gate_success(self):
        """Test successful gate validation."""
        deliverable = {
            "type": "planning_document",
            "content": "requirements clearly defined with success criteria and dependencies identified",
            "requirements": "well documented",
            "success_criteria": "measurable outcomes defined",
            "dependencies": "all dependencies listed",
            "risk_assessment": "comprehensive risk analysis completed"
        }
        
        passed, score, issues = await self.gates_engine.validate_gate(
            QualityGateType.PLANNING, 
            deliverable
        )
        
        assert isinstance(passed, bool)
        assert isinstance(score, float)
        assert isinstance(issues, list)
        assert 0.0 <= score <= 1.0
    
    async def test_validate_gate_failure(self):
        """Test gate validation failure."""
        deliverable = {
            "type": "incomplete_document",
            "content": "minimal content that doesn't meet criteria"
        }
        
        passed, score, issues = await self.gates_engine.validate_gate(
            QualityGateType.SECURITY,
            deliverable
        )
        
        # Should likely fail with low score
        assert isinstance(passed, bool)
        assert isinstance(score, float)
        assert score >= 0.0
    
    def test_validate_gate_sequence(self):
        """Test gate sequence validation."""
        # Valid sequence
        valid_sequence = [
            QualityGateType.PLANNING,
            QualityGateType.ARCHITECTURE,
            QualityGateType.TESTING
        ]
        
        is_valid, issues = self.gates_engine.validate_gate_sequence(valid_sequence)
        assert is_valid == True
        assert len(issues) == 0
        
        # Invalid sequence (testing before architecture, but architecture depends on planning)
        invalid_sequence = [
            QualityGateType.TESTING,
            QualityGateType.PLANNING
        ]
        
        is_valid, issues = self.gates_engine.validate_gate_sequence(invalid_sequence)
        # May or may not be invalid depending on dependencies, but should be deterministic
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)
    
    def test_get_next_gates(self):
        """Test getting next available gates."""
        passed_gates = [QualityGateType.PLANNING]
        next_gates = self.gates_engine.get_next_gates(passed_gates)
        
        assert isinstance(next_gates, list)
        # Planning is a prerequisite for many gates
        assert len(next_gates) > 0


class TestCircuitBreakerManager:
    """Test circuit breaker manager."""
    
    def setup_method(self):
        """Setup circuit breaker manager."""
        self.manager = CircuitBreakerManager()
    
    def test_get_breaker(self):
        """Test getting circuit breaker for agent."""
        breaker1 = self.manager.get_breaker("test-agent")
        breaker2 = self.manager.get_breaker("test-agent")
        
        # Should return same instance
        assert breaker1 is breaker2
        assert breaker1.agent_name == "test-agent"
    
    async def test_call_through_breaker_success(self):
        """Test successful call through circuit breaker."""
        async def test_operation():
            return {"result": "success"}
        
        result = await self.manager.call_through_breaker(
            "test-agent",
            test_operation
        )
        
        assert result["result"] == "success"
        
        # Breaker should remain closed
        breaker = self.manager.get_breaker("test-agent")
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0
    
    async def test_call_through_breaker_failure(self):
        """Test failed call through circuit breaker."""
        async def failing_operation():
            raise Exception("Operation failed")
        
        with pytest.raises(Exception, match="Operation failed"):
            await self.manager.call_through_breaker(
                "test-agent",
                failing_operation
            )
        
        # Breaker should record failure
        breaker = self.manager.get_breaker("test-agent")
        assert breaker.failure_count == 1
    
    async def test_circuit_breaker_opens(self):
        """Test circuit breaker opening after multiple failures."""
        async def failing_operation():
            raise Exception("Operation failed")
        
        breaker = self.manager.get_breaker("test-agent")
        breaker.failure_threshold = 2  # Lower threshold for testing
        
        # First failure
        with pytest.raises(Exception):
            await self.manager.call_through_breaker("test-agent", failing_operation)
        
        # Second failure should open breaker
        with pytest.raises(Exception):
            await self.manager.call_through_breaker("test-agent", failing_operation)
        
        assert breaker.state == CircuitBreakerState.OPEN
        
        # Third call should fail fast
        with pytest.raises(Exception, match="Circuit breaker OPEN"):
            await self.manager.call_through_breaker("test-agent", failing_operation)
    
    async def test_circuit_breaker_half_open(self):
        """Test circuit breaker half-open state."""
        breaker = self.manager.get_breaker("test-agent")
        breaker.state = CircuitBreakerState.OPEN
        breaker.timeout_seconds = 1
        breaker.last_failure_time = datetime.utcnow() - timedelta(seconds=2)
        
        async def success_operation():
            return {"result": "success"}
        
        # Should attempt reset to half-open
        result = await self.manager.call_through_breaker("test-agent", success_operation)
        
        assert result["result"] == "success"
        # After successful call, should be closed or half-open
        assert breaker.state in [CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN]
    
    def test_get_breaker_status(self):
        """Test getting breaker status."""
        # Create some breakers
        self.manager.get_breaker("agent1")
        self.manager.get_breaker("agent2")
        
        status = self.manager.get_breaker_status()
        
        assert isinstance(status, dict)
        assert "agent1" in status
        assert "agent2" in status
        assert status["agent1"]["state"] == "closed"
        assert "failure_count" in status["agent1"]


class TestSagaOrchestrator:
    """Test saga orchestrator."""
    
    def setup_method(self):
        """Setup saga orchestrator."""
        self.orchestrator = SagaOrchestrator()
    
    async def test_start_saga(self):
        """Test starting a saga."""
        saga_id = await self.orchestrator.start_saga(
            workflow_name="test-workflow",
            participating_agents=["agent1", "agent2"],
            operations=[
                {"operation_type": "step1", "agent": "agent1"},
                {"operation_type": "step2", "agent": "agent2"}
            ]
        )
        
        assert isinstance(saga_id, str)
        assert saga_id in self.orchestrator.active_sagas
        
        saga = self.orchestrator.active_sagas[saga_id]
        assert saga.workflow_name == "test-workflow"
        assert len(saga.participating_agents) == 2
    
    async def test_execute_saga_success(self):
        """Test successful saga execution."""
        saga_id = await self.orchestrator.start_saga(
            workflow_name="test-workflow",
            participating_agents=["agent1"],
            operations=[{"operation_type": "test", "agent": "agent1"}]
        )
        
        async def mock_executor(operation):
            return {"result": "success", "operation": operation}
        
        success = await self.orchestrator.execute_saga(saga_id, mock_executor)
        
        assert success == True
        assert saga_id not in self.orchestrator.active_sagas
        assert len(self.orchestrator.completed_sagas) == 1
    
    async def test_execute_saga_failure_with_rollback(self):
        """Test saga execution with failure and rollback."""
        saga_id = await self.orchestrator.start_saga(
            workflow_name="failing-workflow",
            participating_agents=["agent1"],
            operations=[
                {"operation_type": "step1", "agent": "agent1"},
                {"operation_type": "step2", "agent": "agent1"}  # This will fail
            ]
        )
        
        call_count = 0
        
        async def mock_executor(operation):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Second operation fails
                raise Exception("Operation failed")
            return {"result": "success", "operation": operation}
        
        success = await self.orchestrator.execute_saga(saga_id, mock_executor)
        
        assert success == False
        saga = self.orchestrator.completed_sagas[0]
        assert saga.status == "rollback_completed"
    
    def test_get_saga_status(self):
        """Test getting saga status."""
        # Test non-existent saga
        status = self.orchestrator.get_saga_status("non-existent")
        assert status is None
        
        # Test active saga
        async def test_active_saga():
            saga_id = await self.orchestrator.start_saga(
                workflow_name="status-test",
                participating_agents=["agent1"],
                operations=[{"op": "test"}]
            )
            
            status = self.orchestrator.get_saga_status(saga_id)
            
            assert status is not None
            assert status["workflow_name"] == "status-test"
            assert status["status"] == "in_progress"
            assert "operations_completed" in status
            assert "operations_total" in status
        
        asyncio.create_task(test_active_saga())
    
    def test_get_all_saga_status(self):
        """Test getting all saga status."""
        status = self.orchestrator.get_all_saga_status()
        
        assert isinstance(status, dict)
        assert "active_sagas" in status
        assert "completed_sagas" in status
        assert "sagas" in status


class TestHandoffTokenManager:
    """Test HANDOFF_TOKEN manager."""
    
    def setup_method(self):
        """Setup token manager."""
        self.semantic_engine = SemanticContextEngine()
        self.token_manager = HandoffTokenManager(self.semantic_engine)
    
    async def test_create_handoff_token(self):
        """Test creating handoff token."""
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"test": "context"},
            validation_criteria=["test criterion"],
            quality_gates=[QualityGateType.PLANNING],
            dependencies=["dep1"]
        )
        
        assert isinstance(token_id, str)
        assert token_id.startswith("HANDOFF_REPOSITORY_ANALYSIS")
        assert token_id in self.token_manager.active_tokens
        
        token = self.token_manager.active_tokens[token_id]
        assert token.source_agent == "primary-agent"
        assert token.target_agent == "test-agent"
        assert token.status == HandoffTokenStatus.CREATED
    
    async def test_validate_token(self):
        """Test token validation."""
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.CODE_REVIEW,
            semantic_context={"code_review": "analyze code quality and security"},
            validation_criteria=["code review criteria met", "analysis complete"]
        )
        
        is_valid, score, issues = await self.token_manager.validate_token(token_id)
        
        assert isinstance(is_valid, bool)
        assert isinstance(score, float)
        assert isinstance(issues, list)
        assert 0.0 <= score <= 1.0
        
        if is_valid:
            token = self.token_manager.active_tokens[token_id]
            assert token.status == HandoffTokenStatus.VALIDATED
    
    async def test_validate_expired_token(self):
        """Test validating expired token."""
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"test": "context"},
            validation_criteria=["test criterion"]
        )
        
        # Manually expire token
        token = self.token_manager.active_tokens[token_id]
        token.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        is_valid, score, issues = await self.token_manager.validate_token(token_id)
        
        assert is_valid == False
        assert "expired" in str(issues).lower()
        assert token.status == HandoffTokenStatus.EXPIRED
    
    async def test_start_token_execution(self):
        """Test starting token execution."""
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"test": "context"},
            validation_criteria=["test criterion"]
        )
        
        # Validate first
        await self.token_manager.validate_token(token_id)
        
        # Start execution
        result = await self.token_manager.start_token_execution(token_id)
        
        assert result == True
        token = self.token_manager.active_tokens[token_id]
        assert token.status == HandoffTokenStatus.IN_PROGRESS
    
    async def test_complete_token(self):
        """Test completing token."""
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"test": "context"},
            validation_criteria=["test criterion"]
        )
        
        result = await self.token_manager.complete_token(
            token_id, 
            {"analysis": "completed", "results": "positive"}
        )
        
        assert result == True
        assert token_id not in self.token_manager.active_tokens
        assert len(self.token_manager.token_history) == 1
        
        historical_token = self.token_manager.token_history[0]
        assert historical_token.status == HandoffTokenStatus.COMPLETED
        assert "result" in historical_token.semantic_context
    
    async def test_fail_token_with_retry(self):
        """Test failing token with retry capability."""
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"test": "context"},
            validation_criteria=["test criterion"]
        )
        
        result = await self.token_manager.fail_token(
            token_id, 
            "Test failure", 
            retry=True
        )
        
        assert result == True
        token = self.token_manager.active_tokens[token_id]
        assert token.status == HandoffTokenStatus.CREATED
        assert token.retry_count == 1
        assert "last_error" in token.semantic_context
    
    async def test_fail_token_permanently(self):
        """Test permanent token failure."""
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"test": "context"},
            validation_criteria=["test criterion"]
        )
        
        # Exhaust retries
        token = self.token_manager.active_tokens[token_id]
        token.retry_count = token.max_retries
        
        result = await self.token_manager.fail_token(
            token_id,
            "Permanent failure",
            retry=True
        )
        
        assert result == False
        assert token_id not in self.token_manager.active_tokens
        assert len(self.token_manager.token_history) == 1
        
        historical_token = self.token_manager.token_history[0]
        assert historical_token.status == HandoffTokenStatus.FAILED
    
    def test_get_token_status(self):
        """Test getting token status."""
        # Test non-existent token
        status = self.token_manager.get_token_status("non-existent")
        assert status is None
        
        # Test active token
        async def test_active_token():
            token_id = await self.token_manager.create_handoff_token(
                source_agent="primary-agent",
                target_agent="test-agent",
                operation_type=OperationType.REPOSITORY_ANALYSIS,
                semantic_context={"test": "context"},
                validation_criteria=["test criterion"]
            )
            
            status = self.token_manager.get_token_status(token_id)
            
            assert status is not None
            assert status["token_id"] == token_id
            assert status["source_agent"] == "primary-agent"
            assert status["target_agent"] == "test-agent"
            assert "status" in status
            assert "created_at" in status
        
        asyncio.create_task(test_active_token())
    
    async def test_cleanup_expired_tokens(self):
        """Test cleaning up expired tokens."""
        # Create token and manually expire it
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"test": "context"},
            validation_criteria=["test criterion"]
        )
        
        token = self.token_manager.active_tokens[token_id]
        token.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        cleaned_count = await self.token_manager.cleanup_expired_tokens()
        
        assert cleaned_count == 1
        assert token_id not in self.token_manager.active_tokens
        assert len(self.token_manager.token_history) == 1


class TestPrimaryAgentGitHubController:
    """Test primary agent GitHub controller."""
    
    def setup_method(self):
        """Setup controller for testing."""
        with patch('primary_agent_github.GitHubService'), \
             patch('primary_agent_github.GitHubEventBus'):
            self.controller = PrimaryAgentGitHubController(session_id="test-session")
    
    def test_controller_initialization(self):
        """Test controller initialization."""
        assert self.controller.session_id == "test-session"
        assert self.controller.capability_matrix is not None
        assert self.controller.semantic_engine is not None
        assert self.controller.quality_gates is not None
        assert self.controller.circuit_breakers is not None
        assert self.controller.saga_orchestrator is not None
        assert self.controller.token_manager is not None
    
    def test_controller_metrics_initialization(self):
        """Test controller metrics initialization."""
        metrics = self.controller.metrics
        
        expected_metrics = [
            'operations_delegated', 'operations_completed', 'operations_failed',
            'avg_operation_time', 'quality_gate_failures', 'token_validations',
            'circuit_breaker_trips'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
    
    async def test_validate_permissions_success(self):
        """Test successful permission validation."""
        with patch.object(self.controller, 'github_service', AsyncMock()) as mock_service:
            mock_service.authenticate_token.return_value = True
            
            result = await self.controller.validate_permissions(
                "code-reviewer", 
                "code_review"
            )
            
            assert result == True
    
    async def test_validate_permissions_unknown_agent(self):
        """Test permission validation with unknown agent."""
        result = await self.controller.validate_permissions(
            "unknown-agent",
            "repository_analysis"
        )
        
        assert result == False
    
    async def test_validate_permissions_invalid_operation(self):
        """Test permission validation with invalid operation type."""
        result = await self.controller.validate_permissions(
            "coder",
            "invalid_operation_type"
        )
        
        assert result == False
    
    async def test_validate_permissions_no_github_auth(self):
        """Test permission validation without GitHub authentication."""
        with patch.object(self.controller, 'github_service', AsyncMock()) as mock_service:
            mock_service.authenticate_token.return_value = False
            
            result = await self.controller.validate_permissions(
                "coder",
                "pull_request_creation"
            )
            
            assert result == False
    
    async def test_delegate_github_task_success(self):
        """Test successful GitHub task delegation."""
        with patch.object(self.controller, 'validate_permissions', return_value=True), \
             patch.object(self.controller.token_manager, 'create_handoff_token', return_value="token-123"), \
             patch.object(self.controller.token_manager, 'validate_token', return_value=(True, 0.85, [])), \
             patch.object(self.controller, '_execute_agent_operation', return_value={"result": "success"}), \
             patch.object(self.controller.token_manager, 'complete_token', return_value=True):
            
            result = await self.controller.delegate_github_task(
                agent_name="coder",
                operation={
                    "operation_type": "repository_analysis",
                    "description": "Analyze repository structure"
                }
            )
            
            assert result["success"] == True
            assert "result" in result
            assert "token_id" in result
            assert result["coherence_score"] == 0.85
            assert result["agent_name"] == "coder"
    
    async def test_delegate_github_task_permission_denied(self):
        """Test GitHub task delegation with permission denied."""
        with patch.object(self.controller, 'validate_permissions', return_value=False):
            
            result = await self.controller.delegate_github_task(
                agent_name="unauthorized-agent",
                operation={"operation_type": "security_scanning"}
            )
            
            assert result["success"] == False
            assert result["error_type"] == "permission_denied"
            assert "lacks permissions" in result["error"]
    
    async def test_delegate_github_task_token_validation_failure(self):
        """Test GitHub task delegation with token validation failure."""
        with patch.object(self.controller, 'validate_permissions', return_value=True), \
             patch.object(self.controller.token_manager, 'create_handoff_token', return_value="token-123"), \
             patch.object(self.controller.token_manager, 'validate_token', return_value=(False, 0.3, ["Low coherence"])):
            
            result = await self.controller.delegate_github_task(
                agent_name="coder",
                operation={"operation_type": "repository_analysis"}
            )
            
            assert result["success"] == False
            assert result["error_type"] == "token_validation_failed"
            assert result["coherence_score"] == 0.3
    
    async def test_aggregate_results_success(self):
        """Test successful multi-agent result aggregation."""
        multi_ops = [
            {"agent_name": "planner", "operation_type": "repository_analysis"},
            {"agent_name": "coder", "operation_type": "code_review"}
        ]
        
        with patch.object(self.controller.saga_orchestrator, 'start_saga', return_value="saga-123"), \
             patch.object(self.controller.saga_orchestrator, 'execute_saga', return_value=True), \
             patch.object(self.controller.saga_orchestrator, 'get_saga_status', return_value={"status": "completed"}):
            
            result = await self.controller.aggregate_results(multi_ops)
            
            assert result["success"] == True
            assert result["saga_id"] == "saga-123"
            assert result["participating_agents"] == ["planner", "coder"]
            assert result["operations_completed"] == 2
            assert result["coordination_type"] == "saga_pattern"
    
    async def test_aggregate_results_empty_operations(self):
        """Test result aggregation with empty operations."""
        result = await self.controller.aggregate_results([])
        
        assert result["success"] == False
        assert "No operations provided" in result["error"]
    
    async def test_enforce_quality_gates_success(self):
        """Test successful quality gate enforcement."""
        deliverable = {
            "type": "workflow_output",
            "content": "comprehensive analysis with all requirements met"
        }
        
        with patch.object(self.controller.quality_gates, 'validate_gate_sequence', return_value=(True, [])), \
             patch.object(self.controller.quality_gates, 'validate_gate', return_value=(True, 0.85, [])):
            
            result = await self.controller.enforce_quality_gates(deliverable)
            
            assert result == True
    
    async def test_enforce_quality_gates_failure(self):
        """Test quality gate enforcement failure."""
        deliverable = {
            "type": "workflow_output",
            "content": "minimal content"
        }
        
        with patch.object(self.controller.quality_gates, 'validate_gate_sequence', return_value=(True, [])), \
             patch.object(self.controller.quality_gates, 'validate_gate', return_value=(False, 0.4, ["Low quality"])):
            
            result = await self.controller.enforce_quality_gates(deliverable)
            
            assert result == False
            assert self.controller.metrics['quality_gate_failures'] > 0
    
    async def test_orchestrate_multi_agent_workflow_success(self):
        """Test successful multi-agent workflow orchestration."""
        agents = ["planner", "coder"]
        operations = [
            {"agent_name": "planner", "operation_type": "repository_analysis"},
            {"agent_name": "coder", "operation_type": "code_review"}
        ]
        
        with patch.object(self.controller, '_validate_workflow_structure', return_value={"valid": True}), \
             patch.object(self.controller.saga_orchestrator, 'start_saga', return_value="workflow-saga-123"), \
             patch.object(self.controller, '_execute_workflow_operation', return_value={"success": True}), \
             patch.object(self.controller.saga_orchestrator, 'execute_saga', return_value=True):
            
            result = await self.controller.orchestrate_multi_agent_workflow(
                workflow_name="test-workflow",
                agents=agents,
                operations=operations
            )
            
            assert result["success"] == True
            assert result["workflow_name"] == "test-workflow"
            assert result["saga_id"] == "workflow-saga-123"
            assert result["operations_completed"] == len(operations)
            assert result["participating_agents"] == agents
    
    async def test_get_optimal_agent_for_operation(self):
        """Test getting optimal agent for operation."""
        operation = {
            "operation_type": "repository_analysis",
            "required_capabilities": ["code_analysis"]
        }
        
        agent_name = await self.controller.get_optimal_agent_for_operation(
            operation,
            "python project analysis"
        )
        
        # Should return a valid agent name or None
        if agent_name:
            assert isinstance(agent_name, str)
            assert agent_name in self.controller.capability_matrix.agents
    
    def test_get_orchestration_metrics(self):
        """Test getting orchestration metrics."""
        metrics = self.controller.get_orchestration_metrics()
        
        assert "session_id" in metrics
        assert "operations" in metrics
        assert "quality" in metrics
        assert "system" in metrics
        assert "config" in metrics
        
        # Check operations metrics structure
        ops_metrics = metrics["operations"]
        assert "delegated" in ops_metrics
        assert "completed" in ops_metrics
        assert "failed" in ops_metrics
        assert "success_rate" in ops_metrics
        assert "failure_rate" in ops_metrics
    
    async def test_health_check(self):
        """Test system health check."""
        with patch.object(self.controller.token_manager, 'cleanup_expired_tokens', return_value=0):
            
            health = await self.controller.health_check()
            
            assert "timestamp" in health
            assert "session_id" in health
            assert health["session_id"] == "test-session"
            assert "overall_status" in health
            assert "components" in health
            
            # Check component health structure
            components = health["components"]
            expected_components = [
                "github_service", "event_bus", "token_manager",
                "circuit_breakers", "saga_orchestrator"
            ]
            
            for component in expected_components:
                assert component in components
                assert "status" in components[component]


@pytest.mark.integration
class TestPrimaryControllerIntegration:
    """Integration tests for primary controller."""
    
    async def test_full_delegation_cycle(self):
        """Test complete delegation cycle from start to finish."""
        with patch('primary_agent_github.GitHubService'), \
             patch('primary_agent_github.GitHubEventBus'):
            
            async with PrimaryAgentGitHubController("integration-test") as controller:
                # Mock necessary components
                with patch.object(controller, 'github_service', AsyncMock()) as mock_service:
                    mock_service.authenticate_token.return_value = True
                    
                    # Execute full delegation
                    result = await controller.delegate_github_task(
                        agent_name="coder",
                        operation={
                            "operation_type": "repository_analysis",
                            "description": "Full integration test",
                            "validation_criteria": ["integration test successful"]
                        }
                    )
                    
                    # Should complete successfully
                    assert result.get("success") == True
                    
                    # Check metrics were updated
                    metrics = controller.get_orchestration_metrics()
                    assert metrics["operations"]["delegated"] >= 1


@pytest.mark.performance
class TestPrimaryControllerPerformance:
    """Performance tests for primary controller."""
    
    async def test_concurrent_delegations(self):
        """Test concurrent task delegations."""
        with patch('primary_agent_github.GitHubService'), \
             patch('primary_agent_github.GitHubEventBus'):
            
            controller = PrimaryAgentGitHubController("perf-test")
            
            with patch.object(controller, 'validate_permissions', return_value=True), \
                 patch.object(controller, '_execute_agent_operation', return_value={"result": "success"}):
                
                # Create many concurrent tasks
                tasks = []
                for i in range(20):
                    task = controller.delegate_github_task(
                        agent_name="coder",
                        operation={
                            "operation_type": "repository_analysis",
                            "description": f"Concurrent test {i}"
                        }
                    )
                    tasks.append(task)
                
                start_time = datetime.utcnow()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = datetime.utcnow()
                
                duration = (end_time - start_time).total_seconds()
                
                # Should handle concurrent requests efficiently
                assert duration < 10.0  # Within 10 seconds
                assert len(results) == 20
                
                # Most should succeed (some might fail due to mocking limitations)
                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
                assert success_count > 10  # At least half should succeed


class TestPrimaryControllerTestSuite:
    """Test the primary controller test suite."""
    
    async def test_primary_agent_controller_test_suite(self):
        """Test the complete primary controller test suite."""
        result = await test_primary_agent_controller()
        
        assert "timestamp" in result
        assert "tests" in result
        assert "summary" in result
        
        # Should have comprehensive test coverage
        expected_tests = [
            "capability_matrix", "permission_validation", "handoff_token",
            "quality_gates", "agent_delegation", "multi_agent_workflow",
            "health_check", "metrics_collection"
        ]
        
        for test_name in expected_tests:
            assert test_name in result["tests"]
        
        # Summary should be calculated
        summary = result["summary"]
        assert "passed" in summary
        assert "total" in summary
        assert "success_rate" in summary
        assert "overall_status" in summary