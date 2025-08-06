// Analytics-specific types and interfaces

export interface SessionFeature {
  id?: number;
  sessionId: string;
  featureName: string;
  featureValue: number;
  computedAt: number;
}

export interface SessionPrediction {
  id?: number;
  sessionId: string;
  predictionType: string;
  predictedValue: number;
  confidence: number;
  createdAt: number;
}

export interface SessionInsight {
  id?: number;
  sessionId?: string;
  insightType: string;
  insightData: Record<string, any>;
  priority: 'low' | 'medium' | 'high' | 'critical';
  createdAt: number;
}

export interface SessionMetrics {
  sessionId: string;
  duration?: number;
  totalTokens: number;
  tokensPerMinute: number;
  eventCount: number;
  toolUsageCount: number;
  promptCount: number;
  startTime: number;
  endTime?: number;
  isActive: boolean;
  qualityScore?: number;
}

export interface PredictionModel {
  modelType: 'session-duration' | 'token-velocity' | 'pattern-classifier' | 'anomaly-detector';
  version: string;
  accuracy: number;
  lastTrained: number;
  trainingDataSize: number;
}

export interface FeatureVector {
  sessionId: string;
  features: {
    // Time-based features
    hourOfDay: number;
    dayOfWeek: number;
    timeSinceLastSession: number;
    
    // Session features
    averageSessionDuration: number;
    recentTokenVelocity: number;
    toolUsageFrequency: number;
    promptComplexity: number;
    
    // Behavioral features
    sessionGaps: number;
    productivityPattern: number;
    errorRate: number;
    iterationCount: number;
  };
}

export interface UsagePattern {
  patternId: string;
  patternType: 'deep-work' | 'exploration' | 'debugging' | 'learning' | 'rapid-iteration';
  confidence: number;
  characteristics: {
    avgSessionDuration: number;
    tokenVelocity: number;
    toolUsageRatio: number;
    pauseFrequency: number;
  };
}

export interface AnomalyAlert {
  id: string;
  sessionId: string;
  anomalyType: 'duration' | 'token-usage' | 'pattern' | 'performance';
  severity: 'low' | 'medium' | 'high';
  description: string;
  recommendedAction?: string;
  detectedAt: number;
}

export interface OptimizationRecommendation {
  id: string;
  type: 'efficiency' | 'cost' | 'productivity' | 'health';
  title: string;
  description: string;
  potentialImpact: 'low' | 'medium' | 'high';
  actionItems: string[];
  basedOnData: {
    sessionCount: number;
    timespan: string;
    keyMetrics: Record<string, number>;
  };
}

export interface AnalyticsQuery {
  sessionIds?: string[];
  timeRange?: {
    start: number;
    end: number;
  };
  eventTypes?: string[];
  limit?: number;
  aggregation?: 'hourly' | 'daily' | 'weekly';
}

export interface TimeSeriesData {
  timestamp: number;
  value: number;
  metadata?: Record<string, any>;
}

export interface SessionQualityMetrics {
  sessionId: string;
  qualityScore: number; // 0-100
  factors: {
    consistency: number;
    efficiency: number;
    focusTime: number;
    errorRate: number;
    completionRate: number;
  };
  suggestions: string[];
}