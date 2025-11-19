# DeepAgents Control Platform - Quick Start Guide

Get up and running with DeepAgents in under 10 minutes.

## Prerequisites

- **Python 3.13+** with pip
- **Node.js 24+** with npm
- **PostgreSQL 17+** (or Docker)
- **Redis 7+** (or Docker)
- **API Keys**: Anthropic and/or OpenAI

## Option 1: Quick Start with Docker (Recommended)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd deeps
cp backend/.env.example backend/.env
```

### 2. Add API Keys

Edit `backend/.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=$(openssl rand -hex 32)
CREDENTIAL_ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
```

### 3. Start Services

```bash
cd infrastructure
docker-compose up -d  # Starts PostgreSQL + Redis
```

### 4. Initialize Database

```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head  # Run migrations
python init_db.py     # Optional: Add test data
```

### 5. Start Backend

```bash
uvicorn main:app --reload
# Backend running at http://localhost:8000
```

### 6. Start Frontend

```bash
cd ../frontend
npm install
npm start
# Frontend running at http://localhost:3000
```

### 7. Create Your First Agent

1. Open http://localhost:3000
2. Register a new account
3. Navigate to **Agents** → **Create Agent**
4. Configure your agent:
   - Name: "My First Agent"
   - Model: Claude 3.5 Sonnet
   - System Prompt: "You are a helpful AI assistant"
5. Click **Create Agent**
6. Go to **Executions** → **Run Agent**
7. Enter a task and watch it execute!

## Option 2: Manual Setup (No Docker)

### 1. Install PostgreSQL and Redis

**macOS:**
```bash
brew install postgresql@17 redis
brew services start postgresql@17
brew services start redis
```

**Ubuntu:**
```bash
sudo apt install postgresql-17 redis-server
sudo systemctl start postgresql redis
```

### 2. Create Database

```bash
psql postgres
CREATE DATABASE deepagents_platform;
CREATE USER deepagents WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE deepagents_platform TO deepagents;
\q
```

### 3. Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://deepagents:your-password@localhost/deepagents_platform
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=$(openssl rand -hex 32)
CREDENTIAL_ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
```

### 4. Follow Steps 4-7 from Option 1

## What's Next?

### Explore Features

- **Agent Templates**: Pre-configured agents for common tasks
- **Custom Tools**: Add your own tools via the Tool Marketplace
- **External Tools**: Connect PostgreSQL, GitLab, Elasticsearch, HTTP
- **Advanced Config**: Configure backends, memory, HITL approval flows

### Read the Docs

- [CLAUDE.md](CLAUDE.md) - Complete project documentation
- [EXTERNAL_TOOLS_INTEGRATION.md](EXTERNAL_TOOLS_INTEGRATION.md) - External tools guide
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Advanced deepagents features
- [API Documentation](http://localhost:8000/docs) - Interactive Swagger UI

### Production Deployment

- See [infrastructure/DEPLOYMENT.md](infrastructure/DEPLOYMENT.md) for production setup
- Configure SSL/TLS, backups, monitoring, and scaling

## Troubleshooting

### Backend Issues

**"ANTHROPIC_API_KEY not configured"**
- Add API key to `backend/.env`
- Restart uvicorn

**Database connection errors**
- Ensure PostgreSQL is running: `psql -l`
- Check DATABASE_URL in `.env`

**Module not found errors**
- Activate venv: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

### Frontend Issues

**CORS errors**
- Ensure backend is running on port 8000
- Check backend logs for CORS configuration

**White screen / blank page**
- Check browser console for errors
- Ensure `REACT_APP_API_URL=http://localhost:8000` in `.env.local`

**API authentication failures**
- Token expires after 30 minutes - login again
- Clear browser local storage and re-login

### Common Errors

**Port already in use**
```bash
# Backend (8000)
lsof -ti:8000 | xargs kill -9

# Frontend (3000)
lsof -ti:3000 | xargs kill -9
```

**Redis connection failed**
```bash
# Check Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

## Need Help?

- **Issues**: [GitHub Issues](https://github.com/yourusername/deeps/issues)
- **Documentation**: Check [CLAUDE.md](CLAUDE.md) for detailed guides
- **API**: Browse [http://localhost:8000/docs](http://localhost:8000/docs)

## Quick Commands Cheat Sheet

```bash
# Start infrastructure
cd infrastructure && docker-compose up -d

# Backend
cd backend && source venv/bin/activate
uvicorn main:app --reload

# Frontend
cd frontend && npm start

# Run tests
cd backend && pytest
cd frontend && npm test

# Database migrations
cd backend && alembic upgrade head

# Stop all services
docker-compose down
pkill -f uvicorn
pkill -f "react-scripts"
```

## Next Steps

1. **Create more agents** with different models and prompts
2. **Try templates** from the Template Library
3. **Add custom tools** to extend agent capabilities
4. **Configure external tools** for database/API access
5. **Explore advanced features** like memory and HITL approval

Welcome to DeepAgents! 🚀
