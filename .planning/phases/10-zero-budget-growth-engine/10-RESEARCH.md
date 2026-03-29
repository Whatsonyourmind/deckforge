# Phase 10 Research: Zero-Budget Growth Engine

## Research Date: 2026-03-26

## 1. MCP Directory Listings

### Tier 1 — High Traffic Directories

**Smithery.ai**
- Largest MCP marketplace. Requires GitHub repo URL. Listings show: name, description, author, install command, transport type (stdio/SSE), tools list with descriptions, star count, install count.
- Submission: Automated from GitHub repo. Needs valid MCP server manifest or README with tool descriptions.
- Traffic: High — primary discovery channel for Claude Desktop users.

**Glama.ai**
- 20,438+ MCP servers catalogued. Most comprehensive registry.
- Listings show: name, description, author, license, OS compatibility, security/quality/license grades, category tags, GitHub stars, recent 30-day usage.
- Has "Add Server" button for submission. Categories include Developer Tools, Finance.
- Key insight: Grades (security, quality, license) are auto-computed. MIT license + good README = high grades.

**mcpservers.org (via awesome-mcp-servers repo, 3.8k stars)**
- Curated list, does NOT accept PRs. Submit at mcpservers.org/submit.
- Fields: Server Name, Short Description, Link (GitHub), Category, Contact Email.
- Categories: Web Scraping, Communication, Productivity, Development, Database, Cloud Service, File System, Cloud Storage, Version Control, Other.
- Premium submit ($39): expedited review, official badge, dofollow link. Worth it for SEO.
- DeckForge category: "Productivity" or "Other" (no "Presentations" category).

### Tier 2 — Niche/Growing Directories

**OpenTools.com**
- "The API for LLM tool use" — unified completions API over MCP tools.
- Registry of supported MCP servers. FAQ mentions adding servers but process unclear.
- Worth submitting — targets the exact "API for agents" market DeckForge serves.

**mcp.run (now redirects to turbomcp.ai)**
- Rebranded. Publishing via CLI or web. Wasm-based execution model.
- Lower priority — different execution model than DeckForge's stdio/HTTP.

**Cursor Directory**
- Popular with Cursor IDE users. Has MCP server section.
- Submission likely via GitHub PR or web form.
- High value: Cursor users are developer-first, likely DeckForge buyers.

### Tier 3 — GitHub Native Discovery

**GitHub Topics**
- 10,810+ repos tagged `mcp-server` on GitHub.
- Python (3,875 repos) and TypeScript (3,162 repos) dominate.
- DeckForge should use topics: `mcp-server`, `mcp`, `presentations`, `slides`, `pptx`, `ai-agents`, `finance`.

## 2. GitHub Repository Optimization

### Star-Worthy README Patterns

Top starred MCP servers share these README patterns:
1. **Hero badge row** — npm version, stars, license, TypeScript badge
2. **One-liner value prop** — what it does in < 15 words
3. **Install snippet first** — `npx` or `pip install` within first 10 lines
4. **GIF or screenshot** — visual proof it works
5. **Feature matrix** — table comparing to alternatives
6. **Quick Start in < 5 steps** — copy-paste to working
7. **Prominent "Try it now" CTA**

### Trending Algorithm Signals
- Stars velocity (stars/day in first 48 hours)
- README quality and length (measured)
- Topic tags relevance
- Recent commits (active development signal)
- Language diversity (Python + TypeScript = wider appeal)

### Social Preview Image
- 1280x640px Open Graph image
- Show: logo, tagline, key numbers (32 slide types, 15 themes)
- GitHub uses this in social shares, embeds, link previews

## 3. Product Hunt Launch

### Best Practices (2026)
- **Day**: Tuesday or Wednesday (highest traffic)
- **Time**: 12:01 AM PT (full 24 hours of voting)
- **Tagline formula**: [Action] + [Outcome] + [For whom]
  - "Generate executive-ready slides with one API call. Built for AI agents."
- **First comment**: Maker story — why you built it, what makes it different, personal angle
- **Media**: 5+ images, GIF demo, optional video
- **Pre-launch**: Notify supporters 48 hours before, ask for upvotes at launch
- **Categories**: Developer Tools, Artificial Intelligence, Productivity, API

### Tagline Candidates
1. "Executive-ready presentations via API. 32 slide types. 15 themes. Zero design skills."
2. "The API that turns AI agents into presentation experts."
3. "Board-ready slides in one API call. For developers and AI agents."

## 4. Developer Blog Posts

### Platform Analysis

**Dev.to**
- Highest engagement for developer tools. MCP tag is active (43+ reactions on top posts).
- "How I built X" posts with code snippets get most engagement.
- Cross-posting allowed (canonical URL back to your blog).

**Hashnode**
- Good for SEO (custom domain support).
- Technical deep-dives perform well.
- Smaller but more technical audience.

**Medium** (via Better Programming, Towards AI publications)
- Wider reach but paywalled content reduces sharing.
- Good for "Why AI agents need X" thought leadership.

### Topic ROI for API Products

| Topic Type | Traffic | Conversions | Effort |
|------------|---------|-------------|--------|
| "How I built X" technical deep-dive | High | Medium | High |
| Tutorial: "Generate slides with AI in 5 min" | Medium | High | Medium |
| Comparison: "DeckForge vs Beautiful.ai vs Gamma" | High | High | Medium |
| Thought leadership: "Why agents need their own APIs" | Medium | Low | Low |
| Use case: "Automating IC deck generation" | Low | Very High | Medium |

### Recommended Articles (priority order)
1. "Show HN: DeckForge" companion blog post (Dev.to)
2. "How I Built a 6-Layer AI Slide Generation Engine" (Dev.to + Hashnode)
3. "Why AI Agents Need Their Own Presentation API" (Dev.to + Medium)
4. "Generate a McKinsey-Style Strategy Deck in 30 Seconds" (Dev.to — tutorial)
5. "DeckForge vs Beautiful.ai vs Gamma: API-First Wins" (SEO play)

## 5. Hacker News (Show HN)

### What Gets Upvoted
- Novel technical approach (constraint-based layout solver is novel)
- Open source or freemium
- Working demo / try-it-now link
- Builder story with genuine technical depth
- NOT just another wrapper around GPT

### Title Patterns That Work
- "Show HN: [Name] -- [What it does in plain English]"
- "Show HN: DeckForge -- An API that generates executive-ready slides for AI agents"
- Keep under 80 chars. No marketing speak. No superlatives.

### Comment Strategy
- First comment: technical founder story, architecture choices, honest limitations
- Respond to EVERY comment in first 4 hours
- Be humble about limitations, enthusiastic about tech
- Link to GitHub, not landing page (HN culture)

## 6. Agent Framework Integrations

### Priority Frameworks

**LangChain (Highest priority)**
- langchain-community has tool integrations. PR to add DeckForge tool.
- Pattern: Create `langchain_community/tools/deckforge/` with tool class.
- Also: LangChain Hub recipe showing DeckForge in agent workflow.

**CrewAI**
- crewai-tools repo accepts community tools.
- Pattern: `DeckForgeTool` class with `_run()` method.
- High value: CrewAI users build multi-agent workflows, presentations are common output.

**Claude Agent SDK (claude-code, computer-use)**
- Example scripts showing MCP server integration with Claude.
- Not a PR — create example in DeckForge repo, reference in docs.

**AutoGen (Microsoft)**
- autogen-ext has tool registry.
- Pattern: Function tool wrapper around DeckForge SDK.

### Integration Template
Each integration needs:
1. Tool class/wrapper (50-100 lines)
2. Example usage (agent generates a deck)
3. README section in DeckForge repo
4. Link back from framework's docs/examples

## 7. Reddit & Twitter/X

### Reddit

**Target Subreddits:**
| Subreddit | Subscribers | Post Type | Allowed? |
|-----------|-------------|-----------|----------|
| r/programming | 6M+ | Show project, technical | Yes (self-promo rules) |
| r/SaaS | 200K+ | Show SaaS, metrics | Yes (Tuesdays) |
| r/artificial | 1M+ | AI tools | Yes |
| r/fintech | 100K+ | Finance tools | Yes |
| r/ExperiencedDevs | 200K+ | Technical discussion | Careful |
| r/webdev | 2M+ | Show project | Yes |
| r/MachineLearning | 3M+ | Research/tools | Technical only |

**Rules**: Each subreddit has self-promotion rules. r/SaaS allows Tuesday self-promo. r/programming requires substantial technical content. Never cross-post identical content.

### Twitter/X

**Developer community patterns:**
- Launch thread format: 15-tweet thread with problem/solution/demo/CTA structure
- Visual content (screenshots, GIFs of deck generation) drives engagement
- Tag: @AnthropicAI, @LangChainAI, @cursor_ai, @OpenAI for reach
- Hashtags: #buildinpublic, #MCP, #AItools, #devtools
- Best posting time: 9-11 AM EST (developer peak)

## 8. Finance Community Outreach

### Target Communities

**Wall Street Oasis (WSO)**
- 3M+ registered users. IB, PE, HCM professionals.
- Post in "Tech Tools" or "Career Advice" forums.
- Angle: "I built an API that generates IC decks, deal one-pagers, and comp tables automatically."
- WSO loves: time savings quantified ("3 hours -> 30 seconds"), Goldman/McKinsey-quality output.

**LinkedIn**
- IB/PE/Consulting professionals are heavy LinkedIn users.
- Post format: Personal story + demo + link.
- Target groups: Investment Banking Analysts, Private Equity Professionals, Management Consulting.
- Engagement hack: Tag 2-3 connections who do presentations daily.

**Blind (finance section)**
- Anonymous professional network. Less formal, more direct.
- Post as tool recommendation, not marketing.

### Finance-Specific Angles
1. "I automated the worst part of IB analyst life" (relatable pain)
2. "AI generates a comp table with proper formatting in 30 seconds" (specific proof)
3. Demo video: prompt -> finished PE deal memo deck (visual proof)

## 9. npm Discoverability

### Current State
```json
"keywords": ["deckforge", "presentation", "slides", "pptx", "sdk"]
```

### Optimized Keywords (high-search-volume)
```json
"keywords": [
  "deckforge", "presentation", "slides", "pptx", "powerpoint",
  "sdk", "api", "ai", "slide-generation", "deck",
  "mcp", "ai-agents", "charts", "finance", "google-slides",
  "typescript", "executive", "pitch-deck", "board-deck"
]
```

### npm Search Ranking Factors
- **Keywords match** (most important)
- **Description quality** (shown in search results)
- **README richness** (shown on package page)
- **Weekly downloads** (social proof + ranking signal)
- **GitHub stars** (shown in npm, linked)
- **Recent publish date** (freshness signal)

### Visibility Milestones
- 100 downloads/week: Appears in search results
- 1,000 downloads/week: "Popular" signal
- 10,000 downloads/week: Category leader

## 10. Demo Content That Sells

### Viral Demo Deck Concepts

| Demo Deck | Why It Works | Target Audience |
|-----------|-------------|-----------------|
| McKinsey-style strategy deck | Gold standard everyone recognizes | Consultants, executives |
| PE deal memo / IC deck | Saves IB analysts 3+ hours | Finance professionals |
| Startup pitch deck | Everyone building startups | Founders, VCs |
| Board update deck | Recurring need, high stakes | CEOs, board members |
| Product launch deck | Common need across industries | Product managers |

### Demo Execution
- Each deck: 8-12 slides, using different themes
- Show the prompt that generated it (transparency)
- Include before/after: "This prompt -> This deck"
- Save as .pptx in `demos/` directory in repo
- Screenshot key slides for social media content
- Host rendered versions on landing page

### "30 Seconds" Content Formula
Content pattern: "AI generates a [impressive thing] in [short time]"
- "AI generates a McKinsey strategy deck in 30 seconds"
- "One API call creates a PE deal memo with comp tables"
- "From prompt to board-ready slides in under a minute"

## Summary: Channel ROI Matrix

| Channel | Effort | Time to Impact | Expected Impact | Priority |
|---------|--------|----------------|-----------------|----------|
| MCP Directory Listings | Low | 1-2 weeks | High (agent discovery) | P0 |
| GitHub README Optimization | Medium | Immediate | High (all visitors) | P0 |
| npm SDK Optimization | Low | 1 week | Medium (developer discovery) | P0 |
| awesome-mcp-servers lists | Low | 1-2 weeks | Medium (curated traffic) | P0 |
| Show HN Post | Medium | 1 day | High (spike traffic) | P1 |
| Dev.to Articles | Medium | 1-2 weeks | Medium (ongoing SEO) | P1 |
| Demo Decks | High | 1 week | High (conversion) | P1 |
| Twitter Launch Thread | Low | 1 day | Medium (initial buzz) | P1 |
| Agent Framework PRs | High | 2-4 weeks | Very High (ecosystem) | P1 |
| Product Hunt Launch | Medium | 1 day | High (spike + badge) | P2 |
| Reddit Posts | Low | 1-3 days | Low-Medium | P2 |
| Finance Community | Medium | 1-2 weeks | Medium (high-value leads) | P2 |
| Comparison Content | Medium | 2-4 weeks | Medium (SEO long-tail) | P2 |
| LinkedIn Posts | Low | 1-3 days | Low-Medium | P2 |
