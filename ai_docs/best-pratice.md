---
From: https://github.com/coleam00/context-engineering-intro/tree/main/claude-code-full-guide
---

# CLAUDE.md

This file provides comprehensive guidance to Claude Code when working with Python code in this repository.

## Core Development Philosophy

### KISS (Keep It Simple, Stupid)

Simplicity should be a key goal in design. Choose straightforward solutions over complex ones whenever possible. Simple solutions are easier to understand, maintain, and debug.

### YAGNI (You Aren't Gonna Need It)

Avoid building functionality on speculation. Implement features only when they are needed, not when you anticipate they might be useful in the future.

### Design Principles

- **Dependency Inversion**: High-level modules should not depend on low-level modules. Both should depend on abstractions.
- **Open/Closed Principle**: Software entities should be open for extension but closed for modification.
- **Single Responsibility**: Each function, class, and module should have one clear purpose.
- **Fail Fast**: Check for potential errors early and raise exceptions immediately when issues occur.

## 🧱 Code Structure & Modularity

### File and Function Limits

- **Never create a file longer than 500 lines of code**. If approaching this limit, refactor by splitting into modules.
- **Functions should be under 50 lines** with a single, clear responsibility.
- **Classes should be under 100 lines** and represent a single concept or entity.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Line lenght should be max 100 characters** ruff rule in pyproject.toml
- **Use venv_linux** (the virtual environment) whenever executing Python commands, including for unit tests.

### Project Architecture

Follow strict vertical slice architecture with tests living next to the code they test:

```
src/project/
    __init__.py
    main.py
    tests/
        test_main.py
    conftest.py

    # Core modules
    database/
        __init__.py
        connection.py
        models.py
        tests/
            test_connection.py
            test_models.py

    auth/
        __init__.py
        authentication.py
        authorization.py
        tests/
            test_authentication.py
            test_authorization.py

    # Feature slices
    features/
        user_management/
            __init__.py
            handlers.py
            validators.py
            tests/
                test_handlers.py
                test_validators.py

        payment_processing/
            __init__.py
            processor.py
            gateway.py
            tests/
                test_processor.py
                test_gateway.py
```

## 🛠️ Development Environment

### UV Package Management

This project uses UV for blazing-fast Python package and environment management.

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Sync dependencies
uv sync

# Add a package ***NEVER UPDATE A DEPENDENCY DIRECTLY IN PYPROJECT.toml***
# ALWAYS USE UV ADD
uv add requests

# Add development dependency
uv add --dev pytest ruff mypy

# Remove a package
uv remove requests

# Run commands in the environment
uv run python script.py
uv run pytest
uv run ruff check .

# Install specific Python version
uv python install 3.12
```

### Development Commands

```bash
# Run all tests
uv run pytest

# Run specific tests with verbose output
uv run pytest tests/test_module.py -v

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Type checking
uv run mypy src/

# Run pre-commit hooks
uv run pre-commit run --all-files
```

## 📋 Style & Conventions

### Python Style Guide

- **Follow PEP8** with these specific choices:
  - Line length: 100 characters (set by Ruff in pyproject.toml)
  - Use double quotes for strings
  - Use trailing commas in multi-line structures
- **Always use type hints** for function signatures and class attributes
- **Format with `ruff format`** (faster alternative to Black)
- **Use `pydantic` v2** for data validation and settings management

### Docstring Standards

Use Google-style docstrings for all public functions, classes, and modules:

```python
def calculate_discount(
    price: Decimal,
    discount_percent: float,
    min_amount: Decimal = Decimal("0.01")
) -> Decimal:
    """
    Calculate the discounted price for a product.

    Args:
        price: Original price of the product
        discount_percent: Discount percentage (0-100)
        min_amount: Minimum allowed final price

    Returns:
        Final price after applying discount

    Raises:
        ValueError: If discount_percent is not between 0 and 100
        ValueError: If final price would be below min_amount

    Example:
        >>> calculate_discount(Decimal("100"), 20)
        Decimal('80.00')
    """
```

### Naming Conventions

- **Variables and functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private attributes/methods**: `_leading_underscore`
- **Type aliases**: `PascalCase`
- **Enum values**: `UPPER_SNAKE_CASE`

## 🧪 Testing Strategy

### Test-Driven Development (TDD)

1. **Write the test first** - Define expected behavior before implementation
2. **Watch it fail** - Ensure the test actually tests something
3. **Write minimal code** - Just enough to make the test pass
4. **Refactor** - Improve code while keeping tests green
5. **Repeat** - One test at a time

### Testing Best Practices

```python
# Always use pytest fixtures for setup
import pytest
from datetime import datetime

@pytest.fixture
def sample_user():
    """Provide a sample user for testing."""
    return User(
        id=123,
        name="Test User",
        email="test@example.com",
        created_at=datetime.now()
    )

# Use descriptive test names
def test_user_can_update_email_when_valid(sample_user):
    """Test that users can update their email with valid input."""
    new_email = "newemail@example.com"
    sample_user.update_email(new_email)
    assert sample_user.email == new_email

# Test edge cases and error conditions
def test_user_update_email_fails_with_invalid_format(sample_user):
    """Test that invalid email formats are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        sample_user.update_email("not-an-email")
    assert "Invalid email format" in str(exc_info.value)
```

### Test Organization

- Unit tests: Test individual functions/methods in isolation
- Integration tests: Test component interactions
- End-to-end tests: Test complete user workflows
- Keep test files next to the code they test
- Use `conftest.py` for shared fixtures
- Aim for 80%+ code coverage, but focus on critical paths

## 🚨 Error Handling

### Exception Best Practices

```python
# Create custom exceptions for your domain
class PaymentError(Exception):
    """Base exception for payment-related errors."""
    pass

class InsufficientFundsError(PaymentError):
    """Raised when account has insufficient funds."""
    def __init__(self, required: Decimal, available: Decimal):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient funds: required {required}, available {available}"
        )

# Use specific exception handling
try:
    process_payment(amount)
except InsufficientFundsError as e:
    logger.warning(f"Payment failed: {e}")
    return PaymentResult(success=False, reason="insufficient_funds")
except PaymentError as e:
    logger.error(f"Payment error: {e}")
    return PaymentResult(success=False, reason="payment_error")

# Use context managers for resource management
from contextlib import contextmanager

@contextmanager
def database_transaction():
    """Provide a transactional scope for database operations."""
    conn = get_connection()
    trans = conn.begin_transaction()
    try:
        yield conn
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
```

### Logging Strategy

```python
import logging
from functools import wraps

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log function entry/exit for debugging
def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__} successfully")
            return result
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {e}")
            raise
    return wrapper
```

## 🔧 Configuration Management

### Environment Variables and Settings

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with validation."""
    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
    redis_url: str = "redis://localhost:6379"
    api_key: str
    max_connections: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Usage
settings = get_settings()
```

## 🏗️ Data Models and Validation

### Example Pydantic Models strict with pydantic v2

```python
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class ProductBase(BaseModel):
    """Base product model with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    category: str
    tags: List[str] = []

    @validator('price')
    def validate_price(cls, v):
        if v > Decimal('1000000'):
            raise ValueError('Price cannot exceed 1,000,000')
        return v

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

class ProductCreate(ProductBase):
    """Model for creating new products."""
    pass

class ProductUpdate(BaseModel):
    """Model for updating products - all fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    category: Optional[str] = None
    tags: Optional[List[str]] = None

class Product(ProductBase):
    """Complete product model with database fields."""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True  # Enable ORM mode
```

## 🔄 Git Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates
- `refactor/*` - Code refactoring
- `test/*` - Test additions or fixes

### Commit Message Format

Never include claude code, or written by claude code in commit messages

```
<type>(<scope>): <subject>

<body>

<footer>
``
Types: feat, fix, docs, style, refactor, test, chore

Example:
```

feat(auth): add two-factor authentication

- Implement TOTP generation and validation
- Add QR code generation for authenticator apps
- Update user model with 2FA fields

Closes #123

````

## 🗄️ Database Naming Standards

### Entity-Specific Primary Keys
All database tables use entity-specific primary keys for clarity and consistency:

```sql
-- ✅ STANDARDIZED: Entity-specific primary keys
sessions.session_id UUID PRIMARY KEY
leads.lead_id UUID PRIMARY KEY
messages.message_id UUID PRIMARY KEY
daily_metrics.daily_metric_id UUID PRIMARY KEY
agencies.agency_id UUID PRIMARY KEY
````

### Field Naming Conventions

```sql
-- Primary keys: {entity}_id
session_id, lead_id, message_id

-- Foreign keys: {referenced_entity}_id
session_id REFERENCES sessions(session_id)
agency_id REFERENCES agencies(agency_id)

-- Timestamps: {action}_at
created_at, updated_at, started_at, expires_at

-- Booleans: is_{state}
is_connected, is_active, is_qualified

-- Counts: {entity}_count
message_count, lead_count, notification_count

-- Durations: {property}_{unit}
duration_seconds, timeout_minutes
```

### Repository Pattern Auto-Derivation

The enhanced BaseRepository automatically derives table names and primary keys:

```python
# ✅ STANDARDIZED: Convention-based repositories
class LeadRepository(BaseRepository[Lead]):
    def __init__(self):
        super().__init__()  # Auto-derives "leads" and "lead_id"

class SessionRepository(BaseRepository[AvatarSession]):
    def __init__(self):
        super().__init__()  # Auto-derives "sessions" and "session_id"
```

**Benefits**:

- ✅ Self-documenting schema
- ✅ Clear foreign key relationships
- ✅ Eliminates repository method overrides
- ✅ Consistent with entity naming patterns

### Model-Database Alignment

Models mirror database fields exactly to eliminate field mapping complexity:

```python
# ✅ STANDARDIZED: Models mirror database exactly
class Lead(BaseModel):
    lead_id: UUID = Field(default_factory=uuid4)  # Matches database field
    session_id: UUID                               # Matches database field
    agency_id: str                                 # Matches database field
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        alias_generator=None  # Use exact field names
    )
```

### API Route Standards

```python
# ✅ STANDARDIZED: RESTful with consistent parameter naming
router = APIRouter(prefix="/api/v1/leads", tags=["leads"])

@router.get("/{lead_id}")           # GET /api/v1/leads/{lead_id}
@router.put("/{lead_id}")           # PUT /api/v1/leads/{lead_id}
@router.delete("/{lead_id}")        # DELETE /api/v1/leads/{lead_id}

# Sub-resources
@router.get("/{lead_id}/messages")  # GET /api/v1/leads/{lead_id}/messages
@router.get("/agency/{agency_id}")  # GET /api/v1/leads/agency/{agency_id}
```

For complete naming standards, see [NAMING_CONVENTIONS.md](./NAMING_CONVENTIONS.md).

## 📝 Documentation Standards

### Code Documentation

- Every module should have a docstring explaining its purpose
- Public functions must have complete docstrings
- Complex logic should have inline comments with `# Reason:` prefix
- Keep README.md updated with setup instructions and examples
- Maintain CHANGELOG.md for version history

### API Documentation

```python
from fastapi import APIRouter, HTTPException, status
from typing import List

router = APIRouter(prefix="/products", tags=["products"])

@router.get(
    "/",
    response_model=List[Product],
    summary="List all products",
    description="Retrieve a paginated list of all active products"
)
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None
) -> List[Product]:
    """
    Retrieve products with optional filtering.

    - **skip**: Number of products to skip (for pagination)
    - **limit**: Maximum number of products to return
    - **category**: Filter by product category
    """
    # Implementation here
```

## 🚀 Performance Considerations

### Optimization Guidelines

- Profile before optimizing - use `cProfile` or `py-spy`
- Use `lru_cache` for expensive computations
- Prefer generators for large datasets
- Use `asyncio` for I/O-bound operations
- Consider `multiprocessing` for CPU-bound tasks
- Cache database queries appropriately

### Example Optimization

```python
from functools import lru_cache
import asyncio
from typing import AsyncIterator

@lru_cache(maxsize=1000)
def expensive_calculation(n: int) -> int:
    """Cache results of expensive calculations."""
    # Complex computation here
    return result

async def process_large_dataset() -> AsyncIterator[dict]:
    """Process large dataset without loading all into memory."""
    async with aiofiles.open('large_file.json', mode='r') as f:
        async for line in f:
            data = json.loads(line)
            # Process and yield each item
            yield process_item(data)
```

## 🛡️ Security Best Practices

### Security Guidelines

- Never commit secrets - use environment variables
- Validate all user input with Pydantic
- Use parameterized queries for database operations
- Implement rate limiting for APIs
- Keep dependencies updated with `uv`
- Use HTTPS for all external communications
- Implement proper authentication and authorization

### Example Security Implementation

```python
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)
```

## 🔍 Debugging Tools

### Debugging Commands

```bash
# Interactive debugging with ipdb
uv add --dev ipdb
# Add breakpoint: import ipdb; ipdb.set_trace()

# Memory profiling
uv add --dev memory-profiler
uv run python -m memory_profiler script.py

# Line profiling
uv add --dev line-profiler
# Add @profile decorator to functions

# Debug with rich traceback
uv add --dev rich
# In code: from rich.traceback import install; install()
```

## 📊 Monitoring and Observability

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "payment_processed",
    user_id=user.id,
    amount=amount,
    currency="USD",
    processing_time=processing_time
)
```

## 📚 Useful Resources

### Essential Tools

- UV Documentation: https://github.com/astral-sh/uv
- Ruff: https://github.com/astral-sh/ruff
- Pytest: https://docs.pytest.org/
- Pydantic: https://docs.pydantic.dev/
- FastAPI: https://fastapi.tiangolo.com/

### Python Best Practices

- PEP 8: https://pep8.org/
- PEP 484 (Type Hints): https://www.python.org/dev/peps/pep-0484/
- The Hitchhiker's Guide to Python: https://docs.python-guide.org/

## ⚠️ Important Notes

- **NEVER ASSUME OR GUESS** - When in doubt, ask for clarification
- **Always verify file paths and module names** before use
- **Keep CLAUDE.md updated** when adding new patterns or dependencies
- **Test your code** - No feature is complete without tests
- **Document your decisions** - Future developers (including yourself) will thank you

## 🔍 Search Command Requirements

**CRITICAL**: Always use `rg` (ripgrep) instead of traditional `grep` and `find` commands:

```bash
# ❌ Don't use grep
grep -r "pattern" .

# ✅ Use rg instead
rg "pattern"

# ❌ Don't use find with name
find . -name "*.py"

# ✅ Use rg with file filtering
rg --files | rg "\.py$"
# or
rg --files -g "*.py"
```

**Enforcement Rules:**

```
(
    r"^grep\b(?!.*\|)",
    "Use 'rg' (ripgrep) instead of 'grep' for better performance and features",
),
(
    r"^find\s+\S+\s+-name\b",
    "Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance",
),
```

## 🚀 GitHub Flow Workflow Summary

main (protected) ←── PR ←── feature/your-feature
↓ ↑
deploy development

### Daily Workflow:

1. git checkout main && git pull origin main
2. git checkout -b feature/new-feature
3. Make changes + tests
4. git push origin feature/new-feature
5. Create PR → Review → Merge to main

---

_This document is a living guide. Update it as the project evolves and new patterns emerge._

---

# INITIAL.md

## FEATURE:

[Insert your feature here]

## EXAMPLES:

[Provide and explain examples that you have in the `examples/` folder]

## DOCUMENTATION:

[List out any documentation (web pages, sources for an MCP server like Crawl4AI RAG, etc.) that will need to be referenced during development]

## OTHER CONSIDERATIONS:

[Any other considerations or specific requirements - great place to include gotchas that you see AI coding assistants miss with your projects a lot]

---

# install_claude_code_windows.md

(This file was empty)

---

# README.md

# 🚀 Full Guide to Using Claude Code

Everything you need to know to crush building anything with Claude Code! This guide takes you from installation through advanced context engineering, subagents, hooks, and parallel agent workflows.

## 📋 Prerequisites

- Terminal/Command line access
- Node.js installed (for Claude Code installation)
- GitHub account (for GitHub CLI integration)
- Text editor (VS Code recommended)

## 🔧 Installation

**macOS/Linux:**
```bash
npm install -g @anthropic-ai/claude-code
```

**Windows (WSL recommended):**
See detailed instructions in [install_claude_code_windows.md](./install_claude_code_windows.md)

**Verify installation:**
```bash
claude --version
```

---

## ✅ TIP 1: CREATE AND OPTIMIZE CLAUDE.md FILES

Set up context files that Claude automatically pulls into every conversation, containing project-specific information, commands, and guidelines.

```bash
mkdir your-folder-name && cd your-folder-name
claude
```

Use the built-in command:
```
/init
```

Or create your own CLAUDE.md file based on the template in this repository. See `CLAUDE.md` for a Python specific example structure that includes:
- Project awareness and context rules
- Code structure guidelines
- Testing requirements
- Task completion workflow
- Style conventions
- Documentation standards

### Advanced Prompting Techniques

**Power Keywords**: Claude responds to certain keywords with enhanced behavior (information dense keywords):
- **IMPORTANT**: Emphasizes critical instructions that should not be overlooked
- **Proactively**: Encourages Claude to take initiative and suggest improvements
- **Ultra-think**: Can trigger more thorough analysis (use sparingly)

**Essential Prompt Engineering Tips**:
- Avoid prompting for "production-ready" code - this often leads to over-engineering
- Prompt Claude to write scripts to check its work: "After implementing, create a validation script"
- Avoid backward compatibility unless specifically needed - Claude tends to preserve old code unnecessarily
- Focus on clarity and specific requirements rather than vague quality descriptors

### File Placement Strategies

Claude automatically reads CLAUDE.md files from multiple locations:

```bash
# Root of repository (most common)
./CLAUDE.md              # Checked into git, shared with team
./CLAUDE.local.md        # Local only, add to .gitignore

# Parent directories (for monorepos)
root/CLAUDE.md           # General project info
root/frontend/CLAUDE.md  # Frontend-specific context
root/backend/CLAUDE.md   # Backend-specific context

# Reference external files for flexibility
echo "Follow best practices in: ~/company/engineering-standards.md" > CLAUDE.md
```

**Pro Tip**: Many teams keep their CLAUDE.md minimal and reference a shared standards document. This makes it easy to:
- Switch between AI coding assistants
- Update standards without changing every project
- Share best practices across teams

*Note: While Claude Code reads CLAUDE.md automatically, other AI coding assistants can use similar context files (such as .cursorrules for Cursor)*

---

## ✅ TIP 2: SET UP PERMISSION MANAGEMENT

Configure tool allowlists to streamline development while maintaining security for file operations and system commands.

**Method 1: Interactive Allowlist**
When Claude asks for permission, select "Always allow" for common operations.

**Method 2: Use /permissions command**
```
/permissions
```
Then add:
- `Edit` (for file edits)
- `Bash(git commit:*)` (for git commits)
- `Bash(npm:*)` (for npm commands)
- `Read` (for reading files)
- `Write` (for creating files)

**Method 3: Create project settings file**
Create `.claude/settings.local.json`:
```json
{
  "allowedTools": [
    "Edit",
    "Read",
    "Write",
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Bash(npm:*)",
    "Bash(python:*)",
    "Bash(pytest:*)"
  ]
}
```

**Security Best Practices**:
- Never allow `Bash(rm -rf:*)` or similar destructive commands
- Use specific command patterns rather than `Bash(*)`
- Review permissions regularly
- Use different permission sets for different projects

*Note: All AI coding assistants have permission management - some built-in, others require manual approval for each action.*

---

## ✅ TIP 3: MASTER CUSTOM SLASH COMMANDS

Slash commands are the key to adding your own workflows into Claude Code. They live in `.claude/commands/` and enable you to create reusable, parameterized workflows.

### Built-in Commands
- `/init` - Generate initial CLAUDE.md
- `/permissions` - Manage tool permissions
- `/clear` - Clear context between tasks
- `/agents` - Manage subagents
- `/help` - Get help with Claude Code

### Custom Command Example

**Repository Analysis**:
```
/primer
```
Performs comprehensive repository analysis to prime Claude Code on your codebase so you can start implemention fixes or new features and it has all the necessary context to do so.

### Creating Your Own Commands

1. Create a markdown file in `.claude/commands/`:
```markdown
# Command: analyze-performance

Analyze the performance of the file specified in $ARGUMENTS.

## Steps:
1. Read the file at path: $ARGUMENTS
2. Identify performance bottlenecks
3. Suggest optimizations
4. Create a benchmark script
```

2. Use the command:
```
/analyze-performance src/heavy-computation.js
```

Commands can use `$ARGUMENTS` to receive parameters and can invoke any of Claude's tools.

*Note: Other AI coding assistants can use these commands as regular prompts - just copy the command content and paste it with your arguments.*

---

## ✅ TIP 4: INTEGRATE MCP SERVERS

Connect Claude Code to Model Context Protocol (MCP) servers for enhanced functionality. Learn more in the [MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp).

**Add Serena MCP Server** - The most powerful coding toolkit:

Make sure you [install uvx](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) first. Here is how you do that in WSL with Windows:
```bash
sudo snap install astral-uv --classic
```

Then add Serena using the command:
```bash
# Install Serena for semantic code analysis and editing
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project $(pwd)
```

[Serena](https://github.com/oraios/serena) transforms Claude Code into a fully-featured coding agent with:
- Semantic code retrieval and analysis
- Advanced editing capabilities using Language Server Protocol (LSP)
- Support for Python, TypeScript/JavaScript, PHP, Go, Rust, C/C++, Java
- Free and open-source alternative to subscription-based coding assistants

**Manage MCP servers:**
```bash
# List all configured servers
claude mcp list

# Get details about a specific server
claude mcp get serena

# Remove a server
claude mcp remove serena
```

**Coming Soon**: Archon V2 (HUGE Overhaul) - A comprehensive knowledge and task management backbone for AI coding assistants - enabling true human-AI collaboration on code for the first time.

*Note: MCP is integrated with every major AI coding assistant and the servers are managed in a very similar way.*

---

## ✅ TIP 5: CONTEXT ENGINEERING WITH EXAMPLES

Transform your development workflow from simple prompting to comprehensive context engineering - providing AI with all the information needed for end-to-end implementation.

### Quick Start

The PRP (Product Requirements Prompt) framework is a simple 3-step strategy for context engineering:

```bash
# 1. Define your requirements with examples and context
# Edit INITIAL.md to include example code and patterns

# 2. Generate a comprehensive PRP
/generate-prp INITIAL.md

# 3. Execute the PRP to implement your feature
/execute-prp PRPs/your-feature-name.md
```

### Defining Your Requirements

Your INITIAL.md should always include:

```markdown
## FEATURE
Build a user authentication system

## EXAMPLES
- Authentication flow: `examples/auth-flow.js`
- Similar API endpoint: `src/api/users.js` 
- Database schema pattern: `src/models/base-model.js`
- Validation approach: `src/validators/user-validator.js`

## DOCUMENTATION
- JWT library docs: https://github.com/auth0/node-jsonwebtoken
- Our API standards: `docs/api-guidelines.md`

## OTHER CONSIDERATIONS
- Use existing error handling patterns
- Follow our standard response format
- Include rate limiting
```

### Critical PRP Strategies

**Examples**: The most powerful tool - provide code snippets, similar features, and patterns to follow

**Validation Gates**: Ensure comprehensive testing and iteration until all tests pass

**No Vibe Coding**: Validate PRPs before executing them and the code after execution!

The more specific examples you provide, the better Claude can match your existing patterns and style.

*Note: Context engineering works with any AI coding assistant - the PRP framework and example-driven approach are universal principles.*

---

## ✅ TIP 6: LEVERAGE SUBAGENTS FOR SPECIALIZED TASKS

Subagents are specialized AI assistants that operate in separate context windows with focused expertise. They enable Claude to delegate specific tasks to experts, improving quality and efficiency.

### Understanding Subagents

Each subagent:
- Has its own context window (no pollution from main conversation)
- Operates with specialized system prompts
- Can be limited to specific tools
- Works autonomously on delegated tasks

### Example Subagents in This Repository

**Documentation Manager** (`.claude/agents/documentation-manager.md`):
- Automatically updates docs when code changes
- Ensures README accuracy
- Maintains API documentation
- Creates migration guides

**Validation Gates** (`.claude/agents/validation-gates.md`):
- Runs all tests after changes
- Iterates on fixes until tests pass
- Enforces code quality standards
- Never marks tasks complete with failing tests

### Creating Your Own Subagents

1. Use the `/agents` command or create a file in `.claude/agents/`:

```markdown
---
name: security-auditor
description: "Security specialist. Proactively reviews code for vulnerabilities and suggests improvements."
tools: Read, Grep, Glob
---

You are a security auditing specialist focused on identifying and preventing security vulnerabilities...

## Core Responsibilities
1. Review code for OWASP Top 10 vulnerabilities
2. Check for exposed secrets or credentials
3. Validate input sanitization
4. Ensure proper authentication/authorization
...
```

### Subagent Best Practices

**1. Focused Expertise**: Each subagent should have one clear specialty

**2. Proactive Descriptions**: Use "proactively" in descriptions for automatic invocation:
```yaml
description: "Code reviewer. Proactively reviews all code changes for quality."
```

**3. Tool Limitations**: Only give subagents the tools they need:
```yaml
tools: Read, Grep  # No write access for review-only agents
```

**4. Information Flow Design**: Understand how information flows from primary agent → subagent → primary agent. The subagent description is crucial because it tells your primary Claude Code agent when and how to use it. Include clear instructions in the description for how the primary agent should prompt this subagent.

**5. One-Shot Context**: Subagents don't have full conversation history - they receive a single prompt from your primary agent. Design your subagents with this limitation in mind.

Learn more in the [Subagents documentation](https://docs.anthropic.com/en/docs/claude-code/sub-agents).

*Note: While other AI assistants don't have formal subagents, you can achieve similar results by creating specialized prompts and switching between different conversation contexts.*

---

## ✅ TIP 7: AUTOMATE WITH HOOKS

Hooks provide deterministic control over Claude Code's behavior through user-defined shell commands that execute at predefined lifecycle events.

### Available Hook Events

Claude Code provides several predefined actions you can hook into:
- **PreToolUse**: Before tool execution (can block operations)
- **PostToolUse**: After successful tool completion  
- **UserPromptSubmit**: When user submits a prompt
- **SubagentStop**: When a subagent completes its task
- **Stop**: When the main agent finishes responding
- **SessionStart**: At session initialization
- **PreCompact**: Before context compaction
- **Notification**: During system notifications

Learn more in the [Hooks documentation](https://docs.anthropic.com/en/docs/claude-code/hooks).

### Example Hook: Tool Usage Logging

This repository includes a simple hook example in `.claude/hooks/`:

**log-tool-usage.sh** - Logs all tool usage for tracking and debugging:
```bash
#!/bin/bash
# Logs tool usage with timestamps
# Creates .claude/logs/tool-usage.log
# No external dependencies required
```

### Setting Up Hooks

1. **Create hook script** in `.claude/hooks/`
2. **Make it executable**: `chmod +x your-hook.sh`
3. **Add to settings** in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/log-tool-usage.sh"
          }
        ]
      }
    ]
  }
}
```

Hooks ensure certain actions always happen, rather than relying on the AI to remember - perfect for logging, security validations, and build triggers.

*Note: Other AI assistants don't have hooks (though Kiro does!), I can almost guarantee they're coming soon for everyone else.*

---

## ✅ TIP 8: GITHUB CLI INTEGRATION

Set up the GitHub CLI to enable Claude to interact with GitHub for issues, pull requests, and repository management.

```bash
# Install GitHub CLI
# Visit: https://github.com/cli/cli#installation

# Authenticate
gh auth login

# Verify setup
gh repo list
```

### Custom GitHub Commands

Use the `/fix-github-issue` command for automated fixes:

```
/fix-github-issue 123
```

This will:
1. Fetch issue details
2. Analyze the problem
3. Search relevant code
4. Implement the fix
5. Run tests
6. Create a PR

*Note: GitHub CLI works with any AI coding assistant - just install it and the AI can use `gh` commands to interact with your repositories.*

---

## ✅ TIP 9: SAFE YOLO MODE WITH DEV CONTAINERS

Allow Claude Code to perform any action while maintaining safety through containerization. This enables rapid development without destructive behavior on your host machine.

**Prerequisites:**
- Install [Docker](https://www.docker.com/) 
- VS Code (or compatible editors)

**Security Features:**
- Network isolation with whitelist
- No access to host filesystem
- Restricted outbound connections
- Safe experimentation environment

**Setup Process:**

1. **Open in VS Code** and press `F1`
2. **Select** "Dev Containers: Reopen in Container"
3. **Wait** for container build
4. **Open terminal** (`Ctrl+J`)
5. **Authenticate** Claude Code in container
6. **Run in YOLO mode**:
   ```bash
   claude --dangerously-skip-permissions
   ```

**Why Use Dev Containers?**
- Test dangerous operations safely
- Experiment with system changes
- Rapid prototyping
- Consistent development environment
- No fear of breaking your system

---

## ✅ TIP 10: PARALLEL DEVELOPMENT WITH GIT WORKTREES

Use Git worktrees to enable multiple Claude instances working on independent tasks simultaneously, or automate parallel implementations of the same feature.

### Manual Worktree Setup

```bash
# Create worktrees for different features
git worktree add ../project-auth feature/auth
git worktree add ../project-api feature/api

# Launch Claude in each worktree
cd ../project-auth && claude  # Terminal 1
cd ../project-api && claude   # Terminal 2
```

### Automated Parallel Agents

AI coding assistants are non-deterministic. Running multiple attempts increases success probability and provides implementation options.

**Setup parallel worktrees:**
```bash
/prep-parallel user-system 3
```

**Execute parallel implementations:**
1. Create a plan file (`plan.md`)
2. Run parallel execution:

```bash
/execute-parallel user-system plan.md 3
```

**Select the best implementation:**
```bash
# Review results
cat trees/user-system-*/RESULTS.md

# Test each implementation
cd trees/user-system-1 && npm test

# Merge the best
git checkout main
git merge user-system-2
```

### Benefits

- **No Conflicts**: Each instance works in isolation
- **Multiple Approaches**: Compare different implementations
- **Quality Gates**: Only consider implementations where tests pass
- **Easy Integration**: Merge the best solution

---

## 🎯 Quick Command Reference

| Command | Purpose |
|---------|---------|
| `/init` | Generate initial CLAUDE.md |
| `/permissions` | Manage tool permissions |
| `/clear` | Clear context between tasks |
| `/agents` | Create and manage subagents |
| `/primer` | Analyze repository structure |
| `ESC` | Interrupt Claude |
| `Shift+Tab` | Enter planning mode |
| `/generate-prp INITIAL.md` | Create implementation blueprint |
| `/execute-prp PRPs/feature.md` | Implement from blueprint |
| `/prep-parallel [feature] [count]` | Setup parallel worktrees |
| `/execute-parallel [feature] [plan] [count]` | Run parallel implementations |
| `/fix-github-issue [number]` | Auto-fix GitHub issues |
| `/prep-parallel [feature] [count]` | Setup parallel worktrees |
| `/execute-parallel [feature] [plan] [count]` | Run parallel implementations |

---

## 📚 Additional Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [MCP Server Library](https://github.com/modelcontextprotocol)

---

## 🚀 Next Steps

1. **Start Simple**: Set up CLAUDE.md and basic permissions
2. **Add Slash Commands**: Create custom commands for your workflow
3. **Install MCP Servers**: Add Serena for enhanced coding capabilities
4. **Implement Subagents**: Add specialists for your tech stack
5. **Configure Hooks**: Automate repetitive tasks
6. **Try Parallel Development**: Experiment with multiple approaches

Remember: Claude Code is most powerful when you provide clear context, specific examples, and comprehensive validation. Happy coding! 🎉

---

## 🤝 Contributing

This guide is a living document. Contributions are welcome! Please open an issue or submit a pull request with your suggestions.

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.