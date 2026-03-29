"""Temporary spreadsheet cleanup service for Google Slides rendering.

After charts are embedded in a Slides presentation, the temporary
Sheets spreadsheet used to create them can be deleted.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def cleanup_temp_spreadsheets(
    drive_service: Any,
    spreadsheet_ids: list[str],
) -> list[str]:
    """Delete temporary spreadsheets used for chart creation.

    Args:
        drive_service: Google Drive API service instance.
        spreadsheet_ids: List of spreadsheet IDs to delete.

    Returns:
        List of spreadsheet IDs that failed to delete.
    """
    failed: list[str] = []

    for sid in spreadsheet_ids:
        try:
            drive_service.files().delete(fileId=sid).execute()
        except Exception as e:
            logger.warning("Failed to delete temp spreadsheet %s: %s", sid, e)
            failed.append(sid)

    return failed


__all__ = ["cleanup_temp_spreadsheets"]
