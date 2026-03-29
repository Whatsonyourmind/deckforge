# DeckForge Agent Framework Integrations

Use DeckForge from any major AI agent framework. Each integration wraps the same REST API, so you get identical results regardless of framework.

## Framework Integrations

| Framework | File | Pattern | Status |
|-----------|------|---------|--------|
| [LangChain](https://github.com/langchain-ai/langchain) | [`langchain-tool.py`](./langchain-tool.py) | `BaseTool` subclass (2 tools: render + generate) | Ready to submit PR to `langchain-community` |
| [CrewAI](https://github.com/crewAI-Inc/crewAI) | [`crewai-tool.py`](./crewai-tool.py) | `BaseTool` subclass (1 unified tool) | Ready to submit PR to `crewai-tools` |
| [AutoGen](https://github.com/microsoft/autogen) | [`autogen-tool.py`](./autogen-tool.py) | Function tools with `Annotated` types | Ready to submit PR to `autogen` |
| [Claude/MCP](https://modelcontextprotocol.io) | [`claude-agent-example.py`](./claude-agent-example.py) | MCP server (6 tools) + Anthropic SDK | Ships with DeckForge |

## Which Framework Should I Use?

| Use Case | Recommended Framework |
|----------|----------------------|
| Single agent + tools | **LangChain** -- mature ecosystem, most tool integrations |
| Multi-agent collaboration | **CrewAI** -- role-based agents with task delegation |
| Complex agent conversations | **AutoGen** -- flexible multi-turn agent dialogues |
| Claude Desktop / MCP hosts | **Claude/MCP** -- zero-code setup via config file |
| Any framework (raw API) | **httpx + REST API** -- framework-agnostic, full control |

## Quick Start

### 1. Get an API Key

```bash
# Sign up at https://deckforge.io
# Free tier: 50 credits/month
export DECKFORGE_API_KEY=dk_live_your_key_here
```

### 2. Install Dependencies

```bash
# LangChain
pip install langchain-core httpx

# CrewAI
pip install crewai crewai-tools httpx

# AutoGen
pip install autogen-agentchat httpx

# Claude/MCP (no extra deps -- uses DeckForge MCP server)
pip install deckforge
```

### 3. Use in Your Agent

**LangChain:**
```python
from deckforge_langchain import DeckForgeRenderTool, DeckForgeGenerateTool
tools = [DeckForgeRenderTool(), DeckForgeGenerateTool()]
agent = create_react_agent(llm, tools)
```

**CrewAI:**
```python
from deckforge_crewai import DeckForgeTool
presenter = Agent(role="Presenter", tools=[DeckForgeTool()])
```

**AutoGen:**
```python
from deckforge_autogen import generate_presentation, render_presentation
assistant.register_for_llm()(generate_presentation)
user_proxy.register_for_execution()(generate_presentation)
```

**Claude Desktop:**
```json
{
  "mcpServers": {
    "deckforge": {
      "command": "python",
      "args": ["-m", "deckforge.mcp.server"],
      "env": { "DECKFORGE_API_KEY": "dk_live_xxx" }
    }
  }
}
```

## Common API Patterns

All integrations call the same DeckForge REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/render` | POST | Render IR JSON to PPTX/Google Slides |
| `/v1/generate` | POST | Generate deck from natural language prompt |
| `/v1/themes` | GET | List available themes |
| `/v1/slide-types` | GET | List slide types (universal + finance) |
| `/v1/capabilities` | GET | Full API capability discovery |
| `/v1/estimate` | POST | Estimate credit cost before rendering |
| `/v1/pricing` | GET | Pricing tiers and per-call costs |

**Authentication:** `Authorization: Bearer dk_live_xxx` header on all requests.

**Base URL:** `https://api.deckforge.io` (override with `DECKFORGE_API_URL` env var).

## PR Contribution Status

| Framework | Target Repo | PR Status | Notes |
|-----------|-------------|-----------|-------|
| LangChain | [`langchain-ai/langchain`](https://github.com/langchain-ai/langchain/tree/master/libs/community) | Ready to submit | `langchain_community/tools/deckforge.py` |
| CrewAI | [`crewAI-Inc/crewAI-tools`](https://github.com/crewAI-Inc/crewAI-tools) | Ready to submit | `crewai_tools/tools/deckforge_tool/` |
| AutoGen | [`microsoft/autogen`](https://github.com/microsoft/autogen) | Ready to submit | `autogen/tools/deckforge.py` |
| MCP | Ships with DeckForge | Included | `deckforge.mcp.server` module |

## DeckForge Capabilities

What your agent can create:

- **32 slide types**: title, bullets, chart, table, two_column, image, quote, timeline, process, comparison, metrics, SWOT, org_chart, funnel, kanban, pricing_table, feature_matrix, and 9 finance types
- **24 chart types**: bar, line, area, pie, donut, scatter, bubble, combo, radar, funnel, waterfall, heatmap, sankey, gantt, football_field, sensitivity, treemap, tornado, sunburst, and more
- **15 curated themes**: corporate-blue, executive-dark, startup-vibrant, minimal-light, finance-professional, consulting-clean, tech-modern, academic-formal, etc.
- **Quality assurance**: 5-pass QA pipeline with auto-fix (contrast, overflow, data validation)
- **Output formats**: PPTX (PowerPoint) and Google Slides

## Links

- **API Docs**: https://docs.deckforge.io
- **GitHub**: https://github.com/Whatsonyourmind/deckforge
- **npm SDK**: https://www.npmjs.com/package/@deckforge/sdk
- **Landing Page**: https://deckforge.io
- **MCP Server**: https://github.com/Whatsonyourmind/deckforge/tree/main/src/deckforge/mcp
