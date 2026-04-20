# Publishing DeckForge to the MCP Registry

## Status (2026-04-20)

| Directory | Status | URL |
|-----------|--------|-----|
| Glama | ✅ LIVE | https://glama.ai/mcp/servers/kkev9cu5yw (Whatsonyourmind/deckforge) |
| MCP Registry | ❌ NOT LISTED | — |
| Smithery | ❓ Unverified (17d-old memory claims published under `lukastan/deckforge` but that namespace errors on Glama) |
| MCP.so | ❓ Unverified |

## Why deckforge-mcp on npm is a no-go

The `deckforge-mcp`, `deckforge-team-mcp`, and `deckforge-analytics-mcp` npm packages are owned by **another publisher** (`crawde` / DeckForgeAI — a different company). They were first to the name. Publishing under a scoped name like `@lukastan/deckforge-mcp` is possible but less discoverable.

DeckForge's own MCP server is **Python/FastMCP** (not Node.js) — so the natural distribution path is PyPI + the MCP Registry's `registryType: pypi`.

## Publishing steps

### 1. Publish DeckForge to PyPI first

The MCP Registry references a PyPI package identifier. PyPI name `deckforge` appears to be available (returns 404 on pypi.org).

```bash
# From SlideMaker repo root
python -m pip install --upgrade build twine
python -m build
python -m twine upload dist/* \
    --username __token__ \
    --password <PYPI_API_TOKEN>
```

Store the token in `C:/Users/lukep/.claude/secrets/pypi.env` (gitignored) as `PYPI_API_TOKEN=pypi-...`.

### 2. Submit to MCP Registry

Install the publisher:

```bash
# Linux/macOS: curl install; Windows/Git Bash: download from releases
curl -L https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr A-Z a-z)_amd64.tar.gz | tar -xz
```

Authenticate (JWT lasts ~24h, must re-auth each release):

```bash
./mcp-publisher login github
```

Publish:

```bash
cd "C:/Users/lukep/Desktop/Projects AI/SlideMaker"
./mcp-publisher publish
```

The `server.json` at the repo root (already created) handles the rest. It declares:
- `pypi:deckforge` for local install (`pip install deckforge`, then `python -m deckforge.mcp.server`)
- `remote: streamable-http` at `https://deckforge-api.onrender.com/v1/mcp` — no-install option

### 3. Re-verify Smithery + MCP.so

Two directories claimed in 17-day-old memory but never verified:

- **Smithery**: go to https://smithery.ai and search `deckforge`. If missing, submit via their "Add server" flow pointing to `github.com/Whatsonyourmind/deckforge` with `server.json` at the root.
- **MCP.so**: go to https://mcp.so and search. If missing, submit via their form.

### 4. Glama tool inspection (bonus)

Glama listing shows `tools: []` — likely because the Python server needs env vars to boot, so their inspector can't walk the tool list. Two options:

- Add an optional `--dry-run` flag to `deckforge.mcp.server` that starts the server with in-memory stubs so Glama's inspector can enumerate tools
- Or host a public streamable-http endpoint at `deckforge-api.onrender.com/v1/mcp` (already declared in server.json) and point Glama there via the "remote server URL" field on its dashboard

Either path unlocks a B+ → A rating.
