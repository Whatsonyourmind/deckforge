# Wall Street Oasis Thread

## Thread Title

**Built an API that auto-generates IC decks, comp tables, and deal memos (open source)**

## Body

What's up WSO,

Built something I think this community will actually care about. It's called DeckForge -- an API that takes a prompt or structured data and spits out a finished PPTX in under 30 seconds.

**The pain (you already know this)**

Formatting presentations is the #1 time waste for analysts. I'm not talking about the analysis -- that's the valuable part. I'm talking about:

- Spending 45 minutes making a waterfall chart look right because the negative values need different colors and the bridge has to sum correctly
- Fixing comp table alignment for the 4th time because someone added a column and everything shifted
- Reformatting 15 slides at 1 AM because the MD decided to switch from the blue template to the dark one
- Copy-pasting numbers from Excel into PowerPoint text boxes and praying the formatting stays consistent

I tracked it once during a live deal: **3.5 hours on a 12-slide IC deck, just formatting.** The analysis took 2 hours. The formatting took longer than the thinking.

At an all-in analyst cost of $200/hour, that's $700 of value destruction per deck.

**What DeckForge does**

It's not another template library. It's an API.

Input: a prompt like "PE deal memo for $200M LBO of a specialty chemicals company with 8x EBITDA entry, 35% margins, 3 value creation levers" -- or structured data (JSON) if you want exact control.

Output: a .pptx file that opens in PowerPoint with no broken formatting.

**Finance-specific slide types (the stuff that actually matters):**

1. **comp_table** -- EV/EBITDA, EV/Revenue, P/E multiples for N companies. Median row automatically highlighted. Numbers formatted correctly (12.5x, $1.2B, 15.3%). Conditional formatting on outliers.

2. **dcf_summary** -- WACC, terminal value, enterprise value, equity value. Includes sensitivity matrix (WACC vs terminal growth rate) with heat-mapped cells.

3. **waterfall_chart** -- Revenue bridge, EBITDA bridge, value creation bridge. Positive values in green, negative in red, totals in blue. Running subtotals calculated automatically.

4. **deal_overview** -- One-pager with transaction summary, key metrics, sources & uses, and financing structure. The layout adapts to how much data you throw at it.

5. **returns_analysis** -- IRR/MOIC waterfall showing base, upside, downside cases with sensitivity to entry multiple and exit year.

6. **capital_structure** -- Debt/equity stack visualization with tranches, rates, and coverage ratios.

7. **market_landscape** -- TAM/SAM/SOM nested visualization with market sizing data.

8. **investment_thesis** -- Key thesis pillars with supporting evidence and risk factors.

9. **risk_matrix** -- 5x5 impact vs. likelihood heatmap with categorized risks.

Plus 23 universal slide types (title, bullets, charts, tables, comparison, timeline, process, etc.).

**How the layout engine works (it's not templates)**

This is the part that makes it different from "AI slide makers" that just dump text onto premade layouts.

DeckForge uses a constraint-based layout solver. Think of it like CSS flexbox but for slides. Every element has constraints (minimum size, maximum size, margins, alignment rules) and the solver finds the optimal position for everything simultaneously.

So when your comp table has 8 companies instead of 5, it doesn't break -- the engine recalculates column widths, font sizes, and spacing to fit. When your waterfall has 12 steps instead of 6, it adjusts.

Then a 5-pass QA pipeline runs automatically:
1. **Structural check** -- slide count, required elements present
2. **Text overflow** -- no clipped text, font cascading if needed
3. **Visual consistency** -- WCAG contrast ratios, alignment grid
4. **Data validation** -- totals sum correctly, percentages add to 100%
5. **Brand compliance** -- colors match theme, fonts consistent

Average quality score: 87/100.

**What it can't do yet (being honest)**

- No real-time collaboration (it's an API, not Google Slides)
- No custom template import (you pick from 15 curated themes, or use brand kit overlay)
- Chart types are native-editable for basic types (bar, line, pie) but static PNG for complex types (waterfall, sankey, heatmap)
- No PowerPoint-to-IR reverse engineering (yet)

**The numbers**

- 32 slide types (23 universal + 9 finance)
- 24 chart types
- 15 curated themes
- 30-second average render time
- 87/100 average quality score
- Free tier: 50 credits/month (~25 decks)
- Pro: $79/month for 500 credits

**It's open source (MIT license)**

Full codebase on GitHub: https://github.com/Whatsonyourmind/deckforge

TypeScript SDK if you're building tools: `npm install @deckforge/sdk`

Python API if you want to integrate: `pip install deckforge`

Landing page with demos: https://deckforge.io

**Who is this for?**

- IB/PE analysts who are tired of formatting decks at 2 AM
- Finance teams who build the same types of decks repeatedly
- Developers building internal tools for deal teams
- AI agent builders who need presentation generation as a tool

Not for: designers who need pixel-perfect custom layouts, or people who enjoy manual formatting (you exist, I've met you).

Happy to answer questions. Roast it if it sucks, tell me what finance slide types are missing if it doesn't.

---

## Suggested WSO Tags/Category

- **Forum:** Technology
- **Tags:** Investment Banking, Private Equity, Technology, Tools, Presentations
- **Flair:** Resources & Tools

## Follow-up Comment Strategy

**Comment 1 (post immediately after thread):**
"Quick demo: here's what a PE deal memo looks like generated from a single prompt: [screenshot]. The comp table has 8 companies with EV/EBITDA, EV/Revenue, and P/E -- all formatted automatically with median highlight."

**Comment 2 (after first few replies):**
"For the skeptics: the layout engine uses a constraint-based solver (kiwisolver), not templates. This means a comp table with 5 companies and one with 15 companies both look correct -- the engine recalculates column widths, font sizes, and spacing automatically."

**Comment 3 (if someone asks about pricing):**
"Free tier is 50 credits/month. A standard 10-slide deck costs 2 credits to render. So that's ~25 decks/month for free. Pro is $79/month for 500 credits. If you're an AI agent, you can pay per-call in USDC via x402 protocol ($0.05/render)."

## Thread Monitoring Plan

- Check for replies every 4 hours for the first 48 hours
- Respond to every question within 6 hours
- Upvote thoughtful responses
- If thread gains traction, post a follow-up with usage stats after 1 week
- Cross-link to relevant existing WSO threads about "IB tech tools" or "analyst efficiency"
