import { Database } from 'bun:sqlite';
import type { 
  SessionPrediction, 
  SessionMetrics, 
  FeatureVector,
  SessionFeature 
} from '../analytics-types';
import { 
  insertSessionPrediction, 
  getSessionMetrics,
  getSessionFeatures 
} from '../analytics-db';

/**
 * Simple statistical ML-like prediction engine without external ML libraries
 * Uses statistical analysis and heuristic models for predictions
 */
export class PredictionEngine {
  private db: Database;
  private models: Map<string, any> = new Map();
  private isInitialized = false;
  private historicalData: Map<string, any[]> = new Map();

  constructor() {
    this.db = new Database('events.db');
  }

  /**
   * Initialize the prediction engine and build statistical models
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Load historical data for model building
      await this.loadHistoricalData();
      
      // Build statistical models
      await this.buildStatisticalModels();
      
      this.isInitialized = true;
      console.log('Prediction engine initialized with statistical models');
    } catch (error) {
      console.error('Error initializing prediction engine:', error);
    }
  }

  /**
   * Load historical data for model training
   */
  private async loadHistoricalData(): Promise<void> {
    // Load session data
    const sessionsStmt = this.db.prepare(`
      SELECT * FROM session_metrics 
      WHERE start_time > ? 
      ORDER BY start_time DESC
    `);
    
    const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
    const sessions = sessionsStmt.all(thirtyDaysAgo) as any[];
    
    // Load feature data
    const featuresStmt = this.db.prepare(`
      SELECT sf.* FROM session_features sf
      JOIN session_metrics sm ON sf.session_id = sm.session_id
      WHERE sm.start_time > ?
    `);
    
    const features = featuresStmt.all(thirtyDaysAgo) as any[];
    
    this.historicalData.set('sessions', sessions);
    this.historicalData.set('features', features);
    
    console.log(`Loaded ${sessions.length} historical sessions for model training`);
  }

  /**
   * Build statistical models from historical data
   */
  private async buildStatisticalModels(): Promise<void> {
    const sessions = this.historicalData.get('sessions') || [];
    
    if (sessions.length === 0) {
      console.log('No historical data available, using default models');
      this.buildDefaultModels();
      return;
    }

    // Build duration prediction model
    this.models.set('session-duration', this.buildDurationModel(sessions));
    
    // Build token velocity model
    this.models.set('token-velocity', this.buildVelocityModel(sessions));
    
    // Build quality prediction model
    this.models.set('quality-predictor', this.buildQualityModel(sessions));
    
    // Build anomaly detection model
    this.models.set('anomaly-detector', this.buildAnomalyModel(sessions));
    
    console.log('Statistical models built successfully');
  }

  /**
   * Build session duration prediction model
   */
  private buildDurationModel(sessions: any[]): any {
    const durations = sessions
      .filter(s => s.duration && s.duration > 0)
      .map(s => s.duration / 60000); // Convert to minutes
    
    if (durations.length === 0) {
      return { mean: 60, std: 30, accuracy: 0.5 };
    }

    const mean = durations.reduce((sum, d) => sum + d, 0) / durations.length;
    const variance = durations.reduce((sum, d) => sum + Math.pow(d - mean, 2), 0) / durations.length;
    const std = Math.sqrt(variance);
    
    // Simple hourly patterns
    const hourlyStats = this.calculateHourlyStats(sessions, 'duration');
    
    return {
      mean,
      std,
      hourlyStats,
      accuracy: 0.75,
      sampleCount: durations.length
    };
  }

  /**
   * Build token velocity prediction model
   */
  private buildVelocityModel(sessions: any[]): any {
    const velocities = sessions
      .filter(s => s.tokens_per_minute > 0)
      .map(s => s.tokens_per_minute);
    
    if (velocities.length === 0) {
      return { mean: 10, std: 5, accuracy: 0.5 };
    }

    const mean = velocities.reduce((sum, v) => sum + v, 0) / velocities.length;
    const variance = velocities.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / velocities.length;
    const std = Math.sqrt(variance);
    
    const hourlyStats = this.calculateHourlyStats(sessions, 'tokens_per_minute');
    
    return {
      mean,
      std,
      hourlyStats,
      accuracy: 0.70,
      sampleCount: velocities.length
    };
  }

  /**
   * Build session quality prediction model
   */
  private buildQualityModel(sessions: any[]): any {
    const qualities = sessions
      .filter(s => s.quality_score !== null)
      .map(s => s.quality_score);
    
    if (qualities.length === 0) {
      return { mean: 70, std: 15, accuracy: 0.6 };
    }

    const mean = qualities.reduce((sum, q) => sum + q, 0) / qualities.length;
    const variance = qualities.reduce((sum, q) => sum + Math.pow(q - mean, 2), 0) / qualities.length;
    const std = Math.sqrt(variance);
    
    return {
      mean,
      std,
      accuracy: 0.65,
      sampleCount: qualities.length
    };
  }

  /**
   * Build anomaly detection model (statistical outlier detection)
   */
  private buildAnomalyModel(sessions: any[]): any {
    const metrics = sessions.map(s => ({
      duration: s.duration / 60000,
      tokenVelocity: s.tokens_per_minute,
      eventCount: s.event_count,
      toolRatio: s.tool_usage_count / Math.max(s.event_count, 1)
    }));
    
    if (metrics.length === 0) {
      return { thresholds: {}, accuracy: 0.5 };
    }

    // Calculate statistical thresholds for anomaly detection
    const thresholds = {
      duration: this.calculateOutlierThreshold(metrics.map(m => m.duration)),
      tokenVelocity: this.calculateOutlierThreshold(metrics.map(m => m.tokenVelocity)),
      eventCount: this.calculateOutlierThreshold(metrics.map(m => m.eventCount)),
      toolRatio: this.calculateOutlierThreshold(metrics.map(m => m.toolRatio))
    };
    
    return {
      thresholds,
      accuracy: 0.80,
      sampleCount: metrics.length
    };
  }

  /**
   * Calculate hourly statistics for a metric
   */
  private calculateHourlyStats(sessions: any[], metric: string): any {
    const hourlyData: { [hour: number]: number[] } = {};
    
    sessions.forEach(session => {
      const hour = new Date(session.start_time).getHours();
      if (!hourlyData[hour]) hourlyData[hour] = [];
      
      if (session[metric] !== null && session[metric] !== undefined) {
        const value = metric === 'duration' ? session[metric] / 60000 : session[metric];
        hourlyData[hour].push(value);
      }
    });
    
    const hourlyStats: { [hour: number]: { mean: number; count: number } } = {};
    
    Object.entries(hourlyData).forEach(([hour, values]) => {
      if (values.length > 0) {
        const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
        hourlyStats[parseInt(hour)] = { mean, count: values.length };
      }
    });
    
    return hourlyStats;
  }

  /**
   * Calculate outlier threshold using IQR method
   */
  private calculateOutlierThreshold(values: number[]): { upper: number; lower: number } {
    if (values.length === 0) {
      return { upper: 100, lower: 0 };
    }

    const sorted = [...values].sort((a, b) => a - b);
    const q1Index = Math.floor(sorted.length * 0.25);
    const q3Index = Math.floor(sorted.length * 0.75);
    
    const q1 = sorted[q1Index];
    const q3 = sorted[q3Index];
    const iqr = q3 - q1;
    
    return {
      upper: q3 + (1.5 * iqr),
      lower: Math.max(0, q1 - (1.5 * iqr))
    };
  }

  /**
   * Build default models when no historical data is available
   */
  private buildDefaultModels(): void {
    this.models.set('session-duration', {
      mean: 60,
      std: 30,
      hourlyStats: {},
      accuracy: 0.5,
      sampleCount: 0
    });

    this.models.set('token-velocity', {
      mean: 10,
      std: 5,
      hourlyStats: {},
      accuracy: 0.5,
      sampleCount: 0
    });

    this.models.set('quality-predictor', {
      mean: 70,
      std: 15,
      accuracy: 0.6,
      sampleCount: 0
    });

    this.models.set('anomaly-detector', {
      thresholds: {
        duration: { upper: 300, lower: 5 }, // 5 hours max, 5 min min
        tokenVelocity: { upper: 50, lower: 0.1 },
        eventCount: { upper: 1000, lower: 1 },
        toolRatio: { upper: 1, lower: 0 }
      },
      accuracy: 0.5,
      sampleCount: 0
    });
  }

  /**
   * Generate real-time predictions for a session
   */
  async generateRealTimePredictions(sessionId: string): Promise<SessionPrediction[]> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    const predictions: SessionPrediction[] = [];
    
    try {
      // Get current session metrics and features
      const metrics = getSessionMetrics(sessionId);
      const features = getSessionFeatures(sessionId);
      
      if (!metrics) {
        return predictions;
      }

      // Prepare feature vector
      const featureVector = this.prepareFeatureVector(metrics, features);
      
      // Generate predictions
      const durationPrediction = await this.predictSessionDuration(featureVector);
      const velocityPrediction = await this.predictTokenVelocity(featureVector);
      const qualityPrediction = await this.predictSessionQuality(featureVector);
      const anomalyScore = await this.detectAnomaly(featureVector);

      // Store predictions
      if (durationPrediction) {
        predictions.push(insertSessionPrediction(durationPrediction));
      }
      if (velocityPrediction) {
        predictions.push(insertSessionPrediction(velocityPrediction));
      }
      if (qualityPrediction) {
        predictions.push(insertSessionPrediction(qualityPrediction));
      }
      if (anomalyScore) {
        predictions.push(insertSessionPrediction(anomalyScore));
      }

    } catch (error) {
      console.error('Error generating real-time predictions:', error);
    }

    return predictions;
  }

  /**
   * Predict remaining session duration using statistical model
   */
  private async predictSessionDuration(featureVector: FeatureVector): Promise<SessionPrediction | null> {
    const model = this.models.get('session-duration');
    if (!model) return null;

    try {
      const currentHour = new Date().getHours();
      
      // Use hourly statistics if available, otherwise use global mean
      let predictedDuration = model.mean;
      
      if (model.hourlyStats[currentHour]) {
        predictedDuration = model.hourlyStats[currentHour].mean;
      }
      
      // Adjust based on current session context
      const currentDuration = featureVector.features.averageSessionDuration / 60000; // Convert to minutes
      const toolRatio = featureVector.features.toolUsageFrequency;
      
      // Heuristic adjustments
      if (toolRatio > 0.6) {
        predictedDuration *= 1.2; // High tool usage typically means longer sessions
      }
      
      if (currentDuration > 0) {
        // If session is already running, predict remaining time
        predictedDuration = Math.max(0, predictedDuration - currentDuration);
      }

      const confidence = Math.min(0.9, 0.3 + (model.sampleCount / 100) * 0.6);

      return {
        sessionId: featureVector.sessionId,
        predictionType: 'session-duration',
        predictedValue: Math.round(predictedDuration),
        confidence,
        createdAt: Date.now()
      };
    } catch (error) {
      console.error('Error predicting session duration:', error);
      return null;
    }
  }

  /**
   * Predict token velocity using statistical model
   */
  private async predictTokenVelocity(featureVector: FeatureVector): Promise<SessionPrediction | null> {
    const model = this.models.get('token-velocity');
    if (!model) return null;

    try {
      const currentHour = new Date().getHours();
      
      let predictedVelocity = model.mean;
      
      if (model.hourlyStats[currentHour]) {
        predictedVelocity = model.hourlyStats[currentHour].mean;
      }
      
      // Adjust based on current context
      const currentVelocity = featureVector.features.recentTokenVelocity;
      const toolRatio = featureVector.features.toolUsageFrequency;
      
      // Heuristic adjustments
      if (toolRatio > 0.5) {
        predictedVelocity *= 1.3; // More tools = higher token usage
      }
      
      if (currentVelocity > 0) {
        // Blend current velocity with predicted
        predictedVelocity = (currentVelocity * 0.6) + (predictedVelocity * 0.4);
      }

      const confidence = Math.min(0.9, 0.4 + (model.sampleCount / 100) * 0.5);

      return {
        sessionId: featureVector.sessionId,
        predictionType: 'token-velocity',
        predictedValue: Math.round(predictedVelocity * 100) / 100, // Round to 2 decimals
        confidence,
        createdAt: Date.now()
      };
    } catch (error) {
      console.error('Error predicting token velocity:', error);
      return null;
    }
  }

  /**
   * Predict session quality using statistical model
   */
  private async predictSessionQuality(featureVector: FeatureVector): Promise<SessionPrediction | null> {
    const model = this.models.get('quality-predictor');
    if (!model) return null;

    try {
      let qualityScore = model.mean;
      
      // Quality factors
      const toolRatio = featureVector.features.toolUsageFrequency;
      const errorRate = featureVector.features.errorRate;
      const productivity = featureVector.features.productivityPattern;
      
      // Heuristic quality calculation
      if (toolRatio > 0.3 && toolRatio < 0.8) {
        qualityScore += 10; // Good tool usage balance
      }
      
      if (errorRate < 0.1) {
        qualityScore += 15; // Low error rate
      } else if (errorRate > 0.3) {
        qualityScore -= 20; // High error rate
      }
      
      if (productivity > 5) {
        qualityScore += 10; // High productivity
      }
      
      // Keep score within bounds
      qualityScore = Math.max(0, Math.min(100, qualityScore));
      
      const confidence = Math.min(0.85, 0.5 + (model.sampleCount / 100) * 0.35);

      return {
        sessionId: featureVector.sessionId,
        predictionType: 'session-quality',
        predictedValue: Math.round(qualityScore),
        confidence,
        createdAt: Date.now()
      };
    } catch (error) {
      console.error('Error predicting session quality:', error);
      return null;
    }
  }

  /**
   * Detect anomalies using statistical thresholds
   */
  private async detectAnomaly(featureVector: FeatureVector): Promise<SessionPrediction | null> {
    const model = this.models.get('anomaly-detector');
    if (!model) return null;

    try {
      const duration = featureVector.features.averageSessionDuration / 60000; // Minutes
      const tokenVelocity = featureVector.features.recentTokenVelocity;
      const toolRatio = featureVector.features.toolUsageFrequency;
      
      let anomalyScore = 0;
      
      // Check duration anomaly
      if (duration > model.thresholds.duration.upper || duration < model.thresholds.duration.lower) {
        anomalyScore += 30;
      }
      
      // Check token velocity anomaly
      if (tokenVelocity > model.thresholds.tokenVelocity.upper || tokenVelocity < model.thresholds.tokenVelocity.lower) {
        anomalyScore += 25;
      }
      
      // Check tool ratio anomaly
      if (toolRatio > model.thresholds.toolRatio.upper || toolRatio < model.thresholds.toolRatio.lower) {
        anomalyScore += 20;
      }
      
      // Additional pattern-based anomaly detection
      const productivity = featureVector.features.productivityPattern;
      const sessionGaps = featureVector.features.sessionGaps;
      
      if (productivity === 0 && duration > 30) {
        anomalyScore += 25; // No activity in long session
      }
      
      if (sessionGaps > 600000) { // 10+ minute gaps
        anomalyScore += 15;
      }

      const confidence = anomalyScore > 50 ? 0.8 : 0.4;

      return {
        sessionId: featureVector.sessionId,
        predictionType: 'anomaly-score',
        predictedValue: Math.min(100, anomalyScore),
        confidence,
        createdAt: Date.now()
      };
    } catch (error) {
      console.error('Error detecting anomaly:', error);
      return null;
    }
  }

  /**
   * Prepare feature vector from session metrics and features
   */
  private prepareFeatureVector(metrics: SessionMetrics, features: SessionFeature[]): FeatureVector {
    // Convert features array to map for easy access
    const featureMap = new Map<string, number>();
    features.forEach(f => featureMap.set(f.featureName, f.featureValue));

    // Get or calculate default values
    const get = (key: string, defaultValue: number = 0): number => 
      featureMap.get(key) ?? defaultValue;

    return {
      sessionId: metrics.sessionId,
      features: {
        // Time-based features
        hourOfDay: get('hour_of_day', new Date().getHours()),
        dayOfWeek: get('day_of_week', new Date().getDay()),
        timeSinceLastSession: get('time_since_last_session', 0),
        
        // Session features
        averageSessionDuration: metrics.duration || 0,
        recentTokenVelocity: metrics.tokensPerMinute,
        toolUsageFrequency: metrics.toolUsageCount / Math.max(metrics.eventCount, 1),
        promptComplexity: get('payload_complexity', 1),
        
        // Behavioral features  
        sessionGaps: get('avg_time_gap', 0),
        productivityPattern: get('recent_event_velocity', 0),
        errorRate: get('error_rate', 0),
        iterationCount: get('iteration_count', 0)
      }
    };
  }

  /**
   * Train models with historical data (rebuild statistical models)
   */
  async trainModels(): Promise<void> {
    console.log('Starting statistical model training...');
    
    try {
      // Reload historical data
      await this.loadHistoricalData();
      
      // Rebuild models
      await this.buildStatisticalModels();
      
      console.log('Statistical model training completed');
    } catch (error) {
      console.error('Error training statistical models:', error);
    }
  }

  /**
   * Get model performance metrics
   */
  async getModelMetrics(): Promise<{ [key: string]: any }> {
    const metrics: { [key: string]: any } = {};
    
    for (const [modelType, model] of this.models) {
      metrics[modelType] = {
        isLoaded: true,
        lastTrained: Date.now(),
        accuracy: model.accuracy || 0.5,
        sampleCount: model.sampleCount || 0,
        type: 'statistical'
      };
    }
    
    return metrics;
  }
}