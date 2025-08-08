#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "scipy",
#     "json",
#     "typing-extensions",
#     "networkx",
#     "pandas"
# ]
# ///

"""
Population-Based Consensus Engine
================================

This module implements sophisticated population-based consensus algorithms
following evolution-engine.sh patterns from claude-code-agentic-scripts.

Key Features:
- Multi-model population management
- Diversity-based selection algorithms  
- Outlier detection using statistical methods
- Collective intelligence patterns
- Dynamic consensus calculation
- Population health monitoring
"""

import json
import logging
import random
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from scipy import stats
import networkx as nx

logger = logging.getLogger(__name__)


class ConsensusMethod(Enum):
    WEIGHTED_AVERAGE = "weighted_average"
    MEDIAN_CONSENSUS = "median_consensus" 
    BAYESIAN_FUSION = "bayesian_fusion"
    OUTLIER_RESISTANT = "outlier_resistant"
    DIVERSITY_WEIGHTED = "diversity_weighted"


@dataclass
class PopulationMember:
    """Individual member of the validation population"""
    model_id: str
    model_type: str
    score: float
    confidence: float
    dimensions: Dict[str, float]
    reasoning: str
    response_time: float
    tokens_used: int
    error: Optional[str] = None
    
    # Population-specific metrics
    diversity_score: float = 0.0
    reliability_score: float = 1.0
    expertise_weight: float = 1.0
    consensus_history: List[float] = None
    
    def __post_init__(self):
        if self.consensus_history is None:
            self.consensus_history = []


@dataclass
class PopulationDynamics:
    """Population-level dynamics and health metrics"""
    population_size: int
    diversity_index: float
    consensus_strength: float
    outlier_count: int
    reliability_variance: float
    response_time_distribution: Dict[str, float]
    expertise_distribution: Dict[str, float]
    model_type_distribution: Dict[str, int]


@dataclass
class ConsensusResult:
    """Result of population-based consensus calculation"""
    consensus_score: float
    consensus_method: ConsensusMethod
    confidence_level: float
    population_agreement: float
    outliers_detected: List[str]
    diversity_impact: float
    reasoning: str
    
    # Detailed population analysis
    population_dynamics: PopulationDynamics
    member_contributions: Dict[str, float]
    consensus_uncertainty: float
    recommendation_strength: float


class PopulationConsensusEngine:
    """
    Advanced population-based consensus engine implementing collective intelligence
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Population management
        self.population_history = []
        self.member_reliability_scores = {}
        self.expertise_weights = {}
        
        # Consensus algorithms
        self.consensus_methods = {
            ConsensusMethod.WEIGHTED_AVERAGE: self._weighted_average_consensus,
            ConsensusMethod.MEDIAN_CONSENSUS: self._median_consensus,
            ConsensusMethod.BAYESIAN_FUSION: self._bayesian_fusion_consensus,
            ConsensusMethod.OUTLIER_RESISTANT: self._outlier_resistant_consensus,
            ConsensusMethod.DIVERSITY_WEIGHTED: self._diversity_weighted_consensus
        }
        
        # Load historical population data
        self._load_population_history()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration following evolution-engine.sh patterns"""
        return {
            "min_population_size": 3,
            "max_population_size": 7,
            "outlier_threshold": 2.0,  # Standard deviations
            "diversity_weight": 0.3,
            "reliability_decay": 0.95,  # Per validation cycle
            "consensus_threshold": 0.7,
            "expertise_adaptation_rate": 0.1,
            "population_mutation_rate": 0.2,
            "crossover_probability": 0.3
        }
    
    def _load_population_history(self):
        """Load historical population performance data"""
        try:
            history_path = Path(__file__).parent / "utils" / "population_history.json"
            if history_path.exists():
                with open(history_path, 'r') as f:
                    data = json.load(f)
                
                self.member_reliability_scores = data.get("member_reliability", {})
                self.expertise_weights = data.get("expertise_weights", {})
                self.population_history = data.get("population_history", [])[-100:]  # Keep recent history
                
        except Exception as e:
            logger.warning(f"Could not load population history: {e}")
    
    def calculate_population_consensus(self, population: List[PopulationMember],
                                     method: ConsensusMethod = ConsensusMethod.DIVERSITY_WEIGHTED) -> ConsensusResult:
        """
        Calculate consensus from population using specified method
        """
        if not population:
            raise ValueError("Empty population provided")
        
        if len(population) < self.config["min_population_size"]:
            logger.warning(f"Population size {len(population)} below minimum {self.config['min_population_size']}")
        
        # Update population member metrics
        self._update_population_metrics(population)
        
        # Detect and handle outliers
        outliers = self._detect_outliers(population)
        
        # Calculate consensus using selected method
        consensus_func = self.consensus_methods.get(method, self._diversity_weighted_consensus)
        consensus_result = consensus_func(population, outliers)
        
        # Calculate population dynamics
        population_dynamics = self._analyze_population_dynamics(population)
        consensus_result.population_dynamics = population_dynamics
        
        # Update historical data
        self._update_population_history(population, consensus_result)
        
        return consensus_result
    
    def _update_population_metrics(self, population: List[PopulationMember]):
        """Update population member metrics based on historical performance"""
        for member in population:
            # Update reliability score based on historical performance
            member_id = f"{member.model_type}_{member.model_id}"
            
            if member_id in self.member_reliability_scores:
                # Decay current reliability and update with recent performance
                current_reliability = self.member_reliability_scores[member_id]
                
                # Reliability based on confidence and historical accuracy
                new_reliability = current_reliability * self.config["reliability_decay"]
                new_reliability += (1 - self.config["reliability_decay"]) * member.confidence
                
                member.reliability_score = max(0.1, min(1.0, new_reliability))
                self.member_reliability_scores[member_id] = member.reliability_score
            else:
                member.reliability_score = member.confidence
                self.member_reliability_scores[member_id] = member.reliability_score
            
            # Update expertise weights
            if member_id in self.expertise_weights:
                member.expertise_weight = self.expertise_weights[member_id]
            else:
                # Initialize based on model type and performance
                type_weights = {
                    "claude": 1.0,
                    "gemini": 0.9,
                    "gpt": 0.95,
                    "local": 0.8
                }
                member.expertise_weight = type_weights.get(member.model_type.lower(), 0.8)
                self.expertise_weights[member_id] = member.expertise_weight
    
    def _detect_outliers(self, population: List[PopulationMember]) -> List[str]:
        """Detect outliers in population using statistical methods"""
        if len(population) < 3:
            return []  # Need at least 3 members for outlier detection
        
        scores = [member.score for member in population]
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        if std_score == 0:
            return []  # No variation, no outliers
        
        outliers = []
        threshold = self.config["outlier_threshold"]
        
        for member in population:
            z_score = abs(member.score - mean_score) / std_score
            if z_score > threshold:
                outliers.append(f"{member.model_type}_{member.model_id}")
                logger.info(f"Outlier detected: {member.model_id} (z-score: {z_score:.2f})")
        
        return outliers
    
    def _weighted_average_consensus(self, population: List[PopulationMember], 
                                  outliers: List[str]) -> ConsensusResult:
        """Simple weighted average consensus"""
        # Filter out outliers
        valid_members = [m for m in population if f"{m.model_type}_{m.model_id}" not in outliers]
        
        if not valid_members:
            valid_members = population  # Use all if all are outliers
        
        # Weight by confidence and reliability
        total_weight = sum(m.confidence * m.reliability_score for m in valid_members)
        
        if total_weight == 0:
            consensus_score = np.mean([m.score for m in valid_members])
            confidence_level = 0.3
        else:
            weights = [(m.confidence * m.reliability_score) / total_weight for m in valid_members]
            consensus_score = sum(m.score * w for m, w in zip(valid_members, weights))
            confidence_level = np.mean([m.confidence for m in valid_members])
        
        return ConsensusResult(
            consensus_score=consensus_score,
            consensus_method=ConsensusMethod.WEIGHTED_AVERAGE,
            confidence_level=confidence_level,
            population_agreement=1.0 - (np.std([m.score for m in valid_members]) / 100.0),
            outliers_detected=outliers,
            diversity_impact=0.0,
            reasoning=f"Weighted average of {len(valid_members)} valid members",
            population_dynamics=None,  # Will be set by caller
            member_contributions={m.model_id: w for m, w in zip(valid_members, weights or [])},
            consensus_uncertainty=np.std([m.score for m in valid_members]),
            recommendation_strength=confidence_level
        )
    
    def _median_consensus(self, population: List[PopulationMember], 
                         outliers: List[str]) -> ConsensusResult:
        """Median-based consensus (robust to outliers)"""
        valid_members = [m for m in population if f"{m.model_type}_{m.model_id}" not in outliers]
        
        if not valid_members:
            valid_members = population
        
        scores = [m.score for m in valid_members]
        consensus_score = np.median(scores)
        
        # Confidence based on how tightly clustered scores are around median
        mad = np.median([abs(score - consensus_score) for score in scores])  # Median Absolute Deviation
        confidence_level = max(0.3, 1.0 - (mad / 50.0))  # Normalize MAD to confidence
        
        return ConsensusResult(
            consensus_score=consensus_score,
            consensus_method=ConsensusMethod.MEDIAN_CONSENSUS,
            confidence_level=confidence_level,
            population_agreement=1.0 - (mad / 100.0),
            outliers_detected=outliers,
            diversity_impact=0.0,
            reasoning=f"Median consensus from {len(valid_members)} members",
            population_dynamics=None,
            member_contributions={m.model_id: 1.0/len(valid_members) for m in valid_members},
            consensus_uncertainty=mad,
            recommendation_strength=confidence_level
        )
    
    def _bayesian_fusion_consensus(self, population: List[PopulationMember], 
                                  outliers: List[str]) -> ConsensusResult:
        """Bayesian fusion of population beliefs"""
        valid_members = [m for m in population if f"{m.model_type}_{m.model_id}" not in outliers]
        
        if not valid_members:
            valid_members = population
        
        # Treat each member's score as a Gaussian belief
        beliefs = []
        for member in valid_members:
            # Convert confidence to precision (inverse variance)
            precision = max(0.1, member.confidence * 10)  # Higher confidence = higher precision
            beliefs.append((member.score, precision))
        
        # Bayesian fusion: combine Gaussian beliefs
        total_precision = sum(precision for _, precision in beliefs)
        weighted_mean = sum(score * precision for score, precision in beliefs) / total_precision
        
        # Posterior precision is sum of precisions
        posterior_variance = 1.0 / total_precision
        posterior_std = np.sqrt(posterior_variance)
        
        # Confidence based on posterior precision
        confidence_level = min(0.99, total_precision / (total_precision + 1))
        
        return ConsensusResult(
            consensus_score=weighted_mean,
            consensus_method=ConsensusMethod.BAYESIAN_FUSION,
            confidence_level=confidence_level,
            population_agreement=1.0 - (posterior_std / 50.0),
            outliers_detected=outliers,
            diversity_impact=0.0,
            reasoning=f"Bayesian fusion of {len(valid_members)} beliefs",
            population_dynamics=None,
            member_contributions={
                m.model_id: beliefs[i][1] / total_precision 
                for i, m in enumerate(valid_members)
            },
            consensus_uncertainty=posterior_std,
            recommendation_strength=confidence_level
        )
    
    def _outlier_resistant_consensus(self, population: List[PopulationMember], 
                                   outliers: List[str]) -> ConsensusResult:
        """Outlier-resistant consensus using robust statistics"""
        scores = [m.score for m in population]
        
        # Use Winsorized mean (trim extreme values)
        scores_array = np.array(scores)
        winsorized_mean = stats.mstats.winsorize(scores_array, limits=[0.1, 0.1]).mean()
        
        # Calculate robust scale estimate
        mad = stats.median_abs_deviation(scores_array)
        
        # Confidence based on consistency
        confidence_level = max(0.3, 1.0 - (mad / 50.0))
        
        return ConsensusResult(
            consensus_score=float(winsorized_mean),
            consensus_method=ConsensusMethod.OUTLIER_RESISTANT,
            confidence_level=confidence_level,
            population_agreement=1.0 - (mad / 100.0),
            outliers_detected=outliers,
            diversity_impact=0.1,
            reasoning=f"Outlier-resistant consensus using Winsorized mean",
            population_dynamics=None,
            member_contributions={m.model_id: 1.0/len(population) for m in population},
            consensus_uncertainty=float(mad),
            recommendation_strength=confidence_level
        )
    
    def _diversity_weighted_consensus(self, population: List[PopulationMember], 
                                    outliers: List[str]) -> ConsensusResult:
        """Diversity-weighted consensus following evolution-engine.sh patterns"""
        if not population:
            raise ValueError("Empty population")
        
        # Calculate diversity scores for each member
        self._calculate_diversity_scores(population)
        
        # Apply diversity weighting to member contributions
        diversity_weights = []
        total_diversity_weight = 0
        
        for member in population:
            # Skip extreme outliers but include mild outliers for diversity
            member_id = f"{member.model_type}_{member.model_id}"
            is_extreme_outlier = member_id in outliers and member.confidence < 0.5
            
            if is_extreme_outlier:
                weight = 0.0
            else:
                # Combine confidence, reliability, expertise, and diversity
                base_weight = (
                    member.confidence * 0.4 +
                    member.reliability_score * 0.3 +
                    member.expertise_weight * 0.2 +
                    member.diversity_score * 0.1
                )
                weight = max(0.1, base_weight)  # Minimum weight for inclusion
            
            diversity_weights.append(weight)
            total_diversity_weight += weight
        
        if total_diversity_weight == 0:
            # Fallback to equal weighting
            diversity_weights = [1.0] * len(population)
            total_diversity_weight = len(population)
        
        # Normalize weights
        normalized_weights = [w / total_diversity_weight for w in diversity_weights]
        
        # Calculate weighted consensus
        consensus_score = sum(m.score * w for m, w in zip(population, normalized_weights))
        
        # Calculate confidence based on weight distribution and agreement
        score_variance = np.average(
            [(m.score - consensus_score) ** 2 for m in population],
            weights=normalized_weights
        )
        
        # Higher diversity and lower variance = higher confidence
        diversity_index = self._calculate_population_diversity_index(population)
        agreement_factor = 1.0 - min(1.0, score_variance / 1000.0)  # Normalize variance
        confidence_level = min(0.95, agreement_factor * (1.0 + diversity_index * 0.2))
        
        return ConsensusResult(
            consensus_score=consensus_score,
            consensus_method=ConsensusMethod.DIVERSITY_WEIGHTED,
            confidence_level=confidence_level,
            population_agreement=agreement_factor,
            outliers_detected=outliers,
            diversity_impact=diversity_index,
            reasoning=f"Diversity-weighted consensus from {len(population)} members (diversity index: {diversity_index:.2f})",
            population_dynamics=None,
            member_contributions={m.model_id: w for m, w in zip(population, normalized_weights)},
            consensus_uncertainty=np.sqrt(score_variance),
            recommendation_strength=confidence_level * (1.0 + diversity_index * 0.1)
        )
    
    def _calculate_diversity_scores(self, population: List[PopulationMember]):
        """Calculate diversity scores for population members"""
        if len(population) < 2:
            for member in population:
                member.diversity_score = 0.5
            return
        
        # Create feature matrix for diversity calculation
        features = []
        for member in population:
            feature_vector = [
                member.score,
                member.confidence,
                member.dimensions.get("performance", 0),
                member.dimensions.get("novelty", 0),
                member.dimensions.get("efficiency", 0),
                member.dimensions.get("safety", 0),
                member.response_time,
                hash(member.model_type) % 100 / 100.0  # Model type diversity
            ]
            features.append(feature_vector)
        
        features_array = np.array(features)
        
        # Calculate pairwise distances
        from scipy.spatial.distance import pdist, squareform
        distances = squareform(pdist(features_array, metric='euclidean'))
        
        # Diversity score is average distance to other members
        for i, member in enumerate(population):
            other_distances = [distances[i][j] for j in range(len(population)) if j != i]
            member.diversity_score = np.mean(other_distances) if other_distances else 0.5
        
        # Normalize diversity scores to [0, 1]
        diversity_scores = [m.diversity_score for m in population]
        max_diversity = max(diversity_scores) if diversity_scores else 1.0
        
        if max_diversity > 0:
            for member in population:
                member.diversity_score = member.diversity_score / max_diversity
    
    def _calculate_population_diversity_index(self, population: List[PopulationMember]) -> float:
        """Calculate overall population diversity index"""
        if len(population) < 2:
            return 0.0
        
        # Shannon diversity index based on model types
        model_types = [m.model_type for m in population]
        type_counts = {}
        for model_type in model_types:
            type_counts[model_type] = type_counts.get(model_type, 0) + 1
        
        total = len(population)
        shannon_index = -sum((count/total) * np.log(count/total) for count in type_counts.values())
        
        # Normalize by maximum possible diversity
        max_shannon = np.log(len(type_counts))
        normalized_shannon = shannon_index / max_shannon if max_shannon > 0 else 0
        
        # Combine with score diversity
        scores = [m.score for m in population]
        score_cv = np.std(scores) / np.mean(scores) if np.mean(scores) > 0 else 0
        
        # Overall diversity index (0-1)
        return min(1.0, normalized_shannon * 0.7 + min(1.0, score_cv) * 0.3)
    
    def _analyze_population_dynamics(self, population: List[PopulationMember]) -> PopulationDynamics:
        """Analyze population-level dynamics and health metrics"""
        if not population:
            return PopulationDynamics(0, 0, 0, 0, 0, {}, {}, {})
        
        scores = [m.score for m in population]
        response_times = [m.response_time for m in population]
        reliabilities = [m.reliability_score for m in population]
        
        # Diversity index
        diversity_index = self._calculate_population_diversity_index(population)
        
        # Consensus strength (inverse of score variance)
        consensus_strength = 1.0 - min(1.0, np.std(scores) / 100.0)
        
        # Count outliers
        outliers = self._detect_outliers(population)
        outlier_count = len(outliers)
        
        # Reliability variance
        reliability_variance = np.var(reliabilities)
        
        # Response time distribution
        response_time_dist = {
            "mean": float(np.mean(response_times)),
            "std": float(np.std(response_times)),
            "min": float(np.min(response_times)),
            "max": float(np.max(response_times))
        }
        
        # Expertise distribution
        expertise_weights = [m.expertise_weight for m in population]
        expertise_dist = {
            "mean": float(np.mean(expertise_weights)),
            "std": float(np.std(expertise_weights)),
            "min": float(np.min(expertise_weights)),
            "max": float(np.max(expertise_weights))
        }
        
        # Model type distribution
        model_types = [m.model_type for m in population]
        type_dist = {}
        for model_type in model_types:
            type_dist[model_type] = type_dist.get(model_type, 0) + 1
        
        return PopulationDynamics(
            population_size=len(population),
            diversity_index=diversity_index,
            consensus_strength=consensus_strength,
            outlier_count=outlier_count,
            reliability_variance=reliability_variance,
            response_time_distribution=response_time_dist,
            expertise_distribution=expertise_dist,
            model_type_distribution=type_dist
        )
    
    def _update_population_history(self, population: List[PopulationMember], 
                                 consensus_result: ConsensusResult):
        """Update population history for learning"""
        history_entry = {
            "timestamp": time.time(),
            "population_size": len(population),
            "consensus_score": consensus_result.consensus_score,
            "consensus_method": consensus_result.consensus_method.value,
            "confidence_level": consensus_result.confidence_level,
            "diversity_index": consensus_result.diversity_impact,
            "outlier_count": len(consensus_result.outliers_detected),
            "model_types": list(set(m.model_type for m in population))
        }
        
        self.population_history.append(history_entry)
        
        # Update expertise weights based on consensus accuracy (if feedback available)
        self._adapt_expertise_weights(population, consensus_result)
        
        # Save updated history
        self._save_population_history()
    
    def _adapt_expertise_weights(self, population: List[PopulationMember], 
                                consensus_result: ConsensusResult):
        """Adapt expertise weights based on consensus participation"""
        adaptation_rate = self.config["expertise_adaptation_rate"]
        
        for member in population:
            member_id = f"{member.model_type}_{member.model_id}"
            
            # Reward members whose scores are close to consensus
            score_distance = abs(member.score - consensus_result.consensus_score)
            normalized_distance = score_distance / 100.0  # Normalize to 0-1
            
            # Closer to consensus = higher reward
            performance_factor = 1.0 - normalized_distance
            
            # Update expertise weight
            current_weight = self.expertise_weights.get(member_id, 1.0)
            new_weight = current_weight + adaptation_rate * (performance_factor - 0.5)
            
            # Constrain weights to reasonable range
            self.expertise_weights[member_id] = max(0.1, min(2.0, new_weight))
    
    def _save_population_history(self):
        """Save population history and learned parameters"""
        try:
            history_path = Path(__file__).parent / "utils" / "population_history.json"
            history_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "member_reliability": self.member_reliability_scores,
                "expertise_weights": self.expertise_weights,
                "population_history": self.population_history[-100:],  # Keep recent history
                "last_updated": time.time()
            }
            
            with open(history_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save population history: {e}")
    
    def get_population_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive population health report"""
        if not self.population_history:
            return {"message": "No population history available"}
        
        recent_history = self.population_history[-20:]  # Last 20 consensus events
        
        # Analyze trends
        diversity_trend = [h["diversity_index"] for h in recent_history]
        confidence_trend = [h["confidence_level"] for h in recent_history]
        outlier_trend = [h["outlier_count"] for h in recent_history]
        
        return {
            "population_statistics": {
                "total_consensus_events": len(self.population_history),
                "average_diversity": float(np.mean(diversity_trend)),
                "average_confidence": float(np.mean(confidence_trend)),
                "average_outliers": float(np.mean(outlier_trend))
            },
            "member_performance": {
                "reliability_scores": self.member_reliability_scores,
                "expertise_weights": self.expertise_weights,
                "member_count": len(self.member_reliability_scores)
            },
            "trend_analysis": {
                "diversity_trend": "improving" if diversity_trend[-1] > diversity_trend[0] else "declining",
                "confidence_trend": "improving" if confidence_trend[-1] > confidence_trend[0] else "declining",
                "outlier_trend": "improving" if outlier_trend[-1] < outlier_trend[0] else "declining"
            },
            "recommendations": self._generate_population_recommendations(recent_history)
        }
    
    def _generate_population_recommendations(self, recent_history: List[Dict]) -> List[str]:
        """Generate recommendations for population management"""
        recommendations = []
        
        if not recent_history:
            return ["Insufficient history for recommendations"]
        
        avg_diversity = np.mean([h["diversity_index"] for h in recent_history])
        avg_confidence = np.mean([h["confidence_level"] for h in recent_history])
        avg_outliers = np.mean([h["outlier_count"] for h in recent_history])
        
        if avg_diversity < 0.3:
            recommendations.append("Population diversity is low - consider adding different model types")
        
        if avg_confidence < 0.6:
            recommendations.append("Average confidence is low - review threshold settings and member reliability")
        
        if avg_outliers > len(recent_history[-1].get("model_types", [])) * 0.3:
            recommendations.append("High outlier rate - investigate model calibration issues")
        
        # Check for model type imbalances
        model_type_counts = {}
        for history in recent_history:
            for model_type in history.get("model_types", []):
                model_type_counts[model_type] = model_type_counts.get(model_type, 0) + 1
        
        if len(model_type_counts) < 2:
            recommendations.append("Population lacks model diversity - add different provider models")
        
        if not recommendations:
            recommendations.append("Population health is good - maintain current configuration")
        
        return recommendations


# Convenience functions for integration
def create_population_from_validation_results(validation_results: List[Dict[str, Any]]) -> List[PopulationMember]:
    """Create population from validation results for consensus calculation"""
    population = []
    
    for i, result in enumerate(validation_results):
        if result.get("error"):
            continue  # Skip failed validations
        
        member = PopulationMember(
            model_id=f"model_{i}",
            model_type=result.get("model", "unknown"),
            score=result.get("score", 0.0),
            confidence=result.get("confidence", 0.5),
            dimensions=result.get("dimensions", {}),
            reasoning=result.get("reasoning", ""),
            response_time=result.get("response_time", 0.0),
            tokens_used=result.get("tokens_used", 0),
            error=result.get("error")
        )
        
        population.append(member)
    
    return population


def calculate_ensemble_consensus(validation_results: List[Dict[str, Any]], 
                               method: ConsensusMethod = ConsensusMethod.DIVERSITY_WEIGHTED) -> Dict[str, Any]:
    """Calculate ensemble consensus from validation results"""
    population = create_population_from_validation_results(validation_results)
    
    if not population:
        return {
            "consensus_score": 0.0,
            "confidence_level": 0.0,
            "method": "none",
            "error": "No valid population members"
        }
    
    engine = PopulationConsensusEngine()
    consensus_result = engine.calculate_population_consensus(population, method)
    
    return {
        "consensus_score": consensus_result.consensus_score,
        "confidence_level": consensus_result.confidence_level,
        "population_agreement": consensus_result.population_agreement,
        "method": consensus_result.consensus_method.value,
        "outliers": consensus_result.outliers_detected,
        "diversity_impact": consensus_result.diversity_impact,
        "reasoning": consensus_result.reasoning,
        "member_contributions": consensus_result.member_contributions,
        "uncertainty": consensus_result.consensus_uncertainty,
        "recommendation_strength": consensus_result.recommendation_strength,
        "population_dynamics": asdict(consensus_result.population_dynamics) if consensus_result.population_dynamics else {}
    }


if __name__ == "__main__":
    """Test the population consensus engine"""
    def test_population_consensus():
        # Create test population
        test_results = [
            {"model": "claude", "score": 85.0, "confidence": 0.9, "dimensions": {"performance": 90, "novelty": 80}, "reasoning": "Good implementation", "response_time": 1.2, "tokens_used": 150},
            {"model": "gemini", "score": 82.0, "confidence": 0.8, "dimensions": {"performance": 85, "novelty": 75}, "reasoning": "Solid approach", "response_time": 0.8, "tokens_used": 120},
            {"model": "gpt", "score": 88.0, "confidence": 0.85, "dimensions": {"performance": 85, "novelty": 90}, "reasoning": "Creative solution", "response_time": 1.5, "tokens_used": 180},
            {"model": "claude", "score": 45.0, "confidence": 0.6, "dimensions": {"performance": 50, "novelty": 40}, "reasoning": "Issues detected", "response_time": 0.9, "tokens_used": 100}  # Outlier
        ]
        
        # Test different consensus methods
        for method in ConsensusMethod:
            result = calculate_ensemble_consensus(test_results, method)
            print(f"\n{method.value.upper()} CONSENSUS:")
            print(f"Score: {result['consensus_score']:.1f}")
            print(f"Confidence: {result['confidence_level']:.2f}")
            print(f"Agreement: {result['population_agreement']:.2f}")
            print(f"Outliers: {result['outliers']}")
            print(f"Reasoning: {result['reasoning']}")
        
        # Test population health reporting
        engine = PopulationConsensusEngine()
        population = create_population_from_validation_results(test_results)
        
        # Simulate some history
        for _ in range(10):
            consensus = engine.calculate_population_consensus(population)
        
        health_report = engine.get_population_health_report()
        print(f"\nPOPULATION HEALTH REPORT:")
        print(json.dumps(health_report, indent=2))
    
    test_population_consensus()