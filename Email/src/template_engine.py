"""Jinja2-based HTML template rendering for email bodies."""

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class TemplateEngine:
    """Renders HTML email templates from a directory using Jinja2.

    HTML auto-escaping is enabled to prevent XSS when user-supplied
    data is injected into templates.

    Args:
        templates_dir: Directory that contains ``.html`` template files.
    """

    def __init__(self, templates_dir: Path) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a named template with the provided context variables.

        Args:
            template_name: Filename relative to *templates_dir* (e.g. ``"daily_report.html"``).
            context: Mapping of variable names to values passed to the template.

        Returns:
            Rendered HTML string.

        Raises:
            FileNotFoundError: If *template_name* does not exist in the templates directory.
        """
        try:
            template = self._env.get_template(template_name)
        except TemplateNotFound as exc:
            raise FileNotFoundError(f"Template not found: {template_name}") from exc
        return template.render(**context)

    def render_string(self, source: str, context: Dict[str, Any]) -> str:
        """Render a template from a raw string source.

        Useful for ad-hoc or dynamically constructed templates.

        Args:
            source: Jinja2 template source string.
            context: Variable bindings for the template.

        Returns:
            Rendered string.
        """
        template = self._env.from_string(source)
        return template.render(**context)
