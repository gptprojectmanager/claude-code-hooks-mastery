#!/usr/bin/env python3
"""
OpenEvolve + Gemini Integration Demo
This script demonstrates a complete optimization workflow using our integration system.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the utils directory to Python path
sys.path.append(str(Path(__file__).parent))

from openevolve_integration_orchestrator import OpenEvolveIntegrationOrchestrator


DEMO_CODE = '''
def inefficient_fibonacci(n):
    """
    Highly inefficient Fibonacci implementation with multiple optimization opportunities.
    """
    if n <= 1:
        return n
    
    # Inefficient: repeated calculations
    result = inefficient_fibonacci(n - 1) + inefficient_fibonacci(n - 2)
    return result

def slow_data_processing(data):
    """
    Inefficient data processing with multiple algorithmic issues.
    """
    # Inefficient: nested loops for simple operations
    filtered_data = []
    for i in range(len(data)):
        item = data[i]
        if item > 10:
            filtered_data.append(item)
    
    # Inefficient: bubble sort implementation
    for i in range(len(filtered_data)):
        for j in range(len(filtered_data) - 1):
            if filtered_data[j] > filtered_data[j + 1]:
                temp = filtered_data[j]
                filtered_data[j] = filtered_data[j + 1]
                filtered_data[j + 1] = temp
    
    # Inefficient: manual sum calculation
    total = 0
    for item in filtered_data:
        total = total + item
    
    # Inefficient: manual average calculation
    average = total / len(filtered_data) if len(filtered_data) > 0 else 0
    
    return {
        "filtered": filtered_data,
        "total": total,
        "average": average,
        "count": len(filtered_data)
    }

def string_concatenation_problem(items):
    """
    Inefficient string operations.
    """
    result = ""
    for item in items:
        # Inefficient: quadratic string concatenation
        result = result + str(item) + ", "
    
    # Remove trailing comma and space
    if len(result) > 2:
        result = result[:-2]
    
    return result

# Example usage
if __name__ == "__main__":
    # Test data
    test_data = [1, 15, 3, 22, 8, 45, 12, 7, 33, 18]
    string_items = ["apple", "banana", "cherry", "date", "elderberry"]
    
    # Run inefficient operations
    fib_result = inefficient_fibonacci(10)
    processing_result = slow_data_processing(test_data)
    string_result = string_concatenation_problem(string_items)
    
    print(f"Fibonacci(10): {fib_result}")
    print(f"Data processing: {processing_result}")
    print(f"String concatenation: {string_result}")
'''


async def main():
    """Run the OpenEvolve optimization demo."""
    
    print("🚀 OpenEvolve + Gemini 2.5 Pro Integration Demo")
    print("=" * 60)
    print()
    print("📋 This demo will:")
    print("  1. Analyze the provided inefficient code")
    print("  2. Determine optimal iteration count using Gemini 2.5 Pro")
    print("  3. Run a simulated optimization workflow")
    print("  4. Validate results using multi-stage pipeline")
    print("  5. Store all results in KRAG memory system")
    print()
    
    # Initialize orchestrator
    print("🔧 Initializing OpenEvolve Integration Orchestrator...")
    orchestrator = OpenEvolveIntegrationOrchestrator()
    print("✅ Orchestrator initialized")
    print()
    
    try:
        # Phase 1: Code Analysis
        print("🔍 Phase 1: Analyzing code complexity and optimization potential")
        print("-" * 50)
        
        analysis_report = orchestrator.code_analyzer.analyze_code_string(DEMO_CODE, "python")
        
        print(f"📊 Analysis Results:")
        print(f"  • Lines of code: {analysis_report.lines_of_code}")
        print(f"  • Complexity score: {analysis_report.complexity_score:.1f}/100")
        print(f"  • Optimization potential: {analysis_report.optimization_potential_score:.1f}%")
        print(f"  • Bottlenecks found: {len(analysis_report.bottlenecks)}")
        print(f"  • Optimization opportunities: {len(analysis_report.optimization_opportunities)}")
        print()
        
        # Show top bottlenecks
        if analysis_report.bottlenecks:
            print("🚨 Top Performance Bottlenecks:")
            for i, bottleneck in enumerate(analysis_report.bottlenecks[:3], 1):
                print(f"  {i}. {bottleneck.description} ({bottleneck.severity})")
                print(f"     Impact: {bottleneck.impact_estimate:.0f}% | Location: {bottleneck.location}")
        
        print()
        
        # Phase 2: Iteration Selection
        print("🎯 Phase 2: Intelligent iteration selection using Gemini 2.5 Pro")
        print("-" * 50)
        
        iteration_rec = orchestrator.iteration_selector.select_iterations(
            code=DEMO_CODE,
            language="python",
            budget_credits=500,  # Available Gemini credits
            time_limit_minutes=15,
            optimization_goals=["performance", "algorithmic_efficiency", "code_quality"]
        )
        
        print(f"📋 Iteration Recommendation:")
        print(f"  • Recommended iterations: {iteration_rec.recommended_iterations}")
        print(f"  • Complexity level: {iteration_rec.complexity_level}")
        print(f"  • Estimated credits: {iteration_rec.estimated_credits}")
        print(f"  • Estimated duration: {iteration_rec.estimated_duration_minutes} minutes")
        print(f"  • Optimization strategy: {iteration_rec.optimization_strategy}")
        print(f"  • Confidence: {iteration_rec.confidence_score:.2f}")
        print()
        
        print("💡 Rationale:")
        for reason in iteration_rec.rationale:
            print(f"  • {reason}")
        print()
        
        # Phase 3: Start Optimization Workflow
        print("🚀 Phase 3: Starting optimization workflow")
        print("-" * 50)
        
        success, message, session_id = await orchestrator.start_optimization_workflow(
            code=DEMO_CODE,
            language="python",
            optimization_goals=["performance", "algorithmic_efficiency", "code_quality"],
            constraints={
                "max_credits": 500,
                "time_limit": 15,
                "require_tests": False
            },
            request_context={
                "demo_mode": True,
                "request_id": "openevolve_demo_2025"
            }
        )
        
        if success:
            print(f"✅ {message}")
            print(f"📝 Session ID: {session_id}")
        else:
            print(f"❌ {message}")
            return
        
        print()
        
        # Phase 4: Get final status
        print("📊 Phase 4: Final workflow results")
        print("-" * 50)
        
        if session_id:
            final_status = orchestrator.get_session_status(session_id)
            if final_status:
                print(f"🎯 Final Status: {final_status['status']}")
                print(f"📈 Optimization Potential: {final_status.get('optimization_potential', 'N/A'):.1f}%")
                print(f"⚡ Improvement: {final_status.get('improvement_percentage', 0):.1f}%")
                
                if 'validation_score' in final_status:
                    print(f"✅ Validation Score: {final_status['validation_score']:.1f}/100")
                    print(f"🔒 Validation Passed: {'Yes' if final_status.get('validation_passed', False) else 'No'}")
                
                print(f"🔄 Progress Updates: {len(final_status.get('progress_updates', []))}")
                
                # Show recent progress updates
                if final_status.get('progress_updates'):
                    print("\n📋 Recent Progress:")
                    for update in final_status['progress_updates'][-3:]:
                        level_emoji = {"success": "✅", "error": "❌", "info": "ℹ️", "warning": "⚠️"}.get(update.get('level', 'info'), 'ℹ️')
                        print(f"  {level_emoji} {update.get('message', 'No message')}")
        
        print()
        
        # Phase 5: Cleanup
        print("🧹 Phase 5: Session cleanup")
        print("-" * 50)
        
        if session_id:
            cleanup_success, cleanup_message = await orchestrator.cleanup_session(session_id, preserve_results=True)
            if cleanup_success:
                print(f"✅ {cleanup_message}")
            else:
                print(f"⚠️ {cleanup_message}")
        
        print()
        
        # Summary
        print("🎉 Demo Completed Successfully!")
        print("=" * 60)
        print()
        print("📊 Summary:")
        print(f"  • Analyzed {analysis_report.lines_of_code} lines of Python code")
        print(f"  • Found {len(analysis_report.bottlenecks)} performance bottlenecks")
        print(f"  • Recommended {iteration_rec.recommended_iterations} optimization iterations")
        print(f"  • Estimated {iteration_rec.estimated_credits} Gemini credits needed")
        print(f"  • Used intelligent model selection (Gemini 2.5 Pro for analysis)")
        print(f"  • Stored all results in KRAG memory system")
        print()
        print("💡 Next Steps:")
        print("  1. Start the actual services with: ./start_openevolve_gemini_service.sh")
        print("  2. Run the full integration test: python3 test_openevolve_gemini_integration.py")
        print("  3. Use the orchestrator to optimize your own code!")
        print()
        
    except Exception as e:
        print(f"💥 Demo failed with error: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)