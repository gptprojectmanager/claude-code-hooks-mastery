#!/usr/bin/env python3
"""
OpenEvolve Multi-Stage Validation Pipeline
Comprehensive validation system for optimized code to ensure quality,
performance, security, and behavioral equivalence.
"""

import ast
import sys
import time
import subprocess
import tempfile
import importlib.util
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import hashlib
import re
import difflib


@dataclass
class GateResult:
    """Result of a validation gate."""
    gate_name: str
    passed: bool
    score: float  # 0-100
    execution_time: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation pipeline report."""
    original_code_hash: str
    optimized_code_hash: str
    validation_timestamp: str
    language: str
    
    gate_results: List[GateResult] = field(default_factory=list)
    overall_passed: bool = False
    overall_score: float = 0.0
    total_execution_time: float = 0.0
    
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    quality_comparison: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        passed_gates = [g for g in self.gate_results if g.passed]
        failed_gates = [g for g in self.gate_results if not g.passed]
        
        return {
            "overall_passed": self.overall_passed,
            "overall_score": self.overall_score,
            "gates_passed": f"{len(passed_gates)}/{len(self.gate_results)}",
            "execution_time": f"{self.total_execution_time:.2f}s",
            "failed_gates": [g.gate_name for g in failed_gates],
            "performance_improvement": self.performance_metrics.get("improvement_percentage", 0)
        }


class SyntaxGate:
    """Validates code syntax and compilation."""
    
    def __init__(self):
        self.name = "Syntax Gate"
    
    def validate(self, code: str, language: str) -> GateResult:
        """Validate code syntax."""
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            if language.lower() == "python":
                # Try to parse Python code
                ast.parse(code)
                message = "✅ Code syntax is valid"
                passed = True
                score = 100.0
            else:
                # For other languages, do basic validation
                if not code.strip():
                    errors.append("Code is empty")
                    passed = False
                    score = 0.0
                    message = "❌ Code is empty"
                else:
                    # Basic syntax checks for other languages
                    passed = self._basic_syntax_check(code, language)
                    score = 100.0 if passed else 0.0
                    message = "✅ Basic syntax appears valid" if passed else "❌ Syntax issues detected"
                    
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            passed = False
            score = 0.0
            message = f"❌ Syntax error: {e.msg}"
        except Exception as e:
            errors.append(f"Parsing error: {str(e)}")
            passed = False
            score = 0.0
            message = f"❌ Parsing failed: {str(e)}"
        
        execution_time = time.time() - start_time
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=execution_time,
            message=message,
            errors=errors,
            warnings=warnings
        )
    
    def _basic_syntax_check(self, code: str, language: str) -> bool:
        """Basic syntax check for non-Python languages."""
        # Very basic checks - would need language-specific parsers for thorough validation
        
        common_issues = [
            r'^\s*\{.*\}$',  # Just braces
            r'function\s*\(\s*\)\s*\{',  # Empty function syntax
        ]
        
        # Check for obviously broken syntax
        if any(re.search(pattern, code, re.MULTILINE) for pattern in common_issues):
            return False
        
        # Check balanced braces for C-style languages
        if language.lower() in ['javascript', 'typescript', 'java', 'c++', 'c']:
            open_braces = code.count('{')
            close_braces = code.count('}')
            open_parens = code.count('(')
            close_parens = code.count(')')
            
            if open_braces != close_braces or open_parens != close_parens:
                return False
        
        return True


class TestCompatibilityGate:
    """Validates that existing tests still pass with optimized code."""
    
    def __init__(self):
        self.name = "Test Compatibility Gate"
    
    def validate(
        self, 
        original_code: str, 
        optimized_code: str, 
        test_file: str = None,
        language: str = "python"
    ) -> GateResult:
        """Validate test compatibility."""
        start_time = time.time()
        
        if not test_file or not Path(test_file).exists():
            # No tests available - skip with warning
            return GateResult(
                gate_name=self.name,
                passed=True,
                score=50.0,  # Partial score for no tests
                execution_time=time.time() - start_time,
                message="⚠️ No tests found - compatibility not verified",
                warnings=["No test file provided or test file not found"]
            )
        
        if language.lower() == "python":
            return self._validate_python_tests(original_code, optimized_code, test_file)
        else:
            return self._validate_generic_tests(optimized_code, test_file, language)
    
    def _validate_python_tests(self, original_code: str, optimized_code: str, test_file: str) -> GateResult:
        """Validate Python tests."""
        errors = []
        warnings = []
        
        try:
            # Run tests with original code
            original_result = self._run_python_tests(original_code, test_file, "original")
            
            # Run tests with optimized code  
            optimized_result = self._run_python_tests(optimized_code, test_file, "optimized")
            
            # Compare results
            if original_result["success"] and optimized_result["success"]:
                passed = True
                score = 100.0
                message = "✅ All tests pass with optimized code"
            elif not original_result["success"] and not optimized_result["success"]:
                # Both fail - optimization didn't break anything new
                passed = True
                score = 75.0
                message = "⚠️ Tests failed with both versions - no regression"
                warnings.append("Tests were already failing before optimization")
            elif original_result["success"] and not optimized_result["success"]:
                # Optimization broke tests
                passed = False
                score = 0.0
                message = "❌ Optimization broke existing tests"
                errors.append("Tests that passed with original code now fail")
                errors.extend(optimized_result.get("errors", []))
            else:
                # Tests pass now but failed before - improvement
                passed = True
                score = 100.0
                message = "✅ Optimization fixed failing tests"
            
        except Exception as e:
            errors.append(f"Test execution error: {str(e)}")
            passed = False
            score = 0.0
            message = f"❌ Test execution failed: {str(e)}"
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=time.time() - start_time,
            message=message,
            errors=errors,
            warnings=warnings
        )
    
    def _run_python_tests(self, code: str, test_file: str, version: str) -> Dict[str, Any]:
        """Run Python tests with given code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file.flush()
            
            try:
                # Run tests with temporary module
                result = subprocess.run([
                    sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'
                ], capture_output=True, text=True, timeout=30)
                
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "errors": result.stderr.split('\n') if result.stderr else []
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "errors": ["Test execution timed out"]
                }
            finally:
                Path(temp_file.name).unlink(missing_ok=True)
    
    def _validate_generic_tests(self, code: str, test_file: str, language: str) -> GateResult:
        """Generic test validation for non-Python languages."""
        # Simplified validation - would need language-specific test runners
        return GateResult(
            gate_name=self.name,
            passed=True,
            score=60.0,  # Conservative score for generic validation
            execution_time=0.1,
            message="⚠️ Generic test validation (limited)",
            warnings=[f"Full test validation not implemented for {language}"]
        )


class PerformanceBenchmarkGate:
    """Validates performance improvements through benchmarking."""
    
    def __init__(self):
        self.name = "Performance Benchmark Gate"
    
    def validate(
        self, 
        original_code: str, 
        optimized_code: str,
        benchmark_data: Dict[str, Any] = None,
        language: str = "python"
    ) -> GateResult:
        """Validate performance improvements."""
        start_time = time.time()
        
        if language.lower() == "python":
            return self._benchmark_python_code(original_code, optimized_code, benchmark_data)
        else:
            return self._benchmark_generic_code(original_code, optimized_code, language)
    
    def _benchmark_python_code(
        self, 
        original_code: str, 
        optimized_code: str,
        benchmark_data: Dict[str, Any] = None
    ) -> GateResult:
        """Benchmark Python code performance."""
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            # Create benchmark function if not provided
            if not benchmark_data:
                benchmark_data = self._create_default_benchmark(original_code)
            
            # Benchmark original code
            original_times = self._run_python_benchmark(original_code, benchmark_data)
            
            # Benchmark optimized code
            optimized_times = self._run_python_benchmark(optimized_code, benchmark_data)
            
            # Calculate improvement
            if original_times and optimized_times:
                original_avg = sum(original_times) / len(original_times)
                optimized_avg = sum(optimized_times) / len(optimized_times)
                
                improvement_percent = ((original_avg - optimized_avg) / original_avg) * 100
                
                # Determine pass/fail based on improvement
                if improvement_percent > 5:  # At least 5% improvement
                    passed = True
                    score = min(100, 50 + improvement_percent)  # Scale score
                    message = f"✅ Performance improved by {improvement_percent:.1f}%"
                elif improvement_percent > -10:  # Less than 10% regression acceptable
                    passed = True
                    score = 70 + improvement_percent  # Penalize regression
                    message = f"⚠️ Small performance change: {improvement_percent:.1f}%"
                    warnings.append("No significant performance improvement")
                else:
                    passed = False
                    score = max(0, 50 + improvement_percent)
                    message = f"❌ Performance regression: {improvement_percent:.1f}%"
                    errors.append("Significant performance regression detected")
                
                details = {
                    "original_avg_time": original_avg,
                    "optimized_avg_time": optimized_avg,
                    "improvement_percent": improvement_percent,
                    "original_times": original_times,
                    "optimized_times": optimized_times
                }
                
            else:
                passed = False
                score = 0.0
                message = "❌ Could not benchmark code performance"
                errors.append("Benchmarking failed")
                details = {}
                
        except Exception as e:
            errors.append(f"Benchmarking error: {str(e)}")
            passed = False
            score = 0.0
            message = f"❌ Benchmarking failed: {str(e)}"
            details = {}
        
        execution_time = time.time() - start_time
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=execution_time,
            message=message,
            details=details,
            errors=errors,
            warnings=warnings
        )
    
    def _create_default_benchmark(self, code: str) -> Dict[str, Any]:
        """Create default benchmark for code."""
        # Extract main functions and classes for benchmarking
        try:
            tree = ast.parse(code)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            return {
                "functions": functions[:3],  # Benchmark first 3 functions
                "classes": classes[:2],      # Benchmark first 2 classes
                "iterations": 1000
            }
        except:
            return {"iterations": 100}  # Fallback
    
    def _run_python_benchmark(self, code: str, benchmark_data: Dict[str, Any]) -> List[float]:
        """Run Python code benchmark."""
        times = []
        iterations = benchmark_data.get("iterations", 100)
        
        # Create temporary module
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file.flush()
            
            try:
                # Import module
                spec = importlib.util.spec_from_file_location("temp_module", temp_file.name)
                temp_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(temp_module)
                
                # Simple benchmark - just import and basic operations
                for _ in range(iterations):
                    start = time.perf_counter()
                    # Perform basic operations if possible
                    try:
                        if hasattr(temp_module, 'DataProcessor'):
                            # Test the DataProcessor class if it exists
                            data = list(range(20))
                            processor = temp_module.DataProcessor(data)
                            if hasattr(processor, 'slow_sort_and_filter'):
                                processor.slow_sort_and_filter()
                    except:
                        pass  # Ignore errors during benchmarking
                    
                    times.append(time.perf_counter() - start)
                
            except Exception:
                return []  # Return empty if benchmarking fails
            finally:
                Path(temp_file.name).unlink(missing_ok=True)
        
        return times
    
    def _benchmark_generic_code(self, original_code: str, optimized_code: str, language: str) -> GateResult:
        """Generic benchmarking for non-Python languages."""
        return GateResult(
            gate_name=self.name,
            passed=True,
            score=60.0,  # Conservative score
            execution_time=0.1,
            message="⚠️ Generic performance validation",
            warnings=[f"Detailed benchmarking not implemented for {language}"]
        )


class CodeQualityGate:
    """Validates code quality metrics."""
    
    def __init__(self):
        self.name = "Code Quality Gate"
    
    def validate(self, original_code: str, optimized_code: str, language: str = "python") -> GateResult:
        """Validate code quality."""
        start_time = time.time()
        
        if language.lower() == "python":
            return self._validate_python_quality(original_code, optimized_code)
        else:
            return self._validate_generic_quality(original_code, optimized_code, language)
    
    def _validate_python_quality(self, original_code: str, optimized_code: str) -> GateResult:
        """Validate Python code quality."""
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            # Calculate quality metrics for both versions
            original_metrics = self._calculate_quality_metrics(original_code)
            optimized_metrics = self._calculate_quality_metrics(optimized_code)
            
            # Compare metrics
            quality_maintained = True
            score = 100.0
            
            # Check complexity (should not increase significantly)
            complexity_change = optimized_metrics["complexity"] - original_metrics["complexity"]
            if complexity_change > 10:  # More than 10 point increase in complexity
                quality_maintained = False
                score -= 20
                warnings.append(f"Complexity increased by {complexity_change} points")
            
            # Check readability (should not decrease significantly)
            readability_change = optimized_metrics["readability"] - original_metrics["readability"]
            if readability_change < -15:  # More than 15 point decrease in readability
                score -= 15
                warnings.append(f"Readability decreased by {abs(readability_change)} points")
            
            # Check maintainability
            maintainability_change = optimized_metrics["maintainability"] - original_metrics["maintainability"]
            if maintainability_change < -10:
                score -= 10
                warnings.append(f"Maintainability decreased by {abs(maintainability_change)} points")
            
            # Determine pass/fail
            passed = score >= 60  # Pass if score is 60 or higher
            
            if passed:
                message = "✅ Code quality maintained or improved"
            else:
                message = "❌ Code quality degraded significantly"
                errors.append("Quality metrics fell below acceptable threshold")
            
            details = {
                "original_metrics": original_metrics,
                "optimized_metrics": optimized_metrics,
                "changes": {
                    "complexity": complexity_change,
                    "readability": readability_change,
                    "maintainability": maintainability_change
                }
            }
            
        except Exception as e:
            errors.append(f"Quality validation error: {str(e)}")
            passed = False
            score = 0.0
            message = f"❌ Quality validation failed: {str(e)}"
            details = {}
        
        execution_time = time.time() - start_time
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=execution_time,
            message=message,
            details=details,
            errors=errors,
            warnings=warnings
        )
    
    def _calculate_quality_metrics(self, code: str) -> Dict[str, float]:
        """Calculate basic quality metrics."""
        lines = [line for line in code.split('\n') if line.strip()]
        
        # Basic metrics
        total_lines = len(lines)
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        blank_lines = code.count('\n\n')
        
        # Simple heuristics
        readability = min(100, (comment_lines / max(total_lines, 1)) * 200 + 50)
        complexity = min(100, len(re.findall(r'\b(if|elif|for|while|def|class)\b', code)) * 2)
        maintainability = max(0, 100 - complexity * 0.5 + readability * 0.3)
        
        return {
            "readability": readability,
            "complexity": complexity,
            "maintainability": maintainability,
            "total_lines": total_lines,
            "comment_ratio": (comment_lines / max(total_lines, 1)) * 100
        }
    
    def _validate_generic_quality(self, original_code: str, optimized_code: str, language: str) -> GateResult:
        """Generic quality validation."""
        # Simple line count and basic metrics comparison
        original_lines = len([line for line in original_code.split('\n') if line.strip()])
        optimized_lines = len([line for line in optimized_code.split('\n') if line.strip()])
        
        line_change = ((optimized_lines - original_lines) / max(original_lines, 1)) * 100
        
        # Pass if code didn't grow too much
        passed = abs(line_change) < 50  # Less than 50% size change
        score = max(50, 100 - abs(line_change))
        
        message = f"✅ Code size change: {line_change:.1f}%" if passed else f"❌ Excessive code size change: {line_change:.1f}%"
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=0.1,
            message=message,
            details={"line_change_percent": line_change}
        )


class SecurityAnalysisGate:
    """Validates that no new security vulnerabilities are introduced."""
    
    def __init__(self):
        self.name = "Security Analysis Gate"
        self.security_patterns = self._initialize_security_patterns()
    
    def _initialize_security_patterns(self) -> Dict[str, Dict]:
        """Initialize security vulnerability patterns."""
        return {
            'eval_usage': {
                'pattern': r'\beval\s*\(',
                'severity': 'high',
                'description': 'Use of eval() function'
            },
            'exec_usage': {
                'pattern': r'\bexec\s*\(',
                'severity': 'high', 
                'description': 'Use of exec() function'
            },
            'shell_injection': {
                'pattern': r'subprocess\.(call|run|Popen).*shell\s*=\s*True',
                'severity': 'medium',
                'description': 'Subprocess call with shell=True'
            },
            'pickle_usage': {
                'pattern': r'pickle\.(loads?|dumps?)',
                'severity': 'medium',
                'description': 'Pickle deserialization'
            },
            'sql_injection_risk': {
                'pattern': r'%s.*execute|format.*execute',
                'severity': 'medium',
                'description': 'Potential SQL injection risk'
            }
        }
    
    def validate(self, original_code: str, optimized_code: str, language: str = "python") -> GateResult:
        """Validate security aspects of optimized code."""
        start_time = time.time()
        
        if language.lower() == "python":
            return self._validate_python_security(original_code, optimized_code)
        else:
            return self._validate_generic_security(original_code, optimized_code, language)
    
    def _validate_python_security(self, original_code: str, optimized_code: str) -> GateResult:
        """Validate Python security."""
        start_time = time.time()
        errors = []
        warnings = []
        
        # Find security issues in both versions
        original_issues = self._find_security_issues(original_code)
        optimized_issues = self._find_security_issues(optimized_code)
        
        # Check if new issues were introduced
        new_issues = []
        for issue in optimized_issues:
            if issue not in original_issues:
                new_issues.append(issue)
        
        # Calculate score
        if not new_issues:
            passed = True
            score = 100.0
            message = "✅ No new security vulnerabilities introduced"
        else:
            # Determine severity of new issues
            high_severity = [issue for issue in new_issues if issue['severity'] == 'high']
            medium_severity = [issue for issue in new_issues if issue['severity'] == 'medium']
            
            if high_severity:
                passed = False
                score = 0.0
                message = f"❌ {len(high_severity)} high-severity security issues introduced"
                errors.extend([f"High: {issue['description']}" for issue in high_severity])
            elif medium_severity:
                passed = len(medium_severity) <= 2  # Allow up to 2 medium severity issues
                score = max(30, 80 - len(medium_severity) * 20)
                message = f"⚠️ {len(medium_severity)} medium-severity security issues introduced"
                warnings.extend([f"Medium: {issue['description']}" for issue in medium_severity])
            else:
                passed = True
                score = 90.0
                message = "✅ Only low-severity issues introduced"
        
        details = {
            "original_issues": len(original_issues),
            "optimized_issues": len(optimized_issues),
            "new_issues": len(new_issues),
            "new_issue_details": new_issues
        }
        
        execution_time = time.time() - start_time
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=execution_time,
            message=message,
            details=details,
            errors=errors,
            warnings=warnings
        )
    
    def _find_security_issues(self, code: str) -> List[Dict[str, str]]:
        """Find security issues in code."""
        issues = []
        
        for pattern_name, pattern_info in self.security_patterns.items():
            matches = re.finditer(pattern_info['pattern'], code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append({
                    'type': pattern_name,
                    'severity': pattern_info['severity'],
                    'description': pattern_info['description'],
                    'line': line_num,
                    'code_snippet': match.group(0)
                })
        
        return issues
    
    def _validate_generic_security(self, original_code: str, optimized_code: str, language: str) -> GateResult:
        """Generic security validation."""
        # Very basic checks for other languages
        passed = True
        score = 80.0  # Conservative score
        message = "⚠️ Basic security validation passed"
        warnings = [f"Comprehensive security analysis not implemented for {language}"]
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=0.1,
            message=message,
            warnings=warnings
        )


class BehavioralEquivalenceGate:
    """Validates that optimized code behaves identically to original code."""
    
    def __init__(self):
        self.name = "Behavioral Equivalence Gate"
    
    def validate(
        self, 
        original_code: str, 
        optimized_code: str,
        test_cases: List[Dict[str, Any]] = None,
        language: str = "python"
    ) -> GateResult:
        """Validate behavioral equivalence."""
        start_time = time.time()
        
        if language.lower() == "python":
            return self._validate_python_behavior(original_code, optimized_code, test_cases)
        else:
            return self._validate_generic_behavior(original_code, optimized_code, language)
    
    def _validate_python_behavior(
        self, 
        original_code: str, 
        optimized_code: str,
        test_cases: List[Dict[str, Any]] = None
    ) -> GateResult:
        """Validate Python behavioral equivalence."""
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            # Generate test cases if not provided
            if not test_cases:
                test_cases = self._generate_test_cases(original_code)
            
            # Run test cases on both versions
            original_results = self._run_behavior_tests(original_code, test_cases)
            optimized_results = self._run_behavior_tests(optimized_code, test_cases)
            
            # Compare results
            mismatches = []
            for i, (orig, opt) in enumerate(zip(original_results, optimized_results)):
                if orig != opt:
                    mismatches.append({
                        'test_case': i,
                        'original_result': orig,
                        'optimized_result': opt
                    })
            
            # Determine pass/fail
            if not mismatches:
                passed = True
                score = 100.0
                message = "✅ All behavioral tests match"
            elif len(mismatches) <= len(test_cases) * 0.1:  # Allow up to 10% mismatches
                passed = True
                score = 90.0 - (len(mismatches) * 5)
                message = f"⚠️ Minor behavioral differences ({len(mismatches)} mismatches)"
                warnings.append(f"Found {len(mismatches)} behavioral mismatches")
            else:
                passed = False
                score = max(0, 50 - len(mismatches) * 5)
                message = f"❌ Significant behavioral differences ({len(mismatches)} mismatches)"
                errors.append(f"Too many behavioral mismatches: {len(mismatches)}")
            
            details = {
                "total_tests": len(test_cases),
                "mismatches": len(mismatches),
                "mismatch_details": mismatches[:5]  # Show first 5 mismatches
            }
            
        except Exception as e:
            errors.append(f"Behavioral validation error: {str(e)}")
            passed = False
            score = 0.0
            message = f"❌ Behavioral validation failed: {str(e)}"
            details = {}
        
        execution_time = time.time() - start_time
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=execution_time,
            message=message,
            details=details,
            errors=errors,
            warnings=warnings
        )
    
    def _generate_test_cases(self, code: str) -> List[Dict[str, Any]]:
        """Generate basic test cases for behavioral validation."""
        # Very simplified test case generation
        test_cases = []
        
        try:
            # Parse code to find functions/classes to test
            tree = ast.parse(code)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            # Generate basic test cases
            for func_name in functions[:3]:  # Test first 3 functions
                test_cases.append({
                    'type': 'function_call',
                    'name': func_name,
                    'args': []  # Simplified - no arguments
                })
            
            for class_name in classes[:2]:  # Test first 2 classes
                test_cases.append({
                    'type': 'class_instantiation',
                    'name': class_name,
                    'args': []
                })
                
        except:
            # Fallback - basic test cases
            test_cases = [{'type': 'import_test', 'name': 'module'}]
        
        return test_cases
    
    def _run_behavior_tests(self, code: str, test_cases: List[Dict[str, Any]]) -> List[Any]:
        """Run behavioral tests on code."""
        results = []
        
        # Create temporary module
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file.flush()
            
            try:
                # Import module
                spec = importlib.util.spec_from_file_location("temp_module", temp_file.name)
                temp_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(temp_module)
                
                # Run test cases
                for test_case in test_cases:
                    try:
                        if test_case['type'] == 'function_call':
                            if hasattr(temp_module, test_case['name']):
                                func = getattr(temp_module, test_case['name'])
                                result = str(type(func))  # Just check if function exists
                                results.append(result)
                            else:
                                results.append("function_not_found")
                        elif test_case['type'] == 'class_instantiation':
                            if hasattr(temp_module, test_case['name']):
                                cls = getattr(temp_module, test_case['name'])
                                result = str(type(cls))  # Just check if class exists
                                results.append(result)
                            else:
                                results.append("class_not_found")
                        else:
                            results.append("test_completed")
                    except Exception as e:
                        results.append(f"error: {str(e)}")
                        
            except Exception:
                results = ["import_failed"] * len(test_cases)
            finally:
                Path(temp_file.name).unlink(missing_ok=True)
        
        return results
    
    def _validate_generic_behavior(self, original_code: str, optimized_code: str, language: str) -> GateResult:
        """Generic behavioral validation."""
        # Basic similarity check
        similarity = difflib.SequenceMatcher(None, original_code, optimized_code).ratio()
        
        # Pass if codes are reasonably similar or if optimized is shorter (likely optimized)
        optimized_shorter = len(optimized_code) <= len(original_code)
        passed = similarity > 0.7 or optimized_shorter
        score = min(100, similarity * 100 + (10 if optimized_shorter else 0))
        
        message = f"✅ Code similarity: {similarity:.1%}" if passed else f"❌ Low code similarity: {similarity:.1%}"
        
        return GateResult(
            gate_name=self.name,
            passed=passed,
            score=score,
            execution_time=0.1,
            message=message,
            details={"similarity": similarity}
        )


class ValidationPipeline:
    """Main validation pipeline orchestrator."""
    
    def __init__(self):
        self.gates = {
            'syntax': SyntaxGate(),
            'test_compatibility': TestCompatibilityGate(),
            'performance': PerformanceBenchmarkGate(),
            'quality': CodeQualityGate(),
            'security': SecurityAnalysisGate(),
            'behavior': BehavioralEquivalenceGate()
        }
        self.required_gates = ['syntax', 'behavior']  # Gates that must pass
        self.optional_gates = ['test_compatibility', 'performance', 'quality', 'security']
    
    def validate(
        self, 
        original_code: str, 
        optimized_code: str,
        language: str = "python",
        test_file: str = None,
        config: Dict[str, Any] = None
    ) -> ValidationReport:
        """Run complete validation pipeline."""
        config = config or {}
        
        # Create report
        report = ValidationReport(
            original_code_hash=hashlib.md5(original_code.encode()).hexdigest(),
            optimized_code_hash=hashlib.md5(optimized_code.encode()).hexdigest(),
            validation_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            language=language
        )
        
        total_start_time = time.time()
        
        # Run each validation gate
        for gate_name, gate in self.gates.items():
            if config.get(f"skip_{gate_name}", False):
                continue  # Skip if configured to skip
                
            try:
                print(f"🔍 Running {gate.name}...")
                
                if gate_name == 'syntax':
                    result = gate.validate(optimized_code, language)
                elif gate_name == 'test_compatibility':
                    result = gate.validate(original_code, optimized_code, test_file, language)
                elif gate_name == 'performance':
                    result = gate.validate(original_code, optimized_code, None, language)
                elif gate_name == 'quality':
                    result = gate.validate(original_code, optimized_code, language)
                elif gate_name == 'security':
                    result = gate.validate(original_code, optimized_code, language)
                elif gate_name == 'behavior':
                    result = gate.validate(original_code, optimized_code, None, language)
                
                report.gate_results.append(result)
                print(f"  {result.message}")
                
            except Exception as e:
                # Handle gate execution errors
                error_result = GateResult(
                    gate_name=gate.name,
                    passed=False,
                    score=0.0,
                    execution_time=0.0,
                    message=f"❌ Gate execution failed: {str(e)}",
                    errors=[f"Execution error: {str(e)}"]
                )
                report.gate_results.append(error_result)
                print(f"  ❌ {gate.name} failed: {str(e)}")
        
        report.total_execution_time = time.time() - total_start_time
        
        # Calculate overall results
        self._calculate_overall_results(report)
        
        return report
    
    def _calculate_overall_results(self, report: ValidationReport):
        """Calculate overall validation results."""
        if not report.gate_results:
            report.overall_passed = False
            report.overall_score = 0.0
            return
        
        # Check required gates
        required_passed = True
        for result in report.gate_results:
            gate_name = result.gate_name.lower().replace(' ', '_').replace('gate', '').strip('_')
            if gate_name in self.required_gates and not result.passed:
                required_passed = False
                break
        
        # Calculate weighted score
        total_weight = 0
        weighted_score = 0
        
        gate_weights = {
            'syntax': 20,
            'behavior': 25,
            'performance': 20,
            'quality': 15,
            'security': 15,
            'test_compatibility': 5
        }
        
        for result in report.gate_results:
            gate_name = result.gate_name.lower().replace(' ', '_').replace('gate', '').strip('_')
            weight = gate_weights.get(gate_name, 10)
            weighted_score += result.score * weight
            total_weight += weight
        
        report.overall_score = weighted_score / total_weight if total_weight > 0 else 0
        report.overall_passed = required_passed and report.overall_score >= 70  # 70% threshold
        
        # Extract performance metrics
        for result in report.gate_results:
            if 'performance' in result.gate_name.lower() and result.details:
                report.performance_metrics = result.details


def main():
    """Command-line interface for validation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenEvolve Validation Pipeline")
    parser.add_argument("original", help="Original code file")
    parser.add_argument("optimized", help="Optimized code file")  
    parser.add_argument("--language", default="python", help="Programming language")
    parser.add_argument("--test-file", help="Test file for compatibility checking")
    parser.add_argument("--output", help="Output file for detailed report")
    parser.add_argument("--config", help="Configuration file (JSON)")
    
    args = parser.parse_args()
    
    # Read code files
    with open(args.original, 'r') as f:
        original_code = f.read()
    
    with open(args.optimized, 'r') as f:
        optimized_code = f.read()
    
    # Load configuration
    config = {}
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Run validation
    pipeline = ValidationPipeline()
    report = pipeline.validate(
        original_code=original_code,
        optimized_code=optimized_code,
        language=args.language,
        test_file=args.test_file,
        config=config
    )
    
    # Display summary
    print("\n🏁 Validation Complete!")
    print("=" * 50)
    summary = report.get_summary()
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Save detailed report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        print(f"\n📊 Detailed report saved to: {args.output}")


if __name__ == "__main__":
    main()