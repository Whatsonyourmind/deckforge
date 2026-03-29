"""Theme variable resolver — resolves $references in theme dicts with cycle detection."""

from __future__ import annotations

import copy
import re
from typing import Any

VARIABLE_PATTERN = re.compile(r"\$([a-zA-Z_][a-zA-Z0-9_.]*)")


class ThemeResolver:
    """Resolves $variable references in a raw theme dictionary.

    The 3-tier design token structure means:
      - Tier 1 (colors): raw hex values
      - Tier 2 (palette): semantic references using $colors.xxx
      - Tier 3 (slide_masters): references using $palette.xxx or $colors.xxx

    resolve_all() walks the entire dict and resolves every $reference,
    detecting circular references via a resolution stack.
    """

    def __init__(self, raw: dict[str, Any]) -> None:
        self._raw = copy.deepcopy(raw)
        self._resolved: dict[str, Any] = copy.deepcopy(raw)

    def _get_nested(self, data: dict[str, Any], path: str) -> Any:
        """Traverse nested dict by dotted path (e.g., 'colors.navy_900')."""
        keys = path.split(".")
        current: Any = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _set_nested(self, data: dict[str, Any], path: str, value: Any) -> None:
        """Set a value in a nested dict by dotted path."""
        keys = path.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def resolve(self, path: str, _stack: set[str] | None = None) -> Any:
        """Resolve a dotted path to its final value with cycle detection."""
        if _stack is None:
            _stack = set()

        if path in _stack:
            raise ValueError(
                f"Circular reference detected: {' -> '.join(_stack)} -> {path}"
            )

        _stack = _stack | {path}
        value = self._get_nested(self._resolved, path)

        if value is None:
            return None

        if isinstance(value, str):
            match = VARIABLE_PATTERN.fullmatch(value)
            if match:
                ref_path = match.group(1)
                resolved_value = self.resolve(ref_path, _stack)
                if resolved_value is not None:
                    self._set_nested(self._resolved, path, resolved_value)
                    return resolved_value
                return value

            # Handle partial references in strings (e.g., "url($colors.bg)")
            def replace_ref(m: re.Match) -> str:
                ref_path = m.group(1)
                resolved = self.resolve(ref_path, _stack)
                return str(resolved) if resolved is not None else m.group(0)

            if VARIABLE_PATTERN.search(value):
                new_value = VARIABLE_PATTERN.sub(replace_ref, value)
                self._set_nested(self._resolved, path, new_value)
                return new_value

        return value

    def _walk_and_resolve(
        self,
        data: dict[str, Any],
        prefix: str = "",
    ) -> None:
        """Walk the dict tree and resolve all $references."""
        for key, value in list(data.items()):
            current_path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                self._walk_and_resolve(value, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and VARIABLE_PATTERN.search(item):
                        item_path = f"{current_path}[{i}]"
                        match = VARIABLE_PATTERN.fullmatch(item)
                        if match:
                            resolved = self.resolve(match.group(1))
                            if resolved is not None:
                                data[key][i] = resolved
                        else:
                            def make_replacer(stack_path: str):
                                def replace_ref(m: re.Match) -> str:
                                    ref_path = m.group(1)
                                    resolved = self.resolve(ref_path)
                                    return str(resolved) if resolved is not None else m.group(0)
                                return replace_ref

                            data[key][i] = VARIABLE_PATTERN.sub(
                                make_replacer(item_path), item
                            )
            elif isinstance(value, str) and VARIABLE_PATTERN.search(value):
                self.resolve(current_path)

    def resolve_all(self) -> dict[str, Any]:
        """Resolve every $reference in the theme dict.

        Returns a fully-resolved copy with no $references remaining.
        """
        # Process tiers in order: colors first, then palette, then everything else
        tier_order = ["colors", "palette"]
        for tier in tier_order:
            if tier in self._resolved and isinstance(self._resolved[tier], dict):
                self._walk_and_resolve(
                    self._resolved[tier], prefix=tier
                )

        # Now resolve everything else
        self._walk_and_resolve(self._resolved)

        return self._resolved
