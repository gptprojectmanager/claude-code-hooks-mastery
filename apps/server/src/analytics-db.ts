import { Database } from 'bun:sqlite';
import type { 
  SessionFeature, 
  SessionPrediction, 
  SessionInsight, 
  SessionMetrics,
  AnomalyAlert,
  OptimizationRecommendation,
  SessionQualityMetrics 
} from './analytics-types';

// Use the same database instance as the main db
let db: Database;

export function initAnalyticsDatabase(): void {
  db = new Database('events.db');
  
  // Create analytics tables
  
  // Session features table
  db.exec(`
    CREATE TABLE IF NOT EXISTS session_features (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      feature_name TEXT NOT NULL,
      feature_value REAL NOT NULL,
      computed_at INTEGER NOT NULL,
      FOREIGN KEY (session_id) REFERENCES events (session_id)
    )
  `);
  
  // Session predictions table
  db.exec(`
    CREATE TABLE IF NOT EXISTS session_predictions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      prediction_type TEXT NOT NULL,
      predicted_value REAL NOT NULL,
      confidence REAL NOT NULL,
      created_at INTEGER NOT NULL,
      FOREIGN KEY (session_id) REFERENCES events (session_id)
    )
  `);
  
  // Session insights table
  db.exec(`
    CREATE TABLE IF NOT EXISTS session_insights (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT,
      insight_type TEXT NOT NULL,
      insight_data TEXT NOT NULL,
      priority TEXT NOT NULL,
      created_at INTEGER NOT NULL
    )
  `);
  
  // Session metrics table (aggregated data)
  db.exec(`
    CREATE TABLE IF NOT EXISTS session_metrics (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL UNIQUE,
      duration INTEGER,
      total_tokens INTEGER NOT NULL DEFAULT 0,
      tokens_per_minute REAL NOT NULL DEFAULT 0,
      event_count INTEGER NOT NULL DEFAULT 0,
      tool_usage_count INTEGER NOT NULL DEFAULT 0,
      prompt_count INTEGER NOT NULL DEFAULT 0,
      start_time INTEGER NOT NULL,
      end_time INTEGER,
      is_active INTEGER NOT NULL DEFAULT 1,
      quality_score REAL,
      updated_at INTEGER NOT NULL,
      FOREIGN KEY (session_id) REFERENCES events (session_id)
    )
  `);
  
  // Model metadata table
  db.exec(`
    CREATE TABLE IF NOT EXISTS ml_models (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      model_type TEXT NOT NULL,
      version TEXT NOT NULL,
      accuracy REAL NOT NULL,
      last_trained INTEGER NOT NULL,
      training_data_size INTEGER NOT NULL,
      model_data BLOB,
      is_active INTEGER NOT NULL DEFAULT 1,
      created_at INTEGER NOT NULL
    )
  `);
  
  // Anomaly alerts table
  db.exec(`
    CREATE TABLE IF NOT EXISTS anomaly_alerts (
      id TEXT PRIMARY KEY,
      session_id TEXT NOT NULL,
      anomaly_type TEXT NOT NULL,
      severity TEXT NOT NULL,
      description TEXT NOT NULL,
      recommended_action TEXT,
      detected_at INTEGER NOT NULL,
      resolved_at INTEGER,
      is_resolved INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY (session_id) REFERENCES events (session_id)
    )
  `);
  
  // Optimization recommendations table
  db.exec(`
    CREATE TABLE IF NOT EXISTS optimization_recommendations (
      id TEXT PRIMARY KEY,
      type TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT NOT NULL,
      potential_impact TEXT NOT NULL,
      action_items TEXT NOT NULL,
      based_on_data TEXT NOT NULL,
      created_at INTEGER NOT NULL,
      applied_at INTEGER,
      is_applied INTEGER NOT NULL DEFAULT 0
    )
  `);
  
  // Usage patterns table
  db.exec(`
    CREATE TABLE IF NOT EXISTS usage_patterns (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      pattern_type TEXT NOT NULL,
      confidence REAL NOT NULL,
      characteristics TEXT NOT NULL,
      detected_at INTEGER NOT NULL,
      FOREIGN KEY (session_id) REFERENCES events (session_id)
    )
  `);
  
  // Create indexes for analytics tables
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_features_session ON session_features(session_id)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_features_name ON session_features(feature_name)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_predictions_session ON session_predictions(session_id)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_predictions_type ON session_predictions(prediction_type)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_insights_type ON session_insights(insight_type)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_insights_priority ON session_insights(priority)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_metrics_session ON session_metrics(session_id)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_metrics_active ON session_metrics(is_active)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_session ON anomaly_alerts(session_id)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_type ON anomaly_alerts(anomaly_type)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_usage_patterns_session ON usage_patterns(session_id)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_usage_patterns_type ON usage_patterns(pattern_type)');
}

// Session Features
export function insertSessionFeature(feature: SessionFeature): SessionFeature {
  const stmt = db.prepare(`
    INSERT INTO session_features (session_id, feature_name, feature_value, computed_at)
    VALUES (?, ?, ?, ?)
  `);
  
  const computedAt = feature.computedAt || Date.now();
  const result = stmt.run(
    feature.sessionId,
    feature.featureName,
    feature.featureValue,
    computedAt
  );
  
  return {
    ...feature,
    id: result.lastInsertRowid as number,
    computedAt
  };
}

export function getSessionFeatures(sessionId: string): SessionFeature[] {
  const stmt = db.prepare(`
    SELECT id, session_id, feature_name, feature_value, computed_at
    FROM session_features
    WHERE session_id = ?
    ORDER BY computed_at DESC
  `);
  
  const rows = stmt.all(sessionId) as any[];
  
  return rows.map(row => ({
    id: row.id,
    sessionId: row.session_id,
    featureName: row.feature_name,
    featureValue: row.feature_value,
    computedAt: row.computed_at
  }));
}

// Session Predictions
export function insertSessionPrediction(prediction: SessionPrediction): SessionPrediction {
  const stmt = db.prepare(`
    INSERT INTO session_predictions (session_id, prediction_type, predicted_value, confidence, created_at)
    VALUES (?, ?, ?, ?, ?)
  `);
  
  const createdAt = prediction.createdAt || Date.now();
  const result = stmt.run(
    prediction.sessionId,
    prediction.predictionType,
    prediction.predictedValue,
    prediction.confidence,
    createdAt
  );
  
  return {
    ...prediction,
    id: result.lastInsertRowid as number,
    createdAt
  };
}

export function getSessionPredictions(sessionId: string): SessionPrediction[] {
  const stmt = db.prepare(`
    SELECT id, session_id, prediction_type, predicted_value, confidence, created_at
    FROM session_predictions
    WHERE session_id = ?
    ORDER BY created_at DESC
  `);
  
  const rows = stmt.all(sessionId) as any[];
  
  return rows.map(row => ({
    id: row.id,
    sessionId: row.session_id,
    predictionType: row.prediction_type,
    predictedValue: row.predicted_value,
    confidence: row.confidence,
    createdAt: row.created_at
  }));
}

// Session Insights
export function insertSessionInsight(insight: SessionInsight): SessionInsight {
  const stmt = db.prepare(`
    INSERT INTO session_insights (session_id, insight_type, insight_data, priority, created_at)
    VALUES (?, ?, ?, ?, ?)
  `);
  
  const createdAt = insight.createdAt || Date.now();
  const result = stmt.run(
    insight.sessionId || null,
    insight.insightType,
    JSON.stringify(insight.insightData),
    insight.priority,
    createdAt
  );
  
  return {
    ...insight,
    id: result.lastInsertRowid as number,
    createdAt
  };
}

export function getSessionInsights(sessionId?: string, limit: number = 50): SessionInsight[] {
  let sql = `
    SELECT id, session_id, insight_type, insight_data, priority, created_at
    FROM session_insights
  `;
  const params: any[] = [];
  
  if (sessionId) {
    sql += ' WHERE session_id = ?';
    params.push(sessionId);
  }
  
  sql += ' ORDER BY created_at DESC LIMIT ?';
  params.push(limit);
  
  const stmt = db.prepare(sql);
  const rows = stmt.all(...params) as any[];
  
  return rows.map(row => ({
    id: row.id,
    sessionId: row.session_id,
    insightType: row.insight_type,
    insightData: JSON.parse(row.insight_data),
    priority: row.priority as any,
    createdAt: row.created_at
  }));
}

// Session Metrics
export function upsertSessionMetrics(metrics: SessionMetrics): SessionMetrics {
  const stmt = db.prepare(`
    INSERT INTO session_metrics (
      session_id, duration, total_tokens, tokens_per_minute, event_count,
      tool_usage_count, prompt_count, start_time, end_time, is_active, 
      quality_score, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(session_id) DO UPDATE SET
      duration = excluded.duration,
      total_tokens = excluded.total_tokens,
      tokens_per_minute = excluded.tokens_per_minute,
      event_count = excluded.event_count,
      tool_usage_count = excluded.tool_usage_count,
      prompt_count = excluded.prompt_count,
      end_time = excluded.end_time,
      is_active = excluded.is_active,
      quality_score = excluded.quality_score,
      updated_at = excluded.updated_at
  `);
  
  const updatedAt = Date.now();
  stmt.run(
    metrics.sessionId,
    metrics.duration || null,
    metrics.totalTokens,
    metrics.tokensPerMinute,
    metrics.eventCount,
    metrics.toolUsageCount,
    metrics.promptCount,
    metrics.startTime,
    metrics.endTime || null,
    metrics.isActive ? 1 : 0,
    metrics.qualityScore || null,
    updatedAt
  );
  
  return { ...metrics, updatedAt };
}

export function getSessionMetrics(sessionId: string): SessionMetrics | null {
  const stmt = db.prepare(`
    SELECT * FROM session_metrics WHERE session_id = ?
  `);
  
  const row = stmt.get(sessionId) as any;
  if (!row) return null;
  
  return {
    sessionId: row.session_id,
    duration: row.duration,
    totalTokens: row.total_tokens,
    tokensPerMinute: row.tokens_per_minute,
    eventCount: row.event_count,
    toolUsageCount: row.tool_usage_count,
    promptCount: row.prompt_count,
    startTime: row.start_time,
    endTime: row.end_time,
    isActive: Boolean(row.is_active),
    qualityScore: row.quality_score
  };
}

export function getAllActiveSessionMetrics(): SessionMetrics[] {
  const stmt = db.prepare(`
    SELECT * FROM session_metrics WHERE is_active = 1 ORDER BY start_time DESC
  `);
  
  const rows = stmt.all() as any[];
  
  return rows.map(row => ({
    sessionId: row.session_id,
    duration: row.duration,
    totalTokens: row.total_tokens,
    tokensPerMinute: row.tokens_per_minute,
    eventCount: row.event_count,
    toolUsageCount: row.tool_usage_count,
    promptCount: row.prompt_count,
    startTime: row.start_time,
    endTime: row.end_time,
    isActive: Boolean(row.is_active),
    qualityScore: row.quality_score
  }));
}

// Anomaly Alerts
export function insertAnomalyAlert(alert: AnomalyAlert): AnomalyAlert {
  const stmt = db.prepare(`
    INSERT INTO anomaly_alerts (id, session_id, anomaly_type, severity, description, recommended_action, detected_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  
  stmt.run(
    alert.id,
    alert.sessionId,
    alert.anomalyType,
    alert.severity,
    alert.description,
    alert.recommendedAction || null,
    alert.detectedAt
  );
  
  return alert;
}

export function getActiveAnomalyAlerts(): AnomalyAlert[] {
  const stmt = db.prepare(`
    SELECT * FROM anomaly_alerts WHERE is_resolved = 0 ORDER BY detected_at DESC
  `);
  
  const rows = stmt.all() as any[];
  
  return rows.map(row => ({
    id: row.id,
    sessionId: row.session_id,
    anomalyType: row.anomaly_type,
    severity: row.severity,
    description: row.description,
    recommendedAction: row.recommended_action,
    detectedAt: row.detected_at
  }));
}

// Optimization Recommendations
export function insertOptimizationRecommendation(recommendation: OptimizationRecommendation): OptimizationRecommendation {
  const stmt = db.prepare(`
    INSERT INTO optimization_recommendations (id, type, title, description, potential_impact, action_items, based_on_data, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
  
  stmt.run(
    recommendation.id,
    recommendation.type,
    recommendation.title,
    recommendation.description,
    recommendation.potentialImpact,
    JSON.stringify(recommendation.actionItems),
    JSON.stringify(recommendation.basedOnData),
    Date.now()
  );
  
  return recommendation;
}

export function getOptimizationRecommendations(limit: number = 10): OptimizationRecommendation[] {
  const stmt = db.prepare(`
    SELECT * FROM optimization_recommendations WHERE is_applied = 0 
    ORDER BY potential_impact DESC, created_at DESC LIMIT ?
  `);
  
  const rows = stmt.all(limit) as any[];
  
  return rows.map(row => ({
    id: row.id,
    type: row.type,
    title: row.title,
    description: row.description,
    potentialImpact: row.potential_impact,
    actionItems: JSON.parse(row.action_items),
    basedOnData: JSON.parse(row.based_on_data)
  }));
}

export { db };