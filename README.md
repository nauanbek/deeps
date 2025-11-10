# DeepAgents Control Platform

Enterprise administrative platform for creating, configuring, and managing AI agents based on the [deepagents](https://github.com/deepagents/deepagents) framework (LangChain/LangGraph). Transform deepagents from a code-first library into a visual development environment with a FastAPI backend and React frontend.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![React](https://img.shields.io/badge/react-18.3.1-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121-green.svg)

## Features

### Core Platform
- **Visual Agent Studio** - Create and configure AI agents through an intuitive web interface
- **Real-time Execution Monitor** - Stream agent execution traces via WebSocket
- **Template Library** - 8 pre-configured agent templates for common use cases
- **Custom Tool Marketplace** - Build and integrate custom tools for agents
- **Advanced Analytics** - Track performance, costs, and usage metrics

### Agent Capabilities
- **Planning & Task Decomposition** - Built-in support for structured task planning
- **Filesystem Operations** - Sandboxed file system access for agents
- **Subagent Orchestration** - Hierarchical delegation to specialized sub-agents
- **External Tool Integration** - Connect to PostgreSQL, GitLab, Elasticsearch, and HTTP APIs
- **Long-term Memory** - Persistent storage across agent sessions
- **Human-in-the-Loop (HITL)** - Approval workflows for sensitive operations

### Enterprise Features
- **JWT Authentication** - Secure API access with token-based auth
- **Multi-user Support** - User isolation and role-based access
- **Monitoring & Metrics** - Prometheus metrics and Grafana dashboards
- **Centralized Logging** - Loki + Promtail log aggregation
- **Production Ready** - Docker deployment with zero-downtime updates

## Technology Stack

### Backend
- **Python 3.13.3** - Modern async Python
- **FastAPI 0.121+** - High-performance web framework
- **PostgreSQL 17.6** - Primary database (SQLAlchemy 2.0.44 async)
- **Redis 7.4.6** - Caching and session storage
- **deepagents 0.2.5** - LangChain 1.0.3+ / LangGraph 1.0.2+
- **pytest 8.3.4** - 517/521 tests passing (99.2% coverage)

### Frontend
- **React 18.3.1** - Modern UI library
- **TypeScript 5.9.3** - Type-safe development
- **TanStack Query V5** - Server state management
- **Tailwind CSS** - Utility-first styling
- **Monaco Editor** - Code editing
- **Socket.IO** - Real-time WebSocket communication

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy with SSL/TLS
- **Prometheus + Grafana** - Monitoring and visualization
- **Loki + Promtail** - Log aggregation

## Quick Start

### Prerequisites
- **Python 3.13+**
- **Node.js 24.8.0+**
- **PostgreSQL 17.6** (or use Docker Compose)
- **Redis 7.4.6** (or use Docker Compose)
- **API Keys**: Anthropic (`ANTHROPIC_API_KEY`) and/or OpenAI (`OPENAI_API_KEY`)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/deepagents-control-platform.git
cd deepagents-control-platform
```

### 2. Start Infrastructure (PostgreSQL + Redis)

```bash
cd infrastructure
docker-compose up -d
cd ..
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY)
# Generate SECRET_KEY: openssl rand -hex 32
# Generate CREDENTIAL_ENCRYPTION_KEY: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'

# Run migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload
```

Backend will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will be available at: http://localhost:3000

### 5. Create Your First User

**Option A: Via API (Recommended)**

Visit http://localhost:8000/docs and use the `/api/v1/auth/register` endpoint.

**Option B: Seed Development Data**

```bash
cd backend
python init_db.py --seed
```

> **SECURITY WARNING**: This creates a user `admin` with password `admin123`.
> This is for DEVELOPMENT ONLY. Change the password immediately!

## Architecture

```
deeps/
├── backend/              # FastAPI backend (Python 3.13)
│   ├── api/             # REST API endpoints (92 total)
│   ├── models/          # SQLAlchemy database models (14 tables)
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Business logic layer
│   ├── deepagents_integration/  # deepagents framework integration
│   ├── langchain_tools/ # External tool wrappers
│   └── tests/           # Backend tests (517 passing)
├── frontend/            # React frontend (TypeScript)
│   ├── src/pages/      # Page components
│   ├── src/components/ # Reusable UI components
│   ├── src/api/        # API client
│   ├── src/hooks/      # Custom React hooks
│   └── src/types/      # TypeScript definitions
└── infrastructure/      # Docker, monitoring, deployment
    ├── docker-compose.yml
    ├── prometheus/
    ├── grafana/
    └── scripts/
```

## Development

### Backend Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage --watchAll=false

# Build for production
npm run build

# Start Storybook (component development)
npm run storybook
```

### Code Quality

```bash
# Backend: Format with black
black backend/

# Frontend: Check types
cd frontend && npm run type-check

# Frontend: Lint
cd frontend && npm run lint
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user profile

### Agents
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents/{id}` - Get agent details
- `PUT /api/v1/agents/{id}` - Update agent
- `DELETE /api/v1/agents/{id}` - Delete agent

### Executions
- `POST /api/v1/agents/{id}/execute` - Execute agent
- `GET /api/v1/executions` - List executions
- `GET /api/v1/executions/{id}` - Get execution details
- `WS /api/v1/executions/{id}/stream` - Stream execution traces

### Templates
- `GET /api/v1/templates` - List templates
- `POST /api/v1/templates` - Create template
- `POST /api/v1/templates/{id}/clone` - Clone template to agent

### External Tools
- `GET /api/v1/external-tools` - List tool configurations
- `POST /api/v1/external-tools` - Create tool configuration
- `POST /api/v1/external-tools/{id}/test` - Test connection

Full API documentation available at http://localhost:8000/docs

## Configuration

### Environment Variables

**Backend** (`.env`):
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/deepagents_platform

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
CREDENTIAL_ENCRYPTION_KEY=<generate-with-fernet>

# AI Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Frontend** (`.env.local`):
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Production Deployment

See [infrastructure/DEPLOYMENT.md](infrastructure/DEPLOYMENT.md) for comprehensive production deployment guide including:
- Multi-stage Docker builds
- Nginx reverse proxy configuration
- SSL/TLS setup with Let's Encrypt
- Zero-downtime rolling updates
- Database backup/restore procedures
- Monitoring and alerting setup

Quick production start:

```bash
cd infrastructure
cp .env.production.example .env.production
# Edit .env.production with your settings
./scripts/deploy.sh
```

## Testing

### Backend Tests
- **517/521 tests passing** (99.2% coverage)
- Async SQLAlchemy tests with SQLite
- API endpoint integration tests
- deepagents integration tests

```bash
cd backend
pytest
```

### Frontend Tests
- **434/471 tests passing** (92%)
- React component tests with Testing Library
- Integration tests with mocked APIs

```bash
cd frontend
npm test
```

## Security

- JWT authentication with 30-minute token expiry
- bcrypt password hashing (12 rounds)
- Fernet encryption for external tool credentials
- SQL injection protection via SQLAlchemy
- CORS middleware enabled
- Rate limiting on external tool executions
- Credential sanitization in logs

> **Production Security Checklist**:
> - Change all default passwords immediately
> - Use strong, randomly generated SECRET_KEY
> - Enable SSL/TLS for all connections
> - Set up database backups
> - Configure firewall rules
> - Review and update CORS_ORIGINS
> - Enable account lockout after failed login attempts

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` for backend, `npm test` for frontend)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See `/docs` directory for detailed guides
- **API Reference**: http://localhost:8000/docs (Swagger UI)
- **Issues**: [GitHub Issues](https://github.com/yourusername/deepagents-control-platform/issues)

## Acknowledgments

- Built with [deepagents](https://github.com/deepagents/deepagents) framework
- Powered by [LangChain](https://python.langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- UI components from [Headless UI](https://headlessui.com/)
- Monitoring with [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/)

---

**Note**: This platform is under active development. See [project status](docs/PROJECT_STATUS.md) for current feature completion and roadmap.
