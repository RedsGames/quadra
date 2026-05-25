"""Tests for the Jinja2 template engine wrapper."""

from pathlib import Path

import pytest

from src.template_engine import TemplateEngine


@pytest.fixture
def engine(tmp_path: Path) -> TemplateEngine:
    (tmp_path / "hello.html").write_text("<p>Hello, {{ name }}!</p>", encoding="utf-8")
    (tmp_path / "list.html").write_text(
        "{% for item in items %}<li>{{ item }}</li>{% endfor %}", encoding="utf-8"
    )
    (tmp_path / "conditional.html").write_text(
        "{% if show %}visible{% else %}hidden{% endif %}", encoding="utf-8"
    )
    return TemplateEngine(tmp_path)


class TestRender:
    def test_basic_variable_substitution(self, engine):
        result = engine.render("hello.html", {"name": "World"})
        assert "Hello, World!" in result

    def test_missing_template_raises_file_not_found(self, engine):
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            engine.render("nonexistent.html", {})

    def test_loop_rendering(self, engine):
        result = engine.render("list.html", {"items": ["alpha", "beta", "gamma"]})
        assert "<li>alpha</li>" in result
        assert "<li>gamma</li>" in result

    def test_conditional_true(self, engine):
        result = engine.render("conditional.html", {"show": True})
        assert result == "visible"

    def test_conditional_false(self, engine):
        result = engine.render("conditional.html", {"show": False})
        assert result == "hidden"

    def test_html_is_autoescaped(self, engine):
        result = engine.render("hello.html", {"name": "<script>alert(1)</script>"})
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_empty_context(self, engine):
        result = engine.render("hello.html", {})
        assert "<p>Hello, !</p>" in result


class TestRenderString:
    def test_simple_expression(self, engine):
        result = engine.render_string("{{ 1 + 1 }}", {})
        assert result == "2"

    def test_variable_injection(self, engine):
        result = engine.render_string("{{ x }} and {{ y }}", {"x": "foo", "y": "bar"})
        assert result == "foo and bar"

    def test_autoescaped_in_string(self, engine):
        result = engine.render_string("{{ v }}", {"v": "<b>"})
        assert "<b>" not in result
