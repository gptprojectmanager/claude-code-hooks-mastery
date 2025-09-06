#!/usr/bin/env node

/**
 * Agent Validation Script
 * Valida tutti gli agenti utilizzando JSON Schema per garantire consistenza
 * Basato sul sistema claude-code-subagents-collection
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const Ajv = require('ajv');

// Colors per output console
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

// Schema per validazione agenti
const agentSchema = {
    type: 'object',
    required: ['name', 'description', 'category'],
    properties: {
        name: {
            type: 'string',
            pattern: '^[a-z0-9-]+$',
            minLength: 3,
            maxLength: 50
        },
        description: {
            type: 'string',
            minLength: 10,
            maxLength: 500
        },
        category: {
            type: 'string',
            enum: [
                'backend-architecture',
                'business-marketing', 
                'crypto',
                'data-ai',
                'development-architecture',
                'infrastructure-operations',
                'language-specialists',
                'quality-security',
                'specialized-domains',
                'meta-agents'
            ]
        },
        model: {
            type: 'string',
            enum: ['haiku', 'sonnet', 'opus', 'opusplan']
        },
        tools: {
            type: 'string'
        },
        color: {
            type: 'string'
        }
    },
    additionalProperties: true
};

// Schema per validazione comandi slash
const commandSchema = {
    type: 'object',
    required: ['description'],
    properties: {
        'allowed-tools': {
            type: 'string'
        },
        'argument-hint': {
            type: 'string'
        },
        description: {
            type: 'string',
            minLength: 10,
            maxLength: 200
        }
    },
    additionalProperties: true
};

class AgentValidator {
    constructor() {
        this.ajv = new Ajv({ allErrors: true });
        this.validateAgent = this.ajv.compile(agentSchema);
        this.validateCommand = this.ajv.compile(commandSchema);
        this.errors = [];
        this.warnings = [];
        this.successes = [];
    }

    log(message, color = 'reset') {
        console.log(`${colors[color]}${message}${colors.reset}`);
    }

    logError(message) {
        this.log(`❌ ERROR: ${message}`, 'red');
        this.errors.push(message);
    }

    logWarning(message) {
        this.log(`⚠️  WARNING: ${message}`, 'yellow');
        this.warnings.push(message);
    }

    logSuccess(message) {
        this.log(`✅ ${message}`, 'green');
        this.successes.push(message);
    }

    parseFrontmatter(content) {
        const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;
        const match = content.match(frontmatterRegex);
        
        if (!match) {
            throw new Error('No valid YAML frontmatter found');
        }

        const [, frontmatterStr, body] = match;
        
        try {
            const frontmatter = yaml.load(frontmatterStr);
            return { frontmatter, body };
        } catch (error) {
            throw new Error(`Invalid YAML frontmatter: ${error.message}`);
        }
    }

    validateAgentFile(filePath) {
        const fileName = path.basename(filePath, '.md');
        
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const { frontmatter, body } = this.parseFrontmatter(content);

            // Validazione schema base
            const isValid = this.validateAgent(frontmatter);
            
            if (!isValid) {
                this.validateAgent.errors.forEach(error => {
                    this.logError(`${fileName}: ${error.instancePath} ${error.message}`);
                });
                return false;
            }

            // Validazione naming convention
            if (frontmatter.name !== fileName) {
                this.logError(`${fileName}: File name must match 'name' field (${frontmatter.name})`);
                return false;
            }

            // Validazione contenuto
            if (!body.trim().startsWith('# Purpose') && !body.trim().startsWith('#')) {
                this.logWarning(`${fileName}: Missing '# Purpose' section`);
            }

            if (body.length < 100) {
                this.logWarning(`${fileName}: Agent content seems too short (${body.length} chars)`);
            }

            // Validazione description length
            if (frontmatter.description && frontmatter.description.length > 300) {
                this.logWarning(`${fileName}: Description is quite long (${frontmatter.description.length} chars)`);
            }

            this.logSuccess(`${fileName}: Valid agent`);
            return true;

        } catch (error) {
            this.logError(`${fileName}: ${error.message}`);
            return false;
        }
    }

    validateCommandFile(filePath) {
        const fileName = path.basename(filePath, '.md');
        
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const { frontmatter, body } = this.parseFrontmatter(content);

            // Validazione schema comando
            const isValid = this.validateCommand(frontmatter);
            
            if (!isValid) {
                this.validateCommand.errors.forEach(error => {
                    this.logError(`${fileName}: ${error.instancePath} ${error.message}`);
                });
                return false;
            }

            // Validazione contenuto comando
            if (body.length < 50) {
                this.logWarning(`${fileName}: Command content seems too short`);
            }

            this.logSuccess(`${fileName}: Valid command`);
            return true;

        } catch (error) {
            this.logError(`${fileName}: ${error.message}`);
            return false;
        }
    }

    findFiles(directory, extension = '.md') {
        const files = [];
        
        function walkDir(dir) {
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                
                if (entry.isDirectory()) {
                    walkDir(fullPath);
                } else if (entry.isFile() && entry.name.endsWith(extension) && !entry.name.includes('.bak')) {
                    files.push(fullPath);
                }
            }
        }
        
        if (fs.existsSync(directory)) {
            walkDir(directory);
        }
        
        return files;
    }

    validateAll() {
        this.log('\n🔍 Starting Agent Validation...', 'bold');
        
        const agentsDir = '/Users/sam/claude-code-hooks-mastery/.claude/agents';
        const commandsDir = '/Users/sam/claude-code-hooks-mastery/.claude/commands';
        
        // Valida agenti
        this.log('\n📋 Validating Agents...', 'cyan');
        const agentFiles = this.findFiles(agentsDir);
        let validAgents = 0;
        
        agentFiles.forEach(file => {
            if (this.validateAgentFile(file)) {
                validAgents++;
            }
        });

        // Valida comandi (solo quelli con frontmatter)
        this.log('\n⚡ Validating Commands...', 'cyan');
        const commandFiles = this.findFiles(commandsDir).filter(file => {
            const content = fs.readFileSync(file, 'utf8');
            return content.startsWith('---');
        });
        
        let validCommands = 0;
        commandFiles.forEach(file => {
            if (this.validateCommandFile(file)) {
                validCommands++;
            }
        });

        // Report finale
        this.log('\n📊 Validation Summary:', 'bold');
        this.log(`   Agents: ${validAgents}/${agentFiles.length} valid`, validAgents === agentFiles.length ? 'green' : 'yellow');
        this.log(`   Commands: ${validCommands}/${commandFiles.length} valid`, validCommands === commandFiles.length ? 'green' : 'yellow');
        this.log(`   Errors: ${this.errors.length}`, this.errors.length === 0 ? 'green' : 'red');
        this.log(`   Warnings: ${this.warnings.length}`, this.warnings.length === 0 ? 'green' : 'yellow');

        if (this.errors.length === 0) {
            this.log('\n🎉 All validations passed!', 'green');
            return true;
        } else {
            this.log('\n💥 Validation failed with errors', 'red');
            return false;
        }
    }
}

// Execute validation
if (require.main === module) {
    const validator = new AgentValidator();
    const success = validator.validateAll();
    process.exit(success ? 0 : 1);
}

module.exports = AgentValidator;