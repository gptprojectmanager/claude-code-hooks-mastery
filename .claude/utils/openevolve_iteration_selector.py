#!/usr/bin/env python3
"""
OpenEvolve Iteration Selection Algorithm
Intelligent selection of evolution iterations based on code complexity,
optimization potential, and credit budget optimization.
"""

import ast
import re
import math
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib


@dataclass
class CodeComplexity:
    """Code complexity metrics."""
    line_count: int
    function_count: int
    class_count: int
    cyclomatic_complexity: int
    nesting_depth: int
    loop_count: int
    nested_loop_count: int
    import_count: int
    
    def complexity_score(self) -> float:
        """Calculate overall complexity score (0-100)."""
        # Weighted scoring based on different complexity factors
        weights = {
            'lines': min(self.line_count / 500, 1.0) * 20,  # Max 20 points for lines
            'functions': min(self.function_count / 20, 1.0) * 10,  # Max 10 points 
            'cyclomatic': min(self.cyclomatic_complexity / 50, 1.0) * 25,  # Max 25 points
            'nesting': min(self.nesting_depth / 6, 1.0) * 15,  # Max 15 points
            'loops': min(self.nested_loop_count / 5, 1.0) * 20,  # Max 20 points
            'imports': min(self.import_count / 30, 1.0) * 10  # Max 10 points
        }
        return sum(weights.values())


@dataclass 
class OptimizationPotential:
    """Optimization potential assessment."""
    algorithmic_issues: List[str]
    performance_bottlenecks: List[str] 
    inefficiency_patterns: List[str]
    optimization_opportunities: List[str]
    estimated_improvement_potential: float  # 0-100%
    
    def potential_score(self) -> float:
        """Calculate optimization potential score (0-100)."""
        issue_score = len(self.algorithmic_issues) * 15
        bottleneck_score = len(self.performance_bottlenecks) * 20
        pattern_score = len(self.inefficiency_patterns) * 10
        opportunity_score = len(self.optimization_opportunities) * 10
        
        total_score = issue_score + bottleneck_score + pattern_score + opportunity_score
        return min(total_score, 100)


@dataclass
class IterationRecommendation:
    """Iteration recommendation with rationale."""
    recommended_iterations: int
    complexity_level: str  # simple, medium, complex, extreme
    estimated_credits: int
    estimated_duration_minutes: int
    confidence_score: float  # 0-1
    rationale: List[str]
    optimization_strategy: str
    fallback_iterations: int


class PythonCodeAnalyzer:
    """Advanced Python code analysis for optimization potential."""
    
    def __init__(self):
        self.inefficient_patterns = {
            # Algorithmic inefficiencies
            'nested_loops': r'for\s+\w+.*:\s*\n\s*for\s+\w+.*:',
            'redundant_iterations': r'for\s+\w+\s+in\s+.*:\s*\n.*for\s+\w+\s+in\s+.*:',
            'list_comprehension_opportunity': r'for\s+\w+\s+in\s+.*:\s*\n\s*\w+\.append',
            
            # Data structure inefficiencies  
            'dict_key_existence': r'if\s+\w+\s+in\s+\w+\.keys\(\)',
            'inefficient_string_concat': r'\+\=.*[\'"]',
            'repeated_list_operations': r'\.append\(.*\).*\.sort\(\)',
            
            # Function call inefficiencies
            'repeated_function_calls': r'(\w+\([^)]*\)).*\1',
            'unnecessary_lambda': r'lambda\s+\w+:\s+\w+\.\w+\(\w+\)',
            'map_filter_opportunity': r'for\s+\w+\s+in\s+.*if\s+',
        }
        
        self.optimization_opportunities = {
            'builtin_functions': ['sorted', 'max', 'min', 'sum', 'any', 'all'],
            'data_structures': ['set', 'deque', 'defaultdict', 'Counter'],
            'algorithms': ['bisect', 'heapq', 'itertools'],
            'caching': ['lru_cache', 'cache', 'cached_property']
        }
    
    def analyze_complexity(self, code: str) -> CodeComplexity:
        """Analyze code complexity metrics."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fallback to simple text analysis if AST parsing fails
            return self._fallback_complexity_analysis(code)
        
        line_count = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')])
        function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        class_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        import_count = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
        
        # Calculate cyclomatic complexity
        cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)
        
        # Calculate nesting depth
        nesting_depth = self._calculate_nesting_depth(tree)
        
        # Count loops
        loop_count = len([node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))])
        nested_loop_count = self._count_nested_loops(tree)
        
        return CodeComplexity(
            line_count=line_count,
            function_count=function_count,
            class_count=class_count,
            cyclomatic_complexity=cyclomatic_complexity,
            nesting_depth=nesting_depth,
            loop_count=loop_count,
            nested_loop_count=nested_loop_count,
            import_count=import_count
        )
    
    def _fallback_complexity_analysis(self, code: str) -> CodeComplexity:
        """Fallback complexity analysis using text patterns."""
        lines = [line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        return CodeComplexity(
            line_count=len(lines),
            function_count=len(re.findall(r'def\s+\w+', code)),
            class_count=len(re.findall(r'class\s+\w+', code)),
            cyclomatic_complexity=len(re.findall(r'\b(if|elif|while|for|and|or|except)\b', code)),
            nesting_depth=max([line.count('    ') for line in lines] or [0]),
            loop_count=len(re.findall(r'\b(for|while)\b', code)),
            nested_loop_count=len(re.findall(r'for\s+\w+.*:\s*\n\s*for\s+\w+.*:', code, re.MULTILINE)),
            import_count=len(re.findall(r'^(import|from)\s+', code, re.MULTILINE))
        )
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ExceptHandler,)):
                complexity += 1
        
        return complexity
    
    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        
        def calculate_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
                current_depth += 1
            
            for child in ast.iter_child_nodes(node):
                calculate_depth(child, current_depth)
        
        calculate_depth(tree)
        return max_depth
    
    def _count_nested_loops(self, tree: ast.AST) -> int:
        """Count nested loop structures."""
        nested_count = 0
        
        def find_nested_loops(node, in_loop=False):
            nonlocal nested_count
            
            if isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                if in_loop:
                    nested_count += 1
                in_loop = True
            
            for child in ast.iter_child_nodes(node):
                find_nested_loops(child, in_loop)
        
        find_nested_loops(tree)
        return nested_count
    
    def analyze_optimization_potential(self, code: str) -> OptimizationPotential:
        """Analyze code for optimization opportunities."""
        algorithmic_issues = []
        performance_bottlenecks = []
        inefficiency_patterns = []
        optimization_opportunities = []
        
        # Detect inefficient patterns
        for pattern_name, pattern in self.inefficient_patterns.items():
            if re.search(pattern, code, re.MULTILINE):
                inefficiency_patterns.append(pattern_name)
                
                if pattern_name in ['nested_loops', 'redundant_iterations']:
                    algorithmic_issues.append(f"Detected {pattern_name.replace('_', ' ')}")
                else:
                    performance_bottlenecks.append(f"Detected {pattern_name.replace('_', ' ')}")
        
        # Detect optimization opportunities
        for category, functions in self.optimization_opportunities.items():
            for func in functions:
                if func not in code:
                    optimization_opportunities.append(f"Consider using {func} ({category})")
        
        # Estimate improvement potential based on issues found
        potential_multiplier = {
            'nested_loops': 40,
            'redundant_iterations': 35,
            'list_comprehension_opportunity': 20,
            'inefficient_string_concat': 25,
            'repeated_function_calls': 30
        }
        
        improvement_potential = sum(
            potential_multiplier.get(pattern, 10) 
            for pattern in inefficiency_patterns
        )
        improvement_potential = min(improvement_potential, 90)  # Cap at 90%
        
        return OptimizationPotential(
            algorithmic_issues=algorithmic_issues,
            performance_bottlenecks=performance_bottlenecks,
            inefficiency_patterns=inefficiency_patterns,
            optimization_opportunities=optimization_opportunities[:10],  # Limit to top 10
            estimated_improvement_potential=improvement_potential
        )


class IterationSelector:
    """Intelligent iteration selection for OpenEvolve optimization."""
    
    def __init__(self):
        self.python_analyzer = PythonCodeAnalyzer()
        self.credit_cost_per_iteration = 2  # Estimated credits per iteration
        
        # Base iteration ranges by complexity
        self.base_iterations = {
            'simple': (5, 15),
            'medium': (15, 30),
            'complex': (30, 50),
            'extreme': (50, 80)
        }
    
    def select_iterations(
        self, 
        code: str, 
        language: str = "python", 
        budget_credits: int = 1000,
        time_limit_minutes: int = 30,
        optimization_goals: List[str] = None
    ) -> IterationRecommendation:
        """
        Select optimal number of iterations for code optimization.
        
        Args:
            code: Source code to optimize
            language: Programming language  
            budget_credits: Available credit budget
            time_limit_minutes: Maximum time allowed
            optimization_goals: Specific optimization goals
        
        Returns:
            IterationRecommendation with detailed rationale
        """
        if language.lower() == "python":
            return self._select_python_iterations(code, budget_credits, time_limit_minutes, optimization_goals)
        else:
            return self._select_generic_iterations(code, language, budget_credits, time_limit_minutes)
    
    def _select_python_iterations(
        self, 
        code: str, 
        budget_credits: int, 
        time_limit_minutes: int,
        optimization_goals: List[str]
    ) -> IterationRecommendation:
        """Select iterations specifically for Python code."""
        
        # Analyze code complexity and potential
        complexity = self.python_analyzer.analyze_complexity(code)
        potential = self.python_analyzer.analyze_optimization_potential(code)
        
        # Determine complexity level
        complexity_score = complexity.complexity_score()
        if complexity_score < 20:
            complexity_level = "simple"
        elif complexity_score < 50:
            complexity_level = "medium"
        elif complexity_score < 80:
            complexity_level = "complex"
        else:
            complexity_level = "extreme"
        
        # Base iterations from complexity
        min_iterations, max_iterations = self.base_iterations[complexity_level]
        
        # Adjust based on optimization potential
        potential_score = potential.potential_score()
        potential_multiplier = 1.0 + (potential_score / 100) * 0.8  # Up to 80% increase
        
        adjusted_iterations = int(min_iterations * potential_multiplier)
        
        # Adjust for specific optimization goals
        goal_adjustments = {
            'performance': 1.3,
            'algorithmic_efficiency': 1.5,
            'memory_optimization': 1.2,
            'code_quality': 1.1
        }
        
        if optimization_goals:
            for goal in optimization_goals:
                if goal in goal_adjustments:
                    adjusted_iterations = int(adjusted_iterations * goal_adjustments[goal])
        
        # Apply constraints
        max_affordable = budget_credits // self.credit_cost_per_iteration
        max_time_iterations = int(time_limit_minutes * 1.5)  # ~1.5 iterations per minute
        
        final_iterations = min(adjusted_iterations, max_affordable, max_time_iterations, max_iterations)
        fallback_iterations = min(min_iterations, max_affordable // 2)  # Conservative fallback
        
        # Calculate estimates
        estimated_credits = final_iterations * self.credit_cost_per_iteration
        estimated_duration = int(final_iterations / 1.5)
        
        # Build rationale
        rationale = []
        rationale.append(f"Code complexity level: {complexity_level} (score: {complexity_score:.1f})")
        rationale.append(f"Optimization potential: {potential_score:.1f}% (found {len(potential.inefficiency_patterns)} patterns)")
        rationale.append(f"Base iterations: {min_iterations}-{max_iterations}, adjusted to {adjusted_iterations}")
        
        if final_iterations < adjusted_iterations:
            constraints = []
            if final_iterations == max_affordable:
                constraints.append(f"credit budget ({budget_credits})")
            if final_iterations == max_time_iterations:
                constraints.append(f"time limit ({time_limit_minutes} min)")
            rationale.append(f"Constrained by: {', '.join(constraints)}")
        
        # Determine optimization strategy
        if potential_score > 60:
            optimization_strategy = "aggressive"
        elif potential_score > 30:
            optimization_strategy = "balanced"
        else:
            optimization_strategy = "conservative"
        
        # Calculate confidence based on analysis quality
        confidence = 0.8  # Base confidence
        if complexity.line_count > 20:  # More code = better analysis
            confidence += 0.1
        if len(potential.inefficiency_patterns) > 0:  # Found patterns = higher confidence
            confidence += 0.1
        confidence = min(confidence, 1.0)
        
        return IterationRecommendation(
            recommended_iterations=final_iterations,
            complexity_level=complexity_level,
            estimated_credits=estimated_credits,
            estimated_duration_minutes=estimated_duration,
            confidence_score=confidence,
            rationale=rationale,
            optimization_strategy=optimization_strategy,
            fallback_iterations=fallback_iterations
        )
    
    def _select_generic_iterations(
        self, 
        code: str, 
        language: str, 
        budget_credits: int, 
        time_limit_minutes: int
    ) -> IterationRecommendation:
        """Generic iteration selection for non-Python languages."""
        
        # Simple heuristics for other languages
        lines = [line for line in code.split('\n') if line.strip()]
        line_count = len(lines)
        
        # Rough complexity estimation
        if line_count < 50:
            complexity_level = "simple"
            base_iterations = 8
        elif line_count < 150:
            complexity_level = "medium"  
            base_iterations = 18
        elif line_count < 300:
            complexity_level = "complex"
            base_iterations = 35
        else:
            complexity_level = "extreme"
            base_iterations = 55
        
        # Language-specific adjustments
        language_multipliers = {
            'javascript': 1.2,  # More optimization opportunities
            'typescript': 1.1,
            'java': 0.9,       # More constrained optimization space
            'c++': 0.8,        # Lower-level optimization
            'rust': 0.7,       # Already highly optimized
            'go': 0.9
        }
        
        multiplier = language_multipliers.get(language.lower(), 1.0)
        adjusted_iterations = int(base_iterations * multiplier)
        
        # Apply constraints
        max_affordable = budget_credits // self.credit_cost_per_iteration
        max_time_iterations = int(time_limit_minutes * 1.2)  # Slightly slower for other languages
        
        final_iterations = min(adjusted_iterations, max_affordable, max_time_iterations)
        fallback_iterations = max(5, final_iterations // 2)
        
        estimated_credits = final_iterations * self.credit_cost_per_iteration
        estimated_duration = int(final_iterations / 1.2)
        
        rationale = [
            f"Language: {language} (multiplier: {multiplier})",
            f"Line count: {line_count} -> complexity: {complexity_level}",
            f"Base iterations: {base_iterations}, adjusted: {adjusted_iterations}",
            f"Final iterations: {final_iterations} (constraints applied)"
        ]
        
        return IterationRecommendation(
            recommended_iterations=final_iterations,
            complexity_level=complexity_level,
            estimated_credits=estimated_credits,
            estimated_duration_minutes=estimated_duration,
            confidence_score=0.6,  # Lower confidence for generic analysis
            rationale=rationale,
            optimization_strategy="balanced",
            fallback_iterations=fallback_iterations
        )
    
    def evaluate_plateau_early_stopping(
        self, 
        iteration_scores: List[float], 
        window_size: int = 5,
        improvement_threshold: float = 0.02
    ) -> bool:
        """
        Evaluate if optimization has plateaued and should stop early.
        
        Args:
            iteration_scores: Scores from recent iterations
            window_size: Number of recent iterations to consider
            improvement_threshold: Minimum improvement rate to continue
            
        Returns:
            True if should stop early, False to continue
        """
        if len(iteration_scores) < window_size * 2:
            return False  # Not enough data yet
        
        # Compare recent window to previous window
        recent_scores = iteration_scores[-window_size:]
        previous_scores = iteration_scores[-window_size*2:-window_size]
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        previous_avg = sum(previous_scores) / len(previous_scores)
        
        improvement_rate = (recent_avg - previous_avg) / previous_avg if previous_avg > 0 else 0
        
        return improvement_rate < improvement_threshold


def main():
    """Command-line interface for iteration selector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenEvolve Iteration Selector")
    parser.add_argument("code_file", help="Code file to analyze")
    parser.add_argument("--language", default="python", help="Programming language")
    parser.add_argument("--budget", type=int, default=1000, help="Credit budget")
    parser.add_argument("--time-limit", type=int, default=30, help="Time limit in minutes")
    parser.add_argument("--goals", nargs="*", help="Optimization goals")
    parser.add_argument("--output", help="Output file for detailed analysis")
    
    args = parser.parse_args()
    
    # Read code file
    with open(args.code_file, 'r') as f:
        code = f.read()
    
    # Select iterations
    selector = IterationSelector()
    recommendation = selector.select_iterations(
        code=code,
        language=args.language,
        budget_credits=args.budget,
        time_limit_minutes=args.time_limit,
        optimization_goals=args.goals or []
    )
    
    # Display results
    print("🧬 OpenEvolve Iteration Recommendation")
    print("=" * 50)
    print(f"Recommended Iterations: {recommendation.recommended_iterations}")
    print(f"Complexity Level: {recommendation.complexity_level}")
    print(f"Estimated Credits: {recommendation.estimated_credits}")
    print(f"Estimated Duration: {recommendation.estimated_duration_minutes} minutes")
    print(f"Optimization Strategy: {recommendation.optimization_strategy}")
    print(f"Confidence Score: {recommendation.confidence_score:.2f}")
    print(f"Fallback Iterations: {recommendation.fallback_iterations}")
    
    print(f"\n📋 Rationale:")
    for reason in recommendation.rationale:
        print(f"  • {reason}")
    
    # Save detailed analysis if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(asdict(recommendation), f, indent=2)
        print(f"\n💾 Detailed analysis saved to: {args.output}")


if __name__ == "__main__":
    main()