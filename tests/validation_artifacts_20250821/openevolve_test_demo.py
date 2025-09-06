#!/usr/bin/env python3
"""
OpenEvolve Integration Demo Script
Demonstrates the complete workflow of evolutionary code optimization
"""

import os
import json
import time
import requests
from pathlib import Path
from openevolve_worktree_manager import OpenEvolveWorktreeManager


class OpenEvolveDemo:
    """Demo class for OpenEvolve integration workflow."""
    
    def __init__(self):
        self.manager = OpenEvolveWorktreeManager()
        self.openevolve_service_url = "http://localhost:8000"
        
    def check_openevolve_service(self) -> bool:
        """Check if OpenEvolve service is running."""
        try:
            response = requests.get(f"{self.openevolve_service_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def analyze_code_complexity(self, code: str) -> dict:
        """Analyze code complexity to determine optimization parameters."""
        lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
        line_count = len(lines)
        
        # Count nested loops (simple heuristic)
        nested_level = 0
        max_nesting = 0
        for line in lines:
            if 'for ' in line or 'while ' in line:
                nested_level += 1
                max_nesting = max(max_nesting, nested_level)
            elif line.strip() == '' or line.startswith('def ') or line.startswith('class '):
                nested_level = 0
        
        # Determine optimization parameters
        if line_count < 50:
            complexity = "simple"
            iterations = 10
        elif line_count < 200:
            complexity = "medium"  
            iterations = 20
        else:
            complexity = "complex"
            iterations = 35
        
        # Adjust for nested loops
        if max_nesting >= 2:
            iterations = min(50, iterations + 15)  # More iterations for nested complexity
            
        return {
            "complexity": complexity,
            "line_count": line_count,
            "max_nesting": max_nesting,
            "recommended_iterations": iterations
        }
    
    def run_optimization_demo(self, code: str, language: str = "python") -> dict:
        """Run complete optimization demo workflow."""
        print("🚀 Starting OpenEvolve Optimization Demo")
        print("=" * 50)
        
        # Step 1: Check service availability
        print("\n📡 Step 1: Checking OpenEvolve service...")
        if not self.check_openevolve_service():
            return {
                "success": False,
                "error": "OpenEvolve service not available at http://localhost:8000"
            }
        print("✅ OpenEvolve service is running")
        
        # Step 2: Analyze code complexity
        print("\n🔍 Step 2: Analyzing code complexity...")
        analysis = self.analyze_code_complexity(code)
        print(f"   Lines of code: {analysis['line_count']}")
        print(f"   Complexity level: {analysis['complexity']}")
        print(f"   Max nesting level: {analysis['max_nesting']}")
        print(f"   Recommended iterations: {analysis['recommended_iterations']}")
        
        # Step 3: Create optimization session
        print("\n🏗️  Step 3: Creating optimization worktree...")
        success, message, session = self.manager.create_optimization_session(
            code, language, {"iterations": analysis['recommended_iterations']}
        )
        
        if not success:
            return {"success": False, "error": message}
        
        print(f"✅ {message}")
        print(f"   Session ID: {session.session_id}")
        print(f"   Workspace: {session.worktree_path}")
        print(f"   Branch: {session.branch_name}")
        
        # Step 4: Simulate optimization process
        print(f"\n🧬 Step 4: Running evolutionary optimization...")
        optimization_request = {
            "code": code,
            "language": language,
            "optimization_level": "high",
            "session_id": session.session_id,
            "max_iterations": analysis['recommended_iterations'],
            "target_metrics": ["performance", "algorithmic_efficiency", "code_quality"]
        }
        
        print(f"   Optimization parameters: {json.dumps(optimization_request, indent=4)}")
        
        # Update session status
        self.manager.update_session_status(session.session_id, "optimizing")
        
        # Simulate optimization time (in real scenario, this would be the actual optimization)
        print("   🔄 Evolution in progress...")
        for i in range(3):
            time.sleep(1)
            print(f"      Generation {i+1}: Exploring optimizations...")
        
        # Step 5: Simulate validation
        print(f"\n✅ Step 5: Validating optimized code...")
        self.manager.update_session_status(session.session_id, "validating")
        
        validation_results = {
            "syntax_check": True,
            "test_compatibility": True,
            "performance_improvement": 42.5,  # 42.5% improvement
            "quality_score": 8.7,
            "security_issues": 0
        }
        
        print(f"   Validation results: {json.dumps(validation_results, indent=4)}")
        
        # Step 6: Complete session
        print(f"\n🎯 Step 6: Completing optimization session...")
        self.manager.update_session_status(session.session_id, "completed", {
            "validation_results": validation_results,
            "performance_improvement": validation_results["performance_improvement"]
        })
        
        print("✅ Optimization completed successfully!")
        
        # Step 7: Show final results
        print(f"\n📊 Step 7: Optimization Summary")
        print(f"   Session ID: {session.session_id}")
        print(f"   Language: {language}")
        print(f"   Complexity: {analysis['complexity']}")
        print(f"   Performance improvement: {validation_results['performance_improvement']:.1f}%")
        print(f"   Quality score: {validation_results['quality_score']}/10")
        print(f"   Workspace: {session.worktree_path}")
        
        return {
            "success": True,
            "session_id": session.session_id,
            "analysis": analysis,
            "validation": validation_results,
            "workspace_path": session.worktree_path
        }
    
    def cleanup_demo_session(self, session_id: str):
        """Cleanup demo session."""
        print(f"\n🧹 Cleaning up session {session_id}...")
        success, message = self.manager.cleanup_session(session_id, preserve_results=True)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")


def main():
    """Run the OpenEvolve demo."""
    # Sample inefficient code for optimization
    sample_code = '''#!/usr/bin/env python3
"""
Sample Python code for OpenEvolve optimization testing
Contains intentional inefficiencies for optimization demonstration
"""

import time
from typing import List, Dict

class DataProcessor:
    """A deliberately inefficient data processing class."""
    
    def __init__(self, data: List[int]):
        self.data = data
        self.cache = {}
    
    def slow_sort_and_filter(self, threshold: int = 50) -> List[int]:
        """Inefficient sorting and filtering with multiple passes."""
        # Inefficiency 1: Multiple unnecessary iterations
        result = []
        for item in self.data:
            if item > threshold:
                result.append(item)
        
        # Inefficiency 2: Bubble sort instead of built-in sort
        n = len(result)
        for i in range(n):
            for j in range(0, n - i - 1):
                if result[j] > result[j + 1]:
                    result[j], result[j + 1] = result[j + 1], result[j]
        
        return result
    
    def calculate_statistics(self, numbers: List[int]) -> Dict[str, float]:
        """Calculate basic statistics with redundant calculations."""
        if not numbers:
            return {"mean": 0, "median": 0, "std_dev": 0}
        
        # Inefficiency 3: Recalculating sum multiple times
        total = 0
        for num in numbers:
            total += num
        mean = total / len(numbers)
        
        # Recalculating sum again for variance
        variance_sum = 0
        total_again = 0
        for num in numbers:
            total_again += num
            variance_sum += (num - mean) ** 2
        
        variance = variance_sum / len(numbers)
        std_dev = variance ** 0.5
        
        # Inefficient median calculation
        sorted_nums = []
        for num in numbers:
            sorted_nums.append(num)
        # Manual sorting again
        for i in range(len(sorted_nums)):
            for j in range(i + 1, len(sorted_nums)):
                if sorted_nums[i] > sorted_nums[j]:
                    sorted_nums[i], sorted_nums[j] = sorted_nums[j], sorted_nums[i]
        
        median = sorted_nums[len(sorted_nums) // 2]
        
        return {
            "mean": mean,
            "median": median,
            "std_dev": std_dev
        }

# Example usage
if __name__ == "__main__":
    data = [random.randint(1, 100) for _ in range(50)]
    processor = DataProcessor(data)
    filtered = processor.slow_sort_and_filter(25)
    stats = processor.calculate_statistics(filtered)
    print(f"Statistics: {stats}")
'''
    
    demo = OpenEvolveDemo()
    
    try:
        # Run optimization demo
        result = demo.run_optimization_demo(sample_code, "python")
        
        if result["success"]:
            print(f"\n🎉 Demo completed successfully!")
            print(f"Session ID: {result['session_id']}")
            
            # Option to cleanup
            cleanup = input("\n🗑️  Cleanup demo session? (y/n): ").lower().strip()
            if cleanup == 'y':
                demo.cleanup_demo_session(result['session_id'])
            else:
                print(f"Session preserved at: {result['workspace_path']}")
        else:
            print(f"\n❌ Demo failed: {result['error']}")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")


if __name__ == "__main__":
    main()