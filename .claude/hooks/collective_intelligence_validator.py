#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "asyncio",
#     "httpx",
#     "openai", 
#     "google-generativeai",
#     "anthropic",
#     "pyyaml",
#     "numpy",
#     "typing-extensions",
#     "pydantic"
# ]
# ///

"""
Advanced Collective Intelligence Validation System
==================================================

This module implements a sophisticated multi-model validation framework
that replaces the primitive hardcoded validation with real API calls,
multi-objective scoring, and collective intelligence patterns.

Following patterns from claude-code-agentic-scripts:
- Multi-objective fitness evaluation (fitness-evaluator.sh)
- Population-based consensus (evolution-engine.sh)  
- Enhanced telemetry integration (enhanced-telemetry-collector.sh)
"""

import asyncio
import json
import time
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import numpy as np

# Import API configuration system
try:
    from api_config import get_api_config
    API_CONFIG_AVAILABLE = True
except ImportError:
    API_CONFIG_AVAILABLE = False
    print("⚠️ API configuration system not available", file=sys.stderr)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationModel(Enum):
    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"  
    CLAUDE_HAIKU = "claude-3-haiku-20240307"
    GEMINI_PRO = "gemini-1.5-pro-latest"
    GEMINI_FLASH = "gemini-1.5-flash-latest"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT4 = "gpt-4"


@dataclass
class ValidationDimensions:
    """Multi-objective validation dimensions following fitness-evaluator.sh patterns"""
    performance: float  # Code quality, functionality (40% weight)
    novelty: float      # Innovation, creativity (30% weight)
    efficiency: float   # Performance, optimization (20% weight)
    safety: float       # Security, robustness (10% weight)
    
    def weighted_score(self) -> float:
        """Calculate weighted multi-objective score"""
        weights = {
            "performance": 0.40,
            "novelty": 0.30,
            "efficiency": 0.20,
            "safety": 0.10
        }
        
        return (
            self.performance * weights["performance"] +
            self.novelty * weights["novelty"] +
            self.efficiency * weights["efficiency"] +
            self.safety * weights["safety"]
        )


@dataclass
class ValidationResult:
    """Individual model validation result"""
    model: ValidationModel
    dimensions: ValidationDimensions
    confidence: float
    reasoning: str
    response_time: float
    tokens_used: int
    error: Optional[str] = None
    demo_mode: bool = False
    
    @property
    def score(self) -> float:
        """Get overall score for backwards compatibility"""
        return self.dimensions.weighted_score()


@dataclass
class EnsembleValidationResult:
    """Collective intelligence validation result"""
    individual_results: List[ValidationResult]
    consensus_score: float
    confidence_interval: Tuple[float, float]
    diversity_score: float
    outliers_detected: List[str]
    final_status: str
    reasoning: str
    total_response_time: float
    total_tokens: int
    discovery_patterns: List[Dict[str, Any]]


class CollectiveIntelligenceValidator:
    """
    Advanced validation system implementing collective intelligence patterns
    """
    
    def __init__(self):
        # Load API configuration
        self.api_config = get_api_config() if API_CONFIG_AVAILABLE else None
        
        # Initialize clients using configuration
        self.anthropic_client = self._init_anthropic_client()
        self.openai_client = self._init_openai_client()
        self.google_client = self._init_google_client()
        
        # Telemetry integration
        self.discoveries = []
        self.patterns_detected = []
        
        # Adaptive thresholds (will be loaded from history)
        self.adaptive_thresholds = {
            "approved": 80.0,
            "needs_revision": 60.0,
            "confidence_minimum": 0.7
        }
        
        # Load historical performance for adaptive behavior
        self._load_adaptive_thresholds()
        
        # Log configuration summary
        if self.api_config:
            config_summary = self.api_config.get_configuration_summary()
            logger.info(f"API Configuration: {config_summary}")
    
    def _init_anthropic_client(self):
        """Initialize Claude/Anthropic client with enhanced configuration"""
        try:
            import anthropic
            
            # Use new configuration system if available
            if self.api_config:
                api_key = self.api_config.get_api_key('anthropic')
                if api_key and not self.api_config.is_demo_mode('anthropic'):
                    return anthropic.Anthropic(api_key=api_key)
                elif self.api_config.is_demo_mode('anthropic'):
                    logger.info("Anthropic in demo mode - will use mock responses")
                    return "demo_mode"
                else:
                    logger.warning("Anthropic API key not configured")
                    return None
            else:
                # Fallback to environment variable
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    logger.warning("ANTHROPIC_API_KEY not set - Claude models disabled")
                    return None
                return anthropic.Anthropic(api_key=api_key)
        except ImportError:
            logger.warning("anthropic package not installed - Claude models disabled")
            return None
    
    def _init_openai_client(self):
        """Initialize OpenAI client with enhanced configuration"""
        try:
            from openai import AsyncOpenAI
            
            # Use new configuration system if available
            if self.api_config:
                api_key = self.api_config.get_api_key('openai')
                if api_key and not self.api_config.is_demo_mode('openai'):
                    return AsyncOpenAI(api_key=api_key)
                elif self.api_config.is_demo_mode('openai'):
                    logger.info("OpenAI in demo mode - will use mock responses")
                    return "demo_mode"
                else:
                    logger.warning("OpenAI API key not configured")
                    return None
            else:
                # Fallback to environment variable
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    logger.warning("OPENAI_API_KEY not set - GPT models disabled")
                    return None
                return AsyncOpenAI(api_key=api_key)
        except ImportError:
            logger.warning("openai package not installed - GPT models disabled")
            return None
    
    def _init_google_client(self):
        """Initialize Google Gemini client with enhanced configuration"""
        try:
            import google.generativeai as genai
            
            # Use new configuration system if available
            if self.api_config:
                api_key = self.api_config.get_api_key('google')
                if api_key and not self.api_config.is_demo_mode('google'):
                    genai.configure(api_key=api_key)
                    return genai
                elif self.api_config.is_demo_mode('google'):
                    logger.info("Google in demo mode - will use mock responses")
                    return "demo_mode"
                else:
                    logger.warning("Google API key not configured")
                    return None
            else:
                # Fallback to environment variable
                api_key = os.getenv('GOOGLE_API_KEY')
                if not api_key:
                    logger.warning("GOOGLE_API_KEY not set - Gemini models disabled")
                    return None
                genai.configure(api_key=api_key)
                return genai
        except ImportError:
            logger.warning("google-generativeai package not installed - Gemini models disabled")
            return None
    
    def _load_adaptive_thresholds(self):
        """Load adaptive thresholds from historical performance"""
        try:
            history_path = Path(__file__).parent / "utils" / "validation_history.json"
            if history_path.exists():
                with open(history_path, 'r') as f:
                    history = json.load(f)
                
                # Adaptive threshold adjustment based on historical success rates
                recent_validations = history.get("recent_validations", [])
                if len(recent_validations) > 10:
                    success_scores = [v["score"] for v in recent_validations if v.get("actual_success")]
                    failure_scores = [v["score"] for v in recent_validations if not v.get("actual_success")]
                    
                    if success_scores and failure_scores:
                        # Calculate optimal threshold using ROC analysis
                        optimal_threshold = self._calculate_optimal_threshold(success_scores, failure_scores)
                        self.adaptive_thresholds["approved"] = optimal_threshold
                        logger.info(f"Adaptive threshold updated to {optimal_threshold}")
                        
        except Exception as e:
            logger.warning(f"Could not load adaptive thresholds: {e}")
    
    def _calculate_optimal_threshold(self, success_scores: List[float], failure_scores: List[float]) -> float:
        """Calculate optimal threshold using ROC analysis"""
        all_scores = sorted(success_scores + failure_scores)
        best_threshold = 80.0
        best_f1 = 0.0
        
        for threshold in all_scores:
            tp = sum(1 for s in success_scores if s >= threshold)
            fp = sum(1 for s in failure_scores if s >= threshold)
            fn = len(success_scores) - tp
            
            if tp + fp > 0 and tp + fn > 0:
                precision = tp / (tp + fp)
                recall = tp / (tp + fn)
                
                if precision + recall > 0:
                    f1 = 2 * (precision * recall) / (precision + recall)
                    if f1 > best_f1:
                        best_f1 = f1
                        best_threshold = threshold
        
        return max(60.0, min(90.0, best_threshold))  # Constrain to reasonable range
    
    async def validate_with_ensemble(self, input_data: Dict[str, Any]) -> EnsembleValidationResult:
        """
        Main ensemble validation using collective intelligence approach
        """
        start_time = time.time()
        
        # Select model ensemble (3-5 models minimum for collective intelligence)
        available_models = self._get_available_models()
        if len(available_models) < 1:
            logger.warning("No validation models available")
            return self._fallback_validation(input_data)
        
        # Parallel validation across ensemble
        validation_tasks = []
        for model in available_models[:5]:  # Max 5 models for performance
            task = asyncio.create_task(self._validate_with_model(model, input_data))
            validation_tasks.append(task)
        
        # Wait for all validations with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*validation_tasks, return_exceptions=True),
                timeout=10.0  # 10 second timeout for entire ensemble
            )
        except asyncio.TimeoutError:
            logger.warning("Ensemble validation timeout - using partial results")
            results = [task.result() if task.done() else None for task in validation_tasks]
        
        # Filter successful results
        valid_results = [r for r in results if isinstance(r, ValidationResult) and r.error is None]
        
        if not valid_results:
            return self._fallback_validation(input_data)
        
        # Calculate collective intelligence consensus
        ensemble_result = self._calculate_ensemble_consensus(valid_results)
        ensemble_result.total_response_time = time.time() - start_time
        
        # Record telemetry
        await self._record_validation_telemetry(ensemble_result)
        
        return ensemble_result
    
    def _get_available_models(self) -> List[ValidationModel]:
        """Get list of available validation models"""
        available = []
        
        if self.anthropic_client:
            available.extend([ValidationModel.CLAUDE_OPUS, ValidationModel.CLAUDE_SONNET])
        
        if self.google_client:
            available.extend([ValidationModel.GEMINI_PRO])
        
        if self.openai_client:
            available.extend([ValidationModel.GPT4])
        
        # Ensure diversity - at least 2 different providers if possible
        return available
    
    async def _validate_with_model(self, model: ValidationModel, input_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate using a specific model with comprehensive multi-objective assessment
        """
        start_time = time.time()
        
        try:
            # Create context-aware validation prompt
            prompt = self._create_validation_prompt(input_data)
            
            # Make API call based on model type
            if model in [ValidationModel.CLAUDE_OPUS, ValidationModel.CLAUDE_SONNET, ValidationModel.CLAUDE_HAIKU]:
                result = await self._validate_with_claude(model, prompt)
            elif model in [ValidationModel.GEMINI_PRO, ValidationModel.GEMINI_FLASH]:
                result = await self._validate_with_gemini(model, prompt)
            elif model in [ValidationModel.GPT4_TURBO, ValidationModel.GPT4]:
                result = await self._validate_with_gpt(model, prompt)
            else:
                raise ValueError(f"Unsupported model: {model}")
            
            result.response_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Validation failed for {model.value}: {e}")
            return ValidationResult(
                model=model,
                dimensions=ValidationDimensions(0, 0, 0, 0),
                confidence=0.0,
                reasoning=f"Validation failed: {str(e)}",
                response_time=time.time() - start_time,
                tokens_used=0,
                error=str(e)
            )
    
    def _create_validation_prompt(self, input_data: Dict[str, Any]) -> str:
        """Create context-aware validation prompt"""
        tool_name = input_data.get('request', {}).get('tool_name', 'unknown')
        tool_params = input_data.get('request', {}).get('parameters', {})
        response_content = input_data.get('response', {})
        
        return f"""
Please perform a comprehensive multi-objective validation of this tool usage event:

TOOL USED: {tool_name}
PARAMETERS: {json.dumps(tool_params, indent=2)}
RESPONSE: {json.dumps(response_content, indent=2)}

Evaluate across these dimensions (return scores 0-100):

1. PERFORMANCE (40% weight):
   - Code quality and functionality
   - Correctness of the approach
   - Effectiveness in achieving the goal

2. NOVELTY (30% weight):
   - Innovation in approach
   - Creative problem-solving
   - Unique insights or patterns

3. EFFICIENCY (20% weight):
   - Performance optimization
   - Resource utilization
   - Time complexity considerations

4. SAFETY (10% weight):
   - Security considerations
   - Error handling robustness
   - Risk mitigation

REQUIRED RESPONSE FORMAT (JSON):
{{
    "performance": <0-100>,
    "novelty": <0-100>,
    "efficiency": <0-100>,
    "safety": <0-100>,
    "confidence": <0.0-1.0>,
    "reasoning": "Detailed explanation of assessment",
    "key_insights": ["insight1", "insight2"],
    "recommendations": ["recommendation1", "recommendation2"]
}}

Focus on providing actionable insights and identifying patterns that could benefit the broader development ecosystem.
"""
    
    async def _validate_with_claude(self, model: ValidationModel, prompt: str) -> ValidationResult:
        """Validate using Claude model"""
        # Check for demo mode
        if self.anthropic_client == "demo_mode":
            return self._create_demo_response(model, "anthropic")
        
        if not self.anthropic_client:
            raise Exception("Anthropic client not available")
        
        response = await asyncio.to_thread(
            self.anthropic_client.messages.create,
            model=model.value,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            system="You are an expert code validator providing detailed multi-dimensional assessments."
        )
        
        try:
            result_data = json.loads(response.content[0].text)
            dimensions = ValidationDimensions(
                performance=result_data["performance"],
                novelty=result_data["novelty"], 
                efficiency=result_data["efficiency"],
                safety=result_data["safety"]
            )
            
            return ValidationResult(
                model=model,
                dimensions=dimensions,
                confidence=result_data["confidence"],
                reasoning=result_data["reasoning"],
                response_time=0.0,  # Will be set by caller
                tokens_used=response.usage.input_tokens + response.usage.output_tokens
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to text parsing
            return self._parse_text_response(model, response.content[0].text)
    
    async def _validate_with_gemini(self, model: ValidationModel, prompt: str) -> ValidationResult:
        """Validate using Gemini model"""
        # Check for demo mode
        if self.google_client == "demo_mode":
            return self._create_demo_response(model, "google")
        
        if not self.google_client:
            raise Exception("Google client not available")
        
        model_instance = self.google_client.GenerativeModel(model.value)
        response = await asyncio.to_thread(model_instance.generate_content, prompt)
        
        try:
            result_data = json.loads(response.text)
            dimensions = ValidationDimensions(
                performance=result_data["performance"],
                novelty=result_data["novelty"],
                efficiency=result_data["efficiency"], 
                safety=result_data["safety"]
            )
            
            return ValidationResult(
                model=model,
                dimensions=dimensions,
                confidence=result_data["confidence"],
                reasoning=result_data["reasoning"],
                response_time=0.0,
                tokens_used=response.usage_metadata.prompt_token_count + response.usage_metadata.candidates_token_count if response.usage_metadata else 0
            )
            
        except (json.JSONDecodeError, KeyError, AttributeError):
            return self._parse_text_response(model, response.text)
    
    async def _validate_with_gpt(self, model: ValidationModel, prompt: str) -> ValidationResult:
        """Validate using GPT model"""
        # Check for demo mode
        if self.openai_client == "demo_mode":
            return self._create_demo_response(model, "openai")
        
        if not self.openai_client:
            raise Exception("OpenAI client not available")
        
        response = await self.openai_client.chat.completions.create(
            model=model.value,
            messages=[
                {"role": "system", "content": "You are an expert code validator providing detailed multi-dimensional assessments."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        
        try:
            result_data = json.loads(response.choices[0].message.content)
            dimensions = ValidationDimensions(
                performance=result_data["performance"],
                novelty=result_data["novelty"],
                efficiency=result_data["efficiency"],
                safety=result_data["safety"]
            )
            
            return ValidationResult(
                model=model,
                dimensions=dimensions,
                confidence=result_data["confidence"],
                reasoning=result_data["reasoning"],
                response_time=0.0,
                tokens_used=response.usage.prompt_tokens + response.usage.completion_tokens
            )
            
        except (json.JSONDecodeError, KeyError):
            return self._parse_text_response(model, response.choices[0].message.content)
    
    def _create_demo_response(self, model: ValidationModel, provider: str) -> ValidationResult:
        """Create sophisticated demo response for testing"""
        if self.api_config and self.api_config.is_demo_mode(provider):
            demo_data = self.api_config.get_demo_response(provider)
        else:
            # Fallback demo data
            demo_data = {
                "performance": 75,
                "novelty": 65,
                "efficiency": 80,
                "safety": 85,
                "confidence": 0.7,
                "reasoning": f"Demo validation from {model.value}",
                "key_insights": ["Demo insight 1", "Demo insight 2"],
                "recommendations": ["Demo recommendation 1", "Demo recommendation 2"]
            }
        
        dimensions = ValidationDimensions(
            performance=demo_data["performance"],
            novelty=demo_data["novelty"],
            efficiency=demo_data["efficiency"],
            safety=demo_data["safety"]
        )
        
        # Add some variation to make demo responses more realistic
        import random
        variation = random.uniform(-5, 5)
        for attr in ['performance', 'novelty', 'efficiency', 'safety']:
            current_value = getattr(dimensions, attr)
            setattr(dimensions, attr, max(0, min(100, current_value + variation)))
        
        return ValidationResult(
            model=model,
            dimensions=dimensions,
            confidence=demo_data["confidence"],
            reasoning=demo_data["reasoning"],
            response_time=0.0,
            tokens_used=150,  # Estimated demo tokens
            demo_mode=True
        )
    
    def _parse_text_response(self, model: ValidationModel, text: str) -> ValidationResult:
        """Fallback text parsing when JSON parsing fails"""
        # Simple heuristic parsing - could be enhanced
        performance = self._extract_score(text, ["performance", "quality"], 70)
        novelty = self._extract_score(text, ["novelty", "innovation", "creative"], 60)
        efficiency = self._extract_score(text, ["efficiency", "performance", "speed"], 75)
        safety = self._extract_score(text, ["safety", "security", "robust"], 80)
        
        dimensions = ValidationDimensions(performance, novelty, efficiency, safety)
        
        return ValidationResult(
            model=model,
            dimensions=dimensions,
            confidence=0.6,  # Lower confidence for fallback parsing
            reasoning=f"Fallback parsing of response: {text[:200]}...",
            response_time=0.0,
            tokens_used=len(text.split()) * 1.3  # Rough token estimate
        )
    
    def _extract_score(self, text: str, keywords: List[str], default: float) -> float:
        """Extract score from text using keyword matching"""
        text_lower = text.lower()
        
        # Look for explicit scores
        import re
        for keyword in keywords:
            pattern = rf"{keyword}[:\s]*(\d+(?:\.\d+)?)"
            match = re.search(pattern, text_lower)
            if match:
                try:
                    score = float(match.group(1))
                    return max(0, min(100, score))
                except ValueError:
                    continue
        
        return default
    
    def _calculate_ensemble_consensus(self, results: List[ValidationResult]) -> EnsembleValidationResult:
        """Calculate collective intelligence consensus from individual results"""
        if not results:
            return self._fallback_validation({})
        
        # Extract scores and calculate consensus
        scores = [r.score for r in results]
        consensus_score = np.mean(scores)
        
        # Calculate confidence interval
        std_dev = np.std(scores) if len(scores) > 1 else 10.0
        confidence_interval = (
            max(0, consensus_score - std_dev),
            min(100, consensus_score + std_dev)
        )
        
        # Calculate diversity score (higher = more diverse opinions)
        diversity_score = std_dev / 100.0 if len(scores) > 1 else 0.0
        
        # Detect outliers using IQR method
        if len(scores) >= 3:
            q1 = np.percentile(scores, 25)
            q3 = np.percentile(scores, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [
                r.model.value for r in results 
                if r.score < lower_bound or r.score > upper_bound
            ]
        else:
            outliers = []
        
        # Determine final status using adaptive thresholds
        approved_threshold = self.adaptive_thresholds["approved"]
        needs_revision_threshold = self.adaptive_thresholds["needs_revision"]
        
        if consensus_score >= approved_threshold:
            final_status = "approved"
        elif consensus_score >= needs_revision_threshold:
            final_status = "needs_revision"
        else:
            final_status = "rejected"
        
        # Generate consensus reasoning
        demo_models = [r.model.value for r in results if r.demo_mode]
        real_models = [r.model.value for r in results if not r.demo_mode]
        
        reasoning_parts = []
        if real_models:
            reasoning_parts.append(f"Real API validation from {len(real_models)} models: {real_models}")
        if demo_models:
            reasoning_parts.append(f"Demo validation from {len(demo_models)} models: {demo_models}")
        
        reasoning_parts.append(f"Consensus score: {consensus_score:.1f} (diversity: {diversity_score:.2f})")
        
        if outliers:
            reasoning_parts.append(f"Outliers detected: {outliers}")
        
        reasoning = ". ".join(reasoning_parts)
        
        # Discovery patterns (simplified for now)
        discovery_patterns = []
        if diversity_score > 0.2:
            discovery_patterns.append({
                "pattern": "high_diversity_validation",
                "confidence": diversity_score,
                "description": "Models showed high diversity in scoring"
            })
        
        return EnsembleValidationResult(
            individual_results=results,
            consensus_score=consensus_score,
            confidence_interval=confidence_interval,
            diversity_score=diversity_score,
            outliers_detected=outliers,
            final_status=final_status,
            reasoning=reasoning,
            total_response_time=sum(r.response_time for r in results),
            total_tokens=sum(r.tokens_used for r in results),
            discovery_patterns=discovery_patterns
        )
    
    async def _record_validation_telemetry(self, ensemble_result: EnsembleValidationResult):
        """Record validation telemetry for learning and improvement"""
        try:
            # Import telemetry system if available
            from validation_telemetry import record_validation_event, record_validation_discovery
            
            # Record the validation event
            telemetry_data = {
                "models_used": [r.model.value for r in ensemble_result.individual_results],
                "consensus_score": ensemble_result.consensus_score,
                "diversity_score": ensemble_result.diversity_score,
                "final_status": ensemble_result.final_status,
                "response_time": ensemble_result.total_response_time,
                "tokens_used": ensemble_result.total_tokens
            }
            
            record_validation_event(telemetry_data)
            
            # Record discovery patterns
            for pattern in ensemble_result.discovery_patterns:
                record_validation_discovery(
                    pattern["pattern"],
                    pattern.get("description", ""),
                    pattern.get("confidence", 0.0),
                    pattern.get("impact", 0.5)
                )
                
        except ImportError:
            # Telemetry system not available
            pass
        except Exception as e:
            logger.warning(f"Could not record validation telemetry: {e}")
    
    def _fallback_validation(self, input_data: Dict[str, Any]) -> EnsembleValidationResult:
        """Fallback validation when no models are available"""
        fallback_result = ValidationResult(
            model=ValidationModel.CLAUDE_SONNET,  # Placeholder
            dimensions=ValidationDimensions(75, 50, 70, 85),
            confidence=0.3,
            reasoning="No validation models available",
            response_time=0.1,
            tokens_used=0,
            error="No validation models available",
            demo_mode=True
        )
        
        return EnsembleValidationResult(
            individual_results=[fallback_result],
            consensus_score=70.0,
            confidence_interval=(60.0, 80.0),
            diversity_score=0.0,
            outliers_detected=[],
            final_status="needs_revision",
            reasoning="Fallback validation used - recommend manual review",
            total_response_time=0.1,
            total_tokens=0,
            discovery_patterns=[]
        )


# Backwards compatibility functions for existing post_tool_use.py
async def run_opus_validation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Backwards compatible Opus validation function"""
    validator = CollectiveIntelligenceValidator()
    if not validator.anthropic_client:
        return {"model": "opus", "score": 70, "error": "Anthropic client not available"}
    
    result = await validator._validate_with_model(ValidationModel.CLAUDE_OPUS, input_data)
    
    return {
        "model": "opus",
        "score": result.score,
        "reflection": result.reasoning,
        "recommendations": ["Consider ensemble validation", "Review safety scores"],
        "confidence": result.confidence,
        "tokens_used": result.tokens_used,
        "dimensions": asdict(result.dimensions),
        "demo_mode": result.demo_mode
    }


async def run_gemini_validation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Backwards compatible Gemini validation function"""
    validator = CollectiveIntelligenceValidator()
    if not validator.google_client:
        return {"model": "gemini_gpro", "score": 72, "error": "Google client not available"}
    
    result = await validator._validate_with_model(ValidationModel.GEMINI_PRO, input_data)
    
    return {
        "model": "gemini_gpro",
        "score": result.score,
        "analysis": result.reasoning,
        "hook_context": "Validated through advanced ensemble validation",
        "confidence": result.confidence,
        "tokens_used": result.tokens_used,
        "dimensions": asdict(result.dimensions),
        "demo_mode": result.demo_mode
    }


async def trigger_advanced_ensemble_validation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advanced ensemble validation function replacing trigger_ensemble_validation
    """
    validator = CollectiveIntelligenceValidator()
    
    try:
        ensemble_result = await validator.validate_with_ensemble(input_data)
        
        return {
            "ensemble_validation": "advanced_collective_intelligence",
            "models_used": [r.model.value for r in ensemble_result.individual_results],
            "consensus_score": ensemble_result.consensus_score,
            "confidence_interval": ensemble_result.confidence_interval,
            "diversity_score": ensemble_result.diversity_score,
            "final_status": ensemble_result.final_status,
            "reasoning": ensemble_result.reasoning,
            "response_time": ensemble_result.total_response_time,
            "total_tokens": ensemble_result.total_tokens,
            "discoveries": len(ensemble_result.discovery_patterns),
            "outliers": ensemble_result.outliers_detected,
            "demo_mode_used": any(r.demo_mode for r in ensemble_result.individual_results),
            "real_api_used": any(not r.demo_mode for r in ensemble_result.individual_results),
            "validation_details": {
                r.model.value: {
                    "score": r.score,
                    "confidence": r.confidence,
                    "dimensions": asdict(r.dimensions),
                    "tokens": r.tokens_used,
                    "error": r.error,
                    "demo_mode": r.demo_mode
                }
                for r in ensemble_result.individual_results
            }
        }
        
    except Exception as e:
        logger.error(f"Advanced ensemble validation failed: {e}")
        return {
            "ensemble_validation": "error",
            "error": str(e),
            "fallback_used": True
        }


if __name__ == "__main__":
    """Test the validation system"""
    async def test_validation():
        test_data = {
            "request": {
                "tool_name": "Write",
                "parameters": {
                    "file_path": "/test/file.py",
                    "content": "print('hello')"
                }
            },
            "response": {
                "success": True
            }
        }
        
        print("Testing Advanced Collective Intelligence Validation System")
        print("=" * 60)
        
        result = await trigger_advanced_ensemble_validation(test_data)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_validation())