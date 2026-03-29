"""GoogleSlidesRenderer -- orchestrates rendering of a complete Google Slides presentation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from deckforge.rendering.gslides.charts import SheetsChartBuilder
from deckforge.rendering.gslides.cleanup import cleanup_temp_spreadsheets
from deckforge.rendering.gslides.converter import generate_object_id
from deckforge.rendering.gslides.finance_builders import FINANCE_SLIDE_TYPES
from deckforge.rendering.gslides.request_builder import SlideRequestBuilder

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)


@dataclass
class GoogleSlidesResult:
    """Result of rendering a Google Slides presentation."""

    presentation_id: str
    presentation_url: str  # https://docs.google.com/presentation/d/{id}/edit
    title: str
    slide_count: int


class GoogleSlidesRenderer:
    """Renders a complete Google Slides presentation from IR + layout + theme.

    Parallels PptxRenderer but targets the Google Slides API JSON format.
    Creates a presentation, builds all slides via batchUpdate requests.
    """

    # Max requests per batchUpdate call (Google soft limit)
    MAX_BATCH_SIZE = 500

    def render(
        self,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
        credentials: Any = None,
    ) -> GoogleSlidesResult:
        """Render a complete Google Slides presentation.

        Args:
            presentation: The IR Presentation model.
            layout_results: List of LayoutResults from the layout engine.
            theme: Resolved theme for styling.
            credentials: Google OAuth credentials for API access.

        Returns:
            GoogleSlidesResult with presentation URL and metadata.

        Raises:
            RuntimeError: If Google API client is not available.
        """
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
        except ImportError as e:
            raise RuntimeError(
                "google-api-python-client is required for Google Slides rendering. "
                "Install with: pip install 'deckforge[gslides]'"
            ) from e

        # 1. Build Slides API service
        service = build("slides", "v1", credentials=credentials)

        # 2. Create presentation
        title = "DeckForge Presentation"
        if hasattr(presentation, "metadata") and presentation.metadata:
            title = getattr(presentation.metadata, "title", title) or title

        pres_body = {"title": title}
        pres_response = service.presentations().create(body=pres_body).execute()
        presentation_id = pres_response["presentationId"]

        # 3. Delete the default blank slide
        default_slides = pres_response.get("slides", [])
        delete_requests: list[dict] = []
        for ds in default_slides:
            delete_requests.append({"deleteObject": {"objectId": ds["objectId"]}})

        if delete_requests:
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": delete_requests},
            ).execute()

        # 4. Check if any chart elements exist and create SheetsChartBuilder
        has_charts = self._has_chart_elements(layout_results)
        charts_builder: SheetsChartBuilder | None = None
        if has_charts and credentials is not None:
            try:
                charts_builder = SheetsChartBuilder(credentials, presentation_id)
                charts_builder.create_spreadsheet()
            except Exception:
                logger.warning(
                    "Failed to create Sheets chart builder, charts will use placeholders"
                )
                charts_builder = None

        # 5. Build all requests
        all_requests: list[dict] = []
        chart_requests: list[dict] = []  # Charts must be sent after slides exist

        for idx, layout_result in enumerate(layout_results):
            ir_slide = layout_result.slide
            page_id = generate_object_id()
            builder = SlideRequestBuilder(f"slide_{idx}", page_id)

            # Create slide
            all_requests.append(builder.build_create_slide(idx))

            # Set background
            slide_type = ir_slide.slide_type
            if hasattr(slide_type, "value"):
                slide_type = slide_type.value

            master = theme.slide_masters.get(slide_type)
            bg_color = master.background if master else theme.colors.background
            all_requests.append(builder.build_background(bg_color))

            # Finance slides get full-slide rendering
            if slide_type in FINANCE_SLIDE_TYPES:
                finance_reqs = builder.dispatch_finance_slide(ir_slide, theme)
                all_requests.extend(finance_reqs)
            else:
                # Element-by-element rendering
                for element in ir_slide.elements:
                    position = element.position
                    if position is None:
                        continue

                    element_type = element.type
                    if hasattr(element_type, "value"):
                        element_type = element_type.value
                    if element_type == "background":
                        continue

                    try:
                        elem_reqs = builder.dispatch_element(
                            element, position, theme, charts_builder
                        )
                        # Separate chart requests (CreateSheetsChart)
                        for req in elem_reqs:
                            if "createSheetsChart" in req:
                                chart_requests.append(req)
                            else:
                                all_requests.append(req)
                    except Exception:
                        logger.exception(
                            "Failed to build requests for element type=%s",
                            getattr(element, "type", "unknown"),
                        )

            # Speaker notes
            notes = getattr(ir_slide, "speaker_notes", None)
            if notes:
                all_requests.extend(builder.build_speaker_notes(notes))

        # 6. Send main requests (slides + shapes + text + tables + images)
        self._send_batch_requests(service, presentation_id, all_requests, HttpError)

        # 7. Send chart requests (CreateSheetsChart -- slides must exist first)
        if chart_requests:
            self._send_batch_requests(
                service, presentation_id, chart_requests, HttpError
            )

        # 8. Cleanup temp spreadsheets
        if charts_builder and charts_builder.spreadsheet_id:
            try:
                from googleapiclient.discovery import build as build_svc

                drive_svc = build_svc("drive", "v3", credentials=credentials)
                cleanup_temp_spreadsheets(
                    drive_svc, [charts_builder.spreadsheet_id]
                )
            except Exception:
                logger.warning(
                    "Failed to clean up temp spreadsheet %s",
                    charts_builder.spreadsheet_id,
                )

        # 9. Return result
        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"

        return GoogleSlidesResult(
            presentation_id=presentation_id,
            presentation_url=presentation_url,
            title=title,
            slide_count=len(layout_results),
        )

    @staticmethod
    def _has_chart_elements(layout_results: list[LayoutResult]) -> bool:
        """Check if any layout result contains chart elements."""
        for lr in layout_results:
            for element in lr.slide.elements:
                etype = element.type
                if hasattr(etype, "value"):
                    etype = etype.value
                if etype == "chart":
                    return True
        return False

    def _send_batch_requests(
        self,
        service: Any,
        presentation_id: str,
        requests: list[dict],
        http_error_class: type,
    ) -> None:
        """Send requests in batches, with retry for rate limits.

        Args:
            service: Google Slides API service.
            presentation_id: Presentation ID.
            requests: All request dicts to send.
            http_error_class: HttpError class for error handling.
        """
        import time

        batch_size = self.MAX_BATCH_SIZE

        for i in range(0, len(requests), batch_size):
            batch = requests[i : i + batch_size]
            retries = 0
            max_retries = 3

            while retries <= max_retries:
                try:
                    service.presentations().batchUpdate(
                        presentationId=presentation_id,
                        body={"requests": batch},
                    ).execute()
                    break
                except http_error_class as e:
                    if hasattr(e, "resp") and e.resp.status == 429 and retries < max_retries:
                        delay = 2 ** retries
                        logger.warning(
                            "Rate limited on batch %d, retrying in %ds", i, delay
                        )
                        time.sleep(delay)
                        retries += 1
                    else:
                        raise


__all__ = ["GoogleSlidesRenderer", "GoogleSlidesResult"]
