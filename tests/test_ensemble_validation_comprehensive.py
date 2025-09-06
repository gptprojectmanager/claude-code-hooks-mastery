#!/usr/bin/env python3
"""
Test Suite Comprehensivo per Sistema Ensemble Validation
========================================================

Test COMPLETO del sistema ensemble attuale per:
1. Baseline Performance Metrics
2. Identificazione Limitazioni 
3. Stress Testing
4. Edge Cases
5. Comparison con Advanced Patterns
"""

import json
import sys
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, MagicMock

# Add hooks directory to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "hooks"))

import post_tool_use


class EnsembleValidationTester:
    """Test suite comprehensivo per ensemble validation"""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.baseline_data = {}
        
    def log_test(self, test_name: str, passed: bool, details: Dict[str, Any]):
        """Log test result with detailed metrics"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed and "error" in details:
            print(f"   Error: {details['error']}")
        print(f"   Details: {json.dumps(details, indent=2)[:200]}...")


async def test_1_basic_ensemble_functionality():
    """Test 1: Basic Ensemble Function Calls"""
    tester = EnsembleValidationTester()
    
    # Test input che dovrebbe triggare ensemble validation
    test_input = {
        "session_id": "test-ensemble-001",
        "request": {
            "tool_name": "mcp__shrimp-task-manager__verify_task",
            "parameters": {"score": 85}
        },
        "response": {"success": True},
        "timestamp": int(time.time() * 1000)
    }
    
    try:
        # Call ensemble validation
        start_time = time.time()
        result = await post_tool_use.trigger_ensemble_validation(test_input)
        execution_time = time.time() - start_time
        
        # Basic checks
        checks = {
            "has_ensemble_validation_key": "ensemble_validation" in result,
            "has_models_used": "models_used" in result,
            "has_consensus_score": "consensus_score" in result,
            "execution_time_reasonable": execution_time < 5.0,
            "models_array_populated": len(result.get("models_used", [])) > 0,
            "consensus_score_valid": 0 <= result.get("consensus_score", -1) <= 100
        }
        
        all_passed = all(checks.values())
        
        tester.log_test("Basic Ensemble Functionality", all_passed, {
            "result": result,
            "execution_time": execution_time,
            "checks": checks
        })
        
        return result, execution_time
        
    except Exception as e:
        tester.log_test("Basic Ensemble Functionality", False, {
            "error": str(e),
            "execution_time": 0
        })
        return None, 0


async def test_2_consensus_calculation_accuracy():
    """Test 2: Accuracy of Consensus Score Calculation"""
    tester = EnsembleValidationTester()
    
    test_cases = [
        {"opus_score": 85, "gemini_score": 82, "expected_consensus": 83.5},
        {"opus_score": 100, "gemini_score": 100, "expected_consensus": 100.0},
        {"opus_score": 0, "gemini_score": 100, "expected_consensus": 50.0},
        {"opus_score": 60, "gemini_score": 80, "expected_consensus": 70.0}
    ]
    
    accuracy_results = []
    
    for i, case in enumerate(test_cases):
        try:
            # Mock the individual validation functions to return specific scores
            with patch('post_tool_use.run_opus_validation') as mock_opus, \
                 patch('post_tool_use.run_gemini_validation') as mock_gemini:
                
                mock_opus.return_value = {"model": "opus", "score": case["opus_score"]}
                mock_gemini.return_value = {"model": "gemini_gpro", "score": case["gemini_score"]}
                
                test_input = {
                    "request": {"tool_name": "mcp__shrimp-task-manager__verify_task", "parameters": {"score": 85}},
                    "response": {"success": True}
                }
                
                result = await post_tool_use.trigger_ensemble_validation(test_input)
                actual_consensus = result.get("consensus_score", -1)
                expected_consensus = case["expected_consensus"]
                
                # Allow small floating point differences
                accuracy = abs(actual_consensus - expected_consensus) < 0.01
                accuracy_results.append(accuracy)
                
                print(f"   Case {i+1}: Expected {expected_consensus}, Got {actual_consensus}, {'✓' if accuracy else '✗'}")
                
        except Exception as e:
            accuracy_results.append(False)
            print(f"   Case {i+1}: Error - {e}")
    
    overall_accuracy = all(accuracy_results)
    accuracy_percentage = sum(accuracy_results) / len(accuracy_results) * 100
    
    tester.log_test("Consensus Calculation Accuracy", overall_accuracy, {
        "accuracy_percentage": accuracy_percentage,
        "test_cases": len(test_cases),
        "passed_cases": sum(accuracy_results),
        "details": test_cases
    })
    
    return accuracy_percentage


async def test_3_decision_threshold_logic():
    """Test 3: Decision Threshold Logic (approved/needs_revision/rejected)"""
    tester = EnsembleValidationTester()
    
    threshold_tests = [
        {"consensus": 90, "expected_status": "approved"},
        {"consensus": 80, "expected_status": "approved"},  # Boundary
        {"consensus": 79, "expected_status": "needs_revision"},
        {"consensus": 70, "expected_status": "needs_revision"},
        {"consensus": 60, "expected_status": "needs_revision"},  # Boundary
        {"consensus": 59, "expected_status": "rejected"},
        {"consensus": 30, "expected_status": "rejected"},
        {"consensus": 0, "expected_status": "rejected"}
    ]
    
    threshold_results = []
    
    for test_case in threshold_tests:
        try:
            # Mock both validation functions to return scores that average to the target consensus
            target_consensus = test_case["consensus"]
            opus_score = target_consensus + 1
            gemini_score = target_consensus - 1
            
            with patch('post_tool_use.run_opus_validation') as mock_opus, \
                 patch('post_tool_use.run_gemini_validation') as mock_gemini:
                
                mock_opus.return_value = {"model": "opus", "score": opus_score}
                mock_gemini.return_value = {"model": "gemini_gpro", "score": gemini_score}
                
                test_input = {
                    "request": {"tool_name": "mcp__shrimp-task-manager__verify_task", "parameters": {"score": 85}},
                    "response": {"success": True}
                }
                
                result = await post_tool_use.trigger_ensemble_validation(test_input)
                actual_status = result.get("final_status")
                expected_status = test_case["expected_status"]
                
                correct_decision = actual_status == expected_status
                threshold_results.append(correct_decision)
                
                print(f"   Consensus {target_consensus}: Expected '{expected_status}', Got '{actual_status}', {'✓' if correct_decision else '✗'}")
                
        except Exception as e:
            threshold_results.append(False)
            print(f"   Consensus {test_case['consensus']}: Error - {e}")
    
    threshold_accuracy = all(threshold_results)
    threshold_percentage = sum(threshold_results) / len(threshold_results) * 100
    
    tester.log_test("Decision Threshold Logic", threshold_accuracy, {
        "threshold_accuracy": threshold_percentage,
        "test_cases": len(threshold_tests),
        "passed_cases": sum(threshold_results)
    })
    
    return threshold_percentage


async def test_4_error_handling_resilience():
    """Test 4: Error Handling and Resilience"""
    tester = EnsembleValidationTester()
    
    error_scenarios = []
    
    # Scenario 1: Opus fails, Gemini succeeds
    try:
        with patch('post_tool_use.run_opus_validation') as mock_opus, \
             patch('post_tool_use.run_gemini_validation') as mock_gemini:
            
            mock_opus.side_effect = Exception("Opus API timeout")
            mock_gemini.return_value = {"model": "gemini_gpro", "score": 80}
            
            test_input = {
                "request": {"tool_name": "mcp__shrimp-task-manager__verify_task", "parameters": {"score": 85}},
                "response": {"success": True}
            }
            
            result = await post_tool_use.trigger_ensemble_validation(test_input)
            
            # Should handle the error gracefully
            has_error_info = "opus" in result.get("validation_details", {}) and "error" in result["validation_details"]["opus"]
            still_has_gemini = "gemini" in result.get("validation_details", {}) and "score" in result["validation_details"]["gemini"]
            
            error_scenarios.append({
                "scenario": "opus_fails",
                "handled_gracefully": has_error_info and still_has_gemini,
                "result": result
            })
            
    except Exception as e:
        error_scenarios.append({
            "scenario": "opus_fails",
            "handled_gracefully": False,
            "error": str(e)
        })
    
    # Scenario 2: Both models fail
    try:
        with patch('post_tool_use.run_opus_validation') as mock_opus, \
             patch('post_tool_use.run_gemini_validation') as mock_gemini:
            
            mock_opus.side_effect = Exception("Opus API timeout")
            mock_gemini.side_effect = Exception("Gemini API timeout")
            
            result = await post_tool_use.trigger_ensemble_validation(test_input)
            
            # Should still return a valid structure
            has_basic_structure = "ensemble_validation" in result and "models_used" in result
            
            error_scenarios.append({
                "scenario": "both_fail",
                "handled_gracefully": has_basic_structure,
                "result": result
            })
            
    except Exception as e:
        error_scenarios.append({
            "scenario": "both_fail", 
            "handled_gracefully": False,
            "error": str(e)
        })
    
    all_handled = all(scenario["handled_gracefully"] for scenario in error_scenarios)
    
    tester.log_test("Error Handling Resilience", all_handled, {
        "error_scenarios": error_scenarios,
        "total_scenarios": len(error_scenarios),
        "handled_gracefully": sum(1 for s in error_scenarios if s["handled_gracefully"])
    })
    
    return error_scenarios


async def test_5_performance_characteristics():
    """Test 5: Performance and Scalability Characteristics"""
    tester = EnsembleValidationTester()
    
    # Test multiple concurrent requests
    concurrent_tests = []
    test_inputs = []
    
    # Create 10 test inputs
    for i in range(10):
        test_inputs.append({
            "request": {"tool_name": f"test_tool_{i}", "parameters": {"score": 80 + i}},
            "response": {"success": True},
            "test_id": i
        })
    
    # Run concurrent ensemble validations
    start_time = time.time()
    try:
        tasks = [post_tool_use.trigger_ensemble_validation(input_data) for input_data in test_inputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        avg_time_per_request = total_time / len(test_inputs) if test_inputs else 0
        
        performance_metrics = {
            "total_requests": len(test_inputs),
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "total_time": total_time,
            "avg_time_per_request": avg_time_per_request,
            "requests_per_second": len(test_inputs) / total_time if total_time > 0 else 0
        }
        
        # Performance thresholds
        performance_acceptable = (
            avg_time_per_request < 2.0 and  # Less than 2 seconds per request
            len(successful_results) / len(test_inputs) >= 0.9  # 90% success rate
        )
        
        tester.log_test("Performance Characteristics", performance_acceptable, performance_metrics)
        
        return performance_metrics
        
    except Exception as e:
        tester.log_test("Performance Characteristics", False, {
            "error": str(e),
            "total_time": time.time() - start_time
        })
        return {}


async def test_6_identify_current_limitations():
    """Test 6: Identify Current System Limitations"""
    tester = EnsembleValidationTester()
    
    # Analyze current implementation limitations
    limitations = []
    
    # Limitation 1: Hardcoded placeholder functions
    try:
        test_input = {"request": {"tool_name": "test"}, "response": {"success": True}}
        result = await post_tool_use.trigger_ensemble_validation(test_input)
        
        opus_result = result.get("validation_details", {}).get("opus", {})
        gemini_result = result.get("validation_details", {}).get("gemini", {})
        
        # Check if results look like placeholders
        if opus_result.get("score") == 85 and "placeholder" not in str(opus_result).lower():
            limitations.append({
                "limitation": "hardcoded_scores",
                "description": "Opus validation returns hardcoded score of 85",
                "severity": "critical",
                "impact": "No real validation occurring"
            })
        
        if gemini_result.get("score") == 82 and "placeholder" not in str(gemini_result).lower():
            limitations.append({
                "limitation": "hardcoded_scores",
                "description": "Gemini validation returns hardcoded score of 82", 
                "severity": "critical",
                "impact": "No real validation occurring"
            })
        
    except Exception as e:
        limitations.append({
            "limitation": "basic_functionality_broken",
            "description": f"Basic ensemble validation failed: {e}",
            "severity": "critical"
        })
    
    # Limitation 2: Simple averaging algorithm
    limitations.append({
        "limitation": "simple_averaging",
        "description": "Consensus calculated by simple arithmetic mean",
        "severity": "medium", 
        "impact": "No weighted scoring, no confidence intervals, no outlier detection",
        "advanced_alternative": "Multi-objective fitness evaluation with weighted factors"
    })
    
    # Limitation 3: Static thresholds
    limitations.append({
        "limitation": "static_thresholds",
        "description": "Fixed thresholds (80, 60) for decision making",
        "severity": "medium",
        "impact": "No adaptive thresholds, no context-aware decisions",
        "advanced_alternative": "Meta-learning adaptive thresholds based on historical performance"
    })
    
    # Limitation 4: No population-based consensus
    limitations.append({
        "limitation": "no_population_consensus",
        "description": "Only 2 models, no population-based validation",
        "severity": "high",
        "impact": "Limited diversity, no collective intelligence",
        "advanced_alternative": "Population-based consensus with diverse model ensemble"
    })
    
    # Limitation 5: No telemetry integration
    limitations.append({
        "limitation": "no_telemetry",
        "description": "No integration with collective intelligence telemetry",
        "severity": "medium",
        "impact": "No learning from historical patterns, no discovery recording",
        "advanced_alternative": "Enhanced telemetry with pattern detection and discovery recording"
    })
    
    # Limitation 6: No ADAS-like adaptive behavior
    limitations.append({
        "limitation": "no_adaptive_behavior",
        "description": "No self-improving or adaptive validation behavior",
        "severity": "high",
        "impact": "Cannot learn and improve over time",
        "advanced_alternative": "ADAS-inspired adaptive validation with continuous improvement"
    })
    
    critical_limitations = len([l for l in limitations if l.get("severity") == "critical"])
    
    tester.log_test("Current System Limitations Analysis", True, {
        "total_limitations": len(limitations),
        "critical_limitations": critical_limitations,
        "high_severity": len([l for l in limitations if l.get("severity") == "high"]),
        "medium_severity": len([l for l in limitations if l.get("severity") == "medium"]),
        "limitations": limitations
    })
    
    return limitations


async def run_comprehensive_test_suite():
    """Run complete test suite and generate comprehensive report"""
    
    print("🧪 STARTING COMPREHENSIVE ENSEMBLE VALIDATION TEST SUITE")
    print("=" * 70)
    
    test_results = {}
    
    # Run all tests
    print("\n1. Basic Functionality Test")
    basic_result, exec_time = await test_1_basic_ensemble_functionality()
    test_results["basic_functionality"] = {"result": basic_result, "execution_time": exec_time}
    
    print("\n2. Consensus Calculation Accuracy")
    accuracy = await test_2_consensus_calculation_accuracy()
    test_results["consensus_accuracy"] = {"accuracy_percentage": accuracy}
    
    print("\n3. Decision Threshold Logic")
    threshold_accuracy = await test_3_decision_threshold_logic()
    test_results["threshold_logic"] = {"accuracy_percentage": threshold_accuracy}
    
    print("\n4. Error Handling Resilience")
    error_scenarios = await test_4_error_handling_resilience()
    test_results["error_handling"] = {"scenarios": error_scenarios}
    
    print("\n5. Performance Characteristics")
    performance = await test_5_performance_characteristics()
    test_results["performance"] = performance
    
    print("\n6. Current Limitations Analysis")
    limitations = await test_6_identify_current_limitations()
    test_results["limitations"] = limitations
    
    # Generate comprehensive report
    report = generate_baseline_report(test_results)
    
    # Save report
    report_path = Path(__file__).parent / "ensemble_baseline_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 COMPREHENSIVE REPORT SAVED: {report_path}")
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETED")
    
    return report


def generate_baseline_report(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive baseline performance report"""
    
    # Calculate overall system score
    scores = []
    
    if "consensus_accuracy" in test_results:
        scores.append(test_results["consensus_accuracy"]["accuracy_percentage"])
    
    if "threshold_logic" in test_results:
        scores.append(test_results["threshold_logic"]["accuracy_percentage"])
    
    # Performance score (based on execution time)
    if "performance" in test_results and test_results["performance"]:
        avg_time = test_results["performance"].get("avg_time_per_request", 5.0)
        perf_score = max(0, 100 - (avg_time * 20))  # Penalty for slow performance
        scores.append(perf_score)
    
    overall_score = sum(scores) / len(scores) if scores else 0
    
    # Critical issues count
    critical_issues = 0
    if "limitations" in test_results:
        critical_issues = len([l for l in test_results["limitations"] if l.get("severity") == "critical"])
    
    report = {
        "test_timestamp": time.time(),
        "system_type": "Simple Ensemble Validation",
        "overall_score": round(overall_score, 2),
        "critical_issues": critical_issues,
        
        "baseline_metrics": {
            "consensus_accuracy": test_results.get("consensus_accuracy", {}).get("accuracy_percentage", 0),
            "threshold_logic_accuracy": test_results.get("threshold_logic", {}).get("accuracy_percentage", 0),
            "average_response_time": test_results.get("performance", {}).get("avg_time_per_request", 0),
            "error_handling_robustness": len([s for s in test_results.get("error_handling", {}).get("scenarios", []) 
                                            if s.get("handled_gracefully", False)])
        },
        
        "identified_limitations": test_results.get("limitations", []),
        
        "improvement_priorities": [
            {
                "priority": 1,
                "issue": "Replace hardcoded validation functions with real API calls",
                "impact": "Critical - Currently no real validation occurring",
                "solution": "Implement actual Opus and Gemini API integration"
            },
            {
                "priority": 2, 
                "issue": "Implement multi-objective validation framework",
                "impact": "High - Simple averaging insufficient for complex validation",
                "solution": "Multi-dimensional scoring with weighted factors like fitness-evaluator.sh"
            },
            {
                "priority": 3,
                "issue": "Add population-based consensus mechanisms",
                "impact": "High - Limited model diversity reduces validation quality",
                "solution": "Expand to multiple models with collective intelligence patterns"
            },
            {
                "priority": 4,
                "issue": "Implement meta-learning adaptive thresholds",
                "impact": "Medium - Static thresholds don't adapt to context",
                "solution": "Dynamic thresholds based on historical performance"
            },
            {
                "priority": 5,
                "issue": "Integrate collective intelligence telemetry",
                "impact": "Medium - Missing learning and improvement opportunities",
                "solution": "Use enhanced-telemetry-collector.sh patterns"
            }
        ],
        
        "advanced_patterns_identified": {
            "multi_objective_fitness": "fitness-evaluator.sh uses weighted scoring (40% performance, 30% novelty, 20% efficiency, 10% safety)",
            "population_evolution": "evolution-engine.sh implements population-based optimization with mutation/crossover",
            "collective_telemetry": "enhanced-telemetry-collector.sh provides comprehensive data collection and pattern detection",
            "adaptive_behavior": "ADAS-inspired patterns for continuous improvement and self-optimization"
        },
        
        "test_results_detail": test_results
    }
    
    return report


if __name__ == "__main__":
    # Run comprehensive test suite
    asyncio.run(run_comprehensive_test_suite())