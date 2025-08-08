#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "json",
#     "typing-extensions",
#     "scikit-learn",
#     "matplotlib",
#     "pandas"
# ]
# ///

"""
Meta-Learning Adaptive Thresholds System
========================================

This module implements adaptive threshold management using meta-learning
techniques, following ADAS (Adaptive Decision-making Autonomous Systems)
patterns from claude-code-agentic-scripts.

Key Features:
- Historical performance tracking
- Dynamic threshold adjustment using ROC analysis
- Context-aware threshold adaptation
- Continuous learning from validation outcomes
- Performance trend analysis
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np

try:
    from sklearn.metrics import roc_curve, auc
    from sklearn.model_selection import cross_val_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logging.warning("scikit-learn not available - using simplified threshold adaptation")

logger = logging.getLogger(__name__)


@dataclass
class ValidationOutcome:
    """Record of a validation decision and its actual outcome"""
    timestamp: str
    predicted_score: float
    predicted_status: str
    actual_success: bool
    context: Dict[str, Any]
    model_ensemble: List[str]
    response_time: float
    confidence: float
    dimensions: Dict[str, float]


@dataclass
class ThresholdConfig:
    """Dynamic threshold configuration"""
    approved_threshold: float
    needs_revision_threshold: float
    confidence_minimum: float
    context_factors: Dict[str, float]
    last_updated: str
    performance_metrics: Dict[str, float]


@dataclass
class AdaptationContext:
    """Context factors that influence threshold adaptation"""
    tool_complexity: float      # Complexity of the tool being validated
    user_expertise: float       # Estimated user expertise level
    project_criticality: float  # How critical the project is
    time_pressure: float        # Time constraints on the decision
    past_success_rate: float    # Historical success rate in similar contexts


class MetaLearningThresholds:
    """
    Meta-learning system for adaptive threshold management
    """
    
    def __init__(self, history_path: Optional[Path] = None):
        self.history_path = history_path or Path(__file__).parent / "utils" / "validation_history.json"
        self.config_path = self.history_path.parent / "threshold_config.json"
        
        # Ensure directory exists
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load historical data and current config
        self.validation_history = self._load_validation_history()
        self.current_config = self._load_threshold_config()
        
        # Meta-learning parameters
        self.learning_rate = 0.1
        self.adaptation_window = 100  # Number of recent validations to consider
        self.minimum_data_points = 20  # Minimum data for reliable adaptation
        
        # Context weighting factors
        self.context_weights = {
            "tool_complexity": 0.3,
            "user_expertise": 0.2,
            "project_criticality": 0.25,
            "time_pressure": 0.15,
            "past_success_rate": 0.1
        }
    
    def _load_validation_history(self) -> List[ValidationOutcome]:
        """Load historical validation outcomes"""
        try:
            if self.history_path.exists():
                with open(self.history_path, 'r') as f:
                    data = json.load(f)
                
                return [
                    ValidationOutcome(
                        timestamp=item["timestamp"],
                        predicted_score=item["predicted_score"],
                        predicted_status=item["predicted_status"],
                        actual_success=item["actual_success"],
                        context=item.get("context", {}),
                        model_ensemble=item.get("model_ensemble", []),
                        response_time=item.get("response_time", 0.0),
                        confidence=item.get("confidence", 0.0),
                        dimensions=item.get("dimensions", {})
                    )
                    for item in data.get("validation_outcomes", [])
                ]
            
        except Exception as e:
            logger.warning(f"Could not load validation history: {e}")
        
        return []
    
    def _load_threshold_config(self) -> ThresholdConfig:
        """Load current threshold configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                return ThresholdConfig(
                    approved_threshold=data["approved_threshold"],
                    needs_revision_threshold=data["needs_revision_threshold"],
                    confidence_minimum=data["confidence_minimum"],
                    context_factors=data.get("context_factors", {}),
                    last_updated=data["last_updated"],
                    performance_metrics=data.get("performance_metrics", {})
                )
            
        except Exception as e:
            logger.warning(f"Could not load threshold config: {e}")
        
        # Return default configuration
        return ThresholdConfig(
            approved_threshold=80.0,
            needs_revision_threshold=60.0,
            confidence_minimum=0.7,
            context_factors={},
            last_updated=datetime.now().isoformat(),
            performance_metrics={}
        )
    
    def get_adaptive_thresholds(self, context: AdaptationContext) -> Dict[str, float]:
        """
        Get context-aware adaptive thresholds
        """
        base_config = self.current_config
        
        # Apply context-based adjustments
        context_adjustment = self._calculate_context_adjustment(context)
        
        adjusted_thresholds = {
            "approved": max(70.0, min(90.0, 
                base_config.approved_threshold + context_adjustment["approved"])),
            "needs_revision": max(50.0, min(80.0, 
                base_config.needs_revision_threshold + context_adjustment["needs_revision"])),
            "confidence_minimum": max(0.5, min(0.9, 
                base_config.confidence_minimum + context_adjustment["confidence"]))
        }
        
        logger.info(f"Adaptive thresholds: {adjusted_thresholds}")
        return adjusted_thresholds
    
    def _calculate_context_adjustment(self, context: AdaptationContext) -> Dict[str, float]:
        """Calculate threshold adjustments based on context"""
        adjustments = {"approved": 0.0, "needs_revision": 0.0, "confidence": 0.0}
        
        # High complexity -> higher thresholds
        if context.tool_complexity > 0.8:
            adjustments["approved"] += 5.0
            adjustments["confidence"] += 0.1
        
        # Low user expertise -> higher thresholds  
        if context.user_expertise < 0.3:
            adjustments["approved"] += 3.0
            adjustments["needs_revision"] += 2.0
        
        # High criticality -> higher thresholds
        if context.project_criticality > 0.8:
            adjustments["approved"] += 4.0
            adjustments["confidence"] += 0.05
        
        # High time pressure -> slightly lower thresholds
        if context.time_pressure > 0.8:
            adjustments["approved"] -= 2.0
            adjustments["needs_revision"] -= 1.0
        
        # Good past success rate -> slightly lower thresholds
        if context.past_success_rate > 0.85:
            adjustments["approved"] -= 1.0
        
        return adjustments
    
    def record_validation_outcome(self, predicted_score: float, predicted_status: str, 
                                actual_success: bool, context: Dict[str, Any] = None,
                                model_ensemble: List[str] = None, response_time: float = 0.0,
                                confidence: float = 0.0, dimensions: Dict[str, float] = None):
        """Record the outcome of a validation decision"""
        outcome = ValidationOutcome(
            timestamp=datetime.now().isoformat(),
            predicted_score=predicted_score,
            predicted_status=predicted_status,
            actual_success=actual_success,
            context=context or {},
            model_ensemble=model_ensemble or [],
            response_time=response_time,
            confidence=confidence,
            dimensions=dimensions or {}
        )
        
        self.validation_history.append(outcome)
        
        # Trigger adaptive learning if we have enough data
        if len(self.validation_history) >= self.minimum_data_points:
            if len(self.validation_history) % 10 == 0:  # Update every 10 validations
                self._update_thresholds_with_learning()
        
        # Save updated history
        self._save_validation_history()
    
    def _update_thresholds_with_learning(self):
        """Update thresholds using meta-learning from recent outcomes"""
        recent_outcomes = self.validation_history[-self.adaptation_window:]
        
        if len(recent_outcomes) < self.minimum_data_points:
            logger.info("Insufficient data for threshold adaptation")
            return
        
        logger.info(f"Updating thresholds using {len(recent_outcomes)} recent outcomes")
        
        # Calculate current performance metrics
        performance_metrics = self._calculate_performance_metrics(recent_outcomes)
        
        if HAS_SKLEARN:
            new_thresholds = self._sklearn_threshold_optimization(recent_outcomes)
        else:
            new_thresholds = self._simple_threshold_optimization(recent_outcomes, performance_metrics)
        
        # Update configuration with learned thresholds
        self._update_threshold_config(new_thresholds, performance_metrics)
        
        logger.info(f"Thresholds updated: {new_thresholds}")
    
    def _calculate_performance_metrics(self, outcomes: List[ValidationOutcome]) -> Dict[str, float]:
        """Calculate performance metrics from validation outcomes"""
        if not outcomes:
            return {}
        
        # True positives: predicted approved & actually successful
        tp = sum(1 for o in outcomes if o.predicted_status == "approved" and o.actual_success)
        
        # False positives: predicted approved & actually failed
        fp = sum(1 for o in outcomes if o.predicted_status == "approved" and not o.actual_success)
        
        # True negatives: predicted rejected/needs_revision & actually failed
        tn = sum(1 for o in outcomes if o.predicted_status != "approved" and not o.actual_success)
        
        # False negatives: predicted rejected/needs_revision & actually successful
        fn = sum(1 for o in outcomes if o.predicted_status != "approved" and o.actual_success)
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        accuracy = (tp + tn) / len(outcomes) if outcomes else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Success rate by predicted status
        approved_success_rate = sum(1 for o in outcomes if o.predicted_status == "approved" and o.actual_success) / max(1, sum(1 for o in outcomes if o.predicted_status == "approved"))
        
        return {
            "precision": precision,
            "recall": recall,
            "accuracy": accuracy,
            "f1_score": f1_score,
            "approved_success_rate": approved_success_rate,
            "total_validations": len(outcomes)
        }
    
    def _sklearn_threshold_optimization(self, outcomes: List[ValidationOutcome]) -> Dict[str, float]:
        """Use scikit-learn for optimal threshold calculation"""
        scores = [o.predicted_score for o in outcomes]
        labels = [1 if o.actual_success else 0 for o in outcomes]
        
        if len(set(labels)) < 2:  # Need both success and failure examples
            return self._simple_threshold_optimization(outcomes, {})
        
        try:
            # Calculate ROC curve
            fpr, tpr, thresholds = roc_curve(labels, scores)
            
            # Find optimal threshold using Youden's J statistic
            j_scores = tpr - fpr
            optimal_idx = np.argmax(j_scores)
            optimal_threshold = thresholds[optimal_idx]
            
            # Calculate AUC for performance assessment
            roc_auc = auc(fpr, tpr)
            
            logger.info(f"ROC AUC: {roc_auc:.3f}, Optimal threshold: {optimal_threshold:.1f}")
            
            # Set approved threshold near optimal, needs_revision as buffer
            approved_threshold = min(90.0, max(70.0, optimal_threshold))
            needs_revision_threshold = max(50.0, approved_threshold - 20.0)
            
            return {
                "approved": approved_threshold,
                "needs_revision": needs_revision_threshold,
                "confidence_minimum": 0.7,  # Keep stable for now
                "roc_auc": roc_auc
            }
            
        except Exception as e:
            logger.warning(f"ROC analysis failed: {e}, falling back to simple optimization")
            return self._simple_threshold_optimization(outcomes, {})
    
    def _simple_threshold_optimization(self, outcomes: List[ValidationOutcome], 
                                     metrics: Dict[str, float]) -> Dict[str, float]:
        """Simple threshold optimization without scikit-learn"""
        scores = [o.predicted_score for o in outcomes]
        labels = [o.actual_success for o in outcomes]
        
        # Find threshold that maximizes F1 score
        best_threshold = self.current_config.approved_threshold
        best_f1 = 0.0
        
        # Test different thresholds
        for threshold in range(60, 91, 2):
            tp = sum(1 for s, l in zip(scores, labels) if s >= threshold and l)
            fp = sum(1 for s, l in zip(scores, labels) if s >= threshold and not l)
            fn = sum(1 for s, l in zip(scores, labels) if s < threshold and l)
            
            if tp + fp > 0 and tp + fn > 0:
                precision = tp / (tp + fp)
                recall = tp / (tp + fn)
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                
                if f1 > best_f1:
                    best_f1 = f1
                    best_threshold = threshold
        
        # Apply learning rate to smooth adaptation
        current_threshold = self.current_config.approved_threshold
        new_threshold = current_threshold + self.learning_rate * (best_threshold - current_threshold)
        
        return {
            "approved": max(70.0, min(90.0, new_threshold)),
            "needs_revision": max(50.0, new_threshold - 20.0),
            "confidence_minimum": self.current_config.confidence_minimum,
            "f1_score": best_f1
        }
    
    def _update_threshold_config(self, new_thresholds: Dict[str, float], 
                               performance_metrics: Dict[str, float]):
        """Update and save threshold configuration"""
        self.current_config = ThresholdConfig(
            approved_threshold=new_thresholds["approved"],
            needs_revision_threshold=new_thresholds["needs_revision"],
            confidence_minimum=new_thresholds["confidence_minimum"],
            context_factors=self.current_config.context_factors,
            last_updated=datetime.now().isoformat(),
            performance_metrics=performance_metrics
        )
        
        # Save configuration
        try:
            with open(self.config_path, 'w') as f:
                json.dump(asdict(self.current_config), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save threshold config: {e}")
    
    def _save_validation_history(self):
        """Save validation history to disk"""
        try:
            # Keep only recent history to prevent unbounded growth
            max_history = 1000
            recent_history = self.validation_history[-max_history:]
            
            data = {
                "validation_outcomes": [asdict(outcome) for outcome in recent_history],
                "last_updated": datetime.now().isoformat(),
                "total_validations": len(self.validation_history)
            }
            
            with open(self.history_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save validation history: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.validation_history:
            return {"message": "No validation history available"}
        
        recent_outcomes = self.validation_history[-self.adaptation_window:]
        overall_metrics = self._calculate_performance_metrics(self.validation_history)
        recent_metrics = self._calculate_performance_metrics(recent_outcomes)
        
        # Trend analysis
        trend_data = self._analyze_performance_trends()
        
        return {
            "overall_performance": overall_metrics,
            "recent_performance": recent_metrics,
            "current_thresholds": asdict(self.current_config),
            "trend_analysis": trend_data,
            "recommendations": self._generate_recommendations(recent_metrics, trend_data)
        }
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if len(self.validation_history) < 50:
            return {"message": "Insufficient data for trend analysis"}
        
        # Split history into time windows
        window_size = 20
        windows = [
            self.validation_history[i:i+window_size] 
            for i in range(0, len(self.validation_history), window_size)
            if len(self.validation_history[i:i+window_size]) == window_size
        ]
        
        if len(windows) < 3:
            return {"message": "Insufficient windows for trend analysis"}
        
        # Calculate metrics for each window
        window_metrics = [self._calculate_performance_metrics(window) for window in windows]
        
        # Analyze trends
        accuracy_trend = [m["accuracy"] for m in window_metrics]
        f1_trend = [m["f1_score"] for m in window_metrics]
        precision_trend = [m["precision"] for m in window_metrics]
        
        return {
            "accuracy_trend": "improving" if accuracy_trend[-1] > accuracy_trend[0] else "declining",
            "f1_trend": "improving" if f1_trend[-1] > f1_trend[0] else "declining",
            "precision_trend": "improving" if precision_trend[-1] > precision_trend[0] else "declining",
            "latest_accuracy": accuracy_trend[-1],
            "accuracy_change": accuracy_trend[-1] - accuracy_trend[0],
            "windows_analyzed": len(windows)
        }
    
    def _generate_recommendations(self, recent_metrics: Dict[str, float], 
                                trend_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on performance analysis"""
        recommendations = []
        
        if recent_metrics.get("accuracy", 0) < 0.7:
            recommendations.append("Accuracy is below 70% - consider recalibrating thresholds")
        
        if recent_metrics.get("precision", 0) < 0.6:
            recommendations.append("Low precision detected - threshold may be too permissive")
        
        if recent_metrics.get("recall", 0) < 0.6:
            recommendations.append("Low recall detected - threshold may be too restrictive")
        
        if trend_data.get("accuracy_trend") == "declining":
            recommendations.append("Accuracy is declining - investigate validation model performance")
        
        if recent_metrics.get("approved_success_rate", 0) < 0.8:
            recommendations.append("Success rate for approved validations is low - increase approved threshold")
        
        if not recommendations:
            recommendations.append("Performance is stable - continue current threshold configuration")
        
        return recommendations
    
    def estimate_context(self, input_data: Dict[str, Any]) -> AdaptationContext:
        """Estimate context factors from input data"""
        tool_name = input_data.get('request', {}).get('tool_name', 'unknown')
        tool_params = input_data.get('request', {}).get('parameters', {})
        
        # Estimate tool complexity based on tool type and parameters
        complexity_factors = {
            'Write': 0.6,
            'Read': 0.3,
            'Bash': 0.8,
            'search': 0.5,
            'git': 0.7
        }
        
        tool_complexity = complexity_factors.get(tool_name, 0.5)
        
        # Estimate based on parameter complexity
        param_complexity = len(str(tool_params)) / 1000.0  # Rough heuristic
        tool_complexity = min(1.0, tool_complexity + param_complexity)
        
        # Other factors would need more context - using defaults for now
        return AdaptationContext(
            tool_complexity=tool_complexity,
            user_expertise=0.6,  # Default moderate expertise
            project_criticality=0.5,  # Default moderate criticality
            time_pressure=0.4,  # Default low-moderate time pressure
            past_success_rate=self.current_config.performance_metrics.get("approved_success_rate", 0.8)
        )


# Convenience functions for integration with collective_intelligence_validator.py
def get_adaptive_thresholds_for_context(input_data: Dict[str, Any]) -> Dict[str, float]:
    """Get adaptive thresholds for given input context"""
    meta_learner = MetaLearningThresholds()
    context = meta_learner.estimate_context(input_data)
    return meta_learner.get_adaptive_thresholds(context)


def record_validation_feedback(predicted_score: float, predicted_status: str, 
                              actual_success: bool, context: Dict[str, Any] = None):
    """Record validation outcome for learning"""
    meta_learner = MetaLearningThresholds()
    meta_learner.record_validation_outcome(
        predicted_score=predicted_score,
        predicted_status=predicted_status,
        actual_success=actual_success,
        context=context
    )


def get_performance_dashboard() -> Dict[str, Any]:
    """Get performance dashboard for monitoring"""
    meta_learner = MetaLearningThresholds()
    return meta_learner.get_performance_report()


if __name__ == "__main__":
    """Test the meta-learning system"""
    def test_meta_learning():
        meta_learner = MetaLearningThresholds()
        
        # Simulate some validation outcomes
        import random
        for i in range(50):
            score = random.uniform(50, 100)
            success = score > 75 and random.random() > 0.1  # 10% false success rate
            status = "approved" if score > 80 else "needs_revision" if score > 60 else "rejected"
            
            meta_learner.record_validation_outcome(
                predicted_score=score,
                predicted_status=status,
                actual_success=success,
                context={"tool": "test", "iteration": i}
            )
        
        # Get performance report
        report = meta_learner.get_performance_report()
        print("Performance Report:")
        print(json.dumps(report, indent=2))
        
        # Test adaptive thresholds
        test_context = AdaptationContext(
            tool_complexity=0.8,
            user_expertise=0.3,
            project_criticality=0.9,
            time_pressure=0.2,
            past_success_rate=0.85
        )
        
        thresholds = meta_learner.get_adaptive_thresholds(test_context)
        print(f"\nAdaptive Thresholds: {thresholds}")
    
    test_meta_learning()