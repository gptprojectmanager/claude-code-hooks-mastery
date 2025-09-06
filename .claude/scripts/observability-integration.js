#!/usr/bin/env node

/**
 * Observability Integration
 * Integrates Guardrails Enhancement and Performance Metrics with existing observability system
 * Extends the existing SQLite database and WebSocket system
 */

const { Database } = require('bun:sqlite');
const path = require('path');

// Colors for console output
const colors = {
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
    reset: '\x1b[0m',
    bold: '\x1b[1m'
};

class ObservabilityIntegration {
    constructor(dbPath = null) {
        // Use existing database path from server
        this.dbPath = dbPath || path.join(process.cwd(), 'apps/server/events.db');
        this.db = null;
        this.isInitialized = false;
    }

    /**
     * Initialize database connection and extend schema
     */
    initialize() {
        try {
            this.db = new Database(this.dbPath);
            
            // Enable WAL mode for better concurrent performance
            this.db.exec('PRAGMA journal_mode = WAL');
            this.db.exec('PRAGMA synchronous = NORMAL');
            
            this.extendDatabase();
            this.isInitialized = true;
            
            console.log(`${colors.green}[OBSERVABILITY] Integration initialized with database: ${this.dbPath}${colors.reset}`);
        } catch (error) {
            console.error(`${colors.red}[OBSERVABILITY] Failed to initialize: ${error.message}${colors.reset}`);
            throw error;
        }
    }

    /**
     * Extend existing database with new tables for guardrails and performance metrics
     */
    extendDatabase() {
        // Performance Metrics Table
        this.db.exec(`
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                agent_name TEXT,
                agent_model TEXT,
                agent_category TEXT,
                task_type TEXT,
                complexity TEXT,
                start_time INTEGER,
                end_time INTEGER,
                duration INTEGER,
                success INTEGER NOT NULL,
                error_message TEXT,
                context_size INTEGER,
                response_size INTEGER,
                memory_usage TEXT,
                retry_count INTEGER DEFAULT 0,
                validation_score REAL,
                quality_gate TEXT,
                timestamp INTEGER NOT NULL,
                metadata TEXT
            )
        `);

        // Guardrails Events Table
        this.db.exec(`
            CREATE TABLE IF NOT EXISTS guardrails_events (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                agent_id TEXT,
                agent_type TEXT,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                threshold_value REAL,
                actual_value REAL,
                resolution_action TEXT,
                resolved INTEGER DEFAULT 0,
                timestamp INTEGER NOT NULL,
                metadata TEXT
            )
        `);

        // System Health Metrics Table  
        this.db.exec(`
            CREATE TABLE IF NOT EXISTS system_health (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                memory_heap_used INTEGER,
                memory_heap_total INTEGER,
                memory_external INTEGER,
                memory_rss INTEGER,
                memory_usage_percent REAL,
                cpu_user INTEGER,
                cpu_system INTEGER,
                active_agents INTEGER,
                uptime INTEGER,
                buffered_metrics INTEGER,
                timestamp INTEGER NOT NULL
            )
        `);

        // Agent Performance Summary Table (aggregated data)
        this.db.exec(`
            CREATE TABLE IF NOT EXISTS agent_performance_summary (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                agent_model TEXT NOT NULL,
                agent_category TEXT,
                period_start INTEGER NOT NULL,
                period_end INTEGER NOT NULL,
                total_executions INTEGER NOT NULL,
                successful_executions INTEGER NOT NULL,
                failed_executions INTEGER NOT NULL,
                total_duration INTEGER NOT NULL,
                average_duration REAL NOT NULL,
                min_duration INTEGER NOT NULL,
                max_duration INTEGER NOT NULL,
                p95_duration INTEGER,
                total_retries INTEGER NOT NULL,
                average_context_size REAL,
                average_validation_score REAL,
                performance_grade TEXT,
                last_updated INTEGER NOT NULL,
                UNIQUE(agent_name, agent_model, period_start)
            )
        `);

        // Create indexes for performance
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_perf_session ON performance_metrics(session_id)');
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_perf_agent ON performance_metrics(agent_name, agent_model)');
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_metrics(timestamp)');
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_perf_type ON performance_metrics(metric_type)');
        
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_guard_session ON guardrails_events(session_id)');
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_guard_type ON guardrails_events(event_type)');
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_guard_severity ON guardrails_events(severity)');
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_guard_timestamp ON guardrails_events(timestamp)');
        
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_health_session ON system_health(session_id)');
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_health_timestamp ON system_health(timestamp)');
        
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_summary_agent ON agent_performance_summary(agent_name, agent_model)');
        this.db.exec('CREATE INDEX IF NOT EXISTS idx_summary_period ON agent_performance_summary(period_start, period_end)');

        console.log(`${colors.blue}[OBSERVABILITY] Database schema extended with new tables${colors.reset}`);
    }

    /**
     * Record performance metrics (integrates with existing system)
     */
    recordPerformanceMetric(metric) {
        if (!this.isInitialized) {
            throw new Error('ObservabilityIntegration not initialized');
        }

        const stmt = this.db.prepare(`
            INSERT INTO performance_metrics (
                id, session_id, metric_type, agent_name, agent_model, agent_category,
                task_type, complexity, start_time, end_time, duration, success,
                error_message, context_size, response_size, memory_usage, retry_count,
                validation_score, quality_gate, timestamp, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);

        const id = metric.id || this.generateId();
        const timestamp = metric.timestamp || Date.now();

        stmt.run(
            id,
            metric.sessionId,
            metric.metricType || 'agent_execution',
            metric.agentName,
            metric.agentModel,
            metric.agentCategory,
            metric.taskType,
            metric.complexity,
            metric.startTime,
            metric.endTime,
            metric.duration,
            metric.success ? 1 : 0,
            metric.errorMessage || null,
            metric.contextSize || 0,
            metric.responseSize || 0,
            metric.memoryUsage ? JSON.stringify(metric.memoryUsage) : null,
            metric.retryCount || 0,
            metric.validationScore || null,
            metric.qualityGate || null,
            timestamp,
            metric.metadata ? JSON.stringify(metric.metadata) : null
        );

        // Also record as standard HookEvent for integration with existing system
        this.recordAsHookEvent({
            source_app: 'claude-code-hooks-mastery',
            session_id: metric.sessionId,
            hook_event_type: 'performance_metric',
            payload: {
                metric_id: id,
                agent_name: metric.agentName,
                agent_model: metric.agentModel,
                duration: metric.duration,
                success: metric.success,
                validation_score: metric.validationScore,
                performance_grade: this.calculatePerformanceGrade(metric)
            },
            summary: `Agent ${metric.agentName} executed in ${metric.duration}ms (${metric.success ? 'success' : 'failed'})`
        });

        return id;
    }

    /**
     * Record guardrails events (integrates with existing system)
     */
    recordGuardrailsEvent(event) {
        if (!this.isInitialized) {
            throw new Error('ObservabilityIntegration not initialized');
        }

        const stmt = this.db.prepare(`
            INSERT INTO guardrails_events (
                id, session_id, event_type, agent_id, agent_type, severity,
                message, details, threshold_value, actual_value, resolution_action,
                resolved, timestamp, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);

        const id = event.id || this.generateId();
        const timestamp = event.timestamp || Date.now();

        stmt.run(
            id,
            event.sessionId,
            event.eventType,
            event.agentId || null,
            event.agentType || null,
            event.severity,
            event.message,
            event.details || null,
            event.thresholdValue || null,
            event.actualValue || null,
            event.resolutionAction || null,
            event.resolved ? 1 : 0,
            timestamp,
            event.metadata ? JSON.stringify(event.metadata) : null
        );

        // Also record as standard HookEvent
        this.recordAsHookEvent({
            source_app: 'claude-code-hooks-mastery',
            session_id: event.sessionId,
            hook_event_type: 'guardrails_event',
            payload: {
                guardrails_id: id,
                event_type: event.eventType,
                severity: event.severity,
                message: event.message,
                threshold_value: event.thresholdValue,
                actual_value: event.actualValue,
                resolution_action: event.resolutionAction
            },
            summary: `Guardrails ${event.severity}: ${event.message}`
        });

        return id;
    }

    /**
     * Record system health metrics
     */
    recordSystemHealth(health) {
        if (!this.isInitialized) {
            throw new Error('ObservabilityIntegration not initialized');
        }

        const stmt = this.db.prepare(`
            INSERT INTO system_health (
                id, session_id, memory_heap_used, memory_heap_total, memory_external,
                memory_rss, memory_usage_percent, cpu_user, cpu_system, active_agents,
                uptime, buffered_metrics, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);

        const id = this.generateId();
        const timestamp = Date.now();

        stmt.run(
            id,
            health.sessionId,
            health.memory.heapUsed,
            health.memory.heapTotal,
            health.memory.external,
            health.memory.rss,
            health.memory.usagePercent,
            health.cpu?.user || 0,
            health.cpu?.system || 0,
            health.activeAgents || 0,
            health.uptime || 0,
            health.bufferedMetrics || 0,
            timestamp
        );

        return id;
    }

    /**
     * Record as standard HookEvent for integration with existing observability
     */
    recordAsHookEvent(event) {
        try {
            // Use the existing events table structure
            const stmt = this.db.prepare(`
                INSERT INTO events (source_app, session_id, hook_event_type, payload, chat, summary, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            `);

            const timestamp = Date.now();
            stmt.run(
                event.source_app,
                event.session_id,
                event.hook_event_type,
                JSON.stringify(event.payload),
                event.chat ? JSON.stringify(event.chat) : null,
                event.summary || null,
                timestamp
            );
        } catch (error) {
            console.error(`${colors.red}[OBSERVABILITY] Failed to record hook event: ${error.message}${colors.reset}`);
        }
    }

    /**
     * Get performance metrics for dashboard
     */
    getPerformanceMetrics(sessionId = null, timeframe = '1h') {
        const timeframes = {
            '1h': 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '7d': 7 * 24 * 60 * 60 * 1000
        };

        const timeLimit = Date.now() - (timeframes[timeframe] || timeframes['1h']);
        
        let sql = `
            SELECT * FROM performance_metrics 
            WHERE timestamp >= ?
        `;
        const params = [timeLimit];

        if (sessionId) {
            sql += ' AND session_id = ?';
            params.push(sessionId);
        }

        sql += ' ORDER BY timestamp DESC LIMIT 1000';

        const stmt = this.db.prepare(sql);
        const rows = stmt.all(...params);

        return rows.map(row => ({
            ...row,
            memoryUsage: row.memory_usage ? JSON.parse(row.memory_usage) : null,
            metadata: row.metadata ? JSON.parse(row.metadata) : null,
            success: row.success === 1
        }));
    }

    /**
     * Get guardrails events for dashboard
     */
    getGuardrailsEvents(sessionId = null, severity = null, timeframe = '1h') {
        const timeframes = {
            '1h': 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '7d': 7 * 24 * 60 * 60 * 1000
        };

        const timeLimit = Date.now() - (timeframes[timeframe] || timeframes['1h']);
        
        let sql = `
            SELECT * FROM guardrails_events 
            WHERE timestamp >= ?
        `;
        const params = [timeLimit];

        if (sessionId) {
            sql += ' AND session_id = ?';
            params.push(sessionId);
        }

        if (severity) {
            sql += ' AND severity = ?';
            params.push(severity);
        }

        sql += ' ORDER BY timestamp DESC LIMIT 500';

        const stmt = this.db.prepare(sql);
        const rows = stmt.all(...params);

        return rows.map(row => ({
            ...row,
            metadata: row.metadata ? JSON.parse(row.metadata) : null,
            resolved: row.resolved === 1
        }));
    }

    /**
     * Get system health trends
     */
    getSystemHealthTrends(sessionId = null, timeframe = '1h') {
        const timeframes = {
            '1h': 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '7d': 7 * 24 * 60 * 60 * 1000
        };

        const timeLimit = Date.now() - (timeframes[timeframe] || timeframes['1h']);
        
        let sql = `
            SELECT * FROM system_health 
            WHERE timestamp >= ?
        `;
        const params = [timeLimit];

        if (sessionId) {
            sql += ' AND session_id = ?';
            params.push(sessionId);
        }

        sql += ' ORDER BY timestamp ASC';

        const stmt = this.db.prepare(sql);
        return stmt.all(...params);
    }

    /**
     * Get agent performance summary
     */
    getAgentPerformanceSummary(timeframe = '1d') {
        const timeframes = {
            '1h': 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '7d': 7 * 24 * 60 * 60 * 1000,
            '30d': 30 * 24 * 60 * 60 * 1000
        };

        const timeLimit = Date.now() - (timeframes[timeframe] || timeframes['1d']);

        const sql = `
            SELECT 
                agent_name,
                agent_model,
                agent_category,
                COUNT(*) as total_executions,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful_executions,
                COUNT(CASE WHEN success = 0 THEN 1 END) as failed_executions,
                AVG(duration) as average_duration,
                MIN(duration) as min_duration,
                MAX(duration) as max_duration,
                SUM(retry_count) as total_retries,
                AVG(context_size) as average_context_size,
                AVG(validation_score) as average_validation_score
            FROM performance_metrics 
            WHERE timestamp >= ?
            GROUP BY agent_name, agent_model, agent_category
            ORDER BY total_executions DESC
        `;

        const stmt = this.db.prepare(sql);
        const results = stmt.all(timeLimit);

        return results.map(row => ({
            ...row,
            successRate: row.total_executions > 0 ? row.successful_executions / row.total_executions : 0,
            performanceGrade: this.calculatePerformanceGradeFromSummary(row)
        }));
    }

    /**
     * Generate comprehensive dashboard data
     */
    getDashboardData(sessionId = null, timeframe = '1h') {
        return {
            performance: this.getPerformanceMetrics(sessionId, timeframe),
            guardrails: this.getGuardrailsEvents(sessionId, null, timeframe),
            systemHealth: this.getSystemHealthTrends(sessionId, timeframe),
            agentSummary: this.getAgentPerformanceSummary(timeframe),
            summary: this.calculateSummaryStats(sessionId, timeframe)
        };
    }

    /**
     * Calculate summary statistics
     */
    calculateSummaryStats(sessionId = null, timeframe = '1h') {
        const timeframes = {
            '1h': 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '7d': 7 * 24 * 60 * 60 * 1000
        };

        const timeLimit = Date.now() - (timeframes[timeframe] || timeframes['1h']);
        
        // Performance summary
        let perfSql = `
            SELECT 
                COUNT(*) as total_executions,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful_executions,
                AVG(duration) as average_duration,
                COUNT(DISTINCT agent_name || '_' || agent_model) as unique_agents
            FROM performance_metrics 
            WHERE timestamp >= ?
        `;
        const perfParams = [timeLimit];

        if (sessionId) {
            perfSql += ' AND session_id = ?';
            perfParams.push(sessionId);
        }

        const perfStats = this.db.prepare(perfSql).get(...perfParams);

        // Guardrails summary
        let guardSql = `
            SELECT 
                COUNT(*) as total_events,
                COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_events,
                COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_events,
                COUNT(CASE WHEN resolved = 1 THEN 1 END) as resolved_events
            FROM guardrails_events 
            WHERE timestamp >= ?
        `;
        const guardParams = [timeLimit];

        if (sessionId) {
            guardSql += ' AND session_id = ?';
            guardParams.push(sessionId);
        }

        const guardStats = this.db.prepare(guardSql).get(...guardParams);

        return {
            performance: {
                totalExecutions: perfStats.total_executions || 0,
                successRate: perfStats.total_executions > 0 ? 
                    (perfStats.successful_executions || 0) / perfStats.total_executions : 1,
                averageResponseTime: Math.round(perfStats.average_duration || 0),
                uniqueAgents: perfStats.unique_agents || 0
            },
            guardrails: {
                totalEvents: guardStats.total_events || 0,
                criticalEvents: guardStats.critical_events || 0,
                warningEvents: guardStats.warning_events || 0,
                resolvedEvents: guardStats.resolved_events || 0,
                resolutionRate: guardStats.total_events > 0 ? 
                    (guardStats.resolved_events || 0) / guardStats.total_events : 1
            },
            healthStatus: this.getHealthStatus(sessionId)
        };
    }

    /**
     * Calculate overall health status
     */
    getHealthStatus(sessionId = null) {
        const recentMetrics = this.getPerformanceMetrics(sessionId, '1h');
        const recentGuardrails = this.getGuardrailsEvents(sessionId, null, '1h');
        
        const successRate = recentMetrics.length > 0 ? 
            recentMetrics.filter(m => m.success).length / recentMetrics.length : 1;
        
        const criticalEvents = recentGuardrails.filter(g => g.severity === 'critical').length;
        const unresolvedCritical = recentGuardrails.filter(g => g.severity === 'critical' && !g.resolved).length;

        if (successRate < 0.7 || unresolvedCritical > 0) {
            return 'critical';
        } else if (successRate < 0.9 || criticalEvents > 5) {
            return 'warning';
        } else {
            return 'healthy';
        }
    }

    /**
     * Calculate performance grade
     */
    calculatePerformanceGrade(metric) {
        const targetDuration = this.getTargetDuration(metric.agentModel);
        const successWeight = metric.success ? 100 : 0;
        const durationWeight = targetDuration > 0 ? 
            Math.max(0, 100 - ((metric.duration - targetDuration) / targetDuration * 100)) : 100;
        const validationWeight = metric.validationScore || 80;

        const overallScore = (successWeight * 0.4) + (durationWeight * 0.4) + (validationWeight * 0.2);

        if (overallScore >= 90) return 'A';
        if (overallScore >= 80) return 'B';
        if (overallScore >= 70) return 'C';
        if (overallScore >= 60) return 'D';
        return 'F';
    }

    calculatePerformanceGradeFromSummary(summary) {
        const successRate = summary.successful_executions / summary.total_executions;
        const targetDuration = this.getTargetDuration(summary.agent_model);
        const durationScore = targetDuration > 0 ? 
            Math.max(0, 100 - ((summary.average_duration - targetDuration) / targetDuration * 100)) : 100;
        
        const overallScore = (successRate * 40) + (Math.min(durationScore, 100) * 0.4) + 
            ((summary.average_validation_score || 80) * 0.2);

        if (overallScore >= 90) return 'A';
        if (overallScore >= 80) return 'B';
        if (overallScore >= 70) return 'C';
        if (overallScore >= 60) return 'D';
        return 'F';
    }

    getTargetDuration(model) {
        const targets = {
            'haiku': 5000,
            'sonnet': 15000,
            'opus': 30000,
            'opusplan': 45000
        };
        return targets[model] || 30000;
    }

    /**
     * Utility functions
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    /**
     * Close database connection
     */
    close() {
        if (this.db) {
            this.db.close();
            this.isInitialized = false;
            console.log(`${colors.blue}[OBSERVABILITY] Database connection closed${colors.reset}`);
        }
    }
}

// CLI Usage
if (require.main === module) {
    const command = process.argv[2];
    const integration = new ObservabilityIntegration();
    
    try {
        integration.initialize();
        
        switch (command) {
            case 'dashboard':
                const timeframe = process.argv[3] || '1h';
                const dashboardData = integration.getDashboardData(null, timeframe);
                console.log(JSON.stringify(dashboardData, null, 2));
                break;
            
            case 'summary':
                const summaryTimeframe = process.argv[3] || '1h';
                const summary = integration.calculateSummaryStats(null, summaryTimeframe);
                console.log(`\n${colors.bold}${colors.cyan}=== OBSERVABILITY SUMMARY ===${colors.reset}`);
                console.log(`${colors.green}Success Rate: ${(summary.performance.successRate * 100).toFixed(1)}%${colors.reset}`);
                console.log(`${colors.blue}Avg Response Time: ${summary.performance.averageResponseTime}ms${colors.reset}`);
                console.log(`${colors.yellow}Guardrails Events: ${summary.guardrails.totalEvents} (${summary.guardrails.criticalEvents} critical)${colors.reset}`);
                console.log(`${colors.cyan}Health Status: ${summary.healthStatus.toUpperCase()}${colors.reset}`);
                console.log(`${colors.cyan}=================================${colors.reset}\n`);
                break;
            
            case 'test':
                console.log('Testing observability integration...');
                
                // Test performance metric
                const perfId = integration.recordPerformanceMetric({
                    sessionId: 'test-session',
                    agentName: 'test-agent',
                    agentModel: 'sonnet',
                    agentCategory: 'test',
                    taskType: 'test',
                    complexity: 'medium',
                    startTime: Date.now() - 5000,
                    endTime: Date.now(),
                    duration: 5000,
                    success: true,
                    contextSize: 1000,
                    validationScore: 85
                });
                console.log(`✅ Performance metric recorded: ${perfId}`);
                
                // Test guardrails event
                const guardId = integration.recordGuardrailsEvent({
                    sessionId: 'test-session',
                    eventType: 'context_overflow',
                    severity: 'warning',
                    message: 'Context size approaching limit',
                    thresholdValue: 128000,
                    actualValue: 120000,
                    resolved: false
                });
                console.log(`✅ Guardrails event recorded: ${guardId}`);
                
                // Test system health
                const healthId = integration.recordSystemHealth({
                    sessionId: 'test-session',
                    memory: {
                        heapUsed: 50 * 1024 * 1024,
                        heapTotal: 100 * 1024 * 1024,
                        external: 10 * 1024 * 1024,
                        rss: 80 * 1024 * 1024,
                        usagePercent: 50
                    },
                    cpu: { user: 1000, system: 500 },
                    activeAgents: 2,
                    uptime: 3600,
                    bufferedMetrics: 5
                });
                console.log(`✅ System health recorded: ${healthId}`);
                
                console.log('Test completed successfully!');
                break;
                
            default:
                console.log(`
Usage: node observability-integration.js <command>

Commands:
  dashboard [timeframe]   Generate dashboard data (1h, 6h, 1d, 7d)
  summary [timeframe]     Show summary statistics
  test                    Run integration tests

Example:
  node .claude/scripts/observability-integration.js dashboard 1d
                `);
        }
    } catch (error) {
        console.error(`${colors.red}Error: ${error.message}${colors.reset}`);
        process.exit(1);
    } finally {
        integration.close();
    }
}

module.exports = ObservabilityIntegration;