# GitHub Social Preview Image Specification

## Image Requirements

- **Dimensions:** 1280 x 640 pixels (2:1 ratio, GitHub recommended)
- **Format:** PNG
- **File size:** Under 1MB
- **Upload location:** GitHub repo Settings > General > Social preview

## Design Specification

### Background
- Color: Dark navy (#0A1E3D) matching DeckForge brand
- Style: Clean, professional, minimal noise

### Title
- Text: "DeckForge"
- Font: Bold, large (approx 72-96pt equivalent)
- Color: White (#FFFFFF)
- Position: Upper-center area

### Subtitle
- Text: "Executive-Ready Slides, One API Call"
- Font: Regular, medium (approx 28-36pt equivalent)
- Color: Light gray (#B0C4DE) or brand accent
- Position: Below title, centered

### Key Stats Badges
- Layout: Horizontal row of 4 badges, centered
- Badges:
  1. "32 Slide Types"
  2. "15 Themes"
  3. "24 Chart Types"
  4. "9 Finance Types"
- Style: Rounded rectangles with semi-transparent background (#1A3A5C)
- Text color: White
- Font: 16-20pt equivalent

### Code Snippet
- Text: `Presentation.create().addSlide().render()`
- Font: Monospace (Fira Code, JetBrains Mono, or similar)
- Color: Cyan/teal accent (#00D4AA) on dark background
- Style: Code block appearance with slight background
- Position: Center, below badges

### Bottom Bar
- Left: "For AI Agents & Developers"
- Right: "github.com/Whatsonyourmind/deckforge"
- Font: Small (14-16pt)
- Color: Medium gray (#8899AA)

## Color Palette

| Element | Color | Hex |
|---------|-------|-----|
| Background | Dark Navy | #0A1E3D |
| Title | White | #FFFFFF |
| Subtitle | Light Steel Blue | #B0C4DE |
| Badge BG | Navy Accent | #1A3A5C |
| Code Text | Teal Accent | #00D4AA |
| Footer | Medium Gray | #8899AA |

## Creation Options

1. **Figma/Canva:** Create using the specs above
2. **AI Generation:** Use DALL-E/Midjourney with this prompt:
   "Professional dark navy tech product banner, 1280x640, showing 'DeckForge' title, subtitle 'Executive-Ready Slides, One API Call', stats badges, monospace code snippet, clean minimal design, no stock photos"
3. **HTML/CSS:** Render with Puppeteer/Playwright and screenshot

## Upload Instructions

1. Go to https://github.com/Whatsonyourmind/deckforge/settings
2. Scroll to "Social preview" section
3. Click "Edit" > "Upload an image"
4. Select the 1280x640 PNG file
5. Click "Save changes"
6. Verify by sharing the repo URL -- the preview should appear in link previews

## GitHub Topics

Set the following topics on the repository (Settings > General > Topics):

```
mcp-server, mcp, presentations, slides, pptx, powerpoint, ai-agents, typescript-sdk, python, fastapi, finance, charts, ai, api, machine-payments
```

**Total: 15 topics** (GitHub allows max 20)

These cover:
- MCP ecosystem discovery: mcp-server, mcp
- Core functionality: presentations, slides, pptx, powerpoint
- AI/agent ecosystem: ai-agents, ai, machine-payments
- Technology: typescript-sdk, python, fastapi
- Vertical: finance, charts
- General: api

## GitHub Discussions Setup

Enable Discussions at: Settings > Features > Discussions

Create these categories:
1. **General** -- Announcements and community discussion
2. **Q&A** -- Support questions (mark answers)
3. **Ideas** -- Feature requests and suggestions
4. **Show and Tell** -- User-built integrations and showcases
