# Contributing to DeckForge

Thanks for your interest in contributing to DeckForge. This guide covers setup, standards, and the PR process.

## Local Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose (for full stack)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Whatsonyourmind/deckforge.git
cd deckforge

# Python backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# TypeScript SDK
cd sdk
npm install
npm run build
cd ..

# Run tests
pytest tests/ -x -v          # Python
cd sdk && npm test            # TypeScript SDK
```

### Docker Compose (full stack)

```bash
docker compose up -d          # Postgres, Redis, API, Worker
docker compose logs -f api    # Watch API logs
```

## Running Tests

```bash
# Python -- all tests
pytest tests/ -x -v

# Python -- specific file
pytest tests/test_mcp_server.py -v

# Python -- with coverage
pytest tests/ --cov=deckforge --cov-report=term-missing

# TypeScript SDK
cd sdk && npm test
cd sdk && npm run test:watch  # Watch mode
```

## Code Style

### Python

- Formatter: **ruff** (`ruff format .`)
- Linter: **ruff** (`ruff check .`)
- Type checker: **mypy** (`mypy src/deckforge/`)
- Line length: 100
- Target: Python 3.12+

### TypeScript SDK

- Strict mode enabled
- Build: **tsup**
- Tests: **vitest**
- Type check: `npm run typecheck`

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scope): add new feature
fix(scope): fix specific bug
test(scope): add or update tests
refactor(scope): code cleanup, no behavior change
chore(scope): config, tooling, dependencies
docs(scope): documentation updates
```

Scopes: `api`, `sdk`, `mcp`, `render`, `content`, `charts`, `themes`, `billing`, `infra`

## Pull Request Process

1. Fork the repository and create a branch from `master`.
2. Make your changes with tests.
3. Ensure all tests pass (`pytest` and `npm test`).
4. Run linters (`ruff check .` and `npm run typecheck`).
5. Write a clear PR description explaining what and why.
6. Submit the PR -- a maintainer will review within 48 hours.

### PR Checklist

- [ ] Tests added/updated for new functionality
- [ ] All tests pass locally
- [ ] Code follows project style guidelines
- [ ] Commit messages follow conventional format
- [ ] PR description explains the change

## Architecture Overview

```
src/deckforge/
  api/          # FastAPI routes
  billing/      # Tiers, credits, Stripe, x402
  charts/       # Chart recommendation engine
  content/      # NL-to-IR content pipeline (4-stage)
  db/           # SQLAlchemy models, repos
  finance/      # Finance-specific slide renderers
  ir/           # Intermediate Representation schema
  layout/       # Constraint-based layout engine
  llm/          # LLM adapters (Claude, GPT, Gemini, Ollama)
  mcp/          # MCP server for AI agent discovery
  qa/           # Quality assurance pipeline
  rendering/    # PPTX + Google Slides renderers
  services/     # Business logic (cost estimator, registries)
  themes/       # Theme registry and resolver
  workers/      # ARQ async task workers

sdk/            # TypeScript SDK (@deckforge/sdk)
tests/          # Python test suite
```

## Questions?

Open a [Discussion](https://github.com/Whatsonyourmind/deckforge/discussions) or reach out via Issues.
