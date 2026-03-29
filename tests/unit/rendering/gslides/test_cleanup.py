"""Tests for Google Slides temp spreadsheet cleanup."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from deckforge.rendering.gslides.cleanup import cleanup_temp_spreadsheets


class TestCleanupTempSpreadsheets:
    def test_successful_deletion(self):
        drive_svc = MagicMock()
        drive_svc.files().delete().execute.return_value = None

        failed = cleanup_temp_spreadsheets(drive_svc, ["sheet_1", "sheet_2"])
        assert failed == []

    def test_failed_deletion_returns_failed_ids(self):
        drive_svc = MagicMock()
        drive_svc.files().delete().execute.side_effect = Exception("API error")

        failed = cleanup_temp_spreadsheets(drive_svc, ["sheet_1"])
        assert failed == ["sheet_1"]

    def test_empty_list(self):
        drive_svc = MagicMock()
        failed = cleanup_temp_spreadsheets(drive_svc, [])
        assert failed == []

    def test_partial_failure(self):
        drive_svc = MagicMock()

        # First call succeeds, second fails
        def side_effect():
            mock = MagicMock()
            call_count = [0]

            def delete_side_effect(fileId=None):
                result = MagicMock()
                call_count[0] += 1
                if call_count[0] > 1:
                    result.execute.side_effect = Exception("fail")
                else:
                    result.execute.return_value = None
                return result

            mock.delete = delete_side_effect
            return mock

        drive_svc.files.return_value = side_effect()

        failed = cleanup_temp_spreadsheets(drive_svc, ["ok_sheet", "bad_sheet"])
        # At least the bad one should be in failed
        assert "bad_sheet" in failed
