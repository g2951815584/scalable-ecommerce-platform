"""Minimal template renderer (only ``{{var}}`` and ``{{var|default:text}}``)."""

import re

_PATTERN = re.compile(r"\{\{(.*?)\}\}")


def render(template: str, variables: dict) -> str:
    def replace(match: re.Match) -> str:
        inner = match.group(1).strip()
        if "|" in inner:
            name, default = inner.split("|", 1)
            default = default.removeprefix("default:")
            value = variables.get(name.strip())
            return str(value) if value not in (None, "") else default
        return str(variables.get(inner, ""))

    return _PATTERN.sub(replace, template)