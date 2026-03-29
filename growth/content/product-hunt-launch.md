# Product Hunt Launch Kit: DeckForge

## Launch Details

- **Launch Date:** Tuesday (highest traffic day per PH analytics)
- **Launch Time:** 12:01 AM PT (full 24-hour voting window)
- **Hunter:** Self-launch (maker launch)
- **Product URL:** https://deckforge.dev
- **GitHub:** https://github.com/Whatsonyourmind/deckforge

---

## Tagline (60 characters max)

**Executive-ready slides via API. For AI agents & devs.**

(54 characters)

---

## Description (260 characters max)

**Generate professional presentations with one API call. 32 slide types, 15 themes, 24 chart types, finance vertical. MCP server for AI agents. TypeScript SDK. x402 machine payments. Open source.**

(199 characters)

---

## Topics

1. Developer Tools
2. Artificial Intelligence
3. Productivity
4. APIs
5. Open Source

---

## First Comment (Maker Comment)

Hi Product Hunt! I'm the maker of DeckForge.

**Why I built this:** I spent years in financial services watching analysts burn 3-5 hours formatting a single investment committee deck. The content was always ready in 30 minutes -- the remaining hours were spent fighting PowerPoint alignment, fixing text overflow, making charts consistent, and applying brand guidelines.

When AI agents started generating content, I thought the problem was solved. It wasn't. LLMs produce great text, but their slide output is either ugly (raw python-pptx), static (screenshots), or useless for boardrooms (markdown). AI agents are fluent in language but illiterate in visual layout.

**What DeckForge does:** You send structured JSON (an Intermediate Representation describing slide content), and you get back a professionally formatted PowerPoint file. One API call.

**What makes it different:**

- **Constraint-based layout** (not templates) -- kiwisolver adapts layout to content volume. 3 bullets and 15 bullets both look correct.
- **5-pass QA pipeline** -- text overflow detection, WCAG contrast checking, data validation, auto-fix. Every deck scores 0-100.
- **Finance vertical** -- 9 specialized slide types for IC memos, comp tables, DCF summaries, deal overviews. Built for institutional investors who expect Goldman-quality output.
- **MCP server** -- AI agents discover and use DeckForge through the Model Context Protocol. Claude Desktop, Cursor, any MCP client.
- **x402 machine payments** -- AI agents pay per-call in USDC. $0.05 per render. No subscription required.

**Honest limitations:**
- No animation or video support yet
- Google Slides output is functional but less polished than PPTX
- NL-to-slides generation requires your own LLM API key
- Not a SaaS editor -- it produces files, not a collaborative workspace

**What's free:** Starter tier gives you 50 free credits per month. Enough to render 50 presentations. No credit card required.

Try it: `pip install deckforge` or `npm install @deckforge/sdk`

GitHub: https://github.com/Whatsonyourmind/deckforge

I'd love your feedback on the output quality. The demo decks in the repo (McKinsey strategy deck, PE deal memo, startup pitch, board update, product launch) show what DeckForge produces at its best. Happy to answer any questions!

---

## Gallery Images (5 required)

### Image 1: Hero
**Spec:** 1270x760px (PH recommended)
**Content:** DeckForge logo + tagline "Executive-ready slides, one API call away" + 5-line TypeScript code snippet (the SDK quick start) + subtle dark gradient background
**Purpose:** Immediate value proposition + developer credibility

### Image 2: Demo - McKinsey Strategy Deck
**Spec:** 1270x760px
**Content:** 4-slide grid showing title slide, bar chart (revenue trends), comparison (digital vs traditional), and KPI table from the McKinsey strategy demo deck. Corporate-blue theme.
**Purpose:** Visual proof of output quality

### Image 3: SDK - TypeScript Builder API
**Spec:** 1270x760px
**Content:** VS Code screenshot showing the fluent builder API with IntelliSense dropdown displaying all 32 slide types. Code shows Presentation.create().addSlide(Slide.comp_table({...})).build() pattern.
**Purpose:** Developer experience proof point

### Image 4: Finance - PE Deal Memo
**Spec:** 1270x760px
**Content:** 4-slide grid showing comp table (with median highlight), DCF sensitivity matrix, returns analysis (IRR/MOIC scenarios), and capital structure from the PE deal memo demo. Finance-pro theme.
**Purpose:** Finance vertical differentiation

### Image 5: Architecture - 6-Layer Pipeline
**Spec:** 1270x760px
**Content:** Clean diagram showing: Input (JSON IR) -> Validation -> Layout (kiwisolver) -> Theme -> Rendering -> QA -> Output (PPTX). Each layer has an icon and 1-line description. Numbers below: 32 slide types, 15 themes, 24 chart types, 5-pass QA.
**Purpose:** Technical credibility + architecture overview

---

## Launch Day Schedule

| Time (EST) | Action | Channel |
|------------|--------|---------|
| 3:01 AM | Product Hunt goes live (12:01 AM PT) | Product Hunt |
| 3:05 AM | Post maker comment | Product Hunt |
| 8:00 AM | Email supporters "We're live on Product Hunt" | Email list |
| 9:00 AM | Post Twitter/X launch thread (15 tweets) | Twitter/X |
| 9:30 AM | Share PH link on LinkedIn with personal story | LinkedIn |
| 10:00 AM | Post to r/programming | Reddit |
| 10:30 AM | Post to r/SaaS (self-promo Tuesday) | Reddit |
| 11:00 AM | Post to r/artificial | Reddit |
| 12:00 PM | Submit Show HN | Hacker News |
| 12:05 PM | Post HN maker comment | Hacker News |
| 1:00 PM | Cross-post PH link to relevant Discord servers | Discord |
| 2:00 PM | Publish Dev.to Article 1 (architecture) | Dev.to |
| 3:00 PM | Respond to all PH comments | Product Hunt |
| 4:00 PM | Publish Dev.to Article 2 (agents + API) | Dev.to |
| 5:00 PM | Post to r/fintech | Reddit |
| 6:00 PM | Final PH comment engagement pass | Product Hunt |
| 9:00 PM | Share daily results on Twitter | Twitter/X |

---

## Call to Action

**Primary CTA:** "Get your free API key" -> links to deckforge.dev/signup
**Secondary CTA:** "Star on GitHub" -> links to GitHub repo
**Tertiary CTA:** "Try the demo decks" -> links to demos/ directory

---

## Outreach List (ask for upvotes -- 50 people)

1. Personal contacts who build with APIs (15-20 people)
2. Finance industry contacts who feel the deck formatting pain (10-15)
3. Developer friends on Twitter/X (10-15)
4. MCP community members from Discord servers (5-10)

**Message template:**
"Hey [name]! I just launched DeckForge on Product Hunt -- it's an API that generates executive-ready slides for AI agents. Would mean a lot if you could check it out and upvote if you find it interesting: [PH link]. No pressure at all -- just trying to get the word out. Thanks!"

---

## Success Metrics

| Metric | Target | Stretch Goal |
|--------|--------|-------------|
| PH Upvotes | 200+ | 500+ |
| PH Rank (daily) | Top 10 | Top 3 |
| GitHub Stars (launch day) | 100+ | 500+ |
| npm installs (launch week) | 50+ | 200+ |
| Signups (launch day) | 25+ | 100+ |
| HN front page | Yes | Top 10 |
| Dev.to views (first week) | 2,000+ | 10,000+ |
