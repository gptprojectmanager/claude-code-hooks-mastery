#!/usr/bin/env node

/**
 * Guardrails Enhancement System
 * Prevents context overflow, manages timeouts, and ensures system stability
 * Based on analysis of claude-code-hooks-mastery system requirements
 */

const fs = require('fs');
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

class GuardrailsEnhancement {
    constructor(config = {}) {
        this.config = {
            // Context overflow prevention
            maxContextLength: config.maxContextLength || 128000, // chars
            maxContextTokens: config.maxContextTokens || 32000,   // estimated tokens
            contextWarningThreshold: config.contextWarningThreshold || 0.8,
            
            // Timeout management
            defaultAgentTimeout: config.defaultAgentTimeout || 300000, // 5 minutes
            complexTaskTimeout: config.complexTaskTimeout || 900000,   // 15 minutes
            criticalOperationTimeout: config.criticalOperationTimeout || 1800000, // 30 minutes
            
            // Memory management
            maxMemoryUsage: config.maxMemoryUsage || 512 * 1024 * 1024, // 512MB
            memoryCheckInterval: config.memoryCheckInterval || 30000,     // 30 seconds
            
            // Agent orchestration limits
            maxConcurrentAgents: config.maxConcurrentAgents || 5,
            maxTaskDepth: config.maxTaskDepth || 10,
            maxRetryAttempts: config.maxRetryAttempts || 3,
            
            // Performance thresholds
            responseTimeWarning: config.responseTimeWarning || 30000,    // 30 seconds
            responseTimeError: config.responseTimeError || 120000,       // 2 minutes
            
            ...config
        };
        
        this.activeAgents = new Set();
        this.taskStack = [];
        this.memoryUsageHistory = [];
        this.performanceMetrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            averageResponseTime: 0,
            timeouts: 0,
            contextOverflows: 0,
            memoryIssues: 0
        };
        
        this.startMemoryMonitoring();
    }

    /**
     * Context Overflow Prevention
     */
    validateContext(context, taskType = 'standard') {
        const validation = {
            valid: true,
            warnings: [],
            errors: [],
            truncated: false,
            originalSize: 0,
            finalSize: 0
        };

        if (typeof context === 'string') {
            validation.originalSize = context.length;
        } else if (typeof context === 'object') {
            validation.originalSize = JSON.stringify(context).length;
            context = JSON.stringify(context);
        }

        // Check context length
        if (validation.originalSize > this.config.maxContextLength) {
            validation.errors.push(`Context length ${validation.originalSize} exceeds maximum ${this.config.maxContextLength}`);
            
            // Truncate context intelligently
            const truncatedContext = this.intelligentTruncation(context, this.config.maxContextLength);
            validation.truncated = true;
            validation.finalSize = truncatedContext.length;
            this.performanceMetrics.contextOverflows++;
            
            this.log('warning', `Context truncated from ${validation.originalSize} to ${validation.finalSize} chars`);
            return { ...validation, context: truncatedContext };
        }

        // Warning threshold
        if (validation.originalSize > this.config.maxContextLength * this.config.contextWarningThreshold) {
            validation.warnings.push(`Context approaching size limit: ${validation.originalSize}/${this.config.maxContextLength}`);
            this.log('warning', `Context size warning: ${validation.originalSize} chars`);
        }

        validation.finalSize = validation.originalSize;
        return { ...validation, context };
    }

    /**
     * Intelligent context truncation that preserves important information
     */
    intelligentTruncation(context, maxLength) {
        if (context.length <= maxLength) return context;

        // Priority preservation order
        const preservationStrategies = [
            // Keep recent information (last 30%)
            () => {
                const keepSize = Math.floor(maxLength * 0.7);
                return context.slice(-keepSize);
            },
            
            // Keep structured sections (between headers)
            () => {
                const sections = context.split(/\n## |# /);
                let result = '';
                for (const section of sections.reverse()) {
                    if (result.length + section.length < maxLength) {
                        result = section + '\n' + result;
                    } else {
                        break;
                    }
                }
                return result.trim();
            },
            
            // Simple tail truncation
            () => context.slice(-maxLength)
        ];

        // Try strategies in order
        for (const strategy of preservationStrategies) {
            try {
                const truncated = strategy();
                if (truncated.length <= maxLength) {
                    return truncated;
                }
            } catch (error) {
                this.log('error', `Truncation strategy failed: ${error.message}`);
            }
        }

        // Fallback: simple truncation
        return context.slice(-maxLength);
    }

    /**
     * Timeout Management
     */
    createTimeoutManager(taskType = 'standard', customTimeout = null) {
        const timeout = customTimeout || this.getTimeoutForTask(taskType);
        
        return {
            timeout,
            start: Date.now(),
            timeoutId: null,
            
            setHandler: function(handler) {
                this.timeoutId = setTimeout(() => {
                    handler(new Error(`Task timeout after ${timeout}ms`));
                }, timeout);
            },
            
            clear: function() {
                if (this.timeoutId) {
                    clearTimeout(this.timeoutId);
                    this.timeoutId = null;
                }
            },
            
            getElapsed: function() {
                return Date.now() - this.start;
            },
            
            getRemainingTime: function() {
                return Math.max(0, timeout - this.getElapsed());
            }
        };
    }

    getTimeoutForTask(taskType) {
        const timeouts = {
            'simple': this.config.defaultAgentTimeout * 0.5,
            'standard': this.config.defaultAgentTimeout,
            'complex': this.config.complexTaskTimeout,
            'critical': this.config.criticalOperationTimeout,
            'research': this.config.complexTaskTimeout * 1.5,
            'optimization': this.config.complexTaskTimeout * 2,
            'validation': this.config.defaultAgentTimeout * 0.8
        };
        
        return timeouts[taskType] || this.config.defaultAgentTimeout;
    }

    /**
     * Agent Orchestration Limits
     */
    canAddAgent(agentType) {
        const validation = {
            allowed: true,
            reasons: []
        };

        // Check concurrent agent limit
        if (this.activeAgents.size >= this.config.maxConcurrentAgents) {
            validation.allowed = false;
            validation.reasons.push(`Maximum concurrent agents (${this.config.maxConcurrentAgents}) reached`);
        }

        // Check task depth
        if (this.taskStack.length >= this.config.maxTaskDepth) {
            validation.allowed = false;
            validation.reasons.push(`Maximum task depth (${this.config.maxTaskDepth}) reached`);
        }

        // Check memory usage
        const memoryUsage = process.memoryUsage();
        if (memoryUsage.heapUsed > this.config.maxMemoryUsage) {
            validation.allowed = false;
            validation.reasons.push(`Memory limit exceeded: ${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB`);
        }

        return validation;
    }

    addAgent(agentId, agentType) {
        const validation = this.canAddAgent(agentType);
        if (!validation.allowed) {
            throw new Error(`Cannot add agent: ${validation.reasons.join(', ')}`);
        }

        this.activeAgents.add(agentId);
        this.log('info', `Agent ${agentId} (${agentType}) added. Active: ${this.activeAgents.size}/${this.config.maxConcurrentAgents}`);
        
        return {
            agentId,
            startTime: Date.now(),
            timeoutManager: this.createTimeoutManager(agentType)
        };
    }

    removeAgent(agentId) {
        if (this.activeAgents.has(agentId)) {
            this.activeAgents.delete(agentId);
            this.log('info', `Agent ${agentId} removed. Active: ${this.activeAgents.size}/${this.config.maxConcurrentAgents}`);
        }
    }

    /**
     * Memory Management
     */
    startMemoryMonitoring() {
        setInterval(() => {
            const memoryUsage = process.memoryUsage();
            this.memoryUsageHistory.push({
                timestamp: Date.now(),
                heapUsed: memoryUsage.heapUsed,
                heapTotal: memoryUsage.heapTotal,
                external: memoryUsage.external,
                rss: memoryUsage.rss
            });

            // Keep only last 100 measurements
            if (this.memoryUsageHistory.length > 100) {
                this.memoryUsageHistory.shift();
            }

            // Check for memory issues
            if (memoryUsage.heapUsed > this.config.maxMemoryUsage) {
                this.performanceMetrics.memoryIssues++;
                this.log('warning', `High memory usage: ${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB`);
                
                // Trigger garbage collection if available
                if (global.gc) {
                    global.gc();
                    this.log('info', 'Garbage collection triggered');
                }
            }
        }, this.config.memoryCheckInterval);
    }

    getMemoryStats() {
        const current = process.memoryUsage();
        const history = this.memoryUsageHistory.slice(-10); // Last 10 measurements
        
        return {
            current: {
                heapUsed: Math.round(current.heapUsed / 1024 / 1024),
                heapTotal: Math.round(current.heapTotal / 1024 / 1024),
                external: Math.round(current.external / 1024 / 1024),
                rss: Math.round(current.rss / 1024 / 1024)
            },
            trend: history.length > 1 ? {
                direction: history[history.length - 1].heapUsed > history[0].heapUsed ? 'increasing' : 'decreasing',
                changeRate: history.length > 5 ? 
                    (history[history.length - 1].heapUsed - history[history.length - 6].heapUsed) / 5 : 0
            } : null,
            warningThreshold: Math.round(this.config.maxMemoryUsage / 1024 / 1024),
            isNearLimit: current.heapUsed > this.config.maxMemoryUsage * 0.8
        };
    }

    /**
     * Performance Metrics & Health Monitoring
     */
    recordRequest(startTime, success = true) {
        const duration = Date.now() - startTime;
        this.performanceMetrics.totalRequests++;
        
        if (success) {
            this.performanceMetrics.successfulRequests++;
        } else {
            this.performanceMetrics.failedRequests++;
        }

        // Update average response time
        const prevAvg = this.performanceMetrics.averageResponseTime;
        const totalReqs = this.performanceMetrics.totalRequests;
        this.performanceMetrics.averageResponseTime = 
            (prevAvg * (totalReqs - 1) + duration) / totalReqs;

        // Check performance thresholds
        if (duration > this.config.responseTimeError) {
            this.log('error', `Slow response: ${duration}ms (error threshold: ${this.config.responseTimeError}ms)`);
        } else if (duration > this.config.responseTimeWarning) {
            this.log('warning', `Slow response: ${duration}ms (warning threshold: ${this.config.responseTimeWarning}ms)`);
        }

        return {
            duration,
            success,
            averageResponseTime: this.performanceMetrics.averageResponseTime
        };
    }

    recordTimeout() {
        this.performanceMetrics.timeouts++;
        this.log('error', `Timeout recorded. Total timeouts: ${this.performanceMetrics.timeouts}`);
    }

    getHealthStatus() {
        const memoryStats = this.getMemoryStats();
        const successRate = this.performanceMetrics.totalRequests > 0 ? 
            this.performanceMetrics.successfulRequests / this.performanceMetrics.totalRequests : 1;

        return {
            status: this.determineHealthStatus(successRate, memoryStats),
            metrics: {
                ...this.performanceMetrics,
                successRate: Math.round(successRate * 100),
                activeAgents: this.activeAgents.size,
                taskStackDepth: this.taskStack.length,
                memoryUsage: memoryStats.current,
                memoryWarning: memoryStats.isNearLimit
            },
            recommendations: this.generateHealthRecommendations(successRate, memoryStats)
        };
    }

    determineHealthStatus(successRate, memoryStats) {
        if (successRate < 0.7 || memoryStats.isNearLimit || this.activeAgents.size >= this.config.maxConcurrentAgents) {
            return 'critical';
        } else if (successRate < 0.9 || memoryStats.current.heapUsed > memoryStats.warningThreshold * 0.6) {
            return 'warning';
        } else {
            return 'healthy';
        }
    }

    generateHealthRecommendations(successRate, memoryStats) {
        const recommendations = [];

        if (successRate < 0.8) {
            recommendations.push('Consider reducing concurrent agent limit or task complexity');
        }

        if (memoryStats.isNearLimit) {
            recommendations.push('Memory usage high - consider garbage collection or process restart');
        }

        if (this.performanceMetrics.averageResponseTime > this.config.responseTimeWarning) {
            recommendations.push('Average response time elevated - check system resources');
        }

        if (this.performanceMetrics.timeouts > this.performanceMetrics.totalRequests * 0.1) {
            recommendations.push('High timeout rate - consider increasing timeout limits');
        }

        return recommendations;
    }

    /**
     * Circuit Breaker Pattern
     */
    createCircuitBreaker(name, options = {}) {
        const config = {
            failureThreshold: options.failureThreshold || 5,
            resetTimeout: options.resetTimeout || 60000,
            monitoringPeriod: options.monitoringPeriod || 10000,
            ...options
        };

        return {
            name,
            state: 'closed', // closed, open, half-open
            failures: 0,
            lastFailureTime: null,
            successCount: 0,
            
            async execute(operation) {
                if (this.state === 'open') {
                    if (Date.now() - this.lastFailureTime > config.resetTimeout) {
                        this.state = 'half-open';
                        this.successCount = 0;
                    } else {
                        throw new Error(`Circuit breaker ${name} is open`);
                    }
                }

                try {
                    const result = await operation();
                    this.onSuccess();
                    return result;
                } catch (error) {
                    this.onFailure();
                    throw error;
                }
            },

            onSuccess() {
                this.failures = 0;
                if (this.state === 'half-open') {
                    this.successCount++;
                    if (this.successCount >= 2) {
                        this.state = 'closed';
                    }
                }
            },

            onFailure() {
                this.failures++;
                this.lastFailureTime = Date.now();
                if (this.failures >= config.failureThreshold) {
                    this.state = 'open';
                }
            },

            getStatus() {
                return {
                    name,
                    state: this.state,
                    failures: this.failures,
                    lastFailureTime: this.lastFailureTime,
                    isOpen: this.state === 'open'
                };
            }
        };
    }

    /**
     * Utility Functions
     */
    log(level, message) {
        const timestamp = new Date().toISOString();
        const color = colors[level === 'error' ? 'red' : level === 'warning' ? 'yellow' : 'cyan'];
        console.log(`${color}[${timestamp}] [GUARDRAILS-${level.toUpperCase()}] ${message}${colors.reset}`);
    }

    exportMetrics() {
        return {
            timestamp: new Date().toISOString(),
            config: this.config,
            performance: this.performanceMetrics,
            health: this.getHealthStatus(),
            memory: this.getMemoryStats(),
            activeAgents: Array.from(this.activeAgents),
            taskStackDepth: this.taskStack.length
        };
    }

    generateReport() {
        const health = this.getHealthStatus();
        const memory = this.getMemoryStats();
        
        console.log(`\n${colors.bold}${colors.cyan}=== GUARDRAILS ENHANCEMENT REPORT ===${colors.reset}`);
        console.log(`${colors.green}Health Status: ${health.status.toUpperCase()}${colors.reset}`);
        console.log(`${colors.blue}Success Rate: ${health.metrics.successRate}%${colors.reset}`);
        console.log(`${colors.blue}Active Agents: ${health.metrics.activeAgents}/${this.config.maxConcurrentAgents}${colors.reset}`);
        console.log(`${colors.blue}Memory Usage: ${memory.current.heapUsed}MB/${memory.warningThreshold}MB${colors.reset}`);
        console.log(`${colors.blue}Average Response Time: ${Math.round(health.metrics.averageResponseTime)}ms${colors.reset}`);
        
        if (health.recommendations.length > 0) {
            console.log(`\n${colors.yellow}Recommendations:${colors.reset}`);
            health.recommendations.forEach(rec => {
                console.log(`${colors.yellow}  • ${rec}${colors.reset}`);
            });
        }
        
        console.log(`${colors.cyan}=================================${colors.reset}\n`);
    }
}

// CLI Usage
if (require.main === module) {
    const command = process.argv[2];
    const guardrails = new GuardrailsEnhancement();
    
    switch (command) {
        case 'status':
            console.log(JSON.stringify(guardrails.getHealthStatus(), null, 2));
            break;
        
        case 'report':
            guardrails.generateReport();
            break;
        
        case 'metrics':
            console.log(JSON.stringify(guardrails.exportMetrics(), null, 2));
            break;
        
        case 'test':
            console.log('Testing guardrails system...');
            
            // Test context validation
            const longContext = 'A'.repeat(150000);
            const result = guardrails.validateContext(longContext);
            console.log(`Context validation: ${result.valid ? 'PASS' : 'FAIL'}`);
            
            // Test timeout manager
            const timeoutMgr = guardrails.createTimeoutManager('standard');
            console.log(`Timeout manager created: ${timeoutMgr.timeout}ms`);
            
            // Test memory stats
            const memStats = guardrails.getMemoryStats();
            console.log(`Memory stats: ${memStats.current.heapUsed}MB heap used`);
            
            guardrails.generateReport();
            break;
        
        default:
            console.log(`
Usage: node guardrails-enhancement.js <command>

Commands:
  status    Show current health status
  report    Generate detailed report
  metrics   Export all metrics as JSON
  test      Run system tests

Example:
  node .claude/scripts/guardrails-enhancement.js report
            `);
    }
}

module.exports = GuardrailsEnhancement;