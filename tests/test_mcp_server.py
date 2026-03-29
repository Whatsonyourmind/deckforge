"""Tests for the DeckForge MCP server and tools.

Validates that all 6 MCP tools are registered, discoverable, and return
expected data structures. Uses mocks for render/content pipelines.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deckforge.mcp.server import mcp
from deckforge.mcp.tools import (
    estimate_cost,
    get_pricing,
    list_slide_types,
    list_themes,
)


# ---------------------------------------------------------------------------
# Tool registration tests
# ---------------------------------------------------------------------------


class TestMCPToolRegistration:
    """Verify all 6 tools are registered on the MCP server."""

    def test_server_has_correct_name(self):
        assert mcp.name == "DeckForge"

    def test_all_six_tools_registered(self):
        tools = mcp._tool_manager._tools
        assert len(tools) == 6, f"Expected 6 tools, got {len(tools)}: {list(tools.keys())}"

    def test_tool_names(self):
        tools = mcp._tool_manager._tools
        expected = {"render", "generate", "themes", "slide_types", "cost_estimate", "pricing"}
        assert set(tools.keys()) == expected

    def test_tools_have_descriptions(self):
        """Each tool should have a non-empty description for agent discovery."""
        tools = mcp._tool_manager._tools
        for name, tool in tools.items():
            assert tool.description, f"Tool '{name}' has no description"
            assert len(tool.description) > 20, (
                f"Tool '{name}' description too short: {tool.description}"
            )


# ---------------------------------------------------------------------------
# list_themes tool
# ---------------------------------------------------------------------------


class TestListThemes:
    """Test the list_themes tool returns theme catalog."""

    @pytest.mark.asyncio
    async def test_returns_non_empty_list(self):
        result = await list_themes()
        assert isinstance(result, list)
        assert len(result) > 0, "Should return at least one theme"

    @pytest.mark.asyncio
    async def test_theme_has_expected_keys(self):
        result = await list_themes()
        theme = result[0]
        assert "id" in theme
        assert "name" in theme
        assert "description" in theme

    @pytest.mark.asyncio
    async def test_returns_15_themes(self):
        result = await list_themes()
        assert len(result) == 15, f"Expected 15 themes, got {len(result)}"


# ---------------------------------------------------------------------------
# list_slide_types tool
# ---------------------------------------------------------------------------


class TestListSlideTypes:
    """Test the list_slide_types tool returns slide type catalog."""

    @pytest.mark.asyncio
    async def test_returns_32_types(self):
        result = await list_slide_types()
        assert len(result) == 32, f"Expected 32 slide types, got {len(result)}"

    @pytest.mark.asyncio
    async def test_slide_type_has_expected_keys(self):
        result = await list_slide_types()
        st = result[0]
        for key in ("id", "name", "description", "category", "required_elements"):
            assert key in st, f"Missing key '{key}' in slide type"

    @pytest.mark.asyncio
    async def test_filter_by_category(self):
        universal = await list_slide_types(category="universal")
        finance = await list_slide_types(category="finance")
        assert len(universal) == 23, f"Expected 23 universal, got {len(universal)}"
        assert len(finance) == 9, f"Expected 9 finance, got {len(finance)}"

    @pytest.mark.asyncio
    async def test_all_categories_covered(self):
        result = await list_slide_types()
        categories = {st["category"] for st in result}
        assert "universal" in categories
        assert "finance" in categories


# ---------------------------------------------------------------------------
# get_pricing tool
# ---------------------------------------------------------------------------


class TestGetPricing:
    """Test the get_pricing tool returns tier and x402 pricing."""

    @pytest.mark.asyncio
    async def test_returns_tiers_and_x402(self):
        result = await get_pricing()
        assert "tiers" in result
        assert "x402" in result

    @pytest.mark.asyncio
    async def test_three_tiers(self):
        result = await get_pricing()
        assert len(result["tiers"]) == 3

    @pytest.mark.asyncio
    async def test_tier_has_expected_fields(self):
        result = await get_pricing()
        tier = result["tiers"][0]
        for key in ("name", "display_name", "credit_limit", "price_usd", "rate_limit_rpm"):
            assert key in tier, f"Missing key '{key}' in tier"

    @pytest.mark.asyncio
    async def test_x402_pricing_fields(self):
        result = await get_pricing()
        x402 = result["x402"]
        assert x402["currency"] == "USD"
        assert x402["protocol"] == "x402"
        assert "render_per_call_usd" in x402
        assert "generate_per_call_usd" in x402

    @pytest.mark.asyncio
    async def test_starter_tier_is_free(self):
        result = await get_pricing()
        starter = next(t for t in result["tiers"] if t["name"] == "starter")
        assert starter["price_usd"] == 0

    @pytest.mark.asyncio
    async def test_pro_tier_price(self):
        result = await get_pricing()
        pro = next(t for t in result["tiers"] if t["name"] == "pro")
        assert pro["price_usd"] == 79.0


# ---------------------------------------------------------------------------
# estimate_cost tool
# ---------------------------------------------------------------------------


class TestEstimateCost:
    """Test the estimate_cost tool with various IR inputs."""

    @pytest.mark.asyncio
    async def test_minimal_ir(self):
        ir = {
            "schema_version": "1.0",
            "metadata": {"title": "Test", "language": "en"},
            "theme": "corporate-blue",
            "slides": [
                {"slide_type": "title_slide", "elements": []}
            ],
        }
        result = await estimate_cost(json.dumps(ir))
        assert result["total_credits"] >= 1
        assert result["base_credits"] >= 1
        assert "x402_usd" in result
        assert result["x402_usd"] >= 0

    @pytest.mark.asyncio
    async def test_finance_slide_surcharge(self):
        ir = {
            "schema_version": "1.0",
            "metadata": {"title": "Test", "language": "en"},
            "theme": "corporate-blue",
            "slides": [
                {"slide_type": "dcf_summary", "elements": []},
                {"slide_type": "comp_table", "elements": []},
            ],
        }
        result = await estimate_cost(json.dumps(ir))
        assert result["surcharges"].get("finance", 0) > 0

    @pytest.mark.asyncio
    async def test_empty_slides_minimum_cost(self):
        ir = {
            "schema_version": "1.0",
            "metadata": {"title": "Test", "language": "en"},
            "theme": "corporate-blue",
            "slides": [],
        }
        result = await estimate_cost(json.dumps(ir))
        assert result["total_credits"] >= 1  # minimum 1 credit


# ---------------------------------------------------------------------------
# render_presentation tool (mocked)
# ---------------------------------------------------------------------------


class TestRenderPresentation:
    """Test render tool with mocked pipeline."""

    @pytest.mark.asyncio
    async def test_render_returns_expected_fields(self):
        from deckforge.mcp.tools import render_presentation

        mock_qa = MagicMock()
        mock_qa.overall_score = 85
        mock_qa.issues = []

        with patch(
            "deckforge.workers.tasks.render_pipeline",
            return_value=(b"\x00" * 1024, mock_qa),
        ):
            result = await render_presentation(
                ir_json=json.dumps(
                    {
                        "schema_version": "1.0",
                        "metadata": {"title": "Test", "language": "en"},
                        "theme": "corporate-blue",
                        "slides": [
                            {"slide_type": "title_slide", "elements": [
                                {"type": "heading", "content": {"text": "Hello"}}
                            ]}
                        ],
                    }
                ),
            )

        assert "slide_count" in result
        assert "quality_score" in result
        assert "format" in result
        assert result["format"] == "pptx"
        assert result["slide_count"] == 1
        assert result["quality_score"] == 85


# ---------------------------------------------------------------------------
# generate_presentation tool (mocked)
# ---------------------------------------------------------------------------


class TestGeneratePresentation:
    """Test generate tool with mocked content pipeline."""

    @pytest.mark.asyncio
    async def test_generate_returns_expected_fields(self):
        from deckforge.mcp.tools import generate_presentation

        mock_ir = {
            "schema_version": "1.0",
            "metadata": {"title": "Q4 Earnings", "language": "en"},
            "theme": "corporate-blue",
            "slides": [
                {"slide_type": "title_slide", "elements": []},
                {"slide_type": "bullet_points", "elements": []},
            ],
        }

        mock_pipeline = AsyncMock()
        mock_pipeline.run.return_value = mock_ir

        with patch(
            "deckforge.content.pipeline.ContentPipeline",
            return_value=mock_pipeline,
        ), patch(
            "deckforge.llm.router.LLMRouter",
            return_value=MagicMock(),
        ):
            result = await generate_presentation(
                prompt="Create a Q4 earnings deck",
                slide_count=5,
            )

        assert result["title"] == "Q4 Earnings"
        assert result["slide_count"] == 2
        assert result["theme"] == "corporate-blue"
        assert "ir" in result
