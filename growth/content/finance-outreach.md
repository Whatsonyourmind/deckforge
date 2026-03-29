# DeckForge Finance Community Outreach Strategy

> Targeting IB/PE professionals -- the highest-value customer segment for DeckForge.
> Finance professionals create 5-15 presentations per week. Average formatting time: 3-5 hours per IC deck.
> Value proposition: 3 hours -> 30 seconds. $200/hour analyst time saved.

---

## Channel Strategy

### 1. Wall Street Oasis (WSO)

**Priority: HIGH** -- Largest finance professional community, informal tone, number-obsessed audience.

**Actions:**
- [x] Write main thread: "Built an API that auto-generates IC decks, comp tables, and deal memos (open source)" -> See `wso-thread.md`
- [ ] Post thread in Technology forum
- [ ] Prepare 3 follow-up comments with screenshots and technical details
- [ ] Monitor and respond to replies for 48 hours post-launch
- [ ] Comment on existing threads about "IB tech tools", "analyst efficiency", "PowerPoint alternatives"
- [ ] Search for and engage with threads mentioning: "formatting decks", "IC presentation", "pitch book"

**Tone guide:** Direct, quantified, no corporate speak. WSO users are allergic to marketing language. Lead with pain points and numbers.

**Key metrics to highlight:**
- 3.5 hours per IC deck (formatting only)
- $700 analyst cost per deck at $200/hr all-in
- 30 seconds to generate a comparable deck via API
- 87/100 average quality score
- 50 free credits/month (no credit card required)

### 2. LinkedIn

**Priority: HIGH** -- Professional audience, strong finance network effect.

**Actions:**
- [x] Write 3 targeted posts -> See `linkedin-posts.md`
- [ ] Post 1 (Personal story): Monday/Tuesday 7:30-8:30 AM ET
- [ ] Post 2 (Demo showcase): Thursday 12:00-1:00 PM ET
- [ ] Post 3 (Thought leadership): Following Monday 7:30-8:30 AM ET
- [ ] Direct message 10-20 IB/PE professionals who engage with finance content
- [ ] Join and post in LinkedIn Groups: "AI in Finance", "Investment Banking Technology", "Private Equity Technology"

**DM template for warm outreach:**

> Hi [Name], saw your post about [topic]. I've been building something that might be relevant -- an API that auto-generates IC decks and comp tables from prompts or structured data. We built 9 finance-specific slide types (comp tables with median highlights, DCF summaries with sensitivity matrices, waterfall bridges). Would love your feedback if you have 5 minutes to check it out: https://deckforge.io

### 3. Blind (Finance Section)

**Priority: MEDIUM** -- Anonymous professional network, very direct/honest feedback.

**Actions:**
- [ ] Post in Finance section: "Anyone used AI tools for deck formatting? Built one that generates IC decks from prompts"
- [ ] Keep anonymous -- focus on the pain point and solution
- [ ] Include specific time savings: "Tracked my deck formatting time for a month. Average 3.2 hours per IC deck. This tool does it in 30 seconds."
- [ ] Link to GitHub (open source credibility) and landing page

**Tone guide:** Ultra-direct. Blind users are cynical about self-promotion. Lead with the problem, be honest about limitations.

### 4. Finance Twitter/X

**Priority: MEDIUM** -- Good for viral reach, finance meme culture.

**Actions:**
- [ ] Tag relevant accounts: @wallstconfidential, @litquidity, @barbaborsa, @TrungTPhan
- [ ] Quote-tweet finance meme accounts when they post about analyst life / formatting decks
- [ ] Thread: "The economics of analyst time waste" with DeckForge as the solution
- [ ] Share demo GIFs (prompt -> rendered deck in 30 seconds)

**Quantitative angles that resonate on FinTwit:**
- "3 hours -> 30 seconds" (time compression)
- "$200/hour analyst time on $0.05/deck API calls" (cost arbitrage)
- "5-pass QA catches what your MD will complain about at 6 AM" (humor)
- "87/100 quality score, higher than most human-made decks" (provocative)

### 5. Reddit Finance Communities

**Priority: MEDIUM** -- Already covered in reddit-posts.md for r/fintech, r/wallstreetbets.

**Additional subreddits for finance outreach:**
- [ ] r/financialcareers -- "Tool I built to save analysts from formatting hell"
- [ ] r/investmentbanking -- "Open source API for generating IC decks"
- [ ] r/FinancialPlanning -- "AI-generated client presentation decks"

### 6. Finance Newsletters & Podcasts

**Priority: LOW** (longer lead time, but high-value)

**Targets:**
- [ ] The Hustle / Trends.co -- pitch as "API for the $4B presentation market"
- [ ] Banking Dive -- pitch as "AI tools reducing analyst busywork"
- [ ] M&A Science podcast -- offer to discuss "how AI is changing deal execution"
- [ ] PE Hub -- pitch as "open-source tool for PE presentation automation"

**Pitch angle:** "Open-source tool built by a finance professional to solve the formatting problem every analyst knows. 9 finance-specific slide types. Free tier."

---

## Demo Video Script

**Title:** "From Prompt to PE Deal Memo in 30 Seconds"

**Duration:** 60 seconds

**Script:**

[0:00-0:05] Screen: Terminal with cursor blinking
Voiceover: "What if your IC deck formatted itself?"

[0:05-0:15] Type the API call:
```
curl -X POST https://api.deckforge.io/v1/generate \
  -H "Authorization: Bearer dk_live_xxx" \
  -d '{"prompt": "PE deal memo for $200M LBO of CloudPay Systems, B2B payments, 8x EBITDA entry, 35% margins", "theme": "finance-professional"}'
```
Voiceover: "One API call. One prompt. That's it."

[0:15-0:25] Show the SSE progress stream:
```
event: intent_parsed
event: outline_generated (12 slides)
event: slides_expanded
event: quality_check (score: 91/100)
event: complete
```
Voiceover: "DeckForge parses intent, generates an outline, expands each slide, runs a 5-pass QA check."

[0:25-0:45] Open the generated PPTX. Slow scroll through slides:
- Title slide with deal name and date
- Transaction overview one-pager
- Company profile with key metrics
- Comp table with 6 companies, EV/EBITDA highlighted
- DCF summary with sensitivity matrix
- Value creation waterfall bridge
- Returns analysis (base/upside/downside)
Voiceover: "12 slides. Comp tables with median highlights. DCF with sensitivity. Waterfall with auto-coloring. All formatted, all consistent."

[0:45-0:55] Show the quality report:
- Quality Score: 91/100
- Contrast: PASS
- Text overflow: PASS
- Data validation: PASS
Voiceover: "Every deck passes a 5-pass quality pipeline. No text overflow. No broken charts. No contrast issues."

[0:55-1:00] End card:
"DeckForge -- Board-ready decks, one API call away"
"https://deckforge.io | Open Source (MIT)"
Voiceover: "Open source. Free tier. Try it at deckforge.io."

---

## Metrics & Tracking

| Channel | Metric | Target (30 days) |
|---------|--------|-------------------|
| WSO Thread | Views | 5,000+ |
| WSO Thread | Comments | 20+ |
| LinkedIn Posts | Total impressions | 10,000+ |
| LinkedIn Posts | Engagement rate | >3% |
| LinkedIn DMs | Response rate | >30% |
| Blind Post | Views | 2,000+ |
| Finance Twitter | Thread impressions | 5,000+ |
| Demo Video | Views | 1,000+ |
| **Total signups from finance channels** | | **50+** |
| **Conversions to Pro** | | **5+** |

## Key Messages (Consistent Across All Channels)

1. **Time savings:** "3 hours -> 30 seconds" (IC deck formatting)
2. **Cost savings:** "$200/hour analyst time saved" ($700/deck at 3.5 hours)
3. **Quality:** "87/100 average quality score, 5-pass QA pipeline"
4. **Finance-specific:** "9 finance slide types built from scratch (comp tables, DCF, waterfall)"
5. **Open source:** "MIT license, free tier, no vendor lock-in"
6. **API-first:** "Built for developers and AI agents, not designers"

## Timeline

| Week | Actions |
|------|---------|
| Week 1 | Post WSO thread, LinkedIn Post 1 (personal story), Blind post |
| Week 2 | LinkedIn Post 2 (demo), LinkedIn Post 3 (thought leadership), Finance Twitter thread |
| Week 3 | Record and publish demo video, LinkedIn DM outreach (10-20 people) |
| Week 4 | Follow up on all channels, pitch 2-3 newsletters, measure results |
