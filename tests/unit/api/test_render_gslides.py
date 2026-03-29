"""Tests for Google Slides render endpoint and OAuth integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deckforge.api.schemas.responses import GoogleSlidesRenderResponse
from deckforge.rendering.gslides.slides_renderer import GoogleSlidesResult


class TestGoogleSlidesRenderResponse:
    """Test the response schema."""

    def test_schema_fields(self):
        resp = GoogleSlidesRenderResponse(
            id="deck-123",
            status="complete",
            presentation_id="pres_abc",
            presentation_url="https://docs.google.com/presentation/d/pres_abc/edit",
            title="Test Deck",
            slide_count=5,
        )
        assert resp.presentation_id == "pres_abc"
        assert resp.presentation_url.startswith("https://docs.google.com")
        assert resp.slide_count == 5


class TestGoogleSlidesResult:
    """Test the GoogleSlidesResult dataclass."""

    def test_result_fields(self):
        result = GoogleSlidesResult(
            presentation_id="pres_abc",
            presentation_url="https://docs.google.com/presentation/d/pres_abc/edit",
            title="Test Deck",
            slide_count=3,
        )
        assert result.presentation_id == "pres_abc"
        assert result.slide_count == 3


class TestRenderPipelineOutputFormat:
    """Test that render_pipeline dispatches correctly based on output_format."""

    @patch("deckforge.workers.tasks.QAPipeline")
    @patch("deckforge.workers.tasks.PptxRenderer")
    @patch("deckforge.workers.tasks.LayoutEngine")
    @patch("deckforge.workers.tasks.ThemeRegistry")
    @patch("deckforge.workers.tasks.TextMeasurer")
    def test_pptx_default(self, mock_tm, mock_tr, mock_le, mock_pptx, mock_qa):
        """Default output_format should use PptxRenderer."""
        from deckforge.workers.tasks import render_pipeline

        # Setup mocks
        mock_tr_instance = MagicMock()
        mock_tr.return_value = mock_tr_instance
        mock_le_instance = MagicMock()
        mock_le.return_value = mock_le_instance
        mock_le_instance.layout_presentation.return_value = []
        mock_tr_instance.get_theme.return_value = MagicMock()
        mock_pptx_instance = MagicMock()
        mock_pptx.return_value = mock_pptx_instance
        mock_pptx_instance.render.return_value = b"pptx_bytes"
        mock_qa_instance = MagicMock()
        mock_qa.return_value = mock_qa_instance
        mock_qa_instance.run.return_value = MagicMock(quality_score=90, issues=[], fixes=[])

        presentation = MagicMock()
        result, qa_report = render_pipeline(presentation)
        assert result == b"pptx_bytes"
        mock_pptx_instance.render.assert_called_once()

    @patch("deckforge.workers.tasks.QAPipeline")
    @patch("deckforge.rendering.gslides.GoogleSlidesRenderer")
    @patch("deckforge.workers.tasks.LayoutEngine")
    @patch("deckforge.workers.tasks.ThemeRegistry")
    @patch("deckforge.workers.tasks.TextMeasurer")
    def test_gslides_format(self, mock_tm, mock_tr, mock_le, mock_gsr, mock_qa):
        """output_format='gslides' should use GoogleSlidesRenderer."""
        from deckforge.workers.tasks import render_pipeline

        # Setup mocks
        mock_tr_instance = MagicMock()
        mock_tr.return_value = mock_tr_instance
        mock_le_instance = MagicMock()
        mock_le.return_value = mock_le_instance
        mock_le_instance.layout_presentation.return_value = []
        mock_tr_instance.get_theme.return_value = MagicMock()
        mock_qa_instance = MagicMock()
        mock_qa.return_value = mock_qa_instance
        mock_qa_instance.run.return_value = MagicMock(quality_score=90, issues=[], fixes=[])

        mock_gsr_instance = MagicMock()
        mock_gsr.return_value = mock_gsr_instance
        mock_gsr_instance.render.return_value = GoogleSlidesResult(
            presentation_id="pres_abc",
            presentation_url="https://docs.google.com/presentation/d/pres_abc/edit",
            title="Test",
            slide_count=1,
        )

        presentation = MagicMock()
        credentials = MagicMock()
        result, qa_report = render_pipeline(presentation, output_format="gslides", credentials=credentials)

        assert isinstance(result, GoogleSlidesResult)
        assert result.presentation_id == "pres_abc"


class TestOAuthHandler:
    """Test OAuth handler functionality."""

    def test_authorization_url_generation(self):
        from deckforge.rendering.gslides.oauth import GoogleOAuthHandler

        handler = GoogleOAuthHandler(
            client_id="test_client_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/v1/auth/google/callback",
        )

        url = handler.get_authorization_url(state="test_state")
        assert "accounts.google.com" in url
        assert "test_client_id" in url
        assert "test_state" in url
        assert "presentations" in url
        assert "offline" in url

    def test_authorization_url_scopes(self):
        from deckforge.rendering.gslides.oauth import GoogleOAuthHandler

        handler = GoogleOAuthHandler(
            client_id="test_client_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        url = handler.get_authorization_url()
        assert "presentations" in url
        assert "spreadsheets" in url
        assert "drive.file" in url


class TestConfigGoogleSettings:
    """Test that Google OAuth config settings exist."""

    def test_settings_have_google_fields(self):
        from deckforge.config import Settings

        s = Settings()
        assert hasattr(s, "GOOGLE_CLIENT_ID")
        assert hasattr(s, "GOOGLE_CLIENT_SECRET")
        assert hasattr(s, "GOOGLE_REDIRECT_URI")
        assert s.GOOGLE_CLIENT_ID is None
        assert s.GOOGLE_CLIENT_SECRET is None
        assert "callback" in s.GOOGLE_REDIRECT_URI


class TestCleanupService:
    """Test cleanup service integration."""

    def test_cleanup_import(self):
        from deckforge.rendering.gslides.cleanup import cleanup_temp_spreadsheets

        assert callable(cleanup_temp_spreadsheets)

    def test_charts_import(self):
        from deckforge.rendering.gslides.charts import SheetsChartBuilder

        assert SheetsChartBuilder is not None
