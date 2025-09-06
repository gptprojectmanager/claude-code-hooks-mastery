---
allowed-tools: Task, Read, Write, Bash, WebFetch
argument-hint: system_requirements_or_domain
description: Execute comprehensive system architecture design using specialist architect agents
---

# Architecture Command

Progetta architetture di sistema complete utilizzando agenti architect specializzati per diversi domini e layer tecnologici.

## Variables

- **REQUIREMENTS**: $ARGUMENTS or "web application architecture" if not specified
  - System requirements o domain (es. "microservices e-commerce", "AI/ML pipeline", "cloud-native app")
  - Used by: architect agent ensemble

## Architecture Specialist Ensemble

### Core Architecture Agents
- @agent-backend-architect-sonnet (API design, microservices, scalable backends)
- @agent-cloud-architect-opus (infrastructure, IaC, cost optimization)
- @agent-database-architect-opus (schema design, data modeling, optimization)

### Domain-Specific Architects
- @agent-ai-engineer-opus (AI/ML system architecture)
- @agent-data-engineer-sonnet (data pipeline e warehouse architecture)
- @agent-ui-ux-designer-sonnet (frontend architecture e user experience)

### Supporting Specialists
- @agent-security-auditor-opus (security architecture review)
- @agent-performance-engineer-opus (performance e scalability planning)
- @agent-devops-troubleshooter-sonnet (deployment e operational architecture)

## Architecture Design Process

### Phase 1: Requirements Analysis (20 mins)
```
1. Stakeholder requirement gathering
2. Functional e non-functional requirements
3. Constraint identification (budget, timeline, technical)
4. Success criteria definition
```

### Phase 2: High-Level Design (30 mins)
```
1. System boundary definition
2. Major component identification
3. Integration pattern selection
4. Technology stack recommendations
```

### Phase 3: Detailed Architecture (45 mins)
```
1. Component detailed design
2. Interface specifications (APIs, contracts)
3. Data flow e service interactions
4. Security e compliance considerations
```

### Phase 4: Implementation Planning (15 mins)
```
1. Development phases e milestones
2. Risk assessment e mitigation
3. Resource requirement estimation
4. Deployment strategy planning
```

## Architecture Domains

### Web Application Architecture
```
- Frontend: React/Vue + State Management
- Backend: Node.js/Python + REST/GraphQL APIs
- Database: PostgreSQL/MongoDB + Redis cache
- Infrastructure: Docker + Kubernetes/AWS
```

### Microservices Architecture
```
- Service mesh e API gateway
- Event-driven communication patterns
- Database per service pattern
- Observability e monitoring strategy
```

### AI/ML System Architecture
```
- Data ingestion e preprocessing pipelines
- Model training e inference infrastructure  
- Vector databases e RAG systems
- MLOps e model deployment strategies
```

### Cloud-Native Architecture
```
- Container orchestration strategy
- Serverless integration patterns
- Multi-cloud e disaster recovery
- Cost optimization e auto-scaling
```

## Deliverables Structure

```
architecture_design/
└── design_<timestamp>/
    ├── requirements/        # Stakeholder e technical requirements
    ├── high_level/         # System overview e component diagram
    ├── detailed_design/    # Component specifications e interfaces
    ├── data_architecture/  # Database schema e data flow
    ├── security/           # Security patterns e compliance
    ├── deployment/         # Infrastructure e DevOps strategy
    ├── implementation/     # Development phases e timeline
    └── decisions/          # Architecture decision records (ADRs)
```

## Architecture Artifacts

### System Architecture Diagrams
- **C4 Model**: Context, Container, Component, Code views
- **Service Maps**: Microservice interaction diagrams
- **Data Flow**: Information flow through system
- **Network Topology**: Infrastructure e connectivity

### Technical Specifications
- **API Contracts**: OpenAPI/GraphQL specifications
- **Database Schema**: Entity relationship diagrams
- **Interface Definitions**: Service contracts e protocols
- **Security Model**: Authentication, authorization, encryption

### Implementation Guidance
- **Technology Stack**: Framework e library recommendations
- **Development Standards**: Coding conventions e patterns
- **Testing Strategy**: Unit, integration, e2e test approach
- **Deployment Pipeline**: CI/CD e release management

## Architecture Decision Records (ADRs)

For each major decision, document:
```
1. **Context**: What situation necessitated the decision
2. **Decision**: What was decided
3. **Rationale**: Why this option was chosen
4. **Consequences**: Expected positive e negative outcomes
5. **Alternatives**: Other options considered
```

## Quality Gates

### Architecture Review Criteria
- **Scalability**: Can handle expected growth (10x user load)
- **Maintainability**: Clear separation of concerns e modularity
- **Security**: Comprehensive threat model e mitigations
- **Performance**: Meets latency e throughput requirements
- **Cost**: Within budget constraints e optimization opportunities

### Validation Checkpoints
- **Technology Fit**: Appropriate tools for requirements
- **Team Capability**: Skills match architectural choices
- **Operational Readiness**: Monitoring, logging, alerting
- **Compliance**: Regulatory e organizational standards

## Success Metrics

- **Completeness**: All major system areas covered
- **Feasibility**: Realistic implementation timeline
- **Clarity**: Unambiguous specifications e diagrams
- **Consensus**: Stakeholder alignment on major decisions
- **Actionability**: Clear next steps per development team

## Report

Al completamento fornisci:
- Path alla architecture design directory
- Executive summary con key architectural decisions
- Technology stack recommendations con rationale
- Implementation timeline con major milestones
- Risk assessment con mitigation strategies
- Next steps per development teams