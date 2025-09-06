# API Documenter Workflow

## Overview
Structured workflow for comprehensive API documentation generation, from discovery to delivery. This workflow ensures professional, accurate, and developer-friendly API documentation.

## Phase 1: API Discovery & Analysis

### 1.1 Endpoint Discovery
```bash
# Scan codebase for API endpoints
find . -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.go" | xargs grep -l "router\|@app\|@api\|endpoint"

# Analyze route definitions
grep -r "GET\|POST\|PUT\|DELETE\|PATCH" --include="*.js" --include="*.ts" --include="*.py" .
```

### 1.2 Schema Analysis
- Extract request/response models
- Identify data types and validation rules
- Map relationships between entities
- Document authentication requirements

### 1.3 Authentication & Security
```bash
# Identify auth patterns
grep -r "auth\|token\|jwt\|bearer\|api-key" --include="*.js" --include="*.ts" --include="*.py" .
```

## Phase 2: OpenAPI Specification Generation

### 2.1 Base Specification Structure
```yaml
openapi: 3.0.3
info:
  title: API Name
  version: 1.0.0
  description: API Description
servers:
  - url: https://api.example.com/v1
    description: Production server
```

### 2.2 Endpoint Documentation
For each endpoint, document:
- Path parameters
- Query parameters
- Request body schema
- Response schemas (success/error)
- Authentication requirements
- Rate limiting

### 2.3 Schema Definitions
```yaml
components:
  schemas:
    User:
      type: object
      required:
        - id
        - email
      properties:
        id:
          type: integer
          format: int64
        email:
          type: string
          format: email
```

## Phase 3: Interactive Documentation Generation

### 3.1 Swagger UI Setup
```bash
# Generate Swagger UI
swagger-codegen generate -i api-spec.yaml -l html2 -o docs/

# Or use online editor
curl -X POST "https://generator3.swagger.io/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"specURL":"./api-spec.yaml","lang":"html2"}'
```

### 3.2 Live Examples Integration
- Add realistic example data
- Include common use cases
- Provide "Try it out" functionality
- Set up mock server for testing

## Phase 4: Code Examples Generation

### 4.1 cURL Examples
```bash
# GET request
curl -X GET "https://api.example.com/v1/users/123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# POST request
curl -X POST "https://api.example.com/v1/users" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

### 4.2 SDK Examples

#### JavaScript/Node.js
```javascript
const apiClient = new APIClient({
  baseURL: 'https://api.example.com/v1',
  apiKey: 'YOUR_API_KEY'
});

// Get user
const user = await apiClient.users.get(123);

// Create user
const newUser = await apiClient.users.create({
  name: 'John Doe',
  email: 'john@example.com'
});
```

#### Python
```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
}

# Get user
response = requests.get('https://api.example.com/v1/users/123', headers=headers)
user = response.json()

# Create user
data = {'name': 'John Doe', 'email': 'john@example.com'}
response = requests.post('https://api.example.com/v1/users', json=data, headers=headers)
```

### 4.3 Multiple Language Support
Generate examples for:
- JavaScript/TypeScript
- Python
- Java
- PHP
- Go
- Ruby
- C#

## Phase 5: Testing Documentation

### 5.1 Postman Collection Generation
```bash
# Convert OpenAPI to Postman
openapi2postman -s api-spec.yaml -o postman-collection.json

# Add environment variables
{
  "name": "API Environment",
  "values": [
    {"key": "baseUrl", "value": "https://api.example.com/v1"},
    {"key": "apiKey", "value": "{{API_KEY}}"}
  ]
}
```

### 5.2 Test Case Documentation
For each endpoint:
- Happy path scenarios
- Edge cases
- Error scenarios
- Authentication failures
- Rate limiting tests

### 5.3 Automated Testing Examples
```javascript
// Jest/Supertest example
describe('Users API', () => {
  test('GET /users/:id returns user data', async () => {
    const response = await request(app)
      .get('/users/123')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);
    
    expect(response.body).toHaveProperty('id', 123);
    expect(response.body).toHaveProperty('email');
  });
});
```

## Phase 6: Integration Guides

### 6.1 Getting Started Guide
- API key generation
- Authentication setup
- Rate limiting guidelines
- Error handling patterns

### 6.2 Common Use Cases
- User management flows
- Data synchronization
- Webhook implementation
- Pagination handling

### 6.3 SDKs and Libraries
- Official SDKs
- Community libraries
- Framework-specific integrations

## Phase 7: Version Management & Maintenance

### 7.1 Changelog Documentation
```markdown
## v2.1.0 (2024-01-15)
### Added
- New endpoint: GET /users/:id/preferences
- Support for bulk operations

### Changed
- Improved error response format
- Updated rate limiting (100 → 200 req/min)

### Deprecated
- POST /users/bulk (use POST /users with array instead)

### Removed
- Legacy v1 authentication (use v2)
```

### 7.2 Migration Guides
- Version comparison tables
- Breaking changes documentation
- Migration scripts/tools
- Timeline for deprecations

### 7.3 Deprecation Notices
```yaml
paths:
  /users/legacy:
    get:
      deprecated: true
      description: "This endpoint is deprecated. Use /users instead."
      x-sunset-date: "2024-06-01"
```

## API Type Specific Workflows

### REST APIs
- Standard HTTP methods documentation
- Resource-based URL patterns
- HATEOAS implementation guides

### GraphQL APIs
```graphql
# Schema documentation
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
}

type Query {
  user(id: ID!): User
  users(limit: Int, offset: Int): [User!]!
}

# Example queries
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
    posts {
      title
      content
    }
  }
}
```

### WebSocket APIs
```javascript
// Connection examples
const socket = new WebSocket('wss://api.example.com/ws');

// Event documentation
socket.on('user.created', (data) => {
  console.log('New user:', data);
});

// Message format specification
{
  "type": "user.update",
  "data": {
    "id": 123,
    "name": "Updated Name"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Quality Assurance Checklist

### Content Quality
- [ ] All endpoints documented
- [ ] Request/response schemas complete
- [ ] Authentication clearly explained
- [ ] Error codes documented
- [ ] Rate limiting specified

### Code Examples
- [ ] cURL commands tested
- [ ] SDK examples verified
- [ ] Multiple language support
- [ ] Realistic example data
- [ ] Error handling demonstrated

### Testing Resources
- [ ] Postman collection exported
- [ ] Test cases documented
- [ ] Mock data provided
- [ ] Automated test examples

### User Experience
- [ ] Clear getting started guide
- [ ] Interactive examples work
- [ ] Search functionality
- [ ] Mobile-responsive design
- [ ] Fast loading times

## Tools Integration

### Documentation Generation
```bash
# Swagger/OpenAPI tools
swagger-codegen generate -i spec.yaml -l html2 -o docs/
redoc-cli build spec.yaml --output docs/index.html

# Postman integration
postman-to-openapi collection.json > spec.yaml
openapi-to-postman spec.yaml -o collection.json
```

### Validation Tools
```bash
# Validate OpenAPI spec
swagger-tools validate spec.yaml
openapi-validator spec.yaml

# Test documentation
spectral lint spec.yaml
```

### Automation Scripts
```bash
# Auto-generate from code annotations
swagger-jsdoc -d swaggerDef.js routes/*.js > spec.yaml

# Deploy documentation
aws s3 sync ./docs s3://api-docs-bucket --delete
```

## Delivery Standards

### Documentation Package
1. OpenAPI specification file
2. Interactive HTML documentation
3. Postman collection
4. Code examples repository
5. Getting started guide
6. Migration guides (if applicable)

### Quality Metrics
- 100% endpoint coverage
- All examples tested and working
- Response time < 2s for documentation site
- Mobile compatibility score > 90%
- Accessibility compliance (WCAG 2.1)

### Maintenance Schedule
- Weekly: Example validation
- Monthly: Content review and updates
- Quarterly: User feedback integration
- Per release: Version updates and migrations