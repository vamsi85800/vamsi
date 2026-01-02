"""prompt package: helpers for constructing prompts."""

from typing import Mapping


def fill_prompt(template: str, values: Mapping[str, str]) -> str:
    """Return the template filled with values using str.format_map."""
    return template.format_map(values)
