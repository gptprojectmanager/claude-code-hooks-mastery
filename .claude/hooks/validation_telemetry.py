#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "asyncio",
#     "json",
#     "typing-extensions",
#     "httpx",
#     "numpy"
# ]
# ///

"""
Enhanced Validation Telemetry System
====================================

This module implements enhanced telemetry integration for the collective
intelligence validation system, following patterns from enhanced-telemetry-collector.sh
in claude-code-agentic-scripts.

Key Features:
- Discovery pattern recording for collective learning
- Validation performance tracking and analysis
- Pattern detection for validation improvements
- Integration with existing telemetry infrastructure
- Real-time validation metrics collection
"""

import asyncio
import json
import time
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ValidationDiscovery:
    """Discovery pattern detected during validation"""
    discovery_type: str
    pattern_data: Dict[str, Any]
    confidence_score: float
    impact_score: float
    validation_context: Dict[str, Any]
    timestamp: str
    source_models: List[str]


@dataclass
class ValidationPattern:
    """Pattern detected across multiple validation events"""
    pattern_type: str
    pattern_signature: str
    occurrence_count: int
    effectiveness_score: float
    first_detected: str
    last_updated: str
    contributing_models: List[str]
    context_factors: Dict[str, Any]


@dataclass
class ValidationMetrics:
    """Comprehensive validation performance metrics"""
    total_validations: int
    ensemble_validations: int
    average_response_time: float
    average_consensus_score: float
    model_usage_distribution: Dict[str, int]
    discovery_count: int
    pattern_count: int
    success_rate: float
    confidence_distribution: Dict[str, float]


class ValidationTelemetryCollector:
    """
    Enhanced telemetry collector for validation system following
    enhanced-telemetry-collector.sh patterns
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Storage paths
        self.telemetry_dir = Path(__file__).parent / "utils" / "validation_telemetry"
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        # Telemetry data
        self.discoveries = []
        self.patterns_detected = {}
        self.validation_events = []
        self.performance_metrics = {}
        
        # Batch processing
        self.telemetry_batch = []
        self.batch_size = self.config.get("batch_size", 10)
        
        # Load existing data
        self._load_telemetry_data()
        
        # Initialize telemetry session
        self.session_id = f"validation_{int(time.time())}"
        self.session_start = time.time()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default telemetry configuration"""
        return {
            "enabled": os.getenv("TELEMETRY_ENABLED", "true").lower() == "true",
            "batch_size": int(os.getenv("TELEMETRY_BATCH_SIZE", "10")),
            "flush_interval": int(os.getenv("TELEMETRY_FLUSH_INTERVAL", "30")),
            "discovery_confidence_threshold": 0.5,
            "pattern_occurrence_threshold": 3,
            "performance_window_size": 100,
            "enable_external_reporting": True
        }
    
    def _load_telemetry_data(self):
        """Load existing telemetry data"""
        try:
            # Load discoveries
            discoveries_file = self.telemetry_dir / "validation_discoveries.json"
            if discoveries_file.exists():
                with open(discoveries_file, 'r') as f:
                    data = json.load(f)
                    self.discoveries = [
                        ValidationDiscovery(**item) for item in data.get("discoveries", [])
                    ]
            
            # Load patterns
            patterns_file = self.telemetry_dir / "validation_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    self.patterns_detected = {
                        k: ValidationPattern(**v) for k, v in data.get("patterns", {}).items()
                    }
            
            # Load recent validation events
            events_file = self.telemetry_dir / "validation_events.json"
            if events_file.exists():
                with open(events_file, 'r') as f:
                    self.validation_events = json.load(f).get("events", [])[-100:]  # Keep recent
            
        except Exception as e:
            logger.warning(f"Could not load telemetry data: {e}")
    
    def record_validation_event(self, validation_data: Dict[str, Any]):
        """Record a validation event for telemetry analysis"""
        if not self.config["enabled"]:
            return
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "validation_event",
            "data": validation_data
        }
        
        self.validation_events.append(event)
        self.telemetry_batch.append(event)
        
        # Auto-flush if batch is full
        if len(self.telemetry_batch) >= self.batch_size:
            asyncio.create_task(self.flush_telemetry_batch())
        
        # Analyze for patterns and discoveries
        self._analyze_validation_event(validation_data)
    
    def record_discovery(self, discovery_type: str, pattern_data: Dict[str, Any], 
                        confidence: float, impact: float, 
                        validation_context: Dict[str, Any] = None,
                        source_models: List[str] = None):
        """
        Record a discovery following enhanced-telemetry-collector.sh patterns
        """
        if not self.config["enabled"] or confidence < self.config["discovery_confidence_threshold"]:
            return
        
        discovery = ValidationDiscovery(
            discovery_type=discovery_type,
            pattern_data=pattern_data,
            confidence_score=confidence,
            impact_score=impact,
            validation_context=validation_context or {},
            timestamp=datetime.now().isoformat(),
            source_models=source_models or []
        )
        
        self.discoveries.append(discovery)
        
        logger.info(f"Discovery recorded: {discovery_type} (confidence: {confidence:.2f}, impact: {impact:.2f})")
        
        # Save discoveries incrementally
        self._save_discoveries()
    
    def record_pattern(self, pattern_type: str, pattern_signature: str, 
                      occurrence_count: int = 1, effectiveness: float = 0.5,
                      contributing_models: List[str] = None,
                      context_factors: Dict[str, Any] = None):
        """
        Record pattern detection following enhanced-telemetry-collector.sh patterns
        """
        if not self.config["enabled"]:
            return
        
        pattern_key = f"{pattern_type}_{hash(pattern_signature) % 10000}"
        current_time = datetime.now().isoformat()
        
        if pattern_key in self.patterns_detected:
            # Update existing pattern
            existing_pattern = self.patterns_detected[pattern_key]
            existing_pattern.occurrence_count += occurrence_count
            existing_pattern.effectiveness_score = (
                existing_pattern.effectiveness_score * 0.8 + effectiveness * 0.2
            )
            existing_pattern.last_updated = current_time
            
            # Update contributing models
            if contributing_models:
                existing_models = set(existing_pattern.contributing_models)
                existing_models.update(contributing_models)
                existing_pattern.contributing_models = list(existing_models)
        else:
            # Create new pattern
            self.patterns_detected[pattern_key] = ValidationPattern(
                pattern_type=pattern_type,
                pattern_signature=pattern_signature,
                occurrence_count=occurrence_count,
                effectiveness_score=effectiveness,
                first_detected=current_time,
                last_updated=current_time,
                contributing_models=contributing_models or [],
                context_factors=context_factors or {}
            )
        
        logger.info(f"Pattern recorded: {pattern_type} (occurrences: {self.patterns_detected[pattern_key].occurrence_count})")
        
        # Save patterns incrementally
        self._save_patterns()
    
    def _analyze_validation_event(self, validation_data: Dict[str, Any]):
        """Analyze validation event for automatic pattern and discovery detection"""
        try:
            # Extract key metrics
            ensemble_data = validation_data.get("ensemble_validation", {})
            
            if isinstance(ensemble_data, str):
                return  # Skip if ensemble validation failed
            
            consensus_score = ensemble_data.get("consensus_score", 0)
            models_used = ensemble_data.get("models_used", [])
            response_time = ensemble_data.get("response_time", 0)
            diversity_score = ensemble_data.get("diversity_score", 0)
            outliers = ensemble_data.get("outliers", [])
            
            # Pattern 1: High consensus with low diversity (potential groupthink)
            if consensus_score > 85 and diversity_score < 0.1 and len(models_used) > 2:
                self.record_pattern(
                    pattern_type="low_diversity_consensus",
                    pattern_signature=f"consensus_{int(consensus_score)}_diversity_{int(diversity_score*100)}",
                    effectiveness=0.6,  # Moderate effectiveness - might miss edge cases
                    contributing_models=models_used,
                    context_factors={"consensus_score": consensus_score, "diversity_score": diversity_score}
                )
            
            # Pattern 2: High diversity with good consensus (ideal validation)
            if consensus_score > 80 and diversity_score > 0.3 and len(outliers) <= 1:
                self.record_discovery(
                    discovery_type="optimal_validation_conditions",
                    pattern_data={
                        "consensus_score": consensus_score,
                        "diversity_score": diversity_score,
                        "model_count": len(models_used),
                        "outlier_count": len(outliers)
                    },
                    confidence=0.85,
                    impact=0.9,
                    validation_context={"models": models_used, "response_time": response_time},
                    source_models=models_used
                )
            
            # Pattern 3: Fast consensus (efficiency discovery)
            if response_time < 1.0 and consensus_score > 75 and len(models_used) >= 3:
                self.record_discovery(
                    discovery_type="efficient_validation_pattern",
                    pattern_data={
                        "response_time": response_time,
                        "consensus_score": consensus_score,
                        "efficiency_ratio": consensus_score / response_time
                    },
                    confidence=0.75,
                    impact=0.7,
                    validation_context={"models": models_used},
                    source_models=models_used
                )
            
            # Pattern 4: Outlier detection pattern
            if len(outliers) > 0 and len(models_used) > 3:
                outlier_models = [outlier.split('_')[0] for outlier in outliers]
                self.record_pattern(
                    pattern_type="model_outlier_tendency",
                    pattern_signature=f"outlier_models_{'_'.join(sorted(outlier_models))}",
                    effectiveness=0.8,  # High effectiveness for identifying problematic models
                    contributing_models=outlier_models,
                    context_factors={"outlier_count": len(outliers), "total_models": len(models_used)}
                )
            
            # Pattern 5: Consensus improvement over time
            recent_scores = [event["data"].get("ensemble_validation", {}).get("consensus_score", 0) 
                           for event in self.validation_events[-10:] 
                           if isinstance(event["data"].get("ensemble_validation"), dict)]
            
            if len(recent_scores) >= 5:
                trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
                if trend > 2.0:  # Improving trend
                    self.record_discovery(
                        discovery_type="validation_quality_improvement",
                        pattern_data={
                            "trend_slope": float(trend),
                            "recent_average": float(np.mean(recent_scores)),
                            "improvement_rate": float(trend * len(recent_scores))
                        },
                        confidence=0.8,
                        impact=0.8,
                        validation_context={"recent_validations": len(recent_scores)}
                    )
            
        except Exception as e:
            logger.warning(f"Failed to analyze validation event: {e}")
    
    def process_discoveries(self) -> List[Dict[str, Any]]:
        """
        Process and return discoveries for external reporting
        Following enhanced-telemetry-collector.sh patterns
        """
        if not self.discoveries:
            return []
        
        # Group discoveries by type and analyze trends
        discovery_groups = {}
        for discovery in self.discoveries[-50:]:  # Process recent discoveries
            discovery_type = discovery.discovery_type
            if discovery_type not in discovery_groups:
                discovery_groups[discovery_type] = []
            discovery_groups[discovery_type].append(discovery)
        
        processed_discoveries = []
        for discovery_type, group in discovery_groups.items():
            if len(group) >= 2:  # Pattern requires multiple occurrences
                avg_confidence = np.mean([d.confidence_score for d in group])
                avg_impact = np.mean([d.impact_score for d in group])
                
                processed_discoveries.append({
                    "discovery_type": discovery_type,
                    "occurrence_count": len(group),
                    "average_confidence": avg_confidence,
                    "average_impact": avg_impact,
                    "latest_timestamp": group[-1].timestamp,
                    "pattern_strength": len(group) * avg_confidence * avg_impact,
                    "contributing_models": list(set().union(*[d.source_models for d in group])),
                    "representative_data": group[-1].pattern_data
                })
        
        # Sort by pattern strength
        processed_discoveries.sort(key=lambda x: x["pattern_strength"], reverse=True)
        
        return processed_discoveries
    
    def calculate_performance_metrics(self) -> ValidationMetrics:
        """Calculate comprehensive performance metrics"""
        if not self.validation_events:
            return ValidationMetrics(0, 0, 0.0, 0.0, {}, 0, 0, 0.0, {})
        
        recent_events = self.validation_events[-self.config["performance_window_size"]:]
        
        # Basic counts
        total_validations = len(recent_events)
        ensemble_validations = sum(1 for event in recent_events 
                                 if isinstance(event["data"].get("ensemble_validation"), dict))
        
        # Performance metrics
        response_times = []
        consensus_scores = []
        model_usage = {}
        confidences = []
        
        for event in recent_events:
            ensemble_data = event["data"].get("ensemble_validation", {})
            if isinstance(ensemble_data, dict):
                if "response_time" in ensemble_data:
                    response_times.append(ensemble_data["response_time"])
                
                if "consensus_score" in ensemble_data:
                    consensus_scores.append(ensemble_data["consensus_score"])
                
                if "confidence_level" in ensemble_data:
                    confidences.append(ensemble_data["confidence_level"])
                
                for model in ensemble_data.get("models_used", []):
                    model_usage[model] = model_usage.get(model, 0) + 1
        
        avg_response_time = np.mean(response_times) if response_times else 0.0
        avg_consensus_score = np.mean(consensus_scores) if consensus_scores else 0.0
        
        # Success rate (consensus score > 70)
        success_count = sum(1 for score in consensus_scores if score > 70)
        success_rate = success_count / len(consensus_scores) if consensus_scores else 0.0
        
        # Confidence distribution
        confidence_dist = {}
        if confidences:
            confidence_dist = {
                "mean": float(np.mean(confidences)),
                "std": float(np.std(confidences)),
                "min": float(np.min(confidences)),
                "max": float(np.max(confidences))
            }
        
        return ValidationMetrics(
            total_validations=total_validations,
            ensemble_validations=ensemble_validations,
            average_response_time=avg_response_time,
            average_consensus_score=avg_consensus_score,
            model_usage_distribution=model_usage,
            discovery_count=len(self.discoveries),
            pattern_count=len(self.patterns_detected),
            success_rate=success_rate,
            confidence_distribution=confidence_dist
        )
    
    async def flush_telemetry_batch(self):
        """Flush telemetry batch to external systems"""
        if not self.telemetry_batch:
            return
        
        try:
            # Process discoveries and patterns first
            discoveries = self.process_discoveries()
            
            # Create telemetry payload
            payload = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "validation_events": self.telemetry_batch,
                "discoveries": discoveries,
                "patterns": {k: asdict(v) for k, v in self.patterns_detected.items()},
                "performance_metrics": asdict(self.calculate_performance_metrics())
            }
            
            # Send to external systems if configured
            if self.config.get("enable_external_reporting"):
                await self._send_to_external_systems(payload)
            
            # Save locally
            self._save_telemetry_batch(payload)
            
            # Clear batch
            self.telemetry_batch = []
            
            logger.info(f"Telemetry batch flushed: {len(payload['validation_events'])} events")
            
        except Exception as e:
            logger.error(f"Failed to flush telemetry batch: {e}")
    
    async def _send_to_external_systems(self, payload: Dict[str, Any]):
        """Send telemetry to external systems"""
        # Check for Supabase configuration
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if supabase_url and supabase_key:
            try:
                import httpx
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{supabase_url}/rest/v1/validation_telemetry",
                        headers={
                            "apikey": supabase_key,
                            "Authorization": f"Bearer {supabase_key}",
                            "Content-Type": "application/json",
                            "Prefer": "return=minimal"
                        },
                        json=payload
                    )
                    
                    if response.status_code < 300:
                        logger.info("Telemetry sent to Supabase successfully")
                    else:
                        logger.warning(f"Supabase telemetry failed: {response.status_code}")
                        
            except Exception as e:
                logger.warning(f"Failed to send telemetry to Supabase: {e}")
        
        # Check for other telemetry endpoints
        telemetry_url = os.getenv('TELEMETRY_ENDPOINT')
        if telemetry_url:
            try:
                import httpx
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        telemetry_url,
                        headers={"Content-Type": "application/json"},
                        json=payload
                    )
                    
                    if response.status_code < 300:
                        logger.info("Telemetry sent to external endpoint successfully")
                        
            except Exception as e:
                logger.warning(f"Failed to send telemetry to external endpoint: {e}")
    
    def _save_telemetry_batch(self, payload: Dict[str, Any]):
        """Save telemetry batch locally"""
        try:
            batch_file = self.telemetry_dir / f"telemetry_batch_{int(time.time())}.json"
            with open(batch_file, 'w') as f:
                json.dump(payload, f, indent=2)
            
            # Clean up old batch files (keep only last 10)
            batch_files = sorted(self.telemetry_dir.glob("telemetry_batch_*.json"))
            for old_file in batch_files[:-10]:
                old_file.unlink()
                
        except Exception as e:
            logger.error(f"Failed to save telemetry batch: {e}")
    
    def _save_discoveries(self):
        """Save discoveries to disk"""
        try:
            discoveries_file = self.telemetry_dir / "validation_discoveries.json"
            data = {
                "discoveries": [asdict(d) for d in self.discoveries[-500:]],  # Keep recent
                "last_updated": datetime.now().isoformat()
            }
            
            with open(discoveries_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save discoveries: {e}")
    
    def _save_patterns(self):
        """Save patterns to disk"""
        try:
            patterns_file = self.telemetry_dir / "validation_patterns.json"
            data = {
                "patterns": {k: asdict(v) for k, v in self.patterns_detected.items()},
                "last_updated": datetime.now().isoformat()
            }
            
            with open(patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def get_telemetry_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive telemetry dashboard"""
        metrics = self.calculate_performance_metrics()
        discoveries = self.process_discoveries()
        
        # Recent patterns (last 7 days)
        recent_patterns = []
        week_ago = time.time() - (7 * 24 * 3600)
        
        for pattern_key, pattern in self.patterns_detected.items():
            if time.mktime(time.strptime(pattern.last_updated[:19], "%Y-%m-%dT%H:%M:%S")) > week_ago:
                recent_patterns.append({
                    "type": pattern.pattern_type,
                    "signature": pattern.pattern_signature[:50] + "..." if len(pattern.pattern_signature) > 50 else pattern.pattern_signature,
                    "occurrences": pattern.occurrence_count,
                    "effectiveness": pattern.effectiveness_score,
                    "models": pattern.contributing_models
                })
        
        return {
            "session_info": {
                "session_id": self.session_id,
                "session_duration": time.time() - self.session_start,
                "batch_size": len(self.telemetry_batch)
            },
            "performance_metrics": asdict(metrics),
            "recent_discoveries": discoveries[:10],  # Top 10 discoveries
            "recent_patterns": recent_patterns,
            "system_health": {
                "telemetry_enabled": self.config["enabled"],
                "total_discoveries": len(self.discoveries),
                "total_patterns": len(self.patterns_detected),
                "last_flush": datetime.now().isoformat()
            }
        }
    
    async def cleanup(self):
        """Cleanup telemetry session"""
        # Flush remaining telemetry
        if self.telemetry_batch:
            await self.flush_telemetry_batch()
        
        # Save final state
        self._save_discoveries()
        self._save_patterns()
        
        # Save validation events
        try:
            events_file = self.telemetry_dir / "validation_events.json"
            data = {
                "events": self.validation_events[-100:],  # Keep recent
                "last_updated": datetime.now().isoformat()
            }
            
            with open(events_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save validation events: {e}")


# Global telemetry collector instance
_telemetry_collector = None


def get_telemetry_collector() -> ValidationTelemetryCollector:
    """Get global telemetry collector instance"""
    global _telemetry_collector
    if _telemetry_collector is None:
        _telemetry_collector = ValidationTelemetryCollector()
    return _telemetry_collector


# Convenience functions for integration
def record_validation_event(validation_data: Dict[str, Any]):
    """Record validation event"""
    collector = get_telemetry_collector()
    collector.record_validation_event(validation_data)


def record_validation_discovery(discovery_type: str, pattern_data: Dict[str, Any], 
                               confidence: float, impact: float, 
                               validation_context: Dict[str, Any] = None,
                               source_models: List[str] = None):
    """Record validation discovery"""
    collector = get_telemetry_collector()
    collector.record_discovery(discovery_type, pattern_data, confidence, impact, 
                              validation_context, source_models)


def record_validation_pattern(pattern_type: str, pattern_signature: str, 
                            occurrence_count: int = 1, effectiveness: float = 0.5,
                            contributing_models: List[str] = None):
    """Record validation pattern"""
    collector = get_telemetry_collector()
    collector.record_pattern(pattern_type, pattern_signature, occurrence_count, 
                           effectiveness, contributing_models)


def get_validation_dashboard() -> Dict[str, Any]:
    """Get validation telemetry dashboard"""
    collector = get_telemetry_collector()
    return collector.get_telemetry_dashboard()


async def flush_validation_telemetry():
    """Flush validation telemetry batch"""
    collector = get_telemetry_collector()
    await collector.flush_telemetry_batch()


async def cleanup_validation_telemetry():
    """Cleanup validation telemetry"""
    collector = get_telemetry_collector()
    await collector.cleanup()


if __name__ == "__main__":
    """Test the validation telemetry system"""
    async def test_validation_telemetry():
        collector = ValidationTelemetryCollector()
        
        # Simulate validation events
        test_validations = [
            {
                "ensemble_validation": {
                    "consensus_score": 85.0,
                    "models_used": ["claude", "gemini", "gpt"],
                    "response_time": 1.2,
                    "diversity_score": 0.4,
                    "outliers": [],
                    "confidence_level": 0.9
                }
            },
            {
                "ensemble_validation": {
                    "consensus_score": 92.0,
                    "models_used": ["claude", "gemini"],
                    "response_time": 0.8,
                    "diversity_score": 0.1,  # Low diversity
                    "outliers": [],
                    "confidence_level": 0.95
                }
            },
            {
                "ensemble_validation": {
                    "consensus_score": 78.0,
                    "models_used": ["claude", "gemini", "gpt", "local"],
                    "response_time": 2.1,
                    "diversity_score": 0.6,
                    "outliers": ["local_model_1"],
                    "confidence_level": 0.8
                }
            }
        ]
        
        # Record events
        for i, validation in enumerate(test_validations):
            collector.record_validation_event(validation)
            await asyncio.sleep(0.1)  # Small delay
        
        # Process discoveries
        discoveries = collector.process_discoveries()
        print("DISCOVERIES:")
        for discovery in discoveries:
            print(f"- {discovery['discovery_type']}: {discovery['occurrence_count']} occurrences")
        
        # Get dashboard
        dashboard = collector.get_telemetry_dashboard()
        print("\nTELEMETRY DASHBOARD:")
        print(json.dumps(dashboard, indent=2, default=str))
        
        # Cleanup
        await collector.cleanup()
    
    asyncio.run(test_validation_telemetry())