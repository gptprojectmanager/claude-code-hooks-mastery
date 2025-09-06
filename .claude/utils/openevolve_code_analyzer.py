#!/usr/bin/env python3
"""
OpenEvolve Advanced Code Analysis Engine
Comprehensive static analysis for optimization potential assessment,
performance bottleneck detection, and optimization recommendation generation.
"""

import ast
import re
import json
import time
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict, Counter
import hashlib


@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck."""
    type: str  # algorithmic, data_structure, io, memory, etc.
    location: str  # line number or function name
    severity: str  # low, medium, high, critical
    description: str
    impact_estimate: float  # 0-100% performance impact
    suggested_fix: str
    confidence: float  # 0-1


@dataclass  
class OptimizationOpportunity:
    """Specific optimization opportunity."""
    category: str  # algorithm, data_structure, builtin, pattern, etc.
    current_pattern: str
    suggested_improvement: str
    estimated_improvement: float  # 0-100% performance gain
    complexity_reduction: str  # e.g., "O(n²) → O(n log n)"
    implementation_difficulty: str  # easy, medium, hard
    code_example: Optional[str] = None


@dataclass
class CodeQualityMetrics:
    """Code quality and maintainability metrics."""
    maintainability_index: float  # 0-100
    readability_score: float  # 0-100
    code_duplication: float  # 0-100% duplication
    technical_debt_hours: float
    cognitive_complexity: int
    documentation_coverage: float  # 0-100%


@dataclass
class AnalysisReport:
    """Comprehensive code analysis report."""
    file_path: str
    language: str
    analysis_timestamp: str
    
    # Basic metrics
    lines_of_code: int
    complexity_score: float
    
    # Performance analysis
    bottlenecks: List[PerformanceBottleneck] = field(default_factory=list)
    optimization_opportunities: List[OptimizationOpportunity] = field(default_factory=list)
    
    # Quality metrics
    quality_metrics: Optional[CodeQualityMetrics] = None
    
    # Recommendations
    priority_improvements: List[str] = field(default_factory=list)
    quick_wins: List[str] = field(default_factory=list)
    long_term_optimizations: List[str] = field(default_factory=list)
    
    # Scoring
    optimization_potential_score: float = 0.0  # 0-100
    overall_confidence: float = 0.0  # 0-1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            "file": self.file_path,
            "language": self.language,
            "lines_of_code": self.lines_of_code,
            "complexity_score": self.complexity_score,
            "bottlenecks_found": len(self.bottlenecks),
            "optimization_opportunities": len(self.optimization_opportunities),
            "optimization_potential": self.optimization_potential_score,
            "confidence": self.overall_confidence,
            "top_priority": self.priority_improvements[:3] if self.priority_improvements else []
        }


class PythonCodeAnalyzer:
    """Advanced Python code analyzer with deep optimization insights."""
    
    def __init__(self):
        self.performance_patterns = self._initialize_performance_patterns()
        self.optimization_patterns = self._initialize_optimization_patterns()
        self.builtin_alternatives = self._initialize_builtin_alternatives()
    
    def _initialize_performance_patterns(self) -> Dict[str, Dict]:
        """Initialize performance bottleneck patterns."""
        return {
            # Algorithmic inefficiencies
            'nested_loops_same_data': {
                'pattern': r'for\s+(\w+)\s+in\s+(\w+).*:\s*\n.*for\s+\w+\s+in\s+\2',
                'severity': 'high',
                'impact': 70,
                'type': 'algorithmic',
                'description': 'Nested loops over the same data structure'
            },
            'quadratic_string_concat': {
                'pattern': r'(\w+)\s*\+=\s*["\'].*["\']',
                'severity': 'medium', 
                'impact': 40,
                'type': 'algorithmic',
                'description': 'Quadratic string concatenation in loop'
            },
            'repeated_expensive_calls': {
                'pattern': r'(len\(\w+\)|\.count\(.*\)|\.index\(.*\)).*\n.*\1',
                'severity': 'medium',
                'impact': 25,
                'type': 'function_calls',
                'description': 'Repeated expensive function calls'
            },
            'dict_key_iteration': {
                'pattern': r'for\s+\w+\s+in\s+\w+\.keys\(\)',
                'severity': 'low',
                'impact': 10,
                'type': 'data_structure',
                'description': 'Unnecessary .keys() in dictionary iteration'
            },
            'list_extension_in_loop': {
                'pattern': r'for\s+\w+.*:\s*\n.*\.append\(',
                'severity': 'medium',
                'impact': 35,
                'type': 'data_structure', 
                'description': 'List extension in loop instead of list comprehension'
            }
        }
    
    def _initialize_optimization_patterns(self) -> Dict[str, Dict]:
        """Initialize optimization opportunity patterns."""
        return {
            'list_comprehension': {
                'pattern': r'(\w+)\s*=\s*\[\]\s*\n.*for\s+(\w+)\s+in\s+.*:\s*\n.*\1\.append\(\2.*\)',
                'category': 'builtin',
                'improvement': 'Use list comprehension for better performance',
                'estimated_gain': 25,
                'difficulty': 'easy'
            },
            'generator_expression': {
                'pattern': r'sum\(\[.*for.*in.*\]\)',
                'category': 'builtin', 
                'improvement': 'Use generator expression with sum()',
                'estimated_gain': 15,
                'difficulty': 'easy'
            },
            'set_membership': {
                'pattern': r'(\w+)\s+in\s+\[.*\]',
                'category': 'data_structure',
                'improvement': 'Use set for O(1) membership testing',
                'estimated_gain': 60,
                'difficulty': 'easy'
            },
            'dict_get_default': {
                'pattern': r'if\s+(\w+)\s+in\s+(\w+):\s*\n.*\2\[\1\]',
                'category': 'pattern',
                'improvement': 'Use dict.get() with default value',
                'estimated_gain': 10,
                'difficulty': 'easy'
            },
            'enumerate_instead_range': {
                'pattern': r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):.*\n.*\2\[\1\]',
                'category': 'builtin',
                'improvement': 'Use enumerate() instead of range(len())',
                'estimated_gain': 15,
                'difficulty': 'easy'
            }
        }
    
    def _initialize_builtin_alternatives(self) -> Dict[str, Dict]:
        """Initialize built-in function alternatives."""
        return {
            'manual_min_max': {
                'pattern': r'(\w+)\s*=\s*\w+\[0\]\s*\n.*for\s+\w+\s+in\s+\w+.*:\s*\n.*if.*<.*:.*\n.*\1\s*=',
                'alternative': 'min() or max() built-in functions',
                'improvement': 40
            },
            'manual_sum': {
                'pattern': r'(\w+)\s*=\s*0\s*\n.*for\s+\w+\s+in.*:\s*\n.*\1\s*\+=',
                'alternative': 'sum() built-in function',
                'improvement': 30
            },
            'manual_any_all': {
                'pattern': r'(\w+)\s*=\s*(True|False)\s*\n.*for\s+\w+\s+in.*:\s*\n.*if.*:\s*\n.*\1\s*=',
                'alternative': 'any() or all() built-in functions',
                'improvement': 25
            }
        }
    
    def analyze_code(self, code: str, file_path: str = "unknown") -> AnalysisReport:
        """Perform comprehensive code analysis."""
        
        report = AnalysisReport(
            file_path=file_path,
            language="python",
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            lines_of_code=len([line for line in code.split('\n') if line.strip()]),
            complexity_score=0.0
        )
        
        try:
            # Parse AST for deep analysis
            tree = ast.parse(code)
            
            # Analyze performance bottlenecks
            report.bottlenecks = self._analyze_bottlenecks(code, tree)
            
            # Find optimization opportunities
            report.optimization_opportunities = self._find_optimization_opportunities(code, tree)
            
            # Calculate quality metrics
            report.quality_metrics = self._calculate_quality_metrics(code, tree)
            
            # Generate recommendations
            report.priority_improvements, report.quick_wins, report.long_term_optimizations = \
                self._generate_recommendations(report.bottlenecks, report.optimization_opportunities)
            
            # Calculate overall scores
            report.complexity_score = self._calculate_complexity_score(tree)
            report.optimization_potential_score = self._calculate_optimization_potential(
                report.bottlenecks, report.optimization_opportunities
            )
            report.overall_confidence = self._calculate_confidence(code, tree)
            
        except SyntaxError as e:
            # Fallback to text-based analysis for syntax errors
            report.bottlenecks = self._analyze_bottlenecks_text(code)
            report.optimization_opportunities = self._find_opportunities_text(code)
            report.complexity_score = 50.0  # Default for unparseable code
            report.optimization_potential_score = 30.0
            report.overall_confidence = 0.3
        
        return report
    
    def _analyze_bottlenecks(self, code: str, tree: ast.AST) -> List[PerformanceBottleneck]:
        """Analyze code for performance bottlenecks."""
        bottlenecks = []
        
        # Pattern-based detection
        for pattern_name, pattern_info in self.performance_patterns.items():
            matches = re.finditer(pattern_info['pattern'], code, re.MULTILINE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                
                bottleneck = PerformanceBottleneck(
                    type=pattern_info['type'],
                    location=f"line {line_num}",
                    severity=pattern_info['severity'],
                    description=pattern_info['description'],
                    impact_estimate=pattern_info['impact'],
                    suggested_fix=self._get_fix_suggestion(pattern_name),
                    confidence=0.8
                )
                bottlenecks.append(bottleneck)
        
        # AST-based analysis for more complex patterns
        bottlenecks.extend(self._analyze_ast_bottlenecks(tree))
        
        return sorted(bottlenecks, key=lambda x: x.impact_estimate, reverse=True)
    
    def _analyze_bottlenecks_text(self, code: str) -> List[PerformanceBottleneck]:
        """Fallback text-based bottleneck analysis."""
        bottlenecks = []
        
        # Simple pattern matching fallback
        if re.search(r'for.*for.*:', code):
            bottlenecks.append(PerformanceBottleneck(
                type="algorithmic",
                location="multiple locations", 
                severity="high",
                description="Nested loops detected",
                impact_estimate=50.0,
                suggested_fix="Consider algorithmic optimization",
                confidence=0.5
            ))
        
        return bottlenecks
    
    def _analyze_ast_bottlenecks(self, tree: ast.AST) -> List[PerformanceBottleneck]:
        """Analyze AST for complex bottleneck patterns."""
        bottlenecks = []
        
        # Find nested loops with same iteration variable
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check for nested loops within this loop
                nested_loops = [n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While)) and n != node]
                if nested_loops:
                    bottlenecks.append(PerformanceBottleneck(
                        type="algorithmic",
                        location=f"line {node.lineno}",
                        severity="high",
                        description="Nested loop structure detected",
                        impact_estimate=65.0,
                        suggested_fix="Consider using more efficient algorithms or data structures",
                        confidence=0.9
                    ))
        
        return bottlenecks
    
    def _find_optimization_opportunities(self, code: str, tree: ast.AST) -> List[OptimizationOpportunity]:
        """Find specific optimization opportunities."""
        opportunities = []
        
        # Pattern-based opportunities
        for pattern_name, pattern_info in self.optimization_patterns.items():
            matches = re.finditer(pattern_info['pattern'], code, re.MULTILINE)
            for match in matches:
                opportunity = OptimizationOpportunity(
                    category=pattern_info['category'],
                    current_pattern=match.group(0).strip(),
                    suggested_improvement=pattern_info['improvement'],
                    estimated_improvement=pattern_info['estimated_gain'],
                    complexity_reduction=self._get_complexity_reduction(pattern_name),
                    implementation_difficulty=pattern_info['difficulty'],
                    code_example=self._get_code_example(pattern_name, match.group(0))
                )
                opportunities.append(opportunity)
        
        # AST-based opportunities
        opportunities.extend(self._find_ast_opportunities(tree))
        
        return sorted(opportunities, key=lambda x: x.estimated_improvement, reverse=True)
    
    def _find_opportunities_text(self, code: str) -> List[OptimizationOpportunity]:
        """Fallback text-based opportunity finding."""
        opportunities = []
        
        if re.search(r'\.append\(.*\)', code):
            opportunities.append(OptimizationOpportunity(
                category="builtin",
                current_pattern="Manual list building with append",
                suggested_improvement="Consider list comprehensions",
                estimated_improvement=20.0,
                complexity_reduction="Same complexity, better performance",
                implementation_difficulty="easy"
            ))
        
        return opportunities
    
    def _find_ast_opportunities(self, tree: ast.AST) -> List[OptimizationOpportunity]:
        """Find opportunities using AST analysis."""
        opportunities = []
        
        # Find manual implementations of built-in functions
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Look for manual min/max implementations
                if self._is_manual_min_max(node):
                    opportunities.append(OptimizationOpportunity(
                        category="builtin",
                        current_pattern="Manual min/max implementation",
                        suggested_improvement="Use built-in min() or max() functions",
                        estimated_improvement=40.0,
                        complexity_reduction="O(n) → O(n) with better constants",
                        implementation_difficulty="easy",
                        code_example="min(collection) instead of manual loop"
                    ))
        
        return opportunities
    
    def _calculate_quality_metrics(self, code: str, tree: ast.AST) -> CodeQualityMetrics:
        """Calculate code quality and maintainability metrics."""
        lines = [line for line in code.split('\n') if line.strip()]
        
        # Basic quality metrics
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        documentation_coverage = (comment_lines / len(lines)) * 100 if lines else 0
        
        # Complexity metrics
        cognitive_complexity = self._calculate_cognitive_complexity(tree)
        
        # Simple heuristics for other metrics
        maintainability_index = max(0, 100 - cognitive_complexity * 2)
        readability_score = min(100, documentation_coverage + (50 if len(lines) < 100 else 30))
        
        # Duplication detection (simplified)
        line_counts = Counter([line.strip() for line in lines if len(line.strip()) > 5])
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        code_duplication = (duplicate_lines / len(lines)) * 100 if lines else 0
        
        # Technical debt estimation (simplified)
        technical_debt_hours = cognitive_complexity * 0.5 + code_duplication * 0.1
        
        return CodeQualityMetrics(
            maintainability_index=maintainability_index,
            readability_score=readability_score,
            code_duplication=code_duplication,
            technical_debt_hours=technical_debt_hours,
            cognitive_complexity=cognitive_complexity,
            documentation_coverage=documentation_coverage
        )
    
    def _generate_recommendations(
        self, 
        bottlenecks: List[PerformanceBottleneck],
        opportunities: List[OptimizationOpportunity]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Generate prioritized recommendations."""
        
        priority_improvements = []
        quick_wins = []
        long_term_optimizations = []
        
        # High-impact bottlenecks become priority improvements
        for bottleneck in bottlenecks:
            if bottleneck.severity == "critical" or bottleneck.impact_estimate > 50:
                priority_improvements.append(f"{bottleneck.description} at {bottleneck.location}")
        
        # Easy, medium-impact opportunities become quick wins
        for opp in opportunities:
            if opp.implementation_difficulty == "easy" and opp.estimated_improvement > 15:
                quick_wins.append(f"{opp.suggested_improvement} (est. {opp.estimated_improvement}% gain)")
        
        # Hard, high-impact opportunities become long-term optimizations
        for opp in opportunities:
            if opp.implementation_difficulty == "hard" and opp.estimated_improvement > 30:
                long_term_optimizations.append(f"{opp.suggested_improvement} - {opp.complexity_reduction}")
        
        return priority_improvements[:5], quick_wins[:5], long_term_optimizations[:3]
    
    def _calculate_complexity_score(self, tree: ast.AST) -> float:
        """Calculate overall complexity score."""
        # Simplified complexity calculation
        node_count = len(list(ast.walk(tree)))
        function_count = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        class_count = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        
        complexity = (node_count * 0.1) + (function_count * 5) + (class_count * 10)
        return min(complexity, 100)
    
    def _calculate_optimization_potential(
        self, 
        bottlenecks: List[PerformanceBottleneck],
        opportunities: List[OptimizationOpportunity]
    ) -> float:
        """Calculate overall optimization potential score."""
        bottleneck_potential = sum(b.impact_estimate * b.confidence for b in bottlenecks)
        opportunity_potential = sum(o.estimated_improvement for o in opportunities)
        
        total_potential = (bottleneck_potential + opportunity_potential) * 0.6
        return min(total_potential, 100)
    
    def _calculate_confidence(self, code: str, tree: ast.AST) -> float:
        """Calculate analysis confidence."""
        confidence = 0.7  # Base confidence
        
        # Higher confidence for larger code samples
        lines = len([line for line in code.split('\n') if line.strip()])
        if lines > 50:
            confidence += 0.1
        if lines > 100:
            confidence += 0.1
        
        # Higher confidence if we found specific patterns
        if len(list(ast.walk(tree))) > 20:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    # Helper methods
    def _get_fix_suggestion(self, pattern_name: str) -> str:
        """Get fix suggestion for a pattern."""
        suggestions = {
            'nested_loops_same_data': 'Consider using set operations or more efficient algorithms',
            'quadratic_string_concat': 'Use str.join() or f-strings instead',
            'repeated_expensive_calls': 'Cache the result in a variable',
            'dict_key_iteration': 'Iterate directly over dictionary',
            'list_extension_in_loop': 'Use list comprehension or generator expression'
        }
        return suggestions.get(pattern_name, 'Consider refactoring for better performance')
    
    def _get_complexity_reduction(self, pattern_name: str) -> str:
        """Get complexity reduction info for a pattern."""
        reductions = {
            'list_comprehension': 'Same O(n) with better constants',
            'set_membership': 'O(n) → O(1) per lookup',
            'generator_expression': 'Reduced memory usage',
            'enumerate_instead_range': 'Cleaner code, slightly better performance'
        }
        return reductions.get(pattern_name, 'Improved performance characteristics')
    
    def _get_code_example(self, pattern_name: str, original: str) -> Optional[str]:
        """Get code example for improvement."""
        examples = {
            'list_comprehension': 'result = [func(x) for x in items if condition(x)]',
            'generator_expression': 'total = sum(x**2 for x in numbers)',
            'set_membership': 'valid_items = set(valid_list)\nif item in valid_items: ...',
        }
        return examples.get(pattern_name)
    
    def _is_manual_min_max(self, node: ast.For) -> bool:
        """Check if a loop implements manual min/max."""
        # Simplified detection - would need more sophisticated analysis
        return False
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity (simplified)."""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        return complexity


class CodeAnalysisEngine:
    """Main code analysis engine supporting multiple languages."""
    
    def __init__(self):
        self.python_analyzer = PythonCodeAnalyzer()
        self.supported_languages = ['python', 'javascript', 'typescript']
    
    def analyze_file(self, file_path: str, language: str = None) -> AnalysisReport:
        """Analyze a code file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect language if not provided
        if not language:
            language = self._detect_language(path)
        
        # Read file content
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
        except UnicodeDecodeError:
            with open(path, 'r', encoding='latin-1') as f:
                code = f.read()
        
        # Dispatch to appropriate analyzer
        if language.lower() == 'python':
            return self.python_analyzer.analyze_code(code, str(path))
        else:
            return self._analyze_generic(code, str(path), language)
    
    def analyze_code_string(self, code: str, language: str) -> AnalysisReport:
        """Analyze code from string."""
        if language.lower() == 'python':
            return self.python_analyzer.analyze_code(code)
        else:
            return self._analyze_generic(code, "string_input", language)
    
    def _detect_language(self, file_path: Path) -> str:
        """Auto-detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript'
        }
        return extension_map.get(file_path.suffix.lower(), 'unknown')
    
    def _analyze_generic(self, code: str, file_path: str, language: str) -> AnalysisReport:
        """Generic analysis for non-Python languages."""
        return AnalysisReport(
            file_path=file_path,
            language=language,
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            lines_of_code=len([line for line in code.split('\n') if line.strip()]),
            complexity_score=50.0,  # Default complexity
            optimization_potential_score=30.0,  # Conservative estimate
            overall_confidence=0.4  # Lower confidence for generic analysis
        )
    
    def generate_report(self, analysis: AnalysisReport, output_format: str = 'json') -> str:
        """Generate analysis report in specified format."""
        if output_format == 'json':
            return json.dumps(asdict(analysis), indent=2, default=str)
        elif output_format == 'summary':
            return self._generate_text_summary(analysis)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_text_summary(self, analysis: AnalysisReport) -> str:
        """Generate human-readable text summary."""
        summary = []
        summary.append(f"🔍 Code Analysis Report - {analysis.file_path}")
        summary.append("=" * 60)
        summary.append(f"Language: {analysis.language}")
        summary.append(f"Lines of Code: {analysis.lines_of_code}")
        summary.append(f"Complexity Score: {analysis.complexity_score:.1f}/100")
        summary.append(f"Optimization Potential: {analysis.optimization_potential_score:.1f}/100")
        summary.append(f"Analysis Confidence: {analysis.overall_confidence:.2f}")
        
        if analysis.bottlenecks:
            summary.append(f"\n🚨 Performance Bottlenecks ({len(analysis.bottlenecks)}):")
            for i, bottleneck in enumerate(analysis.bottlenecks[:5], 1):
                summary.append(f"  {i}. {bottleneck.description} ({bottleneck.severity}) - {bottleneck.impact_estimate:.0f}% impact")
        
        if analysis.optimization_opportunities:
            summary.append(f"\n💡 Optimization Opportunities ({len(analysis.optimization_opportunities)}):")
            for i, opp in enumerate(analysis.optimization_opportunities[:5], 1):
                summary.append(f"  {i}. {opp.suggested_improvement} - {opp.estimated_improvement:.0f}% gain ({opp.implementation_difficulty})")
        
        if analysis.quick_wins:
            summary.append(f"\n⚡ Quick Wins:")
            for win in analysis.quick_wins:
                summary.append(f"  • {win}")
        
        return '\n'.join(summary)


def main():
    """Command-line interface for code analysis engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenEvolve Code Analysis Engine")
    parser.add_argument("file", help="Code file to analyze")
    parser.add_argument("--language", help="Programming language (auto-detect if not provided)")
    parser.add_argument("--format", choices=['json', 'summary'], default='summary', help="Output format")
    parser.add_argument("--output", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    # Analyze code
    engine = CodeAnalysisEngine()
    analysis = engine.analyze_file(args.file, args.language)
    
    # Generate report
    report = engine.generate_report(analysis, args.format)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📊 Analysis report saved to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()