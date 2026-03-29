# Research: Phase 6 -- Google Slides Output

**Phase:** 06-google-slides-output
**Researched:** 2026-03-26
**Requirements:** GSLIDES-01, GSLIDES-02, GSLIDES-03, GSLIDES-04, GSLIDES-05, GSLIDES-06

## Summary

Phase 6 adds a Google Slides renderer that consumes the same IR + LayoutResult + ResolvedTheme inputs as PptxRenderer but produces a native Google Slides presentation in the user's Google Drive. Charts are backed by temporary Google Sheets spreadsheets with post-creation cleanup.

## 1. Google Slides API -- Core Operations

### presentations.create()

Creates an empty presentation. Returns a `Presentation` resource with `presentationId`.

```python
from googleapiclient.discovery import build

slides_service = build("slides", "v1", credentials=creds)
presentation = slides_service.presentations().create(
    body={"title": "My Deck"}
).execute()
presentation_id = presentation["presentationId"]
```

The new presentation is created in the user's Google Drive root folder. The 16:9 aspect ratio (13.333" x 7.5") is the default -- no configuration needed.

### presentations.batchUpdate()

All mutations go through a single batchUpdate call. Takes a list of `requests` objects. The API processes requests sequentially within a single batch.

```python
slides_service.presentations().batchUpdate(
    presentationId=presentation_id,
    body={"requests": [request1, request2, ...]}
).execute()
```

### Key Request Types

| Request Type | Purpose | Used For |
|-------------|---------|----------|
| CreateSlideRequest | Add blank slide | Every slide |
| CreateShapeRequest | Add shape (rect, textbox) | Text boxes, backgrounds, shapes |
| InsertTextRequest | Insert text into a shape | All text content |
| UpdateTextStyleRequest | Style text (font, size, color, bold) | All text styling |
| UpdateParagraphStyleRequest | Paragraph formatting (alignment, bullets) | Bullet lists, alignment |
| CreateParagraphBulletsRequest | Add bullet/number formatting | Bullet and numbered lists |
| CreateTableRequest | Insert a table | Table slides |
| UpdateTableCellPropertiesRequest | Cell background, borders | Table styling |
| UpdateTableBorderPropertiesRequest | Table border styling | Table formatting |
| CreateImageRequest | Insert image from URL | Image elements |
| CreateSheetsChartRequest | Embed Sheets-backed chart | All chart elements |
| UpdateShapePropertiesRequest | Shape fill, outline, shadow | Backgrounds, callout boxes |
| UpdatePagePropertiesRequest | Slide background color | Slide backgrounds |
| UpdatePageElementTransformRequest | Resize and position elements | All positioning |
| CreateLineRequest | Draw lines/connectors | Dividers |
| DeleteObjectRequest | Remove default placeholders | Clean up blank slides |

## 2. EMU Coordinate System

Google Slides uses English Metric Units (EMU) for all sizing and positioning.

**Conversion factors:**
- 1 inch = 914400 EMU
- 1 point = 12700 EMU
- 1 cm = 360000 EMU

**Slide dimensions (16:9):**
- Width: 13.333" = 12,192,000 EMU
- Height: 7.5" = 6,858,000 EMU

**Mapping from LayoutResult (inches) to Slides API (EMU):**

```python
EMU_PER_INCH = 914400

def inches_to_emu(inches: float) -> int:
    return int(round(inches * EMU_PER_INCH))
```

The LayoutResult.positions dict maps region names to ResolvedPosition(x, y, width, height) in inches. These translate directly:

```python
position = layout_result.positions["title"]
# position.x, position.y, position.width, position.height are all in inches
emu_x = inches_to_emu(position.x)
emu_y = inches_to_emu(position.y)
emu_w = inches_to_emu(position.width)
emu_h = inches_to_emu(position.height)
```

### AffineTransform for Positioning

Elements are positioned via UpdatePageElementTransformRequest using an AffineTransform:

```json
{
    "updatePageElementTransform": {
        "objectId": "element_id",
        "applyMode": "ABSOLUTE",
        "transform": {
            "scaleX": 1,
            "scaleY": 1,
            "translateX": 1828800,
            "translateY": 914400,
            "shearX": 0,
            "shearY": 0,
            "unit": "EMU"
        }
    }
}
```

For CreateShapeRequest, size and position are set via `elementProperties`:

```json
{
    "createShape": {
        "objectId": "shape_id",
        "shapeType": "TEXT_BOX",
        "elementProperties": {
            "pageObjectId": "slide_id",
            "size": {
                "width": {"magnitude": 6096000, "unit": "EMU"},
                "height": {"magnitude": 914400, "unit": "EMU"}
            },
            "transform": {
                "scaleX": 1, "scaleY": 1,
                "translateX": 914400, "translateY": 457200,
                "shearX": 0, "shearY": 0,
                "unit": "EMU"
            }
        }
    }
}
```

## 3. Color/Font Translation from ResolvedTheme

### Colors

ResolvedTheme stores colors as hex strings (e.g., "#0A1E3D"). Google Slides API uses RGB floats (0.0-1.0):

```python
def hex_to_slides_rgb(hex_color: str) -> dict:
    hex_color = hex_color.lstrip("#")
    return {
        "red": int(hex_color[0:2], 16) / 255.0,
        "green": int(hex_color[2:4], 16) / 255.0,
        "blue": int(hex_color[4:6], 16) / 255.0,
    }

# Usage: theme.colors.primary "#0A1E3D" -> {"red": 0.039, "green": 0.118, "blue": 0.239}
```

The color object wrapper for the API:

```python
def make_color(hex_color: str) -> dict:
    return {"opaqueColor": {"rgbColor": hex_to_slides_rgb(hex_color)}}
```

### Fonts

ResolvedTheme has `typography.heading_family` and `typography.body_family`. Google Slides supports Google Fonts natively (no bundling needed -- unlike PPTX where fonts must be installed in Docker). The font is specified as a string in TextStyle:

```json
{
    "updateTextStyle": {
        "objectId": "text_box_id",
        "textRange": {"type": "ALL"},
        "style": {
            "fontFamily": "Montserrat",
            "fontSize": {"magnitude": 28, "unit": "PT"},
            "bold": true,
            "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}}
        },
        "fields": "fontFamily,fontSize,bold,foregroundColor"
    }
}
```

### Font Size Mapping

ResolvedTheme.typography.scale stores sizes as integers (points). Direct mapping:

```python
font_size = theme.typography.scale["h1"]  # 44
# -> {"magnitude": 44, "unit": "PT"}
```

### Font Weight -> Bold

ResolvedTheme.typography.weights stores weights (400=normal, 600/700=bold). Google Slides only supports bold/not-bold:

```python
is_bold = theme.typography.weights.get("heading", 400) >= 600
```

## 4. Sheets-Backed Charts

### Workflow

Google Slides has NO native chart creation API. All charts must be:

1. Create a temporary Google Sheets spreadsheet
2. Write chart data to a sheet (one worksheet per chart)
3. Create an EmbeddedChart in Sheets via Sheets API batchUpdate with AddChartRequest
4. Read back the chartId from the response
5. Use CreateSheetsChartRequest in Slides to embed the chart
6. After all charts are embedded, optionally delete the temporary spreadsheet

### Sheets API -- Create Spreadsheet + Chart

```python
sheets_service = build("sheets", "v4", credentials=creds)

# Create temp spreadsheet
spreadsheet = sheets_service.spreadsheets().create(
    body={"properties": {"title": f"DeckForge Charts - {presentation_id}"}}
).execute()
spreadsheet_id = spreadsheet["spreadsheetId"]

# Write data to first sheet
sheets_service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range="Sheet1!A1",
    valueInputOption="RAW",
    body={"values": [["Q1", "Q2", "Q3", "Q4"], [100, 150, 200, 180]]}
).execute()

# Add chart via batchUpdate
add_chart_request = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "Quarterly Revenue",
                "basicChart": {
                    "chartType": "BAR",
                    "legendPosition": "BOTTOM_LEGEND",
                    "axis": [
                        {"position": "BOTTOM_AXIS", "title": "Quarter"},
                        {"position": "LEFT_AXIS", "title": "Revenue ($M)"}
                    ],
                    "domains": [{
                        "domain": {"sourceRange": {"sources": [{
                            "sheetId": 0,
                            "startRowIndex": 0, "endRowIndex": 1,
                            "startColumnIndex": 0, "endColumnIndex": 4
                        }]}}
                    }],
                    "series": [{
                        "series": {"sourceRange": {"sources": [{
                            "sheetId": 0,
                            "startRowIndex": 1, "endRowIndex": 2,
                            "startColumnIndex": 0, "endColumnIndex": 4
                        }]}},
                        "targetAxis": "LEFT_AXIS"
                    }]
                }
            },
            "position": {"overlayPosition": {"anchorCell": {"sheetId": 0, "rowIndex": 3, "columnIndex": 0}}}
        }
    }
}

result = sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={"requests": [add_chart_request]}
).execute()

chart_id = result["replies"][0]["addChart"]["chart"]["chartId"]
```

### Sheets Chart Types Mapping

Google Sheets `basicChart.chartType` enum:

| Sheets ChartType | DeckForge ChartType |
|-------------------|---------------------|
| BAR | bar, stacked_bar, grouped_bar, horizontal_bar |
| LINE | line, multi_line |
| AREA | area, stacked_area |
| COLUMN | (vertical bars -- use BAR with orientation) |
| SCATTER | scatter, bubble |
| COMBO | combo |
| PIE | pie, donut |
| RADAR | (not available -- use static image fallback) |

For chart types not supported by Sheets (waterfall, funnel, treemap, heatmap, sankey, gantt, football_field, sensitivity, tornado, sunburst, radar), use the existing static Plotly PNG renderer and embed via CreateImageRequest.

### Embed Chart in Slides

```python
{
    "createSheetsChart": {
        "objectId": "chart_element_id",
        "spreadsheetId": spreadsheet_id,
        "chartId": chart_id,
        "linkingMode": "LINKED",
        "elementProperties": {
            "pageObjectId": "slide_id",
            "size": {
                "width": {"magnitude": emu_width, "unit": "EMU"},
                "height": {"magnitude": emu_height, "unit": "EMU"}
            },
            "transform": {
                "scaleX": 1, "scaleY": 1,
                "translateX": emu_x, "translateY": emu_y,
                "shearX": 0, "shearY": 0,
                "unit": "EMU"
            }
        }
    }
}
```

## 5. OAuth 2.0 Flow

### Required Scopes

```python
SCOPES = [
    "https://www.googleapis.com/auth/presentations",  # Create/edit Slides
    "https://www.googleapis.com/auth/spreadsheets",    # Create temp Sheets for charts
    "https://www.googleapis.com/auth/drive.file",      # Manage files created by the app
]
```

`drive.file` is preferred over `drive` (full access) because it limits access to files created by the app.

### Authorization Code Flow (Server-Side)

1. **Redirect user to Google consent:**
   ```
   GET https://accounts.google.com/o/oauth2/v2/auth?
     client_id={GOOGLE_CLIENT_ID}&
     redirect_uri={REDIRECT_URI}&
     response_type=code&
     scope=https://www.googleapis.com/auth/presentations+...&
     access_type=offline&
     state={csrf_token}&
     prompt=consent
   ```

2. **Exchange code for tokens at:**
   ```
   POST https://oauth2.googleapis.com/token
   Body: code={code}&client_id={}&client_secret={}&redirect_uri={}&grant_type=authorization_code
   ```
   Returns: `access_token` (1 hour TTL), `refresh_token` (long-lived), `expires_in`

3. **Refresh when expired:**
   ```
   POST https://oauth2.googleapis.com/token
   Body: refresh_token={}&client_id={}&client_secret={}&grant_type=refresh_token
   ```

### Token Storage

Store encrypted refresh tokens per user in the `api_keys` or a new `google_oauth_tokens` table. Access tokens are short-lived and should be refreshed per-request if within 5 minutes of expiry.

### Configuration

Add to `Settings`:
```python
GOOGLE_CLIENT_ID: str | None = None
GOOGLE_CLIENT_SECRET: str | None = None
GOOGLE_REDIRECT_URI: str = "http://localhost:8000/v1/auth/google/callback"
```

## 6. Rate Limits and Batching Strategy

### Google Slides API Limits

| Operation | Per Project/Min | Per User/Min |
|-----------|-----------------|--------------|
| Read | 3,000 | 600 |
| Write | 600 | 60 |
| Expensive Read (thumbnails) | 300 | 60 |

### Google Sheets API Limits

| Operation | Per Project/Min | Per User/Min |
|-----------|-----------------|--------------|
| Read | 300 | 60 |
| Write | 300 | 60 |

### Batching Strategy

**Critical insight:** Each batchUpdate call counts as ONE write request, regardless of how many individual requests it contains. So the strategy is:

1. **Batch aggressively** -- Build all slide creation, text insertion, and styling requests for the entire presentation, then send as a single batchUpdate call (or a few large batches)
2. **Split into max 2-3 batchUpdate calls per presentation:**
   - Batch 1: Create all slides + shapes + tables + text
   - Batch 2: Style all text + shape properties + slide backgrounds
   - Batch 3: Add all Sheets-backed charts (after temp spreadsheet is ready)
3. **For Sheets chart creation,** batch all AddChartRequest calls into a single Sheets batchUpdate
4. **Rate limit compliance:** At 60 writes/user/min, a presentation with 3 Slides batches + 2 Sheets batches = 5 write calls. Well within limits even for rapid sequential renders.

### Retry Strategy

```python
import time
from googleapiclient.errors import HttpError

def batch_update_with_retry(service, presentation_id, requests, max_retries=3):
    for attempt in range(max_retries):
        try:
            return service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests}
            ).execute()
        except HttpError as e:
            if e.resp.status == 429:
                wait = 2 ** attempt
                time.sleep(wait)
                continue
            raise
```

## 7. Cleanup of Temporary Spreadsheets

### Strategy

After all charts are embedded in Slides:
1. Use Drive API to delete the temp spreadsheet: `drive_service.files().delete(fileId=spreadsheet_id).execute()`
2. If deletion fails (permission error, network), log and schedule for background cleanup
3. Background cleanup cron: query Drive for files matching name pattern `DeckForge Charts - *` older than 1 hour

### Cleanup Safety

- Only delete spreadsheets created by the app (matched by name pattern + metadata)
- Charts embedded with `linkingMode: "LINKED"` become read-only if the source spreadsheet is deleted -- they retain a snapshot but cannot be refreshed. This is acceptable since we create the chart at render time with final data.
- Consider using `linkingMode: "NOT_LINKED_IMAGE"` to avoid any dependency on the temp spreadsheet post-creation. Tradeoff: chart becomes a static image in Slides (not editable).

**Recommendation:** Use `LINKED` mode to preserve editability (requirement GSLIDES-02: "editable charts"), but document that deleting the temp spreadsheet freezes the chart data. Users who need to edit chart data can re-render.

## 8. Architecture Alignment

### Renderer Interface

The GoogleSlidesRenderer mirrors PptxRenderer's interface:

```python
class GoogleSlidesRenderer:
    def render(
        self,
        presentation: Presentation,       # IR model
        layout_results: list[LayoutResult], # Positioned elements in inches
        theme: ResolvedTheme,              # Resolved colors/fonts/spacing
        credentials: Credentials,          # Google OAuth credentials
    ) -> GoogleSlidesResult:
        """Render to Google Slides. Returns presentation URL and ID."""
```

The only addition vs PptxRenderer is `credentials` (Google OAuth) and the return type (URL instead of bytes).

### Integration with render_pipeline

Extend `render_pipeline()` in workers/tasks.py to accept an `output_format` parameter:

```python
def render_pipeline(presentation: Presentation, output_format: str = "pptx", credentials=None):
    # ... layout + theme resolution (shared) ...
    if output_format == "gslides":
        renderer = GoogleSlidesRenderer()
        return renderer.render(presentation, layout_results, theme, credentials)
    else:
        renderer = PptxRenderer()
        return renderer.render(presentation, layout_results, theme)
```

### API Endpoint Extension

The existing `/v1/render` endpoint gets an optional `output_format` query parameter (default: "pptx"). When "gslides", the response is JSON with `presentation_url` and `presentation_id` instead of a PPTX file stream.

## 9. Python Client Library

```
google-api-python-client>=2.150.0
google-auth>=2.35.0
google-auth-oauthlib>=1.2.1
```

These are mature, well-maintained libraries. `google-api-python-client` provides the `build()` function for service discovery. `google-auth` handles credential management. `google-auth-oauthlib` bridges OAuth flows.

## 10. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sheets chart creation adds latency (3-5s per chart) | Medium | Batch all charts into single Sheets batchUpdate |
| OAuth token expiry mid-render | High | Refresh token before render starts if < 5min remaining |
| Orphaned temp spreadsheets | Low | Background cleanup job + name pattern matching |
| Rate limit hit for large decks | Low | Single batchUpdate per batch = 1 write call. 60/min is plenty |
| Radar/funnel/treemap not in Sheets | Medium | Fall back to static PNG via existing Plotly renderers |
| User revokes OAuth access | Medium | Graceful error with re-auth prompt |

## Sources

- [Google Slides API Reference](https://developers.google.com/slides/api/reference/rest)
- [Google Slides batchUpdate](https://developers.google.com/slides/api/reference/rest/v1/presentations/batchUpdate)
- [Google Slides Rate Limits](https://developers.google.com/slides/api/limits)
- [Google Sheets EmbeddedChart](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#EmbeddedChart)
- [Google OAuth 2.0 Web Server](https://developers.google.com/identity/protocols/oauth2/web-server)
- [DeckForge PITFALLS.md -- Pitfall 4](../../research/PITFALLS.md)
- [DeckForge PITFALLS.md -- Pitfall 14](../../research/PITFALLS.md)
