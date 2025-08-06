import { Database } from 'bun:sqlite';
import type { HookEvent } from '../types';
import type { SessionMetrics, FeatureVector, SessionFeature } from '../analytics-types';
import { 
  upsertSessionMetrics, 
  insertSessionFeature, 
  getSessionMetrics 
} from '../analytics-db';

export class DataPipeline {
  private db: Database;
  
  constructor() {
    this.db = new Database('events.db');
  }

  /**
   * Process incoming event and update session metrics
   */
  async processEvent(event: HookEvent): Promise<void> {
    try {
      // Update session metrics
      await this.updateSessionMetrics(event);
      
      // Extract and store features
      await this.extractFeatures(event);
      
      // Trigger real-time predictions if needed
      await this.triggerRealtimeAnalytics(event);
      
    } catch (error) {
      console.error('Error processing event in data pipeline:', error);
    }
  }

  /**
   * Update session metrics with new event data
   */
  private async updateSessionMetrics(event: HookEvent): Promise<void> {
    const sessionId = event.session_id;
    
    // Get current metrics or create new ones
    let metrics = getSessionMetrics(sessionId);
    
    if (!metrics) {
      metrics = {
        sessionId,
        totalTokens: 0,
        tokensPerMinute: 0,
        eventCount: 0,
        toolUsageCount: 0,
        promptCount: 0,
        startTime: event.timestamp || Date.now(),
        isActive: true
      };
    }

    // Update metrics based on event type
    metrics.eventCount++;
    
    switch (event.hook_event_type) {
      case 'PreToolUse':
      case 'PostToolUse':
        metrics.toolUsageCount++;
        break;
      case 'UserPromptSubmit':
        metrics.promptCount++;
        break;
    }

    // Extract token information from payload if available
    if (event.payload?.tokens) {
      metrics.totalTokens += event.payload.tokens;
    } else if (event.payload?.usage?.total_tokens) {
      metrics.totalTokens += event.payload.usage.total_tokens;
    }

    // Calculate duration and tokens per minute
    const currentTime = event.timestamp || Date.now();
    metrics.duration = currentTime - metrics.startTime;
    
    if (metrics.duration > 0) {
      metrics.tokensPerMinute = (metrics.totalTokens / metrics.duration) * 60000; // Convert to per minute
    }

    // Update active status based on recent activity
    const timeSinceLastActivity = currentTime - (event.timestamp || Date.now());
    metrics.isActive = timeSinceLastActivity < 300000; // 5 minutes

    // Calculate quality score
    metrics.qualityScore = this.calculateQualityScore(metrics);

    // Save updated metrics
    upsertSessionMetrics(metrics);
  }

  /**
   * Extract features from event and session data
   */
  private async extractFeatures(event: HookEvent): Promise<void> {
    const sessionId = event.session_id;
    const timestamp = event.timestamp || Date.now();
    
    // Time-based features
    const date = new Date(timestamp);
    const hourOfDay = date.getHours();
    const dayOfWeek = date.getDay();
    
    insertSessionFeature({
      sessionId,
      featureName: 'hour_of_day',
      featureValue: hourOfDay,
      computedAt: timestamp
    });

    insertSessionFeature({
      sessionId,
      featureName: 'day_of_week',
      featureValue: dayOfWeek,
      computedAt: timestamp
    });

    // Event-specific features
    const eventTypeMap: { [key: string]: number } = {
      'PreToolUse': 1,
      'PostToolUse': 2,
      'UserPromptSubmit': 3,
      'Stop': 4,
      'SubagentStop': 5,
      'Notification': 6
    };

    insertSessionFeature({
      sessionId,
      featureName: 'event_type_numeric',
      featureValue: eventTypeMap[event.hook_event_type] || 0,
      computedAt: timestamp
    });

    // Payload complexity feature
    const payloadComplexity = this.calculatePayloadComplexity(event.payload);
    insertSessionFeature({
      sessionId,
      featureName: 'payload_complexity',
      featureValue: payloadComplexity,
      computedAt: timestamp
    });

    // Session context features
    const sessionFeatures = await this.calculateSessionContextFeatures(sessionId);
    for (const [featureName, value] of Object.entries(sessionFeatures)) {
      insertSessionFeature({
        sessionId,
        featureName,
        featureValue: value,
        computedAt: timestamp
      });
    }
  }

  /**
   * Calculate payload complexity score
   */
  private calculatePayloadComplexity(payload: any): number {
    let complexity = 0;
    
    // Basic complexity based on object size
    const jsonStr = JSON.stringify(payload);
    complexity += jsonStr.length / 1000; // Normalize by KB
    
    // Additional complexity for nested objects
    const nestingLevel = this.getMaxNestingLevel(payload);
    complexity += nestingLevel * 0.5;
    
    // Additional complexity for arrays
    const arrayCount = this.countArrays(payload);
    complexity += arrayCount * 0.3;
    
    return Math.min(complexity, 10); // Cap at 10
  }

  /**
   * Calculate session context features
   */
  private async calculateSessionContextFeatures(sessionId: string): Promise<{ [key: string]: number }> {
    const features: { [key: string]: number } = {};
    
    // Get recent events for this session
    const recentEvents = this.getRecentSessionEvents(sessionId, 50);
    
    if (recentEvents.length === 0) {
      return features;
    }

    // Calculate time gaps between events
    const timeGaps = [];
    for (let i = 1; i < recentEvents.length; i++) {
      const gap = recentEvents[i].timestamp - recentEvents[i-1].timestamp;
      timeGaps.push(gap);
    }

    features.avg_time_gap = timeGaps.length > 0 ? 
      timeGaps.reduce((sum, gap) => sum + gap, 0) / timeGaps.length : 0;

    features.max_time_gap = timeGaps.length > 0 ? Math.max(...timeGaps) : 0;
    features.min_time_gap = timeGaps.length > 0 ? Math.min(...timeGaps) : 0;

    // Calculate event type diversity
    const eventTypes = new Set(recentEvents.map(e => e.hook_event_type));
    features.event_type_diversity = eventTypes.size;

    // Calculate recent velocity (events per minute)
    const timeSpan = recentEvents[recentEvents.length - 1].timestamp - recentEvents[0].timestamp;
    features.recent_event_velocity = timeSpan > 0 ? 
      (recentEvents.length / timeSpan) * 60000 : 0;

    // Calculate tool usage ratio
    const toolEvents = recentEvents.filter(e => 
      e.hook_event_type === 'PreToolUse' || e.hook_event_type === 'PostToolUse'
    );
    features.tool_usage_ratio = recentEvents.length > 0 ? 
      toolEvents.length / recentEvents.length : 0;

    return features;
  }

  /**
   * Get recent events for a session
   */
  private getRecentSessionEvents(sessionId: string, limit: number): HookEvent[] {
    const stmt = this.db.prepare(`
      SELECT * FROM events 
      WHERE session_id = ? 
      ORDER BY timestamp DESC 
      LIMIT ?
    `);
    
    const rows = stmt.all(sessionId, limit) as any[];
    
    return rows.map(row => ({
      id: row.id,
      source_app: row.source_app,
      session_id: row.session_id,
      hook_event_type: row.hook_event_type,
      payload: JSON.parse(row.payload),
      chat: row.chat ? JSON.parse(row.chat) : undefined,
      summary: row.summary,
      timestamp: row.timestamp
    })).reverse(); // Return in chronological order
  }

  /**
   * Calculate session quality score
   */
  private calculateQualityScore(metrics: SessionMetrics): number {
    let score = 100;
    
    // Penalize very short or very long sessions
    if (metrics.duration) {
      const durationHours = metrics.duration / (1000 * 60 * 60);
      if (durationHours < 0.1) {
        score -= 20; // Too short
      } else if (durationHours > 8) {
        score -= 30; // Too long
      }
    }

    // Reward consistent activity
    if (metrics.eventCount > 0 && metrics.duration) {
      const eventsPerHour = (metrics.eventCount / metrics.duration) * (1000 * 60 * 60);
      if (eventsPerHour < 10) {
        score -= 15; // Too few events
      } else if (eventsPerHour > 1000) {
        score -= 25; // Too many events (possible spam)
      }
    }

    // Reward balanced tool usage
    if (metrics.eventCount > 0) {
      const toolRatio = metrics.toolUsageCount / metrics.eventCount;
      if (toolRatio > 0.3 && toolRatio < 0.8) {
        score += 10; // Good balance
      }
    }

    // Ensure score is between 0 and 100
    return Math.max(0, Math.min(100, score));
  }

  /**
   * Trigger real-time analytics for critical events
   */
  private async triggerRealtimeAnalytics(event: HookEvent): Promise<void> {
    // Import prediction engine dynamically to avoid circular dependencies
    const { PredictionEngine } = await import('./predictor');
    const predictor = new PredictionEngine();
    
    // Trigger predictions for important events
    if (['UserPromptSubmit', 'Stop'].includes(event.hook_event_type)) {
      await predictor.generateRealTimePredictions(event.session_id);
    }
  }

  /**
   * Utility function to get max nesting level of an object
   */
  private getMaxNestingLevel(obj: any, level: number = 0): number {
    if (typeof obj !== 'object' || obj === null) {
      return level;
    }

    let maxLevel = level;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const childLevel = this.getMaxNestingLevel(obj[key], level + 1);
        maxLevel = Math.max(maxLevel, childLevel);
      }
    }

    return maxLevel;
  }

  /**
   * Utility function to count arrays in an object
   */
  private countArrays(obj: any): number {
    if (typeof obj !== 'object' || obj === null) {
      return 0;
    }

    let count = 0;
    if (Array.isArray(obj)) {
      count = 1;
    }

    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        count += this.countArrays(obj[key]);
      }
    }

    return count;
  }

  /**
   * Batch process historical data for feature extraction
   */
  async batchProcessHistoricalData(): Promise<void> {
    console.log('Starting batch processing of historical data...');
    
    const stmt = this.db.prepare(`
      SELECT DISTINCT session_id FROM events ORDER BY session_id
    `);
    
    const sessions = stmt.all() as { session_id: string }[];
    
    for (const session of sessions) {
      await this.reprocessSession(session.session_id);
    }
    
    console.log(`Batch processing completed for ${sessions.length} sessions`);
  }

  /**
   * Reprocess a single session to update metrics and features
   */
  private async reprocessSession(sessionId: string): Promise<void> {
    const events = this.getRecentSessionEvents(sessionId, 1000);
    
    for (const event of events) {
      await this.updateSessionMetrics(event);
      await this.extractFeatures(event);
    }
  }
}