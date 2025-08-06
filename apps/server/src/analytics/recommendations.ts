import { Database } from 'bun:sqlite';
import { subDays, format, isWithinInterval } from 'date-fns';
import type { 
  OptimizationRecommendation,
  SessionMetrics,
  SessionInsight,
  SessionQualityMetrics
} from '../analytics-types';
import { 
  getAllActiveSessionMetrics,
  getOptimizationRecommendations,
  getSessionInsights
} from '../analytics-db';

export class RecommendationEngine {
  private db: Database;
  
  constructor() {
    this.db = new Database('events.db');
  }

  /**
   * Generate comprehensive recommendations based on user behavior and analytics
   */
  async generateRecommendations(): Promise<OptimizationRecommendation[]> {
    const recommendations: OptimizationRecommendation[] = [];
    
    try {
      // Generate different types of recommendations
      const efficiencyRecs = await this.generateEfficiencyRecommendations();
      const productivityRecs = await this.generateProductivityRecommendations();
      const costRecs = await this.generateCostOptimizationRecommendations();
      const healthRecs = await this.generateHealthRecommendations();
      const learningRecs = await this.generateLearningRecommendations();

      recommendations.push(...efficiencyRecs);
      recommendations.push(...productivityRecs);
      recommendations.push(...costRecs);
      recommendations.push(...healthRecs);
      recommendations.push(...learningRecs);

      // Sort by potential impact and relevance
      return this.prioritizeRecommendations(recommendations);
      
    } catch (error) {
      console.error('Error generating recommendations:', error);
      return [];
    }
  }

  /**
   * Generate efficiency-focused recommendations
   */
  private async generateEfficiencyRecommendations(): Promise<OptimizationRecommendation[]> {
    const recommendations: OptimizationRecommendation[] = [];
    const metrics = getAllActiveSessionMetrics();
    const behaviorData = await this.analyzeBehaviorPatterns();

    // Tool usage optimization
    if (behaviorData.avgToolUsageRatio < 0.3) {
      recommendations.push({
        id: `eff_${Date.now()}_tool_usage`,
        type: 'efficiency',
        title: 'Increase Tool Utilization',
        description: 'You\'re underutilizing available tools. Leveraging more tools could significantly boost your productivity and output quality.',
        potentialImpact: 'high',
        actionItems: [
          'Explore available tools in your current workflow',
          'Set up keyboard shortcuts for frequently used tools',
          'Practice integrating tools into your regular tasks',
          'Review tool documentation to discover advanced features'
        ],
        basedOnData: {
          sessionCount: behaviorData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            currentToolUsage: Math.round(behaviorData.avgToolUsageRatio * 100),
            targetToolUsage: 50,
            potentialProductivityGain: 35
          }
        }
      });
    }

    // Response iteration optimization
    if (behaviorData.avgIterationsPerTask > 3) {
      recommendations.push({
        id: `eff_${Date.now()}_iterations`,
        type: 'efficiency',
        title: 'Reduce Task Iterations',
        description: 'High iteration count suggests prompts could be more specific. More precise initial requests can reduce back-and-forth.',
        potentialImpact: 'medium',
        actionItems: [
          'Provide more context in initial prompts',
          'Specify desired output format upfront',
          'Include relevant constraints and requirements',
          'Use examples to clarify expectations'
        ],
        basedOnData: {
          sessionCount: behaviorData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            avgIterations: behaviorData.avgIterationsPerTask,
            targetIterations: 2,
            timeSavingsPerTask: 3.5
          }
        }
      });
    }

    // Session fragmentation optimization
    if (behaviorData.sessionFragmentation > 0.6) {
      recommendations.push({
        id: `eff_${Date.now()}_fragmentation`,
        type: 'efficiency',
        title: 'Reduce Session Fragmentation',
        description: 'Your sessions are highly fragmented with many interruptions. Consolidating focused work blocks could improve efficiency.',
        potentialImpact: 'medium',
        actionItems: [
          'Block dedicated time slots for focused work',
          'Turn off non-essential notifications during sessions',
          'Prepare materials and context before starting',
          'Use the Pomodoro technique for time management'
        ],
        basedOnData: {
          sessionCount: behaviorData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            fragmentationScore: Math.round(behaviorData.sessionFragmentation * 100),
            averageInterruptions: behaviorData.avgInterruptions,
            focusTimeGain: 25
          }
        }
      });
    }

    return recommendations;
  }

  /**
   * Generate productivity-focused recommendations
   */
  private async generateProductivityRecommendations(): Promise<OptimizationRecommendation[]> {
    const recommendations: OptimizationRecommendation[] = [];
    const productivityData = await this.analyzeProductivityPatterns();

    // Peak hours optimization
    if (productivityData.peakHours.length > 0 && productivityData.offPeakUsage > 0.4) {
      recommendations.push({
        id: `prod_${Date.now()}_peak_hours`,
        type: 'productivity',
        title: 'Optimize Session Timing',
        description: `Your productivity peaks at ${this.formatHours(productivityData.peakHours)}. Scheduling more work during these times could boost overall output.`,
        potentialImpact: 'high',
        actionItems: [
          `Block calendar for focused work during ${this.formatHours(productivityData.peakHours)}`,
          'Move routine tasks to off-peak hours',
          'Schedule important meetings outside peak hours',
          'Use peak hours for your most challenging work'
        ],
        basedOnData: {
          sessionCount: productivityData.sessionCount,
          timespan: '14 days',
          keyMetrics: {
            peakHours: productivityData.peakHours,
            peakProductivityBoost: productivityData.peakBoost,
            currentPeakUtilization: Math.round((1 - productivityData.offPeakUsage) * 100)
          }
        }
      });
    }

    // Session length optimization
    if (productivityData.optimalDuration && Math.abs(productivityData.optimalDuration - productivityData.avgDuration) > 30) {
      const action = productivityData.optimalDuration > productivityData.avgDuration ? 'extend' : 'shorten';
      recommendations.push({
        id: `prod_${Date.now()}_duration`,
        type: 'productivity',
        title: `Optimize Session Duration`,
        description: `Analysis suggests ${action}ing your sessions to ~${Math.round(productivityData.optimalDuration)} minutes could improve productivity.`,
        potentialImpact: 'medium',
        actionItems: [
          `Plan sessions for approximately ${Math.round(productivityData.optimalDuration)} minutes`,
          action === 'extend' ? 'Allow more time for complex tasks' : 'Break large tasks into smaller chunks',
          'Set timers to maintain optimal session length',
          'Monitor productivity metrics to validate changes'
        ],
        basedOnData: {
          sessionCount: productivityData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            currentAvgDuration: Math.round(productivityData.avgDuration),
            optimalDuration: Math.round(productivityData.optimalDuration),
            productivityGain: Math.round(productivityData.potentialGain)
          }
        }
      });
    }

    // Context switching reduction
    if (productivityData.contextSwitches > 5) {
      recommendations.push({
        id: `prod_${Date.now()}_context_switching`,
        type: 'productivity',
        title: 'Reduce Context Switching',
        description: 'High context switching detected. Grouping similar tasks could improve focus and reduce cognitive load.',
        potentialImpact: 'medium',
        actionItems: [
          'Batch similar tasks together',
          'Complete one type of work before switching',
          'Use task lists to maintain focus',
          'Set specific times for checking messages/updates'
        ],
        basedOnData: {
          sessionCount: productivityData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            avgContextSwitches: productivityData.contextSwitches,
            targetSwitches: 3,
            focusImprovement: 20
          }
        }
      });
    }

    return recommendations;
  }

  /**
   * Generate cost optimization recommendations
   */
  private async generateCostOptimizationRecommendations(): Promise<OptimizationRecommendation[]> {
    const recommendations: OptimizationRecommendation[] = [];
    const costData = await this.analyzeCostPatterns();

    // High token usage optimization
    if (costData.dailyTokenUsage > 30000) {
      recommendations.push({
        id: `cost_${Date.now()}_token_usage`,
        type: 'cost',
        title: 'Optimize Token Consumption',
        description: `High token usage detected (${Math.round(costData.dailyTokenUsage / 1000)}K tokens/day). Implementing efficiency measures could reduce costs by up to 30%.`,
        potentialImpact: 'high',
        actionItems: [
          'Use more concise prompts without losing clarity',
          'Avoid repeating context that\'s already established',
          'Break complex requests into focused sub-tasks',
          'Review high-token operations and optimize them'
        ],
        basedOnData: {
          sessionCount: costData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            dailyTokenUsage: Math.round(costData.dailyTokenUsage),
            estimatedMonthlyCost: costData.estimatedMonthlyCost,
            potentialSavings: Math.round(costData.estimatedMonthlyCost * 0.3)
          }
        }
      });
    }

    // Inefficient query patterns
    if (costData.avgTokensPerPrompt > 2000) {
      recommendations.push({
        id: `cost_${Date.now()}_query_efficiency`,
        type: 'cost',
        title: 'Improve Query Efficiency',
        description: 'Your prompts average higher token usage than optimal. More focused queries could maintain quality while reducing costs.',
        potentialImpact: 'medium',
        actionItems: [
          'Focus each prompt on a single specific task',
          'Remove unnecessary background information',
          'Use bullet points instead of long paragraphs',
          'Reference previous context instead of repeating it'
        ],
        basedOnData: {
          sessionCount: costData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            avgTokensPerPrompt: Math.round(costData.avgTokensPerPrompt),
            targetTokensPerPrompt: 1500,
            costSavingsPerPrompt: 0.5
          }
        }
      });
    }

    return recommendations;
  }

  /**
   * Generate health and wellness recommendations
   */
  private async generateHealthRecommendations(): Promise<OptimizationRecommendation[]> {
    const recommendations: OptimizationRecommendation[] = [];
    const healthData = await this.analyzeHealthPatterns();

    // Long session warnings
    if (healthData.avgSessionLength > 240) {
      recommendations.push({
        id: `health_${Date.now()}_long_sessions`,
        type: 'health',
        title: 'Take Regular Breaks',
        description: `Your sessions average ${Math.round(healthData.avgSessionLength)} minutes. Taking regular breaks can improve focus and prevent burnout.`,
        potentialImpact: 'medium',
        actionItems: [
          'Take a 10-15 minute break every hour',
          'Use the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds',
          'Stand and stretch during breaks',
          'Consider splitting long sessions into focused blocks'
        ],
        basedOnData: {
          sessionCount: healthData.sessionCount,
          timespan: '7 days',
          keyMetrics: {
            avgSessionLength: Math.round(healthData.avgSessionLength),
            recommendedMaxLength: 90,
            wellnessImpact: 'Reduced eye strain and improved focus'
          }
        }
      });
    }

    // Burnout risk detection
    if (healthData.burnoutRisk > 0.6) {
      recommendations.push({
        id: `health_${Date.now()}_burnout`,
        type: 'health',
        title: 'Manage Workload to Prevent Burnout',
        description: 'Analysis indicates elevated burnout risk. Consider adjusting your work patterns to maintain long-term productivity.',
        potentialImpact: 'high',
        actionItems: [
          'Schedule mandatory downtime between intensive sessions',
          'Set daily limits on work hours',
          'Vary your tasks to prevent monotony',
          'Consider delegating or postponing non-critical work'
        ],
        basedOnData: {
          sessionCount: healthData.sessionCount,
          timespan: '14 days',
          keyMetrics: {
            burnoutRisk: Math.round(healthData.burnoutRisk * 100),
            riskFactors: healthData.riskFactors,
            sustainabilityGain: 'Long-term productivity preservation'
          }
        }
      });
    }

    // Work-life balance
    if (healthData.afterHoursUsage > 0.3) {
      recommendations.push({
        id: `health_${Date.now()}_work_life_balance`,
        type: 'health',
        title: 'Improve Work-Life Boundaries',
        description: `${Math.round(healthData.afterHoursUsage * 100)}% of your usage occurs outside typical work hours. Setting boundaries can improve overall well-being.`,
        potentialImpact: 'medium',
        actionItems: [
          'Define specific work hours and stick to them',
          'Use \"Do Not Disturb\" settings outside work hours',
          'Create a dedicated workspace separate from relaxation areas',
          'Practice digital detox periods'
        ],
        basedOnData: {
          sessionCount: healthData.sessionCount,
          timespan: '14 days',
          keyMetrics: {
            afterHoursPercentage: Math.round(healthData.afterHoursUsage * 100),
            targetPercentage: 15,
            wellnessImprovement: 'Better sleep and personal time'
          }
        }
      });
    }

    return recommendations;
  }

  /**
   * Generate learning and development recommendations
   */
  private async generateLearningRecommendations(): Promise<OptimizationRecommendation[]> {
    const recommendations: OptimizationRecommendation[] = [];
    const learningData = await this.analyzeLearningPatterns();

    // Skill development opportunities
    if (learningData.underutilizedFeatures.length > 0) {
      recommendations.push({
        id: `learn_${Date.now()}_features`,
        type: 'productivity',
        title: 'Explore Advanced Features',
        description: `You haven't used ${learningData.underutilizedFeatures.length} potentially valuable features. Learning these could enhance your capabilities.`,
        potentialImpact: 'medium',
        actionItems: [
          `Explore: ${learningData.underutilizedFeatures.slice(0, 3).join(', ')}`,
          'Set aside time each week to try new features',
          'Review feature documentation and examples',
          'Practice new features on low-risk tasks first'
        ],
        basedOnData: {
          sessionCount: learningData.sessionCount,
          timespan: '30 days',
          keyMetrics: {
            underutilizedFeatures: learningData.underutilizedFeatures.length,
            featureAdoptionRate: Math.round(learningData.adoptionRate * 100),
            capabilityExpansion: 'New tools and workflows'
          }
        }
      });
    }

    // Pattern recognition improvement
    if (learningData.repetitivePatterns > 3) {
      recommendations.push({
        id: `learn_${Date.now()}_patterns`,
        type: 'efficiency',
        title: 'Automate Repetitive Patterns',
        description: `Detected ${learningData.repetitivePatterns} repetitive patterns. Creating templates or shortcuts could save significant time.`,
        potentialImpact: 'high',
        actionItems: [
          'Identify your most common query patterns',
          'Create templates for frequent use cases',
          'Set up keyboard shortcuts for common actions',
          'Document your best practices for consistency'
        ],
        basedOnData: {
          sessionCount: learningData.sessionCount,
          timespan: '14 days',
          keyMetrics: {
            repetitivePatterns: learningData.repetitivePatterns,
            timeSavingsPotential: Math.round(learningData.timeSavingsPotential),
            efficiencyGain: 'Faster task completion'
          }
        }
      });
    }

    return recommendations;
  }

  /**
   * Prioritize recommendations by impact and relevance
   */
  private prioritizeRecommendations(recommendations: OptimizationRecommendation[]): OptimizationRecommendation[] {
    const priorityScores = recommendations.map(rec => ({
      recommendation: rec,
      score: this.calculatePriorityScore(rec)
    }));

    priorityScores.sort((a, b) => b.score - a.score);
    
    // Return top 10 recommendations to avoid overwhelming the user
    return priorityScores.slice(0, 10).map(item => item.recommendation);
  }

  /**
   * Calculate priority score for recommendations
   */
  private calculatePriorityScore(rec: OptimizationRecommendation): number {
    let score = 0;

    // Impact weighting
    switch (rec.potentialImpact) {
      case 'high': score += 50; break;
      case 'medium': score += 30; break;
      case 'low': score += 10; break;
    }

    // Type weighting (prioritize certain types)
    switch (rec.type) {
      case 'health': score += 20; break; // Prioritize health
      case 'cost': score += 15; break; // Cost savings important
      case 'efficiency': score += 12; break;
      case 'productivity': score += 10; break;
    }

    // Recency bonus (newer data is more relevant)
    const dataAge = Date.now() - (rec.basedOnData.timespan === '7 days' ? 7 : 14) * 24 * 60 * 60 * 1000;
    if (dataAge < 7 * 24 * 60 * 60 * 1000) { // Within last week
      score += 10;
    }

    // Sample size bonus (more data = more confidence)
    if (rec.basedOnData.sessionCount > 20) {
      score += 5;
    }

    return score;
  }

  /**
   * Analytics helper methods
   */
  private async analyzeBehaviorPatterns(): Promise<any> {
    const stmt = this.db.prepare(`
      SELECT 
        AVG(CAST(tool_usage_count AS FLOAT) / NULLIF(event_count, 0)) as avg_tool_usage_ratio,
        COUNT(*) as session_count,
        AVG(event_count) as avg_events_per_session
      FROM session_metrics 
      WHERE start_time > ?
    `);

    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    const result = stmt.get(sevenDaysAgo) as any;

    // Calculate additional metrics
    const iterationsData = await this.calculateIterationMetrics();
    const fragmentationData = await this.calculateFragmentationMetrics();

    return {
      avgToolUsageRatio: result?.avg_tool_usage_ratio || 0,
      sessionCount: result?.session_count || 0,
      avgEventsPerSession: result?.avg_events_per_session || 0,
      avgIterationsPerTask: iterationsData.avgIterations,
      sessionFragmentation: fragmentationData.fragmentation,
      avgInterruptions: fragmentationData.interruptions
    };
  }

  private async analyzeProductivityPatterns(): Promise<any> {
    // Analyze hourly productivity patterns
    const hourlyData = await this.getHourlyProductivityData();
    const peakHours = this.identifyPeakHours(hourlyData);
    
    // Calculate session duration patterns
    const durationData = await this.analyzeDurationPatterns();
    
    // Context switching analysis
    const contextData = await this.analyzeContextSwitching();

    return {
      peakHours: peakHours.hours,
      peakBoost: peakHours.boost,
      offPeakUsage: peakHours.offPeakRatio,
      sessionCount: durationData.sessionCount,
      avgDuration: durationData.avgDuration,
      optimalDuration: durationData.optimalDuration,
      potentialGain: durationData.potentialGain,
      contextSwitches: contextData.avgSwitches
    };
  }

  private async analyzeCostPatterns(): Promise<any> {
    const stmt = this.db.prepare(`
      SELECT 
        AVG(total_tokens) as daily_token_usage,
        AVG(CAST(total_tokens AS FLOAT) / NULLIF(prompt_count, 0)) as avg_tokens_per_prompt,
        COUNT(*) as session_count
      FROM session_metrics 
      WHERE start_time > ?
    `);

    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    const result = stmt.get(sevenDaysAgo) as any;

    const dailyTokenUsage = result?.daily_token_usage || 0;
    const estimatedMonthlyCost = dailyTokenUsage * 30 * 0.015 / 1000; // Rough estimate

    return {
      dailyTokenUsage,
      avgTokensPerPrompt: result?.avg_tokens_per_prompt || 0,
      sessionCount: result?.session_count || 0,
      estimatedMonthlyCost
    };
  }

  private async analyzeHealthPatterns(): Promise<any> {
    const stmt = this.db.prepare(`
      SELECT 
        AVG(CAST(duration AS FLOAT) / (1000 * 60)) as avg_session_minutes,
        COUNT(*) as session_count,
        COUNT(CASE WHEN duration > 4 * 60 * 60 * 1000 THEN 1 END) as long_sessions
      FROM session_metrics 
      WHERE start_time > ?
    `);

    const fourteenDaysAgo = Date.now() - (14 * 24 * 60 * 60 * 1000);
    const result = stmt.get(fourteenDaysAgo) as any;

    // Calculate after-hours usage
    const afterHoursUsage = await this.calculateAfterHoursUsage();
    
    // Calculate burnout risk factors
    const burnoutRisk = this.calculateBurnoutRisk(result, afterHoursUsage);

    return {
      avgSessionLength: result?.avg_session_minutes || 0,
      sessionCount: result?.session_count || 0,
      longSessionsCount: result?.long_sessions || 0,
      afterHoursUsage: afterHoursUsage.ratio,
      burnoutRisk: burnoutRisk.risk,
      riskFactors: burnoutRisk.factors
    };
  }

  private async analyzeLearningPatterns(): Promise<any> {
    // Analyze feature usage patterns
    const featureUsage = await this.analyzeFeatureUsage();
    const repetitivePatterns = await this.identifyRepetitivePatterns();

    return {
      underutilizedFeatures: featureUsage.unused,
      adoptionRate: featureUsage.adoptionRate,
      repetitivePatterns: repetitivePatterns.count,
      timeSavingsPotential: repetitivePatterns.timeSavings,
      sessionCount: featureUsage.sessionCount
    };
  }

  // Helper methods for calculations
  private async calculateIterationMetrics(): Promise<any> {
    // Simplified - in practice would analyze conversation threads
    return { avgIterations: 2.5 };
  }

  private async calculateFragmentationMetrics(): Promise<any> {
    // Simplified - would analyze session gaps and interruptions
    return { fragmentation: 0.4, interruptions: 3.2 };
  }

  private async getHourlyProductivityData(): Promise<any[]> {
    // Simplified - would calculate productivity by hour
    return Array.from({ length: 24 }, (_, hour) => ({
      hour,
      productivity: Math.random() * 100,
      sessionCount: Math.floor(Math.random() * 10)
    }));
  }

  private identifyPeakHours(hourlyData: any[]): any {
    const sorted = hourlyData
      .filter(h => h.sessionCount > 0)
      .sort((a, b) => b.productivity - a.productivity);
    
    const topHours = sorted.slice(0, 3).map(h => h.hour);
    const avgProductivity = hourlyData.reduce((sum, h) => sum + h.productivity, 0) / 24;
    const peakProductivity = sorted[0]?.productivity || 0;
    
    return {
      hours: topHours,
      boost: ((peakProductivity - avgProductivity) / avgProductivity) * 100,
      offPeakRatio: 0.4 // Simplified
    };
  }

  private async analyzeDurationPatterns(): Promise<any> {
    // Simplified duration analysis
    return {
      sessionCount: 15,
      avgDuration: 85,
      optimalDuration: 120,
      potentialGain: 15
    };
  }

  private async analyzeContextSwitching(): Promise<any> {
    // Simplified context switching analysis
    return { avgSwitches: 4.2 };
  }

  private async calculateAfterHoursUsage(): Promise<any> {
    // Simplified - would analyze usage outside 9-5
    return { ratio: 0.25 };
  }

  private calculateBurnoutRisk(sessionData: any, afterHours: any): any {
    let risk = 0;
    const factors = [];

    if (sessionData.avg_session_minutes > 180) {
      risk += 0.3;
      factors.push('Long session duration');
    }
    
    if (afterHours.ratio > 0.4) {
      risk += 0.2;
      factors.push('High after-hours usage');
    }

    if (sessionData.long_sessions > 5) {
      risk += 0.3;
      factors.push('Multiple long sessions');
    }

    return { risk: Math.min(risk, 1.0), factors };
  }

  private async analyzeFeatureUsage(): Promise<any> {
    // Simplified feature usage analysis
    return {
      unused: ['Advanced search', 'Batch processing', 'Templates'],
      adoptionRate: 0.6,
      sessionCount: 20
    };
  }

  private async identifyRepetitivePatterns(): Promise<any> {
    // Simplified pattern identification
    return {
      count: 4,
      timeSavings: 15 // minutes per day
    };
  }

  private formatHours(hours: number[]): string {
    return hours.map(h => {
      const period = h >= 12 ? 'PM' : 'AM';
      const displayHour = h === 0 ? 12 : h > 12 ? h - 12 : h;
      return `${displayHour}${period}`;
    }).join(', ');
  }

  /**
   * Get personalized recommendations for a specific session
   */
  async getSessionRecommendations(sessionId: string): Promise<OptimizationRecommendation[]> {
    const sessionMetrics = this.db.prepare(`
      SELECT * FROM session_metrics WHERE session_id = ?
    `).get(sessionId) as any;

    if (!sessionMetrics) return [];

    const recommendations: OptimizationRecommendation[] = [];

    // Session-specific recommendations
    const duration = sessionMetrics.duration / (1000 * 60); // in minutes
    const tokenVelocity = sessionMetrics.tokens_per_minute;
    const toolRatio = sessionMetrics.tool_usage_count / sessionMetrics.event_count;

    if (duration > 120) {
      recommendations.push({
        id: `session_${sessionId}_break`,
        type: 'health',
        title: 'Take a Break',
        description: 'This session has been running for over 2 hours. Consider taking a short break to maintain focus.',
        potentialImpact: 'medium',
        actionItems: [
          'Take a 10-15 minute break',
          'Step away from the screen',
          'Do some light stretching',
          'Hydrate and refocus'
        ],
        basedOnData: {
          sessionCount: 1,
          timespan: 'current session',
          keyMetrics: {
            currentDuration: Math.round(duration),
            recommendedBreakInterval: 90
          }
        }
      });
    }

    if (toolRatio < 0.2) {
      recommendations.push({
        id: `session_${sessionId}_tools`,
        type: 'efficiency',
        title: 'Consider Using More Tools',
        description: 'You might benefit from utilizing more available tools in this session to enhance productivity.',
        potentialImpact: 'medium',
        actionItems: [
          'Explore available tools for your current task',
          'Try automating repetitive parts of your work',
          'Look for tool shortcuts and integrations'
        ],
        basedOnData: {
          sessionCount: 1,
          timespan: 'current session',
          keyMetrics: {
            toolUsageRatio: Math.round(toolRatio * 100),
            recommendedRatio: 40
          }
        }
      });
    }

    return recommendations;
  }
}