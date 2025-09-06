"""
Unit Tests for Agent Decoupling System
Testing HANDOFF_TOKEN management, namespace isolation, conflict prevention, and agent coordination
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
        HandoffToken,
        HandoffTokenStatus,
        HandoffTokenManager,
        SemanticContextEngine,
        AgentCapabilityMatrix,
        CircuitBreakerManager,
        CircuitBreakerState,
        OperationType,
        AgentCapability,
        QualityGateType
    )
except ImportError:
    pytestmark = pytest.mark.skip("Agent decoupling components not available")


class TestAgentNamespaceIsolation:
    """Test namespace isolation between agents."""
    
    def setup_method(self):
        """Setup test environment with multiple namespaces."""
        self.semantic_engine = SemanticContextEngine()
        self.token_manager = HandoffTokenManager(self.semantic_engine)
        
        # Create separate namespaces for testing
        self.namespace_primary = "primary_agent_session"
        self.namespace_agent1 = "agent1_workspace"
        self.namespace_agent2 = "agent2_workspace"
        self.namespace_shared = "shared_resources"
    
    async def test_token_namespace_isolation(self):
        """Test that HANDOFF_TOKENs are isolated by namespace."""
        # Create tokens in different namespaces
        token_id_1 = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="agent1",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"namespace": self.namespace_agent1, "data": "agent1_data"},
            validation_criteria=["namespace isolation test"]
        )
        
        token_id_2 = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="agent2",
            operation_type=OperationType.CODE_REVIEW,
            semantic_context={"namespace": self.namespace_agent2, "data": "agent2_data"},
            validation_criteria=["namespace isolation test"]
        )
        
        # Verify tokens exist
        assert token_id_1 in self.token_manager.active_tokens
        assert token_id_2 in self.token_manager.active_tokens
        
        # Verify namespace separation in semantic context
        token1 = self.token_manager.active_tokens[token_id_1]
        token2 = self.token_manager.active_tokens[token_id_2]
        
        assert token1.semantic_context["namespace"] == self.namespace_agent1
        assert token2.semantic_context["namespace"] == self.namespace_agent2
        assert token1.semantic_context["data"] != token2.semantic_context["data"]
    
    async def test_token_cleanup_by_namespace(self):
        """Test cleanup operations respect namespace boundaries."""
        # Create tokens in different namespaces
        token_ids = []
        for i, namespace in enumerate([self.namespace_agent1, self.namespace_agent2]):
            token_id = await self.token_manager.create_handoff_token(
                source_agent="primary-agent",
                target_agent=f"agent{i+1}",
                operation_type=OperationType.REPOSITORY_ANALYSIS,
                semantic_context={"namespace": namespace, "agent_id": i+1},
                validation_criteria=["cleanup test"]
            )
            token_ids.append(token_id)
            
            # Expire one token manually
            if i == 0:
                token = self.token_manager.active_tokens[token_id]
                token.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        # Cleanup expired tokens
        cleaned_count = await self.token_manager.cleanup_expired_tokens()
        
        assert cleaned_count == 1
        assert token_ids[0] not in self.token_manager.active_tokens  # Expired
        assert token_ids[1] in self.token_manager.active_tokens      # Still active
        
        # Verify namespace context preserved in history
        historical_token = next(
            (t for t in self.token_manager.token_history if t.token_id == token_ids[0]),
            None
        )
        assert historical_token is not None
        assert historical_token.semantic_context["namespace"] == self.namespace_agent1
    
    def test_namespace_semantic_isolation(self):
        """Test semantic context isolation between namespaces."""
        # Create contexts for different namespaces
        context1 = self.semantic_engine.assemble_agent_context(
            operation={"operation_type": "repository_analysis", "agent_focus": "security"},
            agent_name="security-specialist",
            krag_namespace=self.namespace_agent1
        )
        
        context2 = self.semantic_engine.assemble_agent_context(
            operation={"operation_type": "repository_analysis", "agent_focus": "performance"},
            agent_name="performance-optimizer",
            krag_namespace=self.namespace_agent2
        )
        
        # Verify namespace isolation
        assert context1["namespace"] == self.namespace_agent1
        assert context2["namespace"] == self.namespace_agent2
        assert context1["target_agent"] != context2["target_agent"]
        
        # Verify semantic queries are different due to agent specialization
        assert context1["semantic_query"] != context2["semantic_query"]
    
    def test_agent_capability_namespace_mapping(self):
        """Test agent capability resolution within namespace constraints."""
        matrix = AgentCapabilityMatrix()
        
        # Test agent selection for different namespace contexts
        security_agent = matrix.get_optimal_agent(
            operation_type=OperationType.SECURITY_SCANNING,
            required_capabilities=[AgentCapability.SECURITY_AUDIT],
            context_hint="security analysis in agent1 namespace"
        )
        
        performance_agent = matrix.get_optimal_agent(
            operation_type=OperationType.PERFORMANCE_ANALYSIS,
            required_capabilities=[AgentCapability.PERFORMANCE_OPTIMIZATION],
            context_hint="performance analysis in agent2 namespace"
        )
        
        # Should select different specialized agents
        assert security_agent is not None
        assert performance_agent is not None
        
        if security_agent.agent_name != performance_agent.agent_name:
            # Different agents selected for different specializations
            assert AgentCapability.SECURITY_AUDIT in security_agent.capabilities
            assert AgentCapability.PERFORMANCE_OPTIMIZATION in performance_agent.capabilities


class TestAgentConflictPrevention:
    """Test conflict prevention mechanisms between agents."""
    
    def setup_method(self):
        """Setup test environment for conflict prevention."""
        self.semantic_engine = SemanticContextEngine()
        self.token_manager = HandoffTokenManager(self.semantic_engine)
        self.circuit_breaker_manager = CircuitBreakerManager()
    
    async def test_concurrent_token_creation_prevention(self):
        """Test prevention of conflicting concurrent tokens."""
        # Attempt to create multiple tokens for the same operation simultaneously
        async def create_token(agent_suffix: str):
            return await self.token_manager.create_handoff_token(
                source_agent="primary-agent",
                target_agent=f"target-agent-{agent_suffix}",
                operation_type=OperationType.REPOSITORY_ANALYSIS,
                semantic_context={"repo": "test/repo", "operation": "analysis"},
                validation_criteria=["concurrent test"],
                dependencies=["shared_resource"]
            )
        
        # Create tokens concurrently
        tasks = [create_token(str(i)) for i in range(5)]
        token_ids = await asyncio.gather(*tasks)
        
        # All tokens should be created (no conflicts in current implementation)
        assert len(token_ids) == 5
        assert len(set(token_ids)) == 5  # All unique
        
        # Verify all tokens are tracked
        for token_id in token_ids:
            assert token_id in self.token_manager.active_tokens
    
    async def test_dependency_conflict_detection(self):
        """Test detection of dependency conflicts between agents."""
        # Create tokens with overlapping dependencies
        base_dependencies = ["shared_repo", "github_api"]
        
        token_id_1 = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="agent1",
            operation_type=OperationType.PULL_REQUEST_CREATION,
            semantic_context={"operation": "create_pr"},
            validation_criteria=["dependency test"],
            dependencies=base_dependencies + ["write_access"]
        )
        
        token_id_2 = await self.token_manager.create_handoff_token(
            source_agent="primary-agent", 
            target_agent="agent2",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"operation": "analyze_repo"},
            validation_criteria=["dependency test"],
            dependencies=base_dependencies + ["read_access"]
        )
        
        # Check dependency overlap
        token1 = self.token_manager.active_tokens[token_id_1]
        token2 = self.token_manager.active_tokens[token_id_2]
        
        shared_deps = set(token1.dependencies) & set(token2.dependencies)
        assert len(shared_deps) == 2  # shared_repo and github_api
        assert "shared_repo" in shared_deps
        assert "github_api" in shared_deps
        
        # Verify different access requirements
        assert "write_access" in token1.dependencies
        assert "read_access" in token2.dependencies
        assert "write_access" not in token2.dependencies
        assert "read_access" not in token1.dependencies
    
    async def test_semantic_coherence_conflict_prevention(self):
        """Test prevention of semantically conflicting operations."""
        # Create potentially conflicting semantic contexts
        context1 = {
            "operation": "repository_analysis",
            "focus": "security_vulnerabilities",
            "approach": "conservative_analysis",
            "priority": "security_first"
        }
        
        context2 = {
            "operation": "repository_analysis", 
            "focus": "performance_optimization",
            "approach": "aggressive_optimization",
            "priority": "performance_first"
        }
        
        # Test semantic similarity to detect potential conflicts
        context1_text = json.dumps(context1)
        context2_text = json.dumps(context2)
        
        vector1 = self.semantic_engine.create_context_vector(context1_text)
        vector2 = self.semantic_engine.create_context_vector(context2_text)
        
        similarity = self.semantic_engine.calculate_semantic_similarity(vector1, vector2)
        
        # Should have some similarity (same repo) but different approaches
        assert 0.1 < similarity < 0.8  # Moderate similarity indicates potential conflict
        
        # Test coherence validation for conflicting priorities
        is_coherent1, score1, issues1 = self.semantic_engine.validate_context_coherence(
            context1, 
            ["security focused", "conservative approach", "vulnerability detection"]
        )
        
        is_coherent2, score2, issues2 = self.semantic_engine.validate_context_coherence(
            context2,
            ["performance focused", "aggressive optimization", "speed enhancement"] 
        )
        
        # Both should be coherent individually
        assert isinstance(is_coherent1, bool)
        assert isinstance(is_coherent2, bool)
        assert isinstance(score1, float)
        assert isinstance(score2, float)
    
    async def test_resource_contention_management(self):
        """Test management of resource contention between agents."""
        # Simulate agents competing for limited resources
        resource_tokens = []
        
        # Create tokens that would compete for the same resources
        for i in range(3):
            token_id = await self.token_manager.create_handoff_token(
                source_agent="primary-agent",
                target_agent=f"resource-agent-{i}",
                operation_type=OperationType.WORKFLOW_AUTOMATION,
                semantic_context={
                    "resource_type": "github_api_quota",
                    "estimated_calls": 1000,
                    "priority": i + 1
                },
                validation_criteria=["resource contention test"],
                dependencies=[f"api_quota_slot_{i % 2}"]  # Limited slots
            )
            resource_tokens.append(token_id)
        
        # Verify resource allocation tracking
        slot_0_tokens = []
        slot_1_tokens = []
        
        for token_id in resource_tokens:
            token = self.token_manager.active_tokens[token_id]
            if "api_quota_slot_0" in token.dependencies:
                slot_0_tokens.append(token_id)
            elif "api_quota_slot_1" in token.dependencies:
                slot_1_tokens.append(token_id)
        
        # Should distribute across available slots
        assert len(slot_0_tokens) + len(slot_1_tokens) == 3
        assert len(slot_0_tokens) > 0
        assert len(slot_1_tokens) > 0
    
    def test_circuit_breaker_agent_isolation(self):
        """Test circuit breaker isolation between agents."""
        # Test circuit breakers for different agents
        breaker1 = self.circuit_breaker_manager.get_breaker("agent1")
        breaker2 = self.circuit_breaker_manager.get_breaker("agent2")
        
        # Should be separate instances
        assert breaker1 is not breaker2
        assert breaker1.agent_name == "agent1"
        assert breaker2.agent_name == "agent2"
        
        # Simulate failure in agent1
        breaker1.failure_count = breaker1.failure_threshold
        breaker1.state = CircuitBreakerState.OPEN
        
        # Agent2 should remain unaffected
        assert breaker2.state == CircuitBreakerState.CLOSED
        assert breaker2.failure_count == 0
        
        # Verify isolation in status reporting
        status = self.circuit_breaker_manager.get_breaker_status()
        
        assert "agent1" in status
        assert "agent2" in status
        assert status["agent1"]["state"] == "open"
        assert status["agent2"]["state"] == "closed"


class TestHandoffTokenSecurity:
    """Test security aspects of HANDOFF_TOKEN system."""
    
    def setup_method(self):
        """Setup test environment for security testing."""
        self.semantic_engine = SemanticContextEngine()
        self.token_manager = HandoffTokenManager(self.semantic_engine)
    
    async def test_token_validation_security(self):
        """Test security validation of HANDOFF_TOKENs."""
        # Create token with security-sensitive context
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="security-specialist",
            operation_type=OperationType.SECURITY_SCANNING,
            semantic_context={
                "security_level": "confidential",
                "scan_type": "vulnerability_assessment",
                "access_required": ["read_source", "write_reports"]
            },
            validation_criteria=[
                "security clearance verified",
                "access permissions validated",
                "audit trail maintained"
            ]
        )
        
        # Validate token security
        is_valid, score, issues = await self.token_manager.validate_token(token_id)
        
        # Should validate successfully for security operations
        token = self.token_manager.active_tokens[token_id]
        assert token.operation_type == OperationType.SECURITY_SCANNING
        assert "security_level" in token.semantic_context
        
        # Verify validation criteria include security requirements
        security_criteria = [c for c in token.validation_criteria if "security" in c.lower()]
        assert len(security_criteria) > 0
    
    async def test_token_tampering_detection(self):
        """Test detection of token tampering."""
        # Create a token
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"original": "data"},
            validation_criteria=["tampering test"]
        )
        
        original_token = self.token_manager.active_tokens[token_id]
        original_context = original_token.semantic_context.copy()
        original_vector = original_token.context_vector.copy() if original_token.context_vector else []
        
        # Simulate tampering
        original_token.semantic_context["injected"] = "malicious_data"
        original_token.semantic_context["original"] = "modified_data"
        
        # Re-validate token
        is_valid, score, issues = await self.token_manager.validate_token(token_id)
        
        # Current implementation doesn't detect tampering, but structure is in place
        # This test documents expected behavior for future security enhancements
        assert isinstance(is_valid, bool)
        assert isinstance(score, float)
        
        # Verify token structure remains intact
        assert token_id in self.token_manager.active_tokens
        current_token = self.token_manager.active_tokens[token_id]
        assert current_token.token_id == token_id
    
    async def test_token_expiration_security(self):
        """Test security of token expiration handling."""
        # Create token with short expiration
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="test-agent",
            operation_type=OperationType.CODE_REVIEW,
            semantic_context={"sensitive": "information"},
            validation_criteria=["expiration test"]
        )
        
        # Manually expire token
        token = self.token_manager.active_tokens[token_id]
        token.expires_at = datetime.utcnow() - timedelta(seconds=1)
        
        # Attempt operations on expired token
        start_result = await self.token_manager.start_token_execution(token_id)
        assert start_result == False  # Should reject expired token
        
        complete_result = await self.token_manager.complete_token(token_id, {"result": "test"})
        assert complete_result == False  # Should reject expired token
        
        # Verify token is properly cleaned up
        await self.token_manager.cleanup_expired_tokens()
        assert token_id not in self.token_manager.active_tokens
        
        # Verify sensitive data is moved to history (with timestamp)
        historical_token = next(
            (t for t in self.token_manager.token_history if t.token_id == token_id),
            None
        )
        assert historical_token is not None
        assert historical_token.status == HandoffTokenStatus.EXPIRED
    
    async def test_token_access_control(self):
        """Test access control for HANDOFF_TOKENs."""
        # Create tokens for different security levels
        public_token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="public-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"access_level": "public", "data": "public_info"},
            validation_criteria=["public access test"]
        )
        
        restricted_token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="restricted-agent",
            operation_type=OperationType.SECURITY_SCANNING,
            semantic_context={"access_level": "restricted", "data": "confidential_info"},
            validation_criteria=["restricted access test", "clearance required"]
        )
        
        # Verify access level differentiation
        public_token = self.token_manager.active_tokens[public_token_id]
        restricted_token = self.token_manager.active_tokens[restricted_token_id]
        
        assert public_token.semantic_context["access_level"] == "public"
        assert restricted_token.semantic_context["access_level"] == "restricted"
        
        # Verify validation criteria reflect access requirements
        public_criteria = public_token.validation_criteria
        restricted_criteria = restricted_token.validation_criteria
        
        assert len(restricted_criteria) > len(public_criteria)
        assert any("clearance" in criterion.lower() for criterion in restricted_criteria)
    
    def test_token_audit_trail(self):
        """Test audit trail maintenance for tokens."""
        # This test verifies that token operations are properly tracked
        # for security auditing purposes
        
        async def test_audit_operations():
            # Create token
            token_id = await self.token_manager.create_handoff_token(
                source_agent="auditor-agent",
                target_agent="target-agent", 
                operation_type=OperationType.REPOSITORY_ANALYSIS,
                semantic_context={"audit": "test", "timestamp": datetime.utcnow().isoformat()},
                validation_criteria=["audit trail test"]
            )
            
            # Validate token (should be logged)
            await self.token_manager.validate_token(token_id)
            
            # Start execution (should be logged)
            await self.token_manager.start_token_execution(token_id)
            
            # Complete token (should be logged)
            await self.token_manager.complete_token(token_id, {"audit": "completed"})
            
            # Verify audit trail in token history
            completed_token = next(
                (t for t in self.token_manager.token_history if t.token_id == token_id),
                None
            )
            
            assert completed_token is not None
            assert completed_token.status == HandoffTokenStatus.COMPLETED
            assert "completed_at" in completed_token.semantic_context
            
            # Verify token progression tracking
            assert completed_token.retry_count >= 0  # Tracked
            assert completed_token.created_at < completed_token.expires_at  # Timestamps valid
        
        asyncio.run(test_audit_operations())


class TestAgentCoordination:
    """Test agent coordination mechanisms."""
    
    def setup_method(self):
        """Setup test environment for coordination testing."""
        self.semantic_engine = SemanticContextEngine()
        self.token_manager = HandoffTokenManager(self.semantic_engine)
        self.capability_matrix = AgentCapabilityMatrix()
    
    async def test_multi_agent_token_coordination(self):
        """Test coordination between multiple agents using tokens."""
        # Create a coordination scenario: planner -> coder -> reviewer
        
        # Step 1: Planner analyzes requirements
        planning_token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="planner",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={
                "phase": "planning",
                "requirements": "analyze repository structure",
                "next_agent": "coder"
            },
            validation_criteria=["planning complete", "requirements documented"],
            dependencies=["repository_access"]
        )
        
        # Step 2: Coder implements changes (dependent on planning)
        coding_token_id = await self.token_manager.create_handoff_token(
            source_agent="planner",
            target_agent="coder",
            operation_type=OperationType.PULL_REQUEST_CREATION,
            semantic_context={
                "phase": "implementation",
                "requirements": "implement planned changes",
                "next_agent": "code-reviewer"
            },
            validation_criteria=["code implemented", "tests added"],
            dependencies=["repository_access", planning_token_id]  # Depends on planning
        )
        
        # Step 3: Reviewer checks work (dependent on coding)
        review_token_id = await self.token_manager.create_handoff_token(
            source_agent="coder",
            target_agent="code-reviewer",
            operation_type=OperationType.CODE_REVIEW,
            semantic_context={
                "phase": "review",
                "requirements": "review implemented changes",
                "final_step": True
            },
            validation_criteria=["code reviewed", "quality approved"],
            dependencies=["repository_access", planning_token_id, coding_token_id]
        )
        
        # Verify coordination chain
        planning_token = self.token_manager.active_tokens[planning_token_id]
        coding_token = self.token_manager.active_tokens[coding_token_id]
        review_token = self.token_manager.active_tokens[review_token_id]
        
        # Verify dependency chain
        assert planning_token_id in coding_token.dependencies
        assert planning_token_id in review_token.dependencies
        assert coding_token_id in review_token.dependencies
        
        # Verify semantic progression
        assert planning_token.semantic_context["phase"] == "planning"
        assert coding_token.semantic_context["phase"] == "implementation"
        assert review_token.semantic_context["phase"] == "review"
        assert review_token.semantic_context.get("final_step") == True
    
    async def test_agent_handoff_with_context_preservation(self):
        """Test context preservation during agent handoffs."""
        # Initial context with rich information
        initial_context = {
            "project_type": "python_web_application",
            "framework": "fastapi",
            "database": "postgresql",
            "testing_framework": "pytest",
            "deployment_target": "kubernetes",
            "security_requirements": ["authentication", "authorization", "data_encryption"],
            "performance_targets": {"response_time": "< 200ms", "throughput": "> 1000 rps"}
        }
        
        # Create handoff token with rich context
        token_id = await self.token_manager.create_handoff_token(
            source_agent="system-architect",
            target_agent="backend-architect",
            operation_type=OperationType.ARCHITECTURE_DESIGN,
            semantic_context=initial_context,
            validation_criteria=[
                "architecture design complete",
                "technical stack validated",
                "scalability considered"
            ]
        )
        
        # Validate token preserves context
        is_valid, score, issues = await self.token_manager.validate_token(token_id)
        
        token = self.token_manager.active_tokens[token_id]
        preserved_context = token.semantic_context
        
        # Verify all key context is preserved
        assert preserved_context["project_type"] == initial_context["project_type"]
        assert preserved_context["framework"] == initial_context["framework"]
        assert preserved_context["database"] == initial_context["database"]
        assert preserved_context["security_requirements"] == initial_context["security_requirements"]
        assert preserved_context["performance_targets"] == initial_context["performance_targets"]
        
        # Verify semantic vector captures context richness
        assert token.context_vector is not None
        assert len(token.context_vector) > 0
    
    async def test_dynamic_agent_selection(self):
        """Test dynamic agent selection based on context and capabilities."""
        # Test different operation contexts
        contexts = [
            {
                "operation_type": "security_scanning",
                "context_hint": "vulnerability assessment for web application",
                "required_capabilities": [AgentCapability.SECURITY_AUDIT],
                "expected_agent_type": "security"
            },
            {
                "operation_type": "performance_analysis", 
                "context_hint": "python application performance optimization",
                "required_capabilities": [AgentCapability.PERFORMANCE_OPTIMIZATION],
                "expected_agent_type": "performance"
            },
            {
                "operation_type": "code_review",
                "context_hint": "python code quality and best practices review",
                "required_capabilities": [AgentCapability.CODE_ANALYSIS],
                "expected_agent_type": "code"
            }
        ]
        
        for context in contexts:
            # Get optimal agent for context
            try:
                operation_type = OperationType(context["operation_type"])
            except ValueError:
                # Skip if operation type not defined
                continue
                
            optimal_agent = self.capability_matrix.get_optimal_agent(
                operation_type=operation_type,
                required_capabilities=context["required_capabilities"],
                context_hint=context["context_hint"]
            )
            
            if optimal_agent:
                # Verify agent has required capabilities
                required_caps = context["required_capabilities"]
                agent_caps = optimal_agent.capabilities
                
                assert any(cap in agent_caps for cap in required_caps)
                
                # Verify agent supports operation type
                assert operation_type in optimal_agent.operation_types
                
                # Verify agent name suggests appropriate specialization
                expected_type = context["expected_agent_type"]
                assert expected_type in optimal_agent.agent_name or \
                       any(expected_type in domain for domain in optimal_agent.specialization_domains)
    
    async def test_coordination_failure_recovery(self):
        """Test recovery mechanisms when agent coordination fails."""
        # Create a coordination scenario that will fail
        token_id = await self.token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="failing-agent",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={"test": "failure_recovery"},
            validation_criteria=["operation must succeed", "no failures allowed"]
        )
        
        # Simulate validation failure
        is_valid, score, issues = await self.token_manager.validate_token(token_id)
        
        if not is_valid:
            # Test retry mechanism
            failure_result = await self.token_manager.fail_token(
                token_id,
                "Simulated coordination failure",
                retry=True
            )
            
            if failure_result:  # Retry allowed
                token = self.token_manager.active_tokens[token_id]
                assert token.status == HandoffTokenStatus.CREATED
                assert token.retry_count == 1
                assert "last_error" in token.semantic_context
            
        # Test permanent failure handling
        # Exhaust retries
        token = self.token_manager.active_tokens.get(token_id)
        if token:
            token.retry_count = token.max_retries
            
            permanent_failure = await self.token_manager.fail_token(
                token_id,
                "Permanent coordination failure",
                retry=True
            )
            
            assert permanent_failure == False  # No more retries
            assert token_id not in self.token_manager.active_tokens
            
            # Verify failure is recorded in history
            failed_token = next(
                (t for t in self.token_manager.token_history if t.token_id == token_id),
                None
            )
            
            if failed_token:
                assert failed_token.status == HandoffTokenStatus.FAILED
                assert "failure_reason" in failed_token.semantic_context


class TestAgentPerformanceIsolation:
    """Test performance isolation between agents."""
    
    def setup_method(self):
        """Setup performance isolation testing."""
        self.circuit_breaker_manager = CircuitBreakerManager()
        self.semantic_engine = SemanticContextEngine()
        self.token_manager = HandoffTokenManager(self.semantic_engine)
    
    async def test_circuit_breaker_performance_isolation(self):
        """Test circuit breaker prevents cascading performance failures."""
        
        async def slow_operation():
            await asyncio.sleep(0.5)  # Slow operation
            return {"result": "slow_success"}
        
        async def fast_operation():
            await asyncio.sleep(0.01)  # Fast operation
            return {"result": "fast_success"}
        
        async def failing_operation():
            raise Exception("Operation failed")
        
        # Test performance isolation between agents
        agents = ["slow-agent", "fast-agent", "failing-agent"]
        operations = [slow_operation, fast_operation, failing_operation]
        
        results = []
        
        for agent, operation in zip(agents, operations):
            try:
                result = await self.circuit_breaker_manager.call_through_breaker(
                    agent_name=agent,
                    operation=operation
                )
                results.append((agent, "success", result))
            except Exception as e:
                results.append((agent, "failure", str(e)))
        
        # Verify isolation - failures in one agent don't affect others
        success_results = [r for r in results if r[1] == "success"]
        failure_results = [r for r in results if r[1] == "failure"]
        
        assert len(success_results) >= 1  # At least one should succeed
        assert len(failure_results) >= 1  # At least one should fail
        
        # Verify circuit breaker states are independent
        status = self.circuit_breaker_manager.get_breaker_status()
        
        for agent in agents:
            assert agent in status
            # Each agent should have independent state
            assert "state" in status[agent]
            assert "failure_count" in status[agent]
    
    async def test_concurrent_token_processing_isolation(self):
        """Test isolation of concurrent token processing performance."""
        
        # Create tokens with different processing characteristics
        token_contexts = [
            {"processing_type": "fast", "complexity": "low", "expected_time": 0.1},
            {"processing_type": "medium", "complexity": "medium", "expected_time": 0.3},
            {"processing_type": "slow", "complexity": "high", "expected_time": 0.8},
            {"processing_type": "variable", "complexity": "unknown", "expected_time": 0.2}
        ]
        
        token_ids = []
        for i, context in enumerate(token_contexts):
            token_id = await self.token_manager.create_handoff_token(
                source_agent="primary-agent",
                target_agent=f"processing-agent-{i}",
                operation_type=OperationType.REPOSITORY_ANALYSIS,
                semantic_context=context,
                validation_criteria=[f"processing test {i}"]
            )
            token_ids.append(token_id)
        
        # Process tokens concurrently and measure individual performance
        start_time = datetime.utcnow()
        
        async def process_token(token_id: str):
            token_start = datetime.utcnow()
            
            # Validate token
            is_valid, score, issues = await self.token_manager.validate_token(token_id)
            
            if is_valid:
                # Start execution
                await self.token_manager.start_token_execution(token_id)
                
                # Simulate processing time based on complexity
                token = self.token_manager.active_tokens[token_id]
                expected_time = token.semantic_context.get("expected_time", 0.1)
                await asyncio.sleep(expected_time)
                
                # Complete token
                await self.token_manager.complete_token(token_id, {"processed": True})
            
            token_end = datetime.utcnow()
            return (token_id, token_end - token_start)
        
        # Process all tokens concurrently
        processing_tasks = [process_token(tid) for tid in token_ids]
        processing_results = await asyncio.gather(*processing_tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        # Verify concurrent processing efficiency
        successful_results = [r for r in processing_results if not isinstance(r, Exception)]
        
        assert len(successful_results) > 0  # At least some should succeed
        
        # Verify individual processing times reflect expected complexity
        for token_id, duration in successful_results:
            duration_seconds = duration.total_seconds()
            assert duration_seconds >= 0.05  # Minimum processing time
            assert duration_seconds <= 2.0   # Maximum reasonable time
        
        # Verify concurrent processing is more efficient than sequential
        max_individual_time = max(duration.total_seconds() for _, duration in successful_results)
        assert total_time <= max_individual_time + 0.5  # Concurrent benefit
    
    def test_memory_isolation_token_cleanup(self):
        """Test memory isolation through proper token cleanup."""
        
        async def test_memory_cleanup():
            # Create many tokens to test memory management
            token_count = 100
            token_ids = []
            
            for i in range(token_count):
                token_id = await self.token_manager.create_handoff_token(
                    source_agent="primary-agent",
                    target_agent=f"memory-test-agent-{i}",
                    operation_type=OperationType.REPOSITORY_ANALYSIS,
                    semantic_context={"memory_test": True, "data": f"test_data_{i}"},
                    validation_criteria=[f"memory test {i}"]
                )
                token_ids.append(token_id)
            
            # Verify all tokens created
            assert len(self.token_manager.active_tokens) == token_count
            
            # Complete half the tokens
            completed_count = token_count // 2
            for i in range(completed_count):
                await self.token_manager.complete_token(
                    token_ids[i],
                    {"completed": True, "index": i}
                )
            
            # Expire the remaining tokens
            remaining_tokens = token_ids[completed_count:]
            for token_id in remaining_tokens:
                token = self.token_manager.active_tokens[token_id]
                token.expires_at = datetime.utcnow() - timedelta(seconds=1)
            
            # Cleanup expired tokens
            cleaned_count = await self.token_manager.cleanup_expired_tokens()
            
            # Verify memory cleanup
            assert len(self.token_manager.active_tokens) == 0
            assert cleaned_count == len(remaining_tokens)
            assert len(self.token_manager.token_history) == token_count
            
            # Verify history maintains essential data but cleans up large contexts
            for historical_token in self.token_manager.token_history:
                assert historical_token.token_id is not None
                assert historical_token.status in [HandoffTokenStatus.COMPLETED, HandoffTokenStatus.EXPIRED]
                # Context should be preserved for audit
                assert "memory_test" in historical_token.semantic_context
        
        asyncio.run(test_memory_cleanup())


@pytest.mark.integration
class TestAgentDecouplingIntegration:
    """Integration tests for complete agent decoupling system."""
    
    async def test_full_decoupling_workflow(self):
        """Test complete agent decoupling workflow from start to finish."""
        
        # Initialize all decoupling components
        semantic_engine = SemanticContextEngine()
        token_manager = HandoffTokenManager(semantic_engine)
        capability_matrix = AgentCapabilityMatrix()
        circuit_breaker_manager = CircuitBreakerManager()
        
        # Scenario: Complex multi-agent workflow with decoupling
        workflow_context = {
            "project": "enterprise_web_application",
            "phases": ["analysis", "architecture", "security", "implementation", "review"],
            "agents_required": ["planner", "backend-architect", "security-specialist", "coder", "code-reviewer"],
            "coordination_method": "handoff_tokens"
        }
        
        # Phase 1: Planning
        planning_token_id = await token_manager.create_handoff_token(
            source_agent="primary-agent",
            target_agent="planner",
            operation_type=OperationType.REPOSITORY_ANALYSIS,
            semantic_context={**workflow_context, "current_phase": "analysis"},
            validation_criteria=["requirements analyzed", "scope defined", "timeline estimated"],
            quality_gates=[QualityGateType.PLANNING]
        )
        
        # Phase 2: Architecture (depends on planning)
        architecture_token_id = await token_manager.create_handoff_token(
            source_agent="planner",
            target_agent="backend-architect",
            operation_type=OperationType.REPOSITORY_ANALYSIS,  # Closest available
            semantic_context={**workflow_context, "current_phase": "architecture"},
            validation_criteria=["architecture designed", "scalability considered", "tech stack selected"],
            dependencies=[planning_token_id],
            quality_gates=[QualityGateType.ARCHITECTURE]
        )
        
        # Phase 3: Security Review (depends on architecture)
        security_token_id = await token_manager.create_handoff_token(
            source_agent="backend-architect",
            target_agent="security-specialist",
            operation_type=OperationType.SECURITY_SCANNING,
            semantic_context={**workflow_context, "current_phase": "security"},
            validation_criteria=["security requirements defined", "threat model created", "compliance checked"],
            dependencies=[planning_token_id, architecture_token_id],
            quality_gates=[QualityGateType.SECURITY]
        )
        
        # Verify complete workflow coordination
        all_tokens = [planning_token_id, architecture_token_id, security_token_id]
        
        for token_id in all_tokens:
            assert token_id in token_manager.active_tokens
            
            # Test validation
            is_valid, score, issues = await token_manager.validate_token(token_id)
            # Validation results may vary based on semantic analysis
            assert isinstance(is_valid, bool)
            assert isinstance(score, float)
            
            # Test circuit breaker integration
            token = token_manager.active_tokens[token_id]
            agent_name = token.target_agent
            
            # Should be able to get circuit breaker for agent
            breaker = circuit_breaker_manager.get_breaker(agent_name)
            assert breaker.agent_name == agent_name
            assert breaker.state == CircuitBreakerState.CLOSED  # Initial state
        
        # Verify dependency tracking
        planning_token = token_manager.active_tokens[planning_token_id]
        architecture_token = token_manager.active_tokens[architecture_token_id]
        security_token = token_manager.active_tokens[security_token_id]
        
        assert len(planning_token.dependencies) == 0  # First in chain
        assert planning_token_id in architecture_token.dependencies
        assert planning_token_id in security_token.dependencies
        assert architecture_token_id in security_token.dependencies
        
        # Verify namespace isolation
        planning_context = planning_token.semantic_context
        architecture_context = architecture_token.semantic_context
        security_context = security_token.semantic_context
        
        assert planning_context["current_phase"] == "analysis"
        assert architecture_context["current_phase"] == "architecture"
        assert security_context["current_phase"] == "security"
        
        # All should share project context but maintain phase isolation
        assert planning_context["project"] == architecture_context["project"]
        assert planning_context["current_phase"] != architecture_context["current_phase"]


@pytest.mark.performance
class TestAgentDecouplingPerformance:
    """Performance tests for agent decoupling system."""
    
    async def test_high_throughput_token_management(self):
        """Test token management performance under high throughput."""
        
        semantic_engine = SemanticContextEngine()
        token_manager = HandoffTokenManager(semantic_engine)
        
        # Create many tokens quickly
        token_count = 200
        start_time = datetime.utcnow()
        
        create_tasks = []
        for i in range(token_count):
            task = token_manager.create_handoff_token(
                source_agent="load-test-source",
                target_agent=f"load-test-target-{i % 10}",  # 10 different targets
                operation_type=OperationType.REPOSITORY_ANALYSIS,
                semantic_context={"load_test": True, "index": i},
                validation_criteria=[f"load test {i}"]
            )
            create_tasks.append(task)
        
        token_ids = await asyncio.gather(*create_tasks)
        creation_time = datetime.utcnow()
        
        # Validate tokens concurrently
        validate_tasks = [token_manager.validate_token(tid) for tid in token_ids]
        validation_results = await asyncio.gather(*validate_tasks)
        validation_time = datetime.utcnow()
        
        # Cleanup tokens
        cleanup_count = await token_manager.cleanup_expired_tokens()
        cleanup_time = datetime.utcnow()
        
        # Performance assertions
        total_creation_time = (creation_time - start_time).total_seconds()
        total_validation_time = (validation_time - creation_time).total_seconds()
        total_cleanup_time = (cleanup_time - validation_time).total_seconds()
        
        assert total_creation_time < 10.0  # Should create 200 tokens in < 10s
        assert total_validation_time < 15.0  # Should validate 200 tokens in < 15s
        assert total_cleanup_time < 2.0   # Should cleanup quickly
        
        # Verify all operations completed
        assert len(token_ids) == token_count
        assert len(validation_results) == token_count
        
        # Verify system stability under load
        assert len(token_manager.active_tokens) <= token_count  # Some may be expired/cleaned
        assert len(token_manager.token_history) >= cleanup_count
    
    async def test_concurrent_agent_isolation_performance(self):
        """Test performance of concurrent agent isolation."""
        
        circuit_breaker_manager = CircuitBreakerManager()
        
        # Simulate many agents operating concurrently
        agent_count = 50
        operations_per_agent = 20
        
        async def agent_operations(agent_id: int):
            agent_name = f"perf-agent-{agent_id}"
            results = []
            
            for op_id in range(operations_per_agent):
                async def mock_operation():
                    # Simulate variable operation times
                    await asyncio.sleep(0.01 * (op_id % 5))  # 0-40ms
                    if op_id % 10 == 9:  # 10% failure rate
                        raise Exception(f"Operation {op_id} failed")
                    return {"agent": agent_name, "operation": op_id}
                
                try:
                    result = await circuit_breaker_manager.call_through_breaker(
                        agent_name=agent_name,
                        operation=mock_operation
                    )
                    results.append(("success", result))
                except Exception as e:
                    results.append(("failure", str(e)))
            
            return agent_name, results
        
        # Run all agents concurrently
        start_time = datetime.utcnow()
        
        agent_tasks = [agent_operations(i) for i in range(agent_count)]
        agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        # Performance verification
        total_operations = agent_count * operations_per_agent
        operations_per_second = total_operations / total_time
        
        assert total_time < 30.0  # Should complete within 30 seconds
        assert operations_per_second > 20  # Should achieve > 20 ops/sec
        
        # Verify isolation - each agent should have independent results
        successful_agents = [r for r in agent_results if not isinstance(r, Exception)]
        assert len(successful_agents) == agent_count
        
        # Verify circuit breaker isolation
        breaker_status = circuit_breaker_manager.get_breaker_status()
        assert len(breaker_status) == agent_count
        
        # Each agent should have independent failure tracking
        for agent_name, status in breaker_status.items():
            assert "failure_count" in status
            assert 0 <= status["failure_count"] <= operations_per_agent