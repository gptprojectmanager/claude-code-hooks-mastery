import { Database } from 'bun:sqlite';
import { addHours, format, startOfDay, endOfDay, subDays, differenceInMinutes } from 'date-fns';
import type { 
  SessionInsight, 
  SessionMetrics, 
  AnomalyAlert,
  OptimizationRecommendation,
  UsagePattern,
  SessionQualityMetrics,
  TimeSeriesData
} from '../analytics-types';
import { 
  insertSessionInsight,
  insertAnomalyAlert,
  insertOptimizationRecommendation,
  getAllActiveSessionMetrics,
  getSessionPredictions
} from '../analytics-db';

export class InsightsEngine {
  private db: Database;
  
  constructor() {
    this.db = new Database('events.db');
  }

  /**
   * Generate comprehensive insights for all active sessions
   */
  async generateInsights(): Promise<void> {
    try {
      console.log('Generating comprehensive insights...');
      
      // Generate different types of insights
      await this.generateUsagePatternInsights();
      await this.generateProductivityInsights();
      await this.generateAnomalyInsights();
      await this.generateOptimizationInsights();
      await this.generateHealthInsights();
      
      console.log('Insights generation completed');
    } catch (error) {
      console.error('Error generating insights:', error);
    }
  }

  /**
   * Generate usage pattern insights
   */
  private async generateUsagePatternInsights(): Promise<void> {
    const patterns = await this.analyzeUsagePatterns();
    
    for (const pattern of patterns) {
      const insight: SessionInsight = {
        insightType: 'usage-pattern',
        insightData: {
          pattern: pattern.patternType,
          confidence: pattern.confidence,
          characteristics: pattern.characteristics,
          recommendation: this.getPatternRecommendation(pattern.patternType)
        },
        priority: this.calculatePatternPriority(pattern),
        createdAt: Date.now()
      };
      
      insertSessionInsight(insight);
    }
  }

  /**
   * Generate productivity insights
   */
  private async generateProductivityInsights(): Promise<void> {
    const productivityData = await this.analyzeProductivityTrends();
    
    // Peak hours analysis
    if (productivityData.peakHours.length > 0) {
      insertSessionInsight({
        insightType: 'productivity-peak-hours',
        insightData: {
          peakHours: productivityData.peakHours,
          averageProductivity: productivityData.averageProductivity,
          recommendation: `Your peak productivity hours are ${productivityData.peakHours.join(', ')}. Consider scheduling important tasks during these times.`
        },
        priority: 'medium',
        createdAt: Date.now()
      });
    }

    // Session length optimization
    const optimalDuration = this.calculateOptimalSessionDuration(productivityData);
    if (optimalDuration) {
      insertSessionInsight({
        insightType: 'session-duration-optimization',
        insightData: {
          optimalDuration,
          currentAverage: productivityData.averageDuration,
          potentialImprovement: Math.abs(optimalDuration - productivityData.averageDuration),
          recommendation: optimalDuration > productivityData.averageDuration 
            ? `Consider longer sessions (~${Math.round(optimalDuration)} minutes) for better productivity.`
            : `Consider shorter sessions (~${Math.round(optimalDuration)} minutes) to maintain focus.`
        },
        priority: 'medium',
        createdAt: Date.now()
      });
    }

    // Token usage efficiency
    const efficiencyInsight = this.analyzeTokenEfficiency(productivityData);
    if (efficiencyInsight) {
      insertSessionInsight(efficiencyInsight);
    }
  }

  /**
   * Generate anomaly detection insights
   */
  private async generateAnomalyInsights(): Promise<void> {
    const activeMetrics = getAllActiveSessionMetrics();
    const anomalies = await this.detectSessionAnomalies(activeMetrics);
    
    for (const anomaly of anomalies) {
      // Create anomaly alert
      insertAnomalyAlert(anomaly);
      
      // Create corresponding insight
      insertSessionInsight({
        sessionId: anomaly.sessionId,
        insightType: 'anomaly-detected',
        insightData: {
          anomalyType: anomaly.anomalyType,
          severity: anomaly.severity,
          description: anomaly.description,
          detectedAt: anomaly.detectedAt,
          recommendation: anomaly.recommendedAction
        },
        priority: anomaly.severity === 'high' ? 'high' : 'medium',
        createdAt: Date.now()
      });
    }
  }

  /**
   * Generate optimization recommendations
   */
  private async generateOptimizationInsights(): Promise<void> {
    const recommendations = await this.generateOptimizationRecommendations();
    
    for (const recommendation of recommendations) {
      insertOptimizationRecommendation(recommendation);
      
      // Create insight for high-impact recommendations
      if (recommendation.potentialImpact === 'high') {
        insertSessionInsight({
          insightType: 'optimization-opportunity',
          insightData: {
            type: recommendation.type,
            title: recommendation.title,
            description: recommendation.description,
            actionItems: recommendation.actionItems,
            potentialImpact: recommendation.potentialImpact
          },
          priority: 'high',
          createdAt: Date.now()
        });
      }
    }
  }

  /**
   * Generate health and wellness insights
   */
  private async generateHealthInsights(): Promise<void> {
    const healthData = await this.analyzeSessionHealth();
    
    // Long session warning
    if (healthData.longSessionsCount > 0) {
      insertSessionInsight({
        insightType: 'health-long-sessions',
        insightData: {
          longSessionsCount: healthData.longSessionsCount,
          averageLongSessionDuration: healthData.averageLongSessionDuration,
          recommendation: 'Consider taking regular breaks during long sessions to maintain productivity and well-being.',
          suggestedBreakInterval: 60 // minutes
        },
        priority: 'medium',
        createdAt: Date.now()
      });
    }

    // Break frequency analysis
    if (healthData.breakFrequency < 0.2) { // Less than 20% break time
      insertSessionInsight({
        insightType: 'health-insufficient-breaks',
        insightData: {
          currentBreakFrequency: healthData.breakFrequency,
          recommendedBreakFrequency: 0.2,
          recommendation: 'You may benefit from more frequent breaks to maintain focus and prevent burnout.'
        },
        priority: 'medium',
        createdAt: Date.now()
      });
    }

    // Productivity burnout detection
    if (healthData.burnoutRisk > 0.7) {
      insertSessionInsight({
        insightType: 'health-burnout-risk',
        insightData: {
          burnoutRisk: healthData.burnoutRisk,
          factors: healthData.burnoutFactors,
          recommendation: 'High burnout risk detected. Consider reducing session intensity and taking longer breaks.'
        },
        priority: 'high',
        createdAt: Date.now()
      });
    }
  }

  /**
   * Analyze usage patterns across sessions
   */
  private async analyzeUsagePatterns(): Promise<UsagePattern[]> {
    const patterns: UsagePattern[] = [];
    const metrics = getAllActiveSessionMetrics();
    
    if (metrics.length === 0) return patterns;

    // Analyze patterns for each session
    for (const metric of metrics) {
      const pattern = await this.classifySessionPattern(metric);
      if (pattern) {
        patterns.push(pattern);
      }
    }

    return patterns;
  }

  /**
   * Classify session pattern based on metrics
   */
  private async classifySessionPattern(metric: SessionMetrics): Promise<UsagePattern | null> {
    const toolRatio = metric.toolUsageCount / Math.max(metric.eventCount, 1);
    const tokenVelocity = metric.tokensPerMinute;
    const duration = metric.duration || 0;
    
    // Get recent events to analyze pause patterns
    const recentEvents = this.getRecentSessionEvents(metric.sessionId, 50);
    const pauseFrequency = this.calculatePauseFrequency(recentEvents);

    // Classification logic
    if (duration > 240 * 60000 && tokenVelocity < 10 && toolRatio < 0.3) {
      return {
        patternId: `pattern_${metric.sessionId}_${Date.now()}`,
        patternType: 'deep-work',
        confidence: 0.8,
        characteristics: {
          avgSessionDuration: duration / 60000,
          tokenVelocity,
          toolUsageRatio: toolRatio,
          pauseFrequency
        }
      };
    }

    if (toolRatio > 0.6 && tokenVelocity > 20) {
      return {
        patternId: `pattern_${metric.sessionId}_${Date.now()}`,
        patternType: 'rapid-iteration',
        confidence: 0.7,
        characteristics: {
          avgSessionDuration: duration / 60000,
          tokenVelocity,
          toolUsageRatio: toolRatio,
          pauseFrequency
        }
      };
    }

    if (pauseFrequency > 0.4 && tokenVelocity < 15) {
      return {
        patternId: `pattern_${metric.sessionId}_${Date.now()}`,
        patternType: 'exploration',
        confidence: 0.6,
        characteristics: {
          avgSessionDuration: duration / 60000,
          tokenVelocity,
          toolUsageRatio: toolRatio,
          pauseFrequency
        }
      };
    }

    // Default to learning pattern
    return {
      patternId: `pattern_${metric.sessionId}_${Date.now()}`,
      patternType: 'learning',
      confidence: 0.5,
      characteristics: {
        avgSessionDuration: duration / 60000,
        tokenVelocity,
        toolUsageRatio: toolRatio,
        pauseFrequency
      }
    };
  }

  /**
   * Analyze productivity trends
   */
  private async analyzeProductivityTrends(): Promise<any> {
    const stmt = this.db.prepare(`
      SELECT 
        session_id,
        start_time,
        duration,
        total_tokens,
        tokens_per_minute,
        event_count,
        quality_score
      FROM session_metrics 
      WHERE start_time > ?
      ORDER BY start_time DESC
    `);

    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    const sessions = stmt.all(sevenDaysAgo) as any[];

    // Analyze by hour of day
    const hourlyProductivity = new Array(24).fill(0);
    const hourlyCounts = new Array(24).fill(0);

    let totalDuration = 0;
    let totalQuality = 0;
    let validSessions = 0;

    for (const session of sessions) {
      const hour = new Date(session.start_time).getHours();
      const quality = session.quality_score || 50;
      const productivity = quality * (session.tokens_per_minute || 0) / 100;

      hourlyProductivity[hour] += productivity;
      hourlyCounts[hour]++;
      
      totalDuration += session.duration || 0;
      totalQuality += quality;
      validSessions++;
    }

    // Calculate averages and find peak hours
    const avgProductivityByHour = hourlyProductivity.map((total, hour) => 
      hourlyCounts[hour] > 0 ? total / hourlyCounts[hour] : 0
    );

    const peakHours = avgProductivityByHour
      .map((productivity, hour) => ({ hour, productivity }))
      .filter(item => item.productivity > 0)
      .sort((a, b) => b.productivity - a.productivity)
      .slice(0, 3)
      .map(item => item.hour);

    return {
      peakHours,
      averageProductivity: avgProductivityByHour.reduce((sum, p) => sum + p, 0) / 24,
      averageDuration: validSessions > 0 ? totalDuration / validSessions / 60000 : 0, // in minutes
      averageQuality: validSessions > 0 ? totalQuality / validSessions : 50,
      sessionCount: validSessions
    };
  }

  /**
   * Detect anomalies in session behavior
   */
  private async detectSessionAnomalies(metrics: SessionMetrics[]): Promise<AnomalyAlert[]> {
    const anomalies: AnomalyAlert[] = [];
    
    // Calculate baseline metrics
    const baseline = this.calculateBaselineMetrics(metrics);
    
    for (const metric of metrics) {
      // Check for duration anomalies
      if (metric.duration && metric.duration > baseline.maxNormalDuration) {
        anomalies.push({
          id: `anomaly_${Date.now()}_${metric.sessionId}`,
          sessionId: metric.sessionId,
          anomalyType: 'duration',
          severity: metric.duration > baseline.maxNormalDuration * 2 ? 'high' : 'medium',
          description: `Session duration (${Math.round(metric.duration / 60000)} minutes) is significantly longer than normal`,
          recommendedAction: 'Consider taking a break or splitting the session into smaller chunks',
          detectedAt: Date.now()
        });
      }

      // Check for token velocity anomalies
      if (metric.tokensPerMinute > baseline.maxNormalTokenVelocity) {
        anomalies.push({
          id: `anomaly_${Date.now()}_${metric.sessionId}`,
          sessionId: metric.sessionId,
          anomalyType: 'token-usage',
          severity: metric.tokensPerMinute > baseline.maxNormalTokenVelocity * 2 ? 'high' : 'medium',
          description: `Token usage rate (${Math.round(metric.tokensPerMinute)} tokens/min) is unusually high`,
          recommendedAction: 'Monitor token consumption to avoid exceeding limits',
          detectedAt: Date.now()
        });
      }

      // Check for low activity anomalies
      if (metric.duration && metric.eventCount / (metric.duration / 60000) < baseline.minNormalEventRate) {
        anomalies.push({
          id: `anomaly_${Date.now()}_${metric.sessionId}`,
          sessionId: metric.sessionId,
          anomalyType: 'pattern',
          severity: 'low',
          description: 'Unusually low activity detected in this session',
          recommendedAction: 'Session may be inactive or experiencing issues',
          detectedAt: Date.now()
        });
      }
    }

    return anomalies;
  }

  /**
   * Generate optimization recommendations
   */
  private async generateOptimizationRecommendations(): Promise<OptimizationRecommendation[]> {
    const recommendations: OptimizationRecommendation[] = [];
    const analysisData = await this.gatherOptimizationData();

    // Token efficiency recommendation
    if (analysisData.avgTokensPerTask > 1000) {
      recommendations.push({
        id: `opt_${Date.now()}_token_efficiency`,
        type: 'efficiency',
        title: 'Optimize Token Usage',
        description: 'Your average token consumption per task is higher than optimal. Consider breaking down complex requests into smaller, focused queries.',
        potentialImpact: 'high',
        actionItems: [
          'Break complex queries into smaller parts',
          'Use more specific prompts',
          'Leverage context from previous responses',
          'Consider using fewer examples in prompts'
        ],
        basedOnData: {
          sessionCount: analysisData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            avgTokensPerTask: analysisData.avgTokensPerTask,
            potentialSavings: analysisData.avgTokensPerTask * 0.3
          }
        }
      });
    }

    // Session timing recommendation
    if (analysisData.peakProductivityHours.length > 0) {
      recommendations.push({
        id: `opt_${Date.now()}_timing`,
        type: 'productivity',
        title: 'Optimize Session Timing',
        description: `Your productivity peaks at ${analysisData.peakProductivityHours.join(', ')}. Schedule important work during these hours for better results.`,
        potentialImpact: 'medium',
        actionItems: [
          `Schedule complex tasks between ${analysisData.peakProductivityHours[0]}:00-${analysisData.peakProductivityHours[0] + 2}:00`,
          'Use off-peak hours for routine or administrative tasks',
          'Block calendar during peak hours for focused work'
        ],
        basedOnData: {
          sessionCount: analysisData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            peakHours: analysisData.peakProductivityHours,
            productivityGain: 25 // percentage
          }
        }
      });
    }

    // Cost optimization recommendation
    if (analysisData.dailyTokenUsage > 50000) {
      recommendations.push({
        id: `opt_${Date.now()}_cost`,
        type: 'cost',
        title: 'Reduce Token Consumption',
        description: 'High daily token usage detected. Implementing efficiency measures could reduce costs while maintaining productivity.',
        potentialImpact: 'high',
        actionItems: [
          'Review and optimize frequent queries',
          'Use shorter prompts where possible',
          'Implement response caching for repetitive tasks',
          'Consider using lighter models for simple tasks'
        ],
        basedOnData: {
          sessionCount: analysisData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            dailyTokenUsage: analysisData.dailyTokenUsage,
            monthlyCost: analysisData.estimatedMonthlyCost,
            potentialSavings: analysisData.estimatedMonthlyCost * 0.25
          }
        }
      });
    }

    return recommendations;
  }

  /**
   * Analyze session health metrics
   */
  private async analyzeSessionHealth(): Promise<any> {
    const metrics = getAllActiveSessionMetrics();
    
    let longSessionsCount = 0;
    let totalLongSessionDuration = 0;
    let totalActiveTime = 0;
    let totalBreakTime = 0;
    
    const burnoutFactors: string[] = [];

    for (const metric of metrics) {
      const durationHours = (metric.duration || 0) / (1000 * 60 * 60);
      
      if (durationHours > 4) {
        longSessionsCount++;
        totalLongSessionDuration += durationHours;
      }

      totalActiveTime += metric.duration || 0;
      
      // Estimate break time based on gaps between events
      const events = this.getRecentSessionEvents(metric.sessionId, 100);
      for (let i = 1; i < events.length; i++) {
        const gap = events[i].timestamp - events[i-1].timestamp;
        if (gap > 300000) { // 5+ minute gaps considered breaks
          totalBreakTime += gap;
        }
      }
    }

    const breakFrequency = totalActiveTime > 0 ? totalBreakTime / (totalActiveTime + totalBreakTime) : 0;
    const avgLongSessionDuration = longSessionsCount > 0 ? totalLongSessionDuration / longSessionsCount : 0;

    // Calculate burnout risk
    let burnoutRisk = 0;
    if (longSessionsCount > 3) {
      burnoutRisk += 0.3;
      burnoutFactors.push('Multiple long sessions');
    }
    if (breakFrequency < 0.1) {
      burnoutRisk += 0.3;
      burnoutFactors.push('Insufficient breaks');
    }
    if (avgLongSessionDuration > 6) {
      burnoutRisk += 0.4;
      burnoutFactors.push('Excessive session duration');
    }

    return {
      longSessionsCount,
      averageLongSessionDuration: avgLongSessionDuration,
      breakFrequency,
      burnoutRisk: Math.min(burnoutRisk, 1.0),
      burnoutFactors
    };
  }

  /**
   * Helper methods
   */
  private getRecentSessionEvents(sessionId: string, limit: number): any[] {
    const stmt = this.db.prepare(`
      SELECT timestamp, hook_event_type FROM events 
      WHERE session_id = ? 
      ORDER BY timestamp DESC 
      LIMIT ?
    `);
    
    return stmt.all(sessionId, limit) as any[];
  }

  private calculatePauseFrequency(events: any[]): number {
    if (events.length < 2) return 0;
    
    let pauseCount = 0;
    for (let i = 1; i < events.length; i++) {
      const gap = events[i].timestamp - events[i-1].timestamp;
      if (gap > 60000) { // 1+ minute gaps
        pauseCount++;
      }
    }
    
    return pauseCount / (events.length - 1);
  }

  private calculateBaselineMetrics(metrics: SessionMetrics[]): any {
    if (metrics.length === 0) {
      return {
        maxNormalDuration: 4 * 60 * 60 * 1000, // 4 hours
        maxNormalTokenVelocity: 100,
        minNormalEventRate: 1 // events per minute
      };
    }

    const durations = metrics.map(m => m.duration || 0).filter(d => d > 0);
    const velocities = metrics.map(m => m.tokensPerMinute);
    const eventRates = metrics.map(m => 
      m.duration ? (m.eventCount / (m.duration / 60000)) : 0
    );

    const avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
    const avgVelocity = velocities.reduce((sum, v) => sum + v, 0) / velocities.length;
    const avgEventRate = eventRates.reduce((sum, r) => sum + r, 0) / eventRates.length;

    return {
      maxNormalDuration: avgDuration * 2, // 2x average
      maxNormalTokenVelocity: avgVelocity * 3, // 3x average  
      minNormalEventRate: avgEventRate * 0.3 // 30% of average
    };
  }

  private getPatternRecommendation(patternType: string): string {
    switch (patternType) {
      case 'deep-work':
        return 'Excellent focus! Continue scheduling uninterrupted time blocks for complex tasks.';
      case 'rapid-iteration':
        return 'High activity detected. Ensure you\'re taking breaks to maintain quality.';
      case 'exploration':
        return 'Good exploratory behavior. Consider documenting discoveries for future reference.';
      case 'debugging':
        return 'Systematic debugging approach. Track common issues to build knowledge base.';
      default:
        return 'Continue maintaining good work patterns.';
    }
  }

  private calculatePatternPriority(pattern: UsagePattern): 'low' | 'medium' | 'high' {
    if (pattern.confidence > 0.8 && pattern.characteristics.avgSessionDuration > 240) {
      return 'high';
    }
    if (pattern.confidence > 0.6) {
      return 'medium';
    }
    return 'low';
  }

  private calculateOptimalSessionDuration(productivityData: any): number | null {
    if (productivityData.sessionCount < 3) return null;
    
    // Simple heuristic: optimal duration is where quality * duration product is maximized
    // In practice, this would use more sophisticated analysis
    const avgQuality = productivityData.averageQuality;
    const avgDuration = productivityData.averageDuration;
    
    if (avgQuality > 70 && avgDuration < 120) {
      return avgDuration * 1.5; // Suggest longer sessions
    } else if (avgQuality < 50 && avgDuration > 90) {
      return avgDuration * 0.7; // Suggest shorter sessions
    }
    
    return null;
  }

  private analyzeTokenEfficiency(productivityData: any): SessionInsight | null {
    // Placeholder for token efficiency analysis
    return null;
  }

  private async gatherOptimizationData(): Promise<any> {
    const stmt = this.db.prepare(`
      SELECT 
        AVG(total_tokens / NULLIF(prompt_count, 0)) as avg_tokens_per_task,
        COUNT(*) as session_count,
        AVG(total_tokens) as daily_token_usage
      FROM session_metrics 
      WHERE start_time > ?
    `);

    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    const result = stmt.get(sevenDaysAgo) as any;
    
    const productivityData = await this.analyzeProductivityTrends();

    return {
      avgTokensPerTask: result?.avg_tokens_per_task || 0,
      sessionCount: result?.session_count || 0,
      dailyTokenUsage: result?.daily_token_usage || 0,
      estimatedMonthlyCost: (result?.daily_token_usage || 0) * 30 * 0.01, // Rough estimate
      peakProductivityHours: productivityData.peakHours
    };
  }

  /**
   * Get recent insights for API
   */
  async getRecentInsights(limit: number = 20): Promise<SessionInsight[]> {
    const stmt = this.db.prepare(`
      SELECT * FROM session_insights 
      ORDER BY created_at DESC 
      LIMIT ?
    `);
    
    const rows = stmt.all(limit) as any[];
    
    return rows.map(row => ({
      id: row.id,
      sessionId: row.session_id,
      insightType: row.insight_type,
      insightData: JSON.parse(row.insight_data),
      priority: row.priority,
      createdAt: row.created_at
    }));
  }

  /**
   * Generate session quality metrics
   */
  async calculateSessionQuality(sessionId: string): Promise<SessionQualityMetrics | null> {
    const metrics = getSessionMetrics(sessionId);
    if (!metrics) return null;

    const events = this.getRecentSessionEvents(sessionId, 200);
    
    // Calculate quality factors
    const consistency = this.calculateConsistencyScore(events);
    const efficiency = this.calculateEfficiencyScore(metrics);
    const focusTime = this.calculateFocusScore(events);
    const errorRate = this.calculateErrorRate(events);
    const completionRate = this.calculateCompletionRate(events);

    // Overall quality score (weighted average)
    const qualityScore = Math.round(
      consistency * 0.2 + 
      efficiency * 0.25 + 
      focusTime * 0.2 + 
      (100 - errorRate) * 0.15 + 
      completionRate * 0.2
    );

    const suggestions = this.generateQualitySuggestions({
      consistency,
      efficiency,
      focusTime,
      errorRate,
      completionRate
    });

    return {
      sessionId,
      qualityScore,
      factors: {
        consistency,
        efficiency,
        focusTime,
        errorRate,
        completionRate
      },
      suggestions
    };
  }

  private calculateConsistencyScore(events: any[]): number {
    if (events.length < 2) return 50;

    const gaps = [];
    for (let i = 1; i < events.length; i++) {
      gaps.push(events[i].timestamp - events[i-1].timestamp);
    }

    const avgGap = gaps.reduce((sum, gap) => sum + gap, 0) / gaps.length;
    const variance = gaps.reduce((sum, gap) => sum + Math.pow(gap - avgGap, 2), 0) / gaps.length;
    
    // Lower variance = higher consistency
    const consistencyScore = Math.max(0, 100 - (Math.sqrt(variance) / 1000));
    return Math.min(100, consistencyScore);
  }

  private calculateEfficiencyScore(metrics: SessionMetrics): number {
    const toolUsageRatio = metrics.toolUsageCount / Math.max(metrics.eventCount, 1);
    const tokensPerEvent = metrics.totalTokens / Math.max(metrics.eventCount, 1);
    
    // Balanced tool usage and reasonable tokens per event = efficiency
    const balanceScore = 100 - Math.abs(toolUsageRatio - 0.5) * 100;
    const tokenEfficiency = Math.max(0, 100 - (tokensPerEvent - 100) / 10);
    
    return (balanceScore + tokenEfficiency) / 2;
  }

  private calculateFocusScore(events: any[]): number {
    if (events.length < 2) return 50;

    const longPauses = events.slice(1).filter((event, index) => 
      event.timestamp - events[index].timestamp > 300000 // 5+ minute gaps
    ).length;

    const focusScore = Math.max(0, 100 - (longPauses / events.length) * 200);
    return Math.min(100, focusScore);
  }

  private calculateErrorRate(events: any[]): number {
    // Placeholder - would analyze error patterns in actual implementation
    return Math.random() * 10; // 0-10% error rate
  }

  private calculateCompletionRate(events: any[]): number {
    const stops = events.filter(e => e.hook_event_type === 'Stop').length;
    const prompts = events.filter(e => e.hook_event_type === 'UserPromptSubmit').length;
    
    if (prompts === 0) return 50;
    
    // Assumption: more stops relative to prompts = higher completion rate
    return Math.min(100, (stops / prompts) * 100);
  }

  private generateQualitySuggestions(factors: any): string[] {
    const suggestions = [];

    if (factors.consistency < 60) {
      suggestions.push('Try to maintain more consistent interaction patterns');
    }
    if (factors.efficiency < 60) {
      suggestions.push('Consider optimizing tool usage and token consumption');
    }
    if (factors.focusTime < 60) {
      suggestions.push('Take shorter breaks to maintain focus');
    }
    if (factors.errorRate > 20) {
      suggestions.push('Review and double-check inputs to reduce errors');
    }
    if (factors.completionRate < 60) {
      suggestions.push('Focus on completing tasks before starting new ones');
    }

    if (suggestions.length === 0) {
      suggestions.push('Great session quality! Keep up the good work.');
    }

    return suggestions;
  }
}