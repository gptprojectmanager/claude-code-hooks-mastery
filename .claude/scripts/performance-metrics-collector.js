#!/usr/bin/env node

/**
 * Performance Metrics Collection System
 * Raccoglie, analizza e report metriche di performance per il sistema multi-agent
 * Integrato con guardrails e sistema di orchestrazione
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Colors for console output
const colors = {
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
    reset: '\x1b[0m',
    bold: '\x1b[1m'
};

class PerformanceMetricsCollector {
    constructor(config = {}) {
        this.config = {
            // Storage configuration
            metricsDir: config.metricsDir || path.join(__dirname, '../metrics'),
            retention: config.retention || 30, // days
            batchSize: config.batchSize || 100,
            flushInterval: config.flushInterval || 60000, // 1 minute
            
            // Performance thresholds
            responseTimeTargets: {
                'haiku': 5000,   // 5 seconds
                'sonnet': 15000, // 15 seconds  
                'opus': 30000,   // 30 seconds
                'opusplan': 45000 // 45 seconds
            },
            
            // Quality thresholds
            successRateTarget: 0.95,
            errorRateThreshold: 0.05,
            timeoutRateThreshold: 0.02,
            
            ...config
        };
        
        // In-memory metrics buffer
        this.metricsBuffer = [];
        this.sessionMetrics = new Map();
        this.agentMetrics = new Map();
        this.performanceTrends = new Map();
        
        // Initialize storage
        this.initializeStorage();
        this.startPeriodicFlush();
        
        this.sessionId = this.generateSessionId();
        this.sessionStart = Date.now();
        
        console.log(`${colors.green}[METRICS] Performance collector initialized - Session: ${this.sessionId}${colors.reset}`);
    }

    /**
     * Initialize storage directories and files
     */
    initializeStorage() {
        if (!fs.existsSync(this.config.metricsDir)) {
            fs.mkdirSync(this.config.metricsDir, { recursive: true });
        }
        
        // Create subdirectories
        ['daily', 'agents', 'sessions', 'trends'].forEach(dir => {
            const dirPath = path.join(this.config.metricsDir, dir);
            if (!fs.existsSync(dirPath)) {
                fs.mkdirSync(dirPath, { recursive: true });
            }
        });
    }

    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return `session_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    }

    /**
     * Record agent execution metrics
     */
    recordAgentExecution(agentConfig) {
        const metric = {
            id: crypto.randomUUID(),
            timestamp: Date.now(),
            sessionId: this.sessionId,
            type: 'agent_execution',
            agentName: agentConfig.agentName,
            agentModel: agentConfig.agentModel,
            agentCategory: agentConfig.agentCategory,
            taskType: agentConfig.taskType || 'standard',
            complexity: agentConfig.complexity || 'medium',
            startTime: agentConfig.startTime,
            endTime: agentConfig.endTime || Date.now(),
            duration: (agentConfig.endTime || Date.now()) - agentConfig.startTime,
            success: agentConfig.success !== false,
            error: agentConfig.error || null,
            contextSize: agentConfig.contextSize || 0,
            responseSize: agentConfig.responseSize || 0,
            memoryUsage: process.memoryUsage(),
            retryCount: agentConfig.retryCount || 0,
            validationScore: agentConfig.validationScore || null,
            qualityGate: agentConfig.qualityGate || null
        };

        // Add to buffer
        this.metricsBuffer.push(metric);
        
        // Update agent-specific metrics
        this.updateAgentMetrics(metric);
        
        // Update session metrics
        this.updateSessionMetrics(metric);
        
        // Check performance targets
        this.checkPerformanceTargets(metric);
        
        return metric;
    }

    /**
     * Record task orchestration metrics
     */
    recordTaskOrchestration(taskConfig) {
        const metric = {
            id: crypto.randomUUID(),
            timestamp: Date.now(),
            sessionId: this.sessionId,
            type: 'task_orchestration',
            taskId: taskConfig.taskId,
            taskType: taskConfig.taskType,
            complexity: taskConfig.complexity,
            agentsInvolved: taskConfig.agentsInvolved || [],
            startTime: taskConfig.startTime,
            endTime: taskConfig.endTime || Date.now(),
            duration: (taskConfig.endTime || Date.now()) - taskConfig.startTime,
            success: taskConfig.success !== false,
            error: taskConfig.error || null,
            phaseMetrics: taskConfig.phaseMetrics || [],
            totalAgentTime: taskConfig.totalAgentTime || 0,
            parallelEfficiency: taskConfig.parallelEfficiency || 0,
            sequentialSteps: taskConfig.sequentialSteps || 0,
            validationPasses: taskConfig.validationPasses || 0,
            qualityScore: taskConfig.qualityScore || null
        };

        this.metricsBuffer.push(metric);
        this.updateSessionMetrics(metric);
        
        return metric;
    }

    /**
     * Record system health metrics
     */
    recordSystemHealth() {
        const memUsage = process.memoryUsage();
        const cpuUsage = process.cpuUsage();
        
        const metric = {
            id: crypto.randomUUID(),
            timestamp: Date.now(),
            sessionId: this.sessionId,
            type: 'system_health',
            memory: {
                heapUsed: memUsage.heapUsed,
                heapTotal: memUsage.heapTotal,
                external: memUsage.external,
                rss: memUsage.rss,
                usagePercent: (memUsage.heapUsed / memUsage.heapTotal) * 100
            },
            cpu: {
                user: cpuUsage.user,
                system: cpuUsage.system
            },
            uptime: process.uptime(),
            activeAgents: this.getActiveAgentsCount(),
            bufferedMetrics: this.metricsBuffer.length
        };

        this.metricsBuffer.push(metric);
        return metric;
    }

    /**
     * Update agent-specific metrics
     */
    updateAgentMetrics(metric) {
        const key = `${metric.agentName}_${metric.agentModel}`;
        
        if (!this.agentMetrics.has(key)) {
            this.agentMetrics.set(key, {
                agentName: metric.agentName,
                agentModel: metric.agentModel,
                agentCategory: metric.agentCategory,
                totalExecutions: 0,
                successfulExecutions: 0,
                failedExecutions: 0,
                totalDuration: 0,
                averageDuration: 0,
                minDuration: Infinity,
                maxDuration: 0,
                totalRetries: 0,
                contextSizeStats: { min: Infinity, max: 0, avg: 0, total: 0 },
                qualityScores: [],
                errorTypes: new Map(),
                recentExecutions: []
            });
        }

        const stats = this.agentMetrics.get(key);
        
        // Update counters
        stats.totalExecutions++;
        if (metric.success) {
            stats.successfulExecutions++;
        } else {
            stats.failedExecutions++;
            if (metric.error) {
                const errorType = metric.error.split(':')[0];
                stats.errorTypes.set(errorType, (stats.errorTypes.get(errorType) || 0) + 1);
            }
        }
        
        // Update duration stats
        stats.totalDuration += metric.duration;
        stats.averageDuration = stats.totalDuration / stats.totalExecutions;
        stats.minDuration = Math.min(stats.minDuration, metric.duration);
        stats.maxDuration = Math.max(stats.maxDuration, metric.duration);
        stats.totalRetries += metric.retryCount;
        
        // Update context size stats
        if (metric.contextSize > 0) {
            stats.contextSizeStats.total += metric.contextSize;
            stats.contextSizeStats.min = Math.min(stats.contextSizeStats.min, metric.contextSize);
            stats.contextSizeStats.max = Math.max(stats.contextSizeStats.max, metric.contextSize);
            stats.contextSizeStats.avg = stats.contextSizeStats.total / stats.totalExecutions;
        }
        
        // Update quality scores
        if (metric.validationScore !== null) {
            stats.qualityScores.push(metric.validationScore);
            if (stats.qualityScores.length > 100) {
                stats.qualityScores.shift(); // Keep last 100
            }
        }
        
        // Update recent executions
        stats.recentExecutions.push({
            timestamp: metric.timestamp,
            duration: metric.duration,
            success: metric.success,
            contextSize: metric.contextSize,
            qualityScore: metric.validationScore
        });
        
        if (stats.recentExecutions.length > 20) {
            stats.recentExecutions.shift(); // Keep last 20
        }
    }

    /**
     * Update session-level metrics
     */
    updateSessionMetrics(metric) {
        if (!this.sessionMetrics.has(this.sessionId)) {
            this.sessionMetrics.set(this.sessionId, {
                sessionId: this.sessionId,
                startTime: this.sessionStart,
                totalMetrics: 0,
                agentExecutions: 0,
                taskOrchestrations: 0,
                systemHealthChecks: 0,
                successRate: 0,
                averageResponseTime: 0,
                totalAgentsUsed: new Set(),
                errorsByType: new Map(),
                performanceIssues: []
            });
        }

        const session = this.sessionMetrics.get(this.sessionId);
        session.totalMetrics++;
        
        if (metric.type === 'agent_execution') {
            session.agentExecutions++;
            session.totalAgentsUsed.add(`${metric.agentName}_${metric.agentModel}`);
            
            if (!metric.success && metric.error) {
                const errorType = metric.error.split(':')[0];
                session.errorsByType.set(errorType, (session.errorsByType.get(errorType) || 0) + 1);
            }
        } else if (metric.type === 'task_orchestration') {
            session.taskOrchestrations++;
        } else if (metric.type === 'system_health') {
            session.systemHealthChecks++;
        }
        
        // Update success rate
        const successfulExecutions = Array.from(this.metricsBuffer)
            .filter(m => m.sessionId === this.sessionId && m.type === 'agent_execution' && m.success)
            .length;
        session.successRate = session.agentExecutions > 0 ? successfulExecutions / session.agentExecutions : 1;
        
        // Update average response time
        const durations = Array.from(this.metricsBuffer)
            .filter(m => m.sessionId === this.sessionId && m.type === 'agent_execution')
            .map(m => m.duration);
        session.averageResponseTime = durations.length > 0 ? 
            durations.reduce((a, b) => a + b, 0) / durations.length : 0;
    }

    /**
     * Check performance against targets
     */
    checkPerformanceTargets(metric) {
        if (metric.type !== 'agent_execution') return;
        
        const target = this.config.responseTimeTargets[metric.agentModel] || 30000;
        
        if (metric.duration > target * 1.5) {
            console.log(`${colors.red}[METRICS] Performance issue: ${metric.agentName} took ${metric.duration}ms (target: ${target}ms)${colors.reset}`);
        } else if (metric.duration > target) {
            console.log(`${colors.yellow}[METRICS] Performance warning: ${metric.agentName} took ${metric.duration}ms (target: ${target}ms)${colors.reset}`);
        }
    }

    /**
     * Generate performance report
     */
    generatePerformanceReport(timeframe = '1d') {
        const now = Date.now();
        const timeframes = {
            '1h': 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '7d': 7 * 24 * 60 * 60 * 1000,
            '30d': 30 * 24 * 60 * 60 * 1000
        };
        
        const timeLimit = now - (timeframes[timeframe] || timeframes['1d']);
        const relevantMetrics = this.metricsBuffer.filter(m => m.timestamp >= timeLimit);
        
        const report = {
            timeframe,
            period: {
                start: new Date(timeLimit).toISOString(),
                end: new Date(now).toISOString()
            },
            summary: this.generateSummaryStats(relevantMetrics),
            agentPerformance: this.generateAgentPerformanceStats(relevantMetrics),
            systemHealth: this.generateSystemHealthStats(relevantMetrics),
            trends: this.generateTrendAnalysis(relevantMetrics),
            recommendations: this.generateRecommendations(relevantMetrics)
        };
        
        return report;
    }

    /**
     * Generate summary statistics
     */
    generateSummaryStats(metrics) {
        const agentExecutions = metrics.filter(m => m.type === 'agent_execution');
        const successful = agentExecutions.filter(m => m.success);
        
        return {
            totalMetrics: metrics.length,
            agentExecutions: agentExecutions.length,
            successRate: agentExecutions.length > 0 ? successful.length / agentExecutions.length : 1,
            averageResponseTime: agentExecutions.length > 0 ? 
                agentExecutions.reduce((sum, m) => sum + m.duration, 0) / agentExecutions.length : 0,
            uniqueAgentsUsed: new Set(agentExecutions.map(m => `${m.agentName}_${m.agentModel}`)).size,
            totalRetries: agentExecutions.reduce((sum, m) => sum + (m.retryCount || 0), 0),
            errorRate: agentExecutions.length > 0 ? 
                agentExecutions.filter(m => !m.success).length / agentExecutions.length : 0
        };
    }

    /**
     * Generate agent performance statistics
     */
    generateAgentPerformanceStats(metrics) {
        const agentStats = new Map();
        
        metrics
            .filter(m => m.type === 'agent_execution')
            .forEach(metric => {
                const key = `${metric.agentName}_${metric.agentModel}`;
                
                if (!agentStats.has(key)) {
                    agentStats.set(key, {
                        agentName: metric.agentName,
                        agentModel: metric.agentModel,
                        executions: 0,
                        successes: 0,
                        durations: [],
                        qualityScores: []
                    });
                }
                
                const stats = agentStats.get(key);
                stats.executions++;
                if (metric.success) stats.successes++;
                stats.durations.push(metric.duration);
                if (metric.validationScore !== null) {
                    stats.qualityScores.push(metric.validationScore);
                }
            });
        
        // Convert to final format
        return Array.from(agentStats.entries()).map(([key, stats]) => ({
            agent: key,
            executions: stats.executions,
            successRate: stats.successes / stats.executions,
            averageDuration: stats.durations.reduce((a, b) => a + b, 0) / stats.durations.length,
            medianDuration: this.calculateMedian(stats.durations),
            p95Duration: this.calculatePercentile(stats.durations, 95),
            averageQuality: stats.qualityScores.length > 0 ? 
                stats.qualityScores.reduce((a, b) => a + b, 0) / stats.qualityScores.length : null,
            performanceGrade: this.calculatePerformanceGrade(stats, key)
        })).sort((a, b) => b.executions - a.executions);
    }

    /**
     * Generate system health statistics
     */
    generateSystemHealthStats(metrics) {
        const healthMetrics = metrics.filter(m => m.type === 'system_health');
        
        if (healthMetrics.length === 0) return null;
        
        const memoryUsages = healthMetrics.map(m => m.memory.usagePercent);
        const activeAgentCounts = healthMetrics.map(m => m.activeAgents);
        
        return {
            samplesCount: healthMetrics.length,
            memory: {
                averageUsage: memoryUsages.reduce((a, b) => a + b, 0) / memoryUsages.length,
                peakUsage: Math.max(...memoryUsages),
                trend: this.calculateTrend(memoryUsages)
            },
            concurrency: {
                averageActiveAgents: activeAgentCounts.reduce((a, b) => a + b, 0) / activeAgentCounts.length,
                peakActiveAgents: Math.max(...activeAgentCounts),
                trend: this.calculateTrend(activeAgentCounts)
            }
        };
    }

    /**
     * Generate trend analysis
     */
    generateTrendAnalysis(metrics) {
        const agentExecutions = metrics.filter(m => m.type === 'agent_execution');
        
        // Group by hour
        const hourlyStats = new Map();
        agentExecutions.forEach(metric => {
            const hour = new Date(metric.timestamp).setMinutes(0, 0, 0);
            
            if (!hourlyStats.has(hour)) {
                hourlyStats.set(hour, {
                    timestamp: hour,
                    executions: 0,
                    successes: 0,
                    totalDuration: 0
                });
            }
            
            const stats = hourlyStats.get(hour);
            stats.executions++;
            if (metric.success) stats.successes++;
            stats.totalDuration += metric.duration;
        });
        
        return Array.from(hourlyStats.values()).map(stats => ({
            timestamp: stats.timestamp,
            executions: stats.executions,
            successRate: stats.successes / stats.executions,
            averageDuration: stats.totalDuration / stats.executions
        })).sort((a, b) => a.timestamp - b.timestamp);
    }

    /**
     * Generate recommendations
     */
    generateRecommendations(metrics) {
        const recommendations = [];
        const summary = this.generateSummaryStats(metrics);
        
        if (summary.successRate < this.config.successRateTarget) {
            recommendations.push({
                type: 'critical',
                message: `Success rate (${(summary.successRate * 100).toFixed(1)}%) below target (${(this.config.successRateTarget * 100)}%)`,
                action: 'Review failing agents and increase timeout limits or reduce task complexity'
            });
        }
        
        if (summary.errorRate > this.config.errorRateThreshold) {
            recommendations.push({
                type: 'warning',
                message: `Error rate (${(summary.errorRate * 100).toFixed(1)}%) above threshold (${(this.config.errorRateThreshold * 100)}%)`,
                action: 'Implement better error handling and retry mechanisms'
            });
        }
        
        if (summary.averageResponseTime > 20000) {
            recommendations.push({
                type: 'performance',
                message: `Average response time (${Math.round(summary.averageResponseTime)}ms) is high`,
                action: 'Consider optimizing agent prompts or increasing computational resources'
            });
        }
        
        if (summary.totalRetries > summary.agentExecutions * 0.1) {
            recommendations.push({
                type: 'reliability',
                message: `High retry rate detected (${summary.totalRetries} retries for ${summary.agentExecutions} executions)`,
                action: 'Investigate root causes of failures and improve system stability'
            });
        }
        
        return recommendations;
    }

    /**
     * Utility functions
     */
    calculateMedian(numbers) {
        const sorted = numbers.slice().sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);
        return sorted.length % 2 === 0 ? 
            (sorted[middle - 1] + sorted[middle]) / 2 : sorted[middle];
    }

    calculatePercentile(numbers, percentile) {
        const sorted = numbers.slice().sort((a, b) => a - b);
        const index = Math.ceil((percentile / 100) * sorted.length) - 1;
        return sorted[index];
    }

    calculateTrend(values) {
        if (values.length < 2) return 'stable';
        
        const recent = values.slice(-Math.min(5, values.length));
        const older = values.slice(0, -Math.min(5, values.length));
        
        if (older.length === 0) return 'stable';
        
        const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
        const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
        
        const change = (recentAvg - olderAvg) / olderAvg;
        
        if (change > 0.1) return 'increasing';
        if (change < -0.1) return 'decreasing';
        return 'stable';
    }

    calculatePerformanceGrade(stats, agentKey) {
        const successRate = stats.successes / stats.executions;
        const avgDuration = stats.durations.reduce((a, b) => a + b, 0) / stats.durations.length;
        const model = agentKey.split('_').pop();
        const target = this.config.responseTimeTargets[model] || 30000;
        
        let score = 100;
        
        // Success rate impact (40% of grade)
        score -= (1 - successRate) * 40;
        
        // Duration impact (40% of grade)
        if (avgDuration > target) {
            score -= Math.min(40, (avgDuration - target) / target * 40);
        }
        
        // Quality impact (20% of grade)
        if (stats.qualityScores.length > 0) {
            const avgQuality = stats.qualityScores.reduce((a, b) => a + b, 0) / stats.qualityScores.length;
            score -= (100 - avgQuality) * 0.2;
        }
        
        if (score >= 90) return 'A';
        if (score >= 80) return 'B';
        if (score >= 70) return 'C';
        if (score >= 60) return 'D';
        return 'F';
    }

    getActiveAgentsCount() {
        // This would need to be integrated with the actual orchestration system
        return this.sessionMetrics.get(this.sessionId)?.totalAgentsUsed?.size || 0;
    }

    /**
     * Periodic operations
     */
    startPeriodicFlush() {
        setInterval(() => {
            this.flushMetrics();
            this.recordSystemHealth();
            this.cleanupOldMetrics();
        }, this.config.flushInterval);
    }

    flushMetrics() {
        if (this.metricsBuffer.length === 0) return;
        
        const today = new Date().toISOString().split('T')[0];
        const filename = path.join(this.config.metricsDir, 'daily', `metrics_${today}.jsonl`);
        
        const metricsToFlush = this.metricsBuffer.splice(0, this.config.batchSize);
        const lines = metricsToFlush.map(metric => JSON.stringify(metric)).join('\n') + '\n';
        
        fs.appendFileSync(filename, lines);
        
        console.log(`${colors.blue}[METRICS] Flushed ${metricsToFlush.length} metrics to ${filename}${colors.reset}`);
    }

    cleanupOldMetrics() {
        const cutoffDate = new Date(Date.now() - this.config.retention * 24 * 60 * 60 * 1000);
        const cutoffDateStr = cutoffDate.toISOString().split('T')[0];
        
        const dailyDir = path.join(this.config.metricsDir, 'daily');
        
        try {
            const files = fs.readdirSync(dailyDir);
            files.forEach(file => {
                if (file.startsWith('metrics_') && file < `metrics_${cutoffDateStr}.jsonl`) {
                    fs.unlinkSync(path.join(dailyDir, file));
                    console.log(`${colors.yellow}[METRICS] Cleaned up old metrics file: ${file}${colors.reset}`);
                }
            });
        } catch (error) {
            console.error(`${colors.red}[METRICS] Error cleaning up old metrics: ${error.message}${colors.reset}`);
        }
    }

    /**
     * Export and reporting
     */
    exportMetrics(format = 'json') {
        const report = this.generatePerformanceReport('1d');
        
        switch (format) {
            case 'json':
                return JSON.stringify(report, null, 2);
            
            case 'csv':
                return this.convertToCSV(report);
            
            case 'console':
                this.printConsoleReport(report);
                return null;
            
            default:
                throw new Error(`Unsupported format: ${format}`);
        }
    }

    printConsoleReport(report) {
        console.log(`\n${colors.bold}${colors.cyan}=== PERFORMANCE METRICS REPORT ===${colors.reset}`);
        console.log(`${colors.blue}Period: ${report.period.start} to ${report.period.end}${colors.reset}`);
        
        console.log(`\n${colors.yellow}SUMMARY:${colors.reset}`);
        console.log(`  Success Rate: ${(report.summary.successRate * 100).toFixed(1)}%`);
        console.log(`  Avg Response Time: ${Math.round(report.summary.averageResponseTime)}ms`);
        console.log(`  Total Executions: ${report.summary.agentExecutions}`);
        console.log(`  Unique Agents: ${report.summary.uniqueAgentsUsed}`);
        console.log(`  Error Rate: ${(report.summary.errorRate * 100).toFixed(1)}%`);
        
        console.log(`\n${colors.yellow}TOP PERFORMING AGENTS:${colors.reset}`);
        report.agentPerformance.slice(0, 5).forEach(agent => {
            console.log(`  ${agent.agent}: Grade ${agent.performanceGrade} (${agent.executions} exec, ${(agent.successRate * 100).toFixed(1)}% success)`);
        });
        
        if (report.recommendations.length > 0) {
            console.log(`\n${colors.yellow}RECOMMENDATIONS:${colors.reset}`);
            report.recommendations.forEach(rec => {
                const color = rec.type === 'critical' ? colors.red : rec.type === 'warning' ? colors.yellow : colors.blue;
                console.log(`  ${color}${rec.type.toUpperCase()}: ${rec.message}${colors.reset}`);
                console.log(`    Action: ${rec.action}`);
            });
        }
        
        console.log(`${colors.cyan}=================================${colors.reset}\n`);
    }
}

// CLI Usage
if (require.main === module) {
    const command = process.argv[2];
    const collector = new PerformanceMetricsCollector();
    
    switch (command) {
        case 'report':
            const timeframe = process.argv[3] || '1d';
            collector.exportMetrics('console');
            break;
        
        case 'export':
            const format = process.argv[3] || 'json';
            const output = collector.exportMetrics(format);
            if (output) console.log(output);
            break;
        
        case 'test':
            console.log('Testing performance metrics collector...');
            
            // Simulate some agent executions
            for (let i = 0; i < 5; i++) {
                collector.recordAgentExecution({
                    agentName: 'test-agent',
                    agentModel: 'sonnet',
                    agentCategory: 'test',
                    startTime: Date.now() - Math.random() * 10000,
                    endTime: Date.now(),
                    success: Math.random() > 0.1,
                    contextSize: Math.floor(Math.random() * 50000),
                    validationScore: Math.random() * 100
                });
            }
            
            setTimeout(() => {
                collector.exportMetrics('console');
            }, 1000);
            break;
        
        default:
            console.log(`
Usage: node performance-metrics-collector.js <command>

Commands:
  report [timeframe]   Generate performance report (1h, 1d, 7d, 30d)
  export [format]      Export metrics (json, csv, console)
  test                 Run test simulation

Example:
  node .claude/scripts/performance-metrics-collector.js report 1d
            `);
    }
}

module.exports = PerformanceMetricsCollector;