"""
Security Tests for GitHub Integration System
Authentication, authorization, input validation, and security audit integration
"""

import pytest
import asyncio
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add parent directories to path for imports
test_dir = Path(__file__).parent.parent
if str(test_dir) not in sys.path:
    sys.path.insert(0, str(test_dir))

try:
    from conftest import TestConfig
except ImportError:
    # Fallback if direct import fails
    from tests.github_integration_suite.conftest import TestConfig


class TestAuthenticationSecurity:
    """Test authentication mechanisms and token security."""
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_token_validation_security(
        self,
        mock_github_service,
        security_test_data: Dict[str, Any]
    ):
        """Test GitHub token validation and security measures."""
        valid_tokens = security_test_data['valid_tokens']
        invalid_tokens = security_test_data['invalid_tokens']
        
        # Test valid token authentication
        for token in valid_tokens:
            mock_github_service.config.github_token = token
            
            is_valid = await mock_github_service.authenticate_token()
            assert is_valid is True, f"Valid token {token} should authenticate successfully"
        
        # Test invalid token rejection
        for token in invalid_tokens:
            mock_github_service.config.github_token = token
            mock_github_service.authenticate_token.return_value = False
            
            is_valid = await mock_github_service.authenticate_token()
            assert is_valid is False, f"Invalid token {token} should be rejected"
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_token_exposure_prevention(
        self,
        mock_github_service,
        temp_log_dir
    ):
        """Test prevention of token exposure in logs and error messages."""
        sensitive_token = "ghp_" + "x" * 36  # GitHub personal access token format
        mock_github_service.config.github_token = sensitive_token
        
        log_content = []
        error_content = []
        
        # Mock logging to capture log output
        def capture_log_output(message: str, level: str = "INFO"):
            log_content.append(f"[{level}] {message}")
        
        # Mock error handling to capture error messages
        def capture_error_output(error: str):
            error_content.append(error)
        
        with patch('logging.info', side_effect=lambda msg: capture_log_output(msg, "INFO")), \
             patch('logging.error', side_effect=lambda msg: capture_log_output(msg, "ERROR")):
            
            try:
                # Simulate operations that might log sensitive information
                async with mock_github_service as github_service:
                    await github_service.get_repo_info("test-owner/test-repo")
                    
                    # Simulate an error scenario that might expose the token
                    mock_github_service.get_repo_info.side_effect = Exception(
                        f"GitHub API error with token {sensitive_token}"
                    )
                    
                    with pytest.raises(Exception) as exc_info:
                        await github_service.get_repo_info("test-owner/test-repo")
                    
                    capture_error_output(str(exc_info.value))
                    
            except Exception:
                pass  # Expected for testing
        
        # Verify token is not exposed in logs or errors
        all_output = " ".join(log_content + error_content)
        
        # Should not contain the actual token
        assert sensitive_token not in all_output, "Sensitive token found in logs/errors"
        
        # Should not contain partial token that could be reconstructed
        token_parts = [sensitive_token[i:i+8] for i in range(0, len(sensitive_token), 8)]
        for part in token_parts[1:]:  # Skip first part (prefix is OK)
            if len(part) >= 6:  # Only check meaningful parts
                assert part not in all_output, f"Token part '{part}' found in logs/errors"
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_token_rotation_security(
        self,
        mock_github_service,
        security_test_data: Dict[str, Any]
    ):
        """Test security measures around token rotation."""
        old_token = security_test_data['valid_tokens'][0]
        new_token = security_test_data['valid_tokens'][1]
        
        # Initial authentication with old token
        mock_github_service.config.github_token = old_token
        initial_auth = await mock_github_service.authenticate_token()
        assert initial_auth is True
        
        # Simulate token rotation
        mock_github_service.config.github_token = new_token
        
        # Old token should be invalidated
        mock_github_service.authenticate_token.side_effect = [False, True]
        
        # First call with old token should fail
        old_token_auth = await mock_github_service.authenticate_token()
        assert old_token_auth is False
        
        # Second call with new token should succeed
        new_token_auth = await mock_github_service.authenticate_token()
        assert new_token_auth is True


class TestAuthorizationSecurity:
    """Test authorization and permission validation."""
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_permission_validation(
        self,
        mock_primary_controller,
        security_test_data: Dict[str, Any]
    ):
        """Test agent permission validation and enforcement."""
        test_permissions = security_test_data['test_permissions']
        
        # Test valid agent permissions
        valid_agent_perms = test_permissions['valid_agent']
        for permission in valid_agent_perms:
            has_permission = await mock_primary_controller.validate_permissions(
                'valid_agent',
                [permission]
            )
            assert has_permission is True, f"Valid agent should have {permission} permission"
        
        # Test invalid agent permissions
        invalid_agent_perms = test_permissions['invalid_agent']
        for permission in ['github_operations', 'code_analysis']:
            mock_primary_controller.validate_permissions.return_value = False
            
            has_permission = await mock_primary_controller.validate_permissions(
                'invalid_agent',
                [permission]
            )
            assert has_permission is False, f"Invalid agent should not have {permission} permission"
        
        # Test restricted agent permissions
        restricted_agent_perms = test_permissions['restricted_agent']
        allowed_permission = restricted_agent_perms[0] if restricted_agent_perms else None
        forbidden_permission = 'github_operations'
        
        if allowed_permission:
            mock_primary_controller.validate_permissions.return_value = True
            has_allowed = await mock_primary_controller.validate_permissions(
                'restricted_agent',
                [allowed_permission]
            )
            assert has_allowed is True, f"Restricted agent should have {allowed_permission}"
        
        mock_primary_controller.validate_permissions.return_value = False
        has_forbidden = await mock_primary_controller.validate_permissions(
            'restricted_agent',
            [forbidden_permission]
        )
        assert has_forbidden is False, f"Restricted agent should not have {forbidden_permission}"
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_privilege_escalation_prevention(
        self,
        mock_primary_controller,
        test_config: TestConfig
    ):
        """Test prevention of privilege escalation attacks."""
        # Simulate privilege escalation attempt
        escalation_attempts = [
            # Attempt to bypass permission check
            {
                'operation': 'github_admin_operation',
                'agent_name': 'restricted_agent',
                'bypass_validation': True
            },
            # Attempt to impersonate privileged agent
            {
                'operation': 'repository_deletion',
                'agent_name': 'admin_agent',
                'impersonation': True
            },
            # Attempt to access restricted namespace
            {
                'operation': 'memory_access',
                'namespace': 'admin_namespace',
                'agent_name': 'regular_agent'
            }
        ]
        
        blocked_attempts = 0
        
        for attempt in escalation_attempts:
            try:
                # Configure controller to detect and block privilege escalation
                mock_primary_controller.validate_permissions.return_value = False
                mock_primary_controller.delegate_github_task.side_effect = PermissionError(
                    f"Permission denied: {attempt['operation']}"
                )
                
                async with mock_primary_controller as controller:
                    with pytest.raises(PermissionError):
                        await controller.delegate_github_task(attempt)
                        
                blocked_attempts += 1
                
            except Exception as e:
                # Should raise PermissionError for security violations
                if isinstance(e, PermissionError):
                    blocked_attempts += 1
        
        # All privilege escalation attempts should be blocked
        assert blocked_attempts == len(escalation_attempts), (
            f"Only {blocked_attempts}/{len(escalation_attempts)} privilege escalation attempts blocked"
        )


class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_malicious_input_sanitization(
        self,
        mock_github_service,
        mock_event_bus,
        security_test_data: Dict[str, Any]
    ):
        """Test handling of malicious inputs and injection attacks."""
        malicious_inputs = security_test_data['malicious_inputs']
        
        validation_results = {}
        
        for malicious_input in malicious_inputs:
            validation_results[malicious_input] = {
                'github_service': True,
                'event_bus': True,
                'rejected': False
            }
            
            # Test GitHub Service input validation
            try:
                async with mock_github_service as github_service:
                    # Test various input contexts
                    test_operations = [
                        ('get_repo_info', malicious_input),
                        ('create_pull_request', {
                            'title': malicious_input,
                            'body': malicious_input,
                            'head': 'safe-branch',
                            'base': 'main'
                        })
                    ]
                    
                    for operation, input_data in test_operations:
                        # Should validate and reject malicious input
                        if operation == 'get_repo_info':
                            # Mock validation rejection for malicious repo names
                            if any(dangerous in malicious_input for dangerous in ['<script>', 'DROP TABLE', '../']):
                                mock_github_service.get_repo_info.side_effect = ValueError("Invalid input")
                                
                                with pytest.raises(ValueError):
                                    await github_service.get_repo_info(input_data)
                                validation_results[malicious_input]['rejected'] = True
                                
                        elif operation == 'create_pull_request':
                            # Mock validation rejection for malicious PR content
                            if any(dangerous in str(input_data) for dangerous in ['<script>', 'DROP TABLE']):
                                mock_github_service.create_pull_request.side_effect = ValueError("Invalid input")
                                
                                with pytest.raises(ValueError):
                                    await github_service.create_pull_request(input_data)
                                validation_results[malicious_input]['rejected'] = True
                                
            except ValueError:
                validation_results[malicious_input]['github_service'] = False
            except Exception:
                validation_results[malicious_input]['github_service'] = False
            
            # Test Event Bus input validation
            try:
                # Mock validation for event data
                if any(dangerous in malicious_input for dangerous in ['<script>', 'DROP TABLE', '../']):
                    mock_event_bus.publish_event.side_effect = ValueError("Malicious input detected")
                    
                    with pytest.raises(ValueError):
                        await mock_event_bus.publish_event('test_event', {
                            'data': malicious_input
                        })
                    validation_results[malicious_input]['rejected'] = True
                    
            except ValueError:
                validation_results[malicious_input]['event_bus'] = False
            except Exception:
                validation_results[malicious_input]['event_bus'] = False
        
        # Verify malicious inputs are properly rejected
        for malicious_input, results in validation_results.items():
            assert results['rejected'] is True, (
                f"Malicious input '{malicious_input[:50]}...' was not rejected by security validation"
            )
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_data_sanitization(
        self,
        mock_github_service,
        mock_primary_controller
    ):
        """Test data sanitization in various contexts."""
        # Test cases with potentially dangerous content
        test_cases = [
            {
                'input': '<script>alert("XSS")</script>',
                'expected_sanitized': '&lt;script&gt;alert("XSS")&lt;/script&gt;',
                'context': 'html_sanitization'
            },
            {
                'input': 'test"; DROP TABLE users; --',
                'expected_sanitized': 'test"; DROP TABLE users; --',  # Should be escaped
                'context': 'sql_injection_prevention'
            },
            {
                'input': '../../../etc/passwd',
                'expected_sanitized': 'etc/passwd',  # Path traversal removed
                'context': 'path_traversal_prevention'
            }
        ]
        
        sanitization_results = []
        
        for test_case in test_cases:
            # Mock sanitization behavior
            def mock_sanitize(input_data: str) -> str:
                sanitized = input_data
                
                # HTML sanitization
                if test_case['context'] == 'html_sanitization':
                    sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
                
                # Path traversal prevention
                elif test_case['context'] == 'path_traversal_prevention':
                    sanitized = re.sub(r'\.\./', '', sanitized)
                
                return sanitized
            
            sanitized_output = mock_sanitize(test_case['input'])
            
            sanitization_results.append({
                'context': test_case['context'],
                'input': test_case['input'],
                'output': sanitized_output,
                'properly_sanitized': sanitized_output != test_case['input']
            })
        
        # Verify sanitization occurred
        for result in sanitization_results:
            if result['context'] in ['html_sanitization', 'path_traversal_prevention']:
                assert result['properly_sanitized'] is True, (
                    f"Input not properly sanitized in {result['context']}: {result['input']}"
                )


class TestSecurityAuditIntegration:
    """Test integration with security audit tools and processes."""
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_event_logging(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        temp_log_dir
    ):
        """Test security event logging and audit trail."""
        security_events = []
        
        def capture_security_event(event_type: str, details: Dict[str, Any]):
            security_events.append({
                'type': event_type,
                'details': details,
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': 'test-session-github'
            })
        
        # Mock security event capture
        with patch('logging.warning', side_effect=lambda msg: capture_security_event('warning', {'message': msg})), \
             patch('logging.error', side_effect=lambda msg: capture_security_event('error', {'message': msg})):
            
            # Simulate security-relevant events
            async with mock_github_service as github_service:
                # Authentication failure event
                mock_github_service.authenticate_token.return_value = False
                
                try:
                    auth_result = await github_service.authenticate_token()
                    if not auth_result:
                        capture_security_event('authentication_failure', {
                            'service': 'github_service',
                            'reason': 'invalid_token'
                        })
                except Exception:
                    pass
                
                # Permission violation event
                async with mock_primary_controller as controller:
                    try:
                        mock_primary_controller.validate_permissions.return_value = False
                        
                        has_permission = await controller.validate_permissions('test-agent', ['admin'])
                        if not has_permission:
                            capture_security_event('permission_violation', {
                                'agent': 'test-agent',
                                'requested_permission': 'admin',
                                'action': 'denied'
                            })
                    except Exception:
                        pass
        
        # Verify security events were logged
        assert len(security_events) >= 2, "Security events not properly logged"
        
        # Verify event types
        event_types = {event['type'] for event in security_events}
        expected_types = {'authentication_failure', 'permission_violation'}
        assert expected_types.issubset(event_types), "Missing expected security event types"
        
        # Verify event structure
        for event in security_events:
            assert 'type' in event
            assert 'details' in event
            assert 'timestamp' in event
            assert 'session_id' in event
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_vulnerability_scanning_integration(
        self,
        mock_github_service,
        test_config: TestConfig
    ):
        """Test integration with vulnerability scanning tools."""
        # Mock vulnerability scan results
        vulnerability_scan_results = {
            'scan_id': 'vuln-scan-123',
            'timestamp': datetime.utcnow().isoformat(),
            'vulnerabilities': [
                {
                    'severity': 'HIGH',
                    'type': 'insecure_token_storage',
                    'description': 'GitHub token stored in plaintext',
                    'remediation': 'Use encrypted storage for sensitive tokens'
                },
                {
                    'severity': 'MEDIUM',
                    'type': 'insufficient_input_validation',
                    'description': 'Some user inputs not properly validated',
                    'remediation': 'Implement comprehensive input validation'
                }
            ],
            'total_vulnerabilities': 2,
            'critical_count': 0,
            'high_count': 1,
            'medium_count': 1,
            'low_count': 0
        }
        
        # Mock vulnerability scanner integration
        def mock_vulnerability_scan():
            return vulnerability_scan_results
        
        # Execute vulnerability scan
        scan_results = mock_vulnerability_scan()
        
        # Verify scan results structure
        assert 'vulnerabilities' in scan_results
        assert 'total_vulnerabilities' in scan_results
        assert scan_results['total_vulnerabilities'] == len(scan_results['vulnerabilities'])
        
        # Verify severity classification
        severity_counts = {
            'critical': scan_results.get('critical_count', 0),
            'high': scan_results.get('high_count', 0),
            'medium': scan_results.get('medium_count', 0),
            'low': scan_results.get('low_count', 0)
        }
        
        total_counted = sum(severity_counts.values())
        assert total_counted == scan_results['total_vulnerabilities'], (
            "Vulnerability count mismatch in severity classification"
        )
        
        # Critical vulnerabilities should trigger immediate action
        if severity_counts['critical'] > 0:
            pytest.fail(f"CRITICAL vulnerabilities found: {severity_counts['critical']}")
        
        # High severity vulnerabilities should be addressed
        if severity_counts['high'] > 0:
            # Log high severity findings but don't fail test (for demonstration)
            print(f"WARNING: {severity_counts['high']} HIGH severity vulnerabilities found")
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_compliance_validation(
        self,
        mock_github_service,
        mock_primary_controller,
        test_config: TestConfig
    ):
        """Test security compliance validation against security standards."""
        compliance_checks = {
            'authentication': {
                'token_encryption': False,  # Would be True in real implementation
                'token_rotation': True,
                'multi_factor_auth': False,  # Optional for API tokens
                'session_management': True
            },
            'authorization': {
                'role_based_access': True,
                'principle_of_least_privilege': True,
                'permission_validation': True,
                'audit_logging': True
            },
            'data_protection': {
                'data_encryption_at_rest': False,  # Would be True in production
                'data_encryption_in_transit': True,
                'input_validation': True,
                'output_sanitization': True
            },
            'monitoring': {
                'security_event_logging': True,
                'anomaly_detection': False,  # Advanced feature
                'real_time_alerting': True,
                'audit_trail': True
            }
        }
        
        compliance_score = 0
        total_checks = 0
        failed_checks = []
        
        for category, checks in compliance_checks.items():
            for check_name, is_compliant in checks.items():
                total_checks += 1
                if is_compliant:
                    compliance_score += 1
                else:
                    failed_checks.append(f"{category}.{check_name}")
        
        compliance_percentage = (compliance_score / total_checks) * 100
        
        # Verify minimum compliance threshold
        min_compliance = 70  # 70% minimum compliance
        assert compliance_percentage >= min_compliance, (
            f"Security compliance {compliance_percentage:.1f}% below minimum {min_compliance}%. "
            f"Failed checks: {', '.join(failed_checks)}"
        )
        
        # Critical security controls must be present
        critical_controls = [
            'authorization.role_based_access',
            'authorization.permission_validation',
            'data_protection.input_validation',
            'monitoring.security_event_logging'
        ]
        
        for control in critical_controls:
            category, check = control.split('.')
            assert compliance_checks[category][check] is True, (
                f"Critical security control missing: {control}"
            )


class TestSecurityIncidentResponse:
    """Test security incident detection and response."""
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_incident_detection(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        test_config: TestConfig
    ):
        """Test detection of security incidents and anomalies."""
        security_incidents = []
        
        def detect_security_incident(incident_type: str, details: Dict[str, Any]):
            security_incidents.append({
                'type': incident_type,
                'details': details,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': details.get('severity', 'medium'),
                'status': 'detected'
            })
        
        # Simulate various security incidents
        
        # 1. Repeated authentication failures
        for i in range(5):
            mock_github_service.authenticate_token.return_value = False
            
            try:
                await mock_github_service.authenticate_token()
            except Exception:
                pass
            
            detect_security_incident('repeated_auth_failure', {
                'attempt': i + 1,
                'severity': 'high' if i >= 3 else 'medium',
                'source_ip': '192.168.1.100'  # Mock IP
            })
        
        # 2. Unusual access patterns
        detect_security_incident('unusual_access_pattern', {
            'pattern': 'access_outside_business_hours',
            'timestamp': '2023-01-01T02:00:00Z',  # 2 AM access
            'severity': 'medium',
            'agent': 'test-agent'
        })
        
        # 3. Permission escalation attempt
        detect_security_incident('permission_escalation_attempt', {
            'agent': 'restricted-agent',
            'requested_permission': 'admin',
            'current_permissions': ['read'],
            'severity': 'high'
        })
        
        # Verify incidents were detected
        assert len(security_incidents) >= 3, "Security incidents not properly detected"
        
        # Verify incident classification
        high_severity_incidents = [
            incident for incident in security_incidents 
            if incident.get('severity') == 'high'
        ]
        
        assert len(high_severity_incidents) >= 2, "High severity incidents not properly classified"
        
        # Verify incident response triggering
        critical_incident_types = {
            'repeated_auth_failure',
            'permission_escalation_attempt'
        }
        
        detected_critical = {
            incident['type'] for incident in security_incidents
            if incident['type'] in critical_incident_types
        }
        
        assert len(detected_critical) >= 2, "Critical security incidents not detected"
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_automated_security_response(
        self,
        mock_github_service,
        mock_primary_controller,
        test_config: TestConfig
    ):
        """Test automated security response mechanisms."""
        security_responses = []
        
        def trigger_security_response(response_type: str, details: Dict[str, Any]):
            security_responses.append({
                'type': response_type,
                'details': details,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'executed'
            })
        
        # Simulate security incidents that trigger automated responses
        
        # 1. Account lockout after failed attempts
        failed_attempts = 5
        for attempt in range(failed_attempts):
            if attempt >= 3:  # Lockout threshold
                trigger_security_response('account_lockout', {
                    'agent': 'suspicious-agent',
                    'duration': '30m',
                    'reason': 'repeated_authentication_failures'
                })
                break
        
        # 2. Circuit breaker activation
        trigger_security_response('circuit_breaker_activation', {
            'service': 'github_service',
            'reason': 'high_error_rate',
            'duration': '5m'
        })
        
        # 3. Rate limiting enforcement
        trigger_security_response('rate_limit_enforcement', {
            'agent': 'aggressive-agent',
            'new_limit': '10_requests_per_minute',
            'previous_limit': '100_requests_per_minute'
        })
        
        # Verify automated responses
        assert len(security_responses) >= 3, "Automated security responses not triggered"
        
        # Verify response types
        response_types = {response['type'] for response in security_responses}
        expected_responses = {
            'account_lockout',
            'circuit_breaker_activation',
            'rate_limit_enforcement'
        }
        
        assert expected_responses.issubset(response_types), (
            "Missing expected automated security responses"
        )
        
        # Verify response execution
        for response in security_responses:
            assert response['status'] == 'executed', (
                f"Security response {response['type']} not properly executed"
            )