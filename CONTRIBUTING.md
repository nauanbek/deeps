# Contributing to DeepAgents Control Platform

Thank you for your interest in contributing! This guide will help you get started.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/deeps.git
cd deeps
git remote add upstream https://github.com/original/deeps.git
```

### 2. Set Up Development Environment

Follow [QUICKSTART.md](QUICKSTART.md) to set up your local environment.

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## Development Workflow

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run linter
ruff check .
black --check .

# Format code
black .
ruff check --fix .

# Type checking
mypy .
```

### Frontend Development

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage --watchAll=false

# Run linter
npm run lint

# Format code
npm run format

# Type checking
npm run type-check
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Description"

# Review the generated migration file
# Edit if necessary

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Pull Request Process

### 1. Before Submitting

- [ ] All tests pass (`pytest` and `npm test`)
- [ ] Code follows style guidelines (run linters)
- [ ] New features have tests (>80% coverage)
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive

### 2. Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(agents): Add support for GPT-4 Turbo model

- Added GPT-4 Turbo to model selection
- Updated model configuration schema
- Added tests for new model type

Closes #123
```

```
fix(api): Resolve CORS issue with WebSocket connections

The WebSocket endpoint was rejecting connections due to
incorrect CORS configuration.

Fixes #456
```

### 3. Create Pull Request

1. Push your branch: `git push origin feature/your-feature`
2. Go to GitHub and create a Pull Request
3. Fill in the PR template:
   - Description of changes
   - Related issue number
   - Testing performed
   - Screenshots (if UI changes)

### 4. Code Review Process

- Maintainers will review your PR
- Address feedback by pushing new commits
- Once approved, your PR will be merged

## Testing Guidelines

### Backend Tests

**Test Structure:**
```python
def test_create_agent_success(test_user, db_session):
    """Test successful agent creation."""
    # Arrange
    agent_data = AgentCreate(name="Test Agent", ...)

    # Act
    result = await agent_service.create_agent(
        db_session, agent_data, test_user.id
    )

    # Assert
    assert result.name == "Test Agent"
    assert result.user_id == test_user.id
```

**Coverage Requirements:**
- New features: >80% coverage
- Bug fixes: Add regression tests
- Critical paths: 100% coverage

### Frontend Tests

**Component Tests:**
```typescript
describe('AgentCard', () => {
  it('renders agent information correctly', () => {
    const agent = { id: 1, name: 'Test Agent', ... };
    render(<AgentCard agent={agent} />);

    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });
});
```

**Integration Tests:**
```typescript
it('creates a new agent', async () => {
  const user = userEvent.setup();
  render(<AgentStudio />);

  await user.click(screen.getByText('Create Agent'));
  await user.type(screen.getByLabelText('Name'), 'New Agent');
  await user.click(screen.getByText('Submit'));

  await waitFor(() => {
    expect(screen.getByText('New Agent')).toBeInTheDocument();
  });
});
```

## Code Style Guidelines

### Python (Backend)

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all functions
- Maximum line length: 100 characters
- Use `black` for formatting
- Use `ruff` for linting

**Example:**
```python
async def create_agent(
    db: AsyncSession,
    agent_data: AgentCreate,
    user_id: int
) -> Agent:
    """
    Create a new agent for the specified user.

    Args:
        db: Database session
        agent_data: Agent creation data
        user_id: ID of the user creating the agent

    Returns:
        Agent: The created agent instance

    Raises:
        ValueError: If agent_data is invalid
    """
    agent = Agent(**agent_data.dict(), user_id=user_id)
    db.add(agent)
    await db.commit()
    return agent
```

### TypeScript (Frontend)

- Follow [Airbnb Style Guide](https://github.com/airbnb/javascript)
- Use functional components with hooks
- Use TypeScript strict mode
- Maximum line length: 100 characters

**Example:**
```typescript
interface AgentCardProps {
  agent: Agent;
  onDelete?: (id: number) => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  onDelete
}) => {
  const handleDelete = useCallback(() => {
    if (onDelete) {
      onDelete(agent.id);
    }
  }, [agent.id, onDelete]);

  return (
    <div className="agent-card">
      <h3>{agent.name}</h3>
      <Button onClick={handleDelete}>Delete</Button>
    </div>
  );
};
```

## Documentation

### Code Documentation

- **Python**: Use Google-style docstrings
- **TypeScript**: Use JSDoc comments
- **README updates**: Required for new features
- **CLAUDE.md updates**: Required for architecture changes

### Documentation Structure

```
docs/
├── api/           # API documentation
├── architecture/  # System architecture
├── guides/        # How-to guides
└── tutorials/     # Step-by-step tutorials
```

## Feature Development

### 1. Discuss First

For major features:
1. Open an issue describing the feature
2. Discuss design and approach
3. Get approval from maintainers
4. Create a design document if needed

### 2. Implementation Steps

1. Write tests first (TDD approach)
2. Implement the feature
3. Update documentation
4. Add examples if applicable
5. Submit PR

### 3. Breaking Changes

If your change breaks backward compatibility:
1. Discuss in the issue first
2. Provide migration guide
3. Update CHANGELOG.md
4. Increment major version

## Bug Reports

### Good Bug Report Includes:

- **Description**: What happened vs. what you expected
- **Steps to Reproduce**: Detailed steps
- **Environment**: OS, Python/Node version, browser
- **Logs**: Relevant error messages
- **Screenshots**: If UI-related

### Example:

```markdown
**Bug Description**
Agent execution fails with "ANTHROPIC_API_KEY not configured"
even though the key is set in .env

**Steps to Reproduce**
1. Add ANTHROPIC_API_KEY to backend/.env
2. Restart uvicorn
3. Create and execute an agent
4. See error

**Environment**
- OS: macOS 14.0
- Python: 3.13.0
- Backend logs: [attached]

**Expected Behavior**
Agent should execute successfully using the configured API key

**Actual Behavior**
Error: "ANTHROPIC_API_KEY not configured"
```

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

- [ ] All tests passing
- [ ] CHANGELOG.md updated
- [ ] Version bumped in package.json / pyproject.toml
- [ ] Documentation updated
- [ ] Migration guide (if breaking changes)
- [ ] Tag created: `git tag v1.2.3`
- [ ] Release notes published

## Questions?

- **General questions**: Open a Discussion on GitHub
- **Bug reports**: Open an Issue
- **Security issues**: Email security@example.com
- **Chat**: Join our Discord/Slack

## Recognition

Contributors will be:
- Listed in CHANGELOG.md for each release
- Mentioned in release notes
- Added to Contributors section in README.md

Thank you for contributing! 🎉
