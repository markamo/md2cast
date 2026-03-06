#!/usr/bin/env python3
"""Tests for md2cast."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

# Add parent dir to path so we can import md2cast as a module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import md2cast functions (script has no .py extension)
MD2CAST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "md2cast")

import importlib.util
spec = importlib.util.spec_from_file_location("md2cast", MD2CAST,
                                               submodule_search_locations=[])
if spec is None:
    # Fallback: create a loader manually for extensionless files
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader("md2cast_mod", MD2CAST)
    spec = importlib.util.spec_from_loader("md2cast_mod", loader)
m = importlib.util.module_from_spec(spec)
# Prevent argparse from consuming test runner args
_orig_argv = sys.argv
sys.argv = [MD2CAST]
spec.loader.exec_module(m)
sys.argv = _orig_argv


# ── Color parsing ─────────────────────────────────────────────────────────

class TestParseColor(unittest.TestCase):
    def test_named_green(self):
        self.assertEqual(m._parse_color("green"), "\033[0;32m")

    def test_named_cyan(self):
        self.assertEqual(m._parse_color("cyan"), "\033[0;36m")

    def test_named_red(self):
        self.assertEqual(m._parse_color("red"), "\033[0;31m")

    def test_bold(self):
        self.assertEqual(m._parse_color("bold"), "\033[1m")

    def test_dim(self):
        self.assertEqual(m._parse_color("dim"), "\033[2m")

    def test_reset_empty(self):
        self.assertEqual(m._parse_color(""), "\033[0m")

    def test_reset_keyword(self):
        self.assertEqual(m._parse_color("reset"), "\033[0m")

    def test_hex_color(self):
        result = m._parse_color("#ff6600")
        self.assertEqual(result, "\033[38;2;255;102;0m")

    def test_hex_black(self):
        result = m._parse_color("#000000")
        self.assertEqual(result, "\033[38;2;0;0;0m")

    def test_256_color(self):
        result = m._parse_color("256:208")
        self.assertEqual(result, "\033[38;5;208m")

    def test_raw_sgr(self):
        result = m._parse_color("1;38;5;214")
        self.assertEqual(result, "\033[1;38;5;214m")


class TestParseBgColor(unittest.TestCase):
    def test_hex_bg(self):
        result = m._parse_bg_color("#ff0000")
        self.assertEqual(result, "\033[48;2;255;0;0m")

    def test_256_bg(self):
        result = m._parse_bg_color("256:100")
        self.assertEqual(result, "\033[48;5;100m")

    def test_empty_bg(self):
        self.assertEqual(m._parse_bg_color(""), "")

    def test_reset_bg(self):
        self.assertEqual(m._parse_bg_color("reset"), "")


# ── Theme ─────────────────────────────────────────────────────────────────

class TestTheme(unittest.TestCase):
    def test_default_theme(self):
        t = m.Theme()
        self.assertEqual(t.cols, 110)
        self.assertEqual(t.rows, 35)
        self.assertEqual(t.type_delay, 0.03)
        self.assertEqual(t.cmd_pause, 0.8)
        self.assertTrue(t.syntax_highlight)
        self.assertEqual(t.highlight_style, "monokai")

    def test_custom_theme_overrides(self):
        cfg = {"terminal": {"cols": 80, "rows": 24},
               "timing": {"type_delay": 0.01}}
        t = m.Theme(cfg)
        self.assertEqual(t.cols, 80)
        self.assertEqual(t.rows, 24)
        self.assertEqual(t.type_delay, 0.01)
        # Unspecified values keep defaults
        self.assertEqual(t.cmd_pause, 0.8)

    def test_theme_colors_resolved(self):
        t = m.Theme()
        self.assertIn("\033[", t.prompt)
        self.assertIn("\033[", t.title_border)
        self.assertEqual(t.nc, "\033[0m")

    def test_player_metadata(self):
        cfg = {"player": {"theme": "dracula", "font_size": 18}}
        t = m.Theme(cfg)
        self.assertEqual(t.player_theme, "dracula")
        self.assertEqual(t.font_size, 18)


class TestDeepMerge(unittest.TestCase):
    def test_simple_merge(self):
        base = {"a": 1, "b": 2}
        over = {"b": 3, "c": 4}
        result = m._deep_merge(base, over)
        self.assertEqual(result, {"a": 1, "b": 3, "c": 4})

    def test_nested_merge(self):
        base = {"x": {"a": 1, "b": 2}}
        over = {"x": {"b": 3}}
        result = m._deep_merge(base, over)
        self.assertEqual(result, {"x": {"a": 1, "b": 3}})

    def test_does_not_mutate_base(self):
        base = {"a": 1}
        over = {"a": 2}
        m._deep_merge(base, over)
        self.assertEqual(base, {"a": 1})


# ── Markdown parser ──────────────────────────────────────────────────────

class TestParseMarkdown(unittest.TestCase):
    def test_heading_levels(self):
        blocks = m.parse_markdown("# Title\n## Section\n### Sub")
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].kind, "heading")
        self.assertEqual(blocks[0].level, 1)
        self.assertEqual(blocks[0].content, "Title")
        self.assertEqual(blocks[1].level, 2)
        self.assertEqual(blocks[2].level, 3)

    def test_bash_code_block(self):
        md = "```bash\necho hello\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "code")
        self.assertEqual(blocks[0].lang, "bash")
        self.assertEqual(blocks[0].content, "echo hello")

    def test_plain_code_block_is_output(self):
        md = "```\nsome output\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "output")
        self.assertEqual(blocks[0].content, "some output")

    def test_yaml_block_is_output(self):
        md = "```yaml\nkey: value\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "output")
        self.assertEqual(blocks[0].lang, "yaml")

    def test_python_block_is_output(self):
        md = "```python\nprint('hi')\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "output")
        self.assertEqual(blocks[0].lang, "python")

    def test_text_paragraph(self):
        blocks = m.parse_markdown("Hello world\nmore text")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "text")
        self.assertEqual(blocks[0].content, "Hello world more text")

    def test_blockquote(self):
        blocks = m.parse_markdown("> This is a note\n> continued")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "quote")
        self.assertEqual(blocks[0].content, "This is a note\ncontinued")

    def test_horizontal_rule(self):
        blocks = m.parse_markdown("---")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "hr")

    def test_hr_with_asterisks(self):
        blocks = m.parse_markdown("***")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "hr")

    def test_pause_directive(self):
        blocks = m.parse_markdown("<!-- pause 3 -->")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "pause")
        self.assertEqual(blocks[0].content, "3")

    def test_pause_float(self):
        blocks = m.parse_markdown("<!-- pause 1.5 -->")
        self.assertEqual(blocks[0].content, "1.5")

    def test_skip_directive(self):
        md = "<!-- skip -->\n```bash\nrm -rf /\n```\n## Next"
        blocks = m.parse_markdown(md)
        # Skipped block should not appear
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "heading")

    def test_clear_directive(self):
        blocks = m.parse_markdown("<!-- clear -->")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "hr")

    def test_exec_directive(self):
        md = "<!-- exec -->\n```bash\necho hi\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(len(blocks), 1)
        self.assertTrue(blocks[0].directives.get("exec"))

    def test_no_exec_directive(self):
        md = "<!-- no-exec -->\n```bash\necho hi\n```"
        blocks = m.parse_markdown(md)
        self.assertTrue(blocks[0].directives.get("no-exec"))

    def test_output_directive_on_bash(self):
        md = "<!-- output -->\n```bash\necho hi\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(blocks[0].kind, "output")

    def test_type_delay_directive(self):
        md = "<!-- type-delay 0.01 -->\n```bash\nls\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(blocks[0].directives.get("type-delay"), 0.01)

    def test_prompt_directive(self):
        md = "<!-- prompt # -->\n```bash\napt install nginx\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(blocks[0].directives.get("prompt"), "#")

    def test_view_exec_directive(self):
        md = "<!-- view-exec -->\n```bash\nls\npwd\n```"
        blocks = m.parse_markdown(md)
        self.assertTrue(blocks[0].directives.get("view-exec"))

    def test_browser_directive(self):
        md = "<!-- browser -->\n```steps\nopen https://example.com\nscreenshot home\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "browser")
        self.assertTrue(blocks[0].directives.get("browser"))

    def test_gui_directive(self):
        md = "<!-- gui -->\n```steps\nlaunch code .\nsleep 2\nscreenshot editor\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "gui")
        self.assertTrue(blocks[0].directives.get("gui"))

    def test_stacked_directives(self):
        md = "<!-- prompt # -->\n<!-- type-delay 0.08 -->\n```bash\napt install nginx\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(blocks[0].directives.get("prompt"), "#")
        self.assertEqual(blocks[0].directives.get("type-delay"), 0.08)

    def test_multiline_code_block(self):
        md = "```bash\necho one\necho two\necho three\n```"
        blocks = m.parse_markdown(md)
        self.assertEqual(blocks[0].content, "echo one\necho two\necho three")

    def test_mixed_content(self):
        md = """# Title

Some text.

## Section 1

```bash
ls -la
```

> A note

---

## Section 2

```yaml
key: value
```
"""
        blocks = m.parse_markdown(md)
        kinds = [b.kind for b in blocks]
        self.assertEqual(kinds, [
            "heading", "text", "heading", "code", "quote", "hr", "heading", "output"
        ])


# ── Text utilities ────────────────────────────────────────────────────────

class TestStripMd(unittest.TestCase):
    def test_bold(self):
        self.assertEqual(m.strip_md("**hello**"), "hello")

    def test_italic(self):
        self.assertEqual(m.strip_md("*hello*"), "hello")

    def test_inline_code(self):
        self.assertEqual(m.strip_md("`code`"), "code")

    def test_link(self):
        self.assertEqual(m.strip_md("[text](url)"), "text")

    def test_image(self):
        # strip_md removes image markdown but may leave artifacts
        result = m.strip_md("![alt](img.png)")
        # Image link should be removed or reduced
        self.assertNotIn("img.png", result)

    def test_mixed(self):
        self.assertEqual(m.strip_md("Use **bold** and `code` here"), "Use bold and code here")


class TestWordWrap(unittest.TestCase):
    def test_short_text(self):
        result = m.word_wrap("hello", width=80)
        self.assertEqual(result, ["hello"])

    def test_wraps_at_width(self):
        text = "word " * 20  # 100 chars
        result = m.word_wrap(text.strip(), width=30)
        for line in result:
            self.assertLessEqual(len(line), 30)

    def test_empty_text(self):
        result = m.word_wrap("", width=80)
        self.assertEqual(result, [])


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(m.slugify("Hello World"), "hello-world")

    def test_special_chars(self):
        self.assertEqual(m.slugify("Step 1: Install!"), "step-1-install")

    def test_markdown_formatting(self):
        self.assertEqual(m.slugify("**Bold** Title"), "bold-title")

    def test_max_length(self):
        long_text = "a" * 100
        result = m.slugify(long_text)
        self.assertLessEqual(len(result), 60)


# ── CastWriter ────────────────────────────────────────────────────────────

class TestCastWriter(unittest.TestCase):
    def test_basic_cast(self):
        t = m.Theme()
        cw = m.CastWriter(t, title="Test")
        cw.write("hello")
        cw.pause(1.0)
        cw.write("world")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cast", delete=False) as f:
            path = f.name
        try:
            cw.save(path)
            with open(path) as f:
                lines = f.readlines()

            # First line is JSON header
            header = json.loads(lines[0])
            self.assertEqual(header["version"], 2)
            self.assertEqual(header["width"], 110)
            self.assertEqual(header["height"], 35)
            self.assertEqual(header["title"], "Test")

            # Events follow
            events = [json.loads(l) for l in lines[1:]]
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0][1], "o")
            self.assertEqual(events[0][2], "hello")
            self.assertEqual(events[1][2], "world")
            # Second event should be ~1s later
            self.assertAlmostEqual(events[1][0] - events[0][0], 1.0, places=2)
        finally:
            os.unlink(path)

    def test_type_text(self):
        t = m.Theme({"timing": {"type_delay": 0.01}})
        cw = m.CastWriter(t)
        cw.type_text("abc")

        self.assertEqual(len(cw.events), 3)
        self.assertEqual(cw.events[0][2], "a")
        self.assertEqual(cw.events[1][2], "b")
        self.assertEqual(cw.events[2][2], "c")

    def test_write_line(self):
        t = m.Theme()
        cw = m.CastWriter(t)
        cw.write_line("test")
        self.assertEqual(cw.events[0][2], "test\r\n")

    def test_clear(self):
        t = m.Theme()
        cw = m.CastWriter(t)
        cw.clear()
        self.assertEqual(cw.events[0][2], "\033[2J\033[H")

    def test_player_metadata_in_header(self):
        t = m.Theme({"player": {"theme": "dracula", "font_family": "Fira Code", "font_size": 14}})
        cw = m.CastWriter(t)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cast", delete=False) as f:
            path = f.name
        try:
            cw.save(path)
            with open(path) as f:
                header = json.loads(f.readline())
            self.assertEqual(header["env"]["THEME"], "dracula")
            self.assertEqual(header["env"]["FONT_FAMILY"], "Fira Code")
            self.assertEqual(header["env"]["FONT_SIZE"], "14")
        finally:
            os.unlink(path)


# ── Renderer ──────────────────────────────────────────────────────────────

class TestRenderer(unittest.TestCase):
    def _make_renderer(self, **kwargs):
        t = m.Theme({"timing": {"type_delay": 0.001, "cmd_pause": 0.01,
                                "output_pause": 0.01, "section_pause": 0.01,
                                "text_pause": 0.01, "end_pause": 0.01}})
        cw = m.CastWriter(t)
        return m.Renderer(cw, t, **kwargs), cw

    def test_render_title_card(self):
        r, cw = self._make_renderer()
        r.render_title_card("My Title")
        text = "".join(e[2] for e in cw.events)
        self.assertIn("My Title", text)

    def test_render_section(self):
        r, cw = self._make_renderer()
        r.render_section("Section One")
        text = "".join(e[2] for e in cw.events)
        self.assertIn("Section One", text)

    def test_render_text(self):
        r, cw = self._make_renderer()
        r.render_text("This is narrated text")
        text = "".join(e[2] for e in cw.events)
        self.assertIn("# This is narrated text", text)

    def test_render_quote(self):
        r, cw = self._make_renderer()
        r.render_quote("A helpful tip")
        text = "".join(e[2] for e in cw.events)
        self.assertIn("A helpful tip", text)

    def test_render_command_no_exec(self):
        r, cw = self._make_renderer(execute=False)
        r.render_command("echo hello")
        text = "".join(e[2] for e in cw.events)
        self.assertIn("$", text)
        # Characters of "echo hello" should be typed individually
        chars = [e[2] for e in cw.events if len(e[2]) == 1]
        typed = "".join(chars)
        self.assertIn("echo hello", typed)

    def test_render_command_with_exec(self):
        r, cw = self._make_renderer(execute=True)
        r.render_command("echo test123")
        text = "".join(e[2] for e in cw.events)
        self.assertIn("test123", text)

    def test_render_command_exec_directive(self):
        r, cw = self._make_renderer(execute=False)
        r.render_command("echo directive_test", directives={"exec": True})
        text = "".join(e[2] for e in cw.events)
        self.assertIn("directive_test", text)

    def test_render_command_no_exec_directive(self):
        r, cw = self._make_renderer(execute=True)
        r.render_command("echo should_not_run", directives={"no-exec": True})
        text = "".join(e[2] for e in cw.events)
        # The command is typed but not executed, so output shouldn't appear as a separate line
        # (it appears in the typed chars but not as command output)
        output_lines = [e[2] for e in cw.events if "should_not_run\r\n" == e[2]]
        self.assertEqual(len(output_lines), 0)

    def test_render_command_custom_prompt(self):
        r, cw = self._make_renderer()
        r.render_command("apt install nginx", directives={"prompt": "#"})
        text = "".join(e[2] for e in cw.events)
        self.assertIn("# ", text)

    def test_render_command_comment_lines(self):
        r, cw = self._make_renderer()
        r.render_command("# This is a comment\necho hi")
        text = "".join(e[2] for e in cw.events)
        self.assertIn("# This is a comment", text)


# ── Output rendering ─────────────────────────────────────────────────────

class TestRenderOutput(unittest.TestCase):
    def test_render_output(self):
        t = m.Theme({"timing": {"output_pause": 0.01}})
        cw = m.CastWriter(t)
        r = m.Renderer(cw, t)
        r.render_output("line1\nline2")
        text = "".join(e[2] for e in cw.events)
        self.assertIn("line1", text)
        self.assertIn("line2", text)


# ── CLI integration ──────────────────────────────────────────────────────

class TestCLI(unittest.TestCase):
    def test_version(self):
        result = subprocess.run([MD2CAST, "--version"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("md2cast", result.stdout)

    def test_init_theme(self):
        result = subprocess.run([MD2CAST, "--init-theme"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        theme = json.loads(result.stdout)
        self.assertIn("terminal", theme)
        self.assertIn("colors", theme)
        self.assertIn("timing", theme)
        self.assertIn("player", theme)

    def test_no_input_error(self):
        result = subprocess.run([MD2CAST], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_missing_file_error(self):
        result = subprocess.run([MD2CAST, "/nonexistent.md"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_basic_conversion(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Hello\n\nSome text.\n\n```bash\necho hi\n```\n")
            md_path = f.name
        cast_path = md_path.replace(".md", ".cast")
        try:
            result = subprocess.run([MD2CAST, md_path, "-o", cast_path],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(os.path.exists(cast_path))

            with open(cast_path) as f:
                lines = f.readlines()
            header = json.loads(lines[0])
            self.assertEqual(header["version"], 2)
            self.assertGreater(len(lines), 1)
        finally:
            os.unlink(md_path)
            if os.path.exists(cast_path):
                os.unlink(cast_path)

    def test_list_sections(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n## Section A\n## Section B\n")
            md_path = f.name
        try:
            result = subprocess.run([MD2CAST, md_path, "--list"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Section A", result.stdout)
            self.assertIn("Section B", result.stdout)
        finally:
            os.unlink(md_path)

    def test_execute_mode(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("```bash\necho exec_test_42\n```\n")
            md_path = f.name
        cast_path = md_path.replace(".md", ".cast")
        try:
            result = subprocess.run([MD2CAST, md_path, "-o", cast_path, "--execute"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)

            with open(cast_path) as f:
                content = f.read()
            self.assertIn("exec_test_42", content)
        finally:
            os.unlink(md_path)
            if os.path.exists(cast_path):
                os.unlink(cast_path)

    def test_custom_cols_rows(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            md_path = f.name
        cast_path = md_path.replace(".md", ".cast")
        try:
            result = subprocess.run([MD2CAST, md_path, "-o", cast_path,
                                     "--cols", "80", "--rows", "24"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)

            with open(cast_path) as f:
                header = json.loads(f.readline())
            self.assertEqual(header["width"], 80)
            self.assertEqual(header["height"], 24)
        finally:
            os.unlink(md_path)
            if os.path.exists(cast_path):
                os.unlink(cast_path)

    def test_split_mode(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n## Part One\n```bash\nls\n```\n## Part Two\n```bash\npwd\n```\n")
            md_path = f.name
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run([MD2CAST, md_path, "--split", "-o", tmpdir],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0)
                casts = [f for f in os.listdir(tmpdir) if f.endswith(".cast")]
                self.assertGreaterEqual(len(casts), 2)
        finally:
            os.unlink(md_path)

    def test_theme_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"terminal": {"cols": 60, "rows": 20}}, f)
            theme_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            md_path = f.name
        cast_path = md_path.replace(".md", ".cast")
        try:
            result = subprocess.run([MD2CAST, md_path, "-o", cast_path,
                                     "--theme", theme_path],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)

            with open(cast_path) as f:
                header = json.loads(f.readline())
            self.assertEqual(header["width"], 60)
            self.assertEqual(header["height"], 20)
        finally:
            os.unlink(md_path)
            os.unlink(theme_path)
            if os.path.exists(cast_path):
                os.unlink(cast_path)


# ── Render modes ─────────────────────────────────────────────────────────

class TestRenderMarkdown(unittest.TestCase):
    def test_render_produces_output(self):
        md = "# Title\n\n## Section\n\n```bash\necho hello\n```\n"
        t = m.Theme({"timing": {"type_delay": 0.001, "cmd_pause": 0.01,
                                "output_pause": 0.01, "section_pause": 0.01,
                                "text_pause": 0.01, "end_pause": 0.01}})
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = os.path.join(tmpdir, "assets")
            rendered, count = m.render_markdown(md, t, assets)
            self.assertGreaterEqual(count, 1)
            self.assertIn("# Title", rendered)
            self.assertIn(".gif", rendered)

    def test_render_footer(self):
        md = "# Title\n\n```bash\necho hi\n```\n"
        t = m.Theme({"timing": {"type_delay": 0.001, "cmd_pause": 0.01,
                                "output_pause": 0.01, "section_pause": 0.01,
                                "text_pause": 0.01, "end_pause": 0.01}})
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = os.path.join(tmpdir, "assets")
            rendered, _ = m.render_markdown(md, t, assets)
            self.assertIn("Made with", rendered)
            self.assertIn("md2cast", rendered)

    def test_render_preserves_text(self):
        md = "# Title\n\nSome description text.\n\n```bash\necho hi\n```\n"
        t = m.Theme({"timing": {"type_delay": 0.001, "cmd_pause": 0.01,
                                "output_pause": 0.01, "section_pause": 0.01,
                                "text_pause": 0.01, "end_pause": 0.01}})
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = os.path.join(tmpdir, "assets")
            rendered, _ = m.render_markdown(md, t, assets)
            self.assertIn("Some description text.", rendered)


class TestRenderHTML(unittest.TestCase):
    def test_render_html_produces_output(self):
        md = "# Title\n\n## Section\n\n```bash\necho hello\n```\n"
        t = m.Theme({"timing": {"type_delay": 0.001, "cmd_pause": 0.01,
                                "output_pause": 0.01, "section_pause": 0.01,
                                "text_pause": 0.01, "end_pause": 0.01}})
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = os.path.join(tmpdir, "assets")
            html, count = m.render_html(md, t, assets)
            self.assertGreaterEqual(count, 1)
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn("asciinema-player", html)

    def test_render_html_footer(self):
        md = "# Title\n\n```bash\necho hi\n```\n"
        t = m.Theme({"timing": {"type_delay": 0.001, "cmd_pause": 0.01,
                                "output_pause": 0.01, "section_pause": 0.01,
                                "text_pause": 0.01, "end_pause": 0.01}})
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = os.path.join(tmpdir, "assets")
            html, _ = m.render_html(md, t, assets)
            self.assertIn("Made with", html)
            self.assertIn("md2cast", html)

    def test_render_html_title(self):
        md = "# My Amazing Tutorial\n\n```bash\necho hi\n```\n"
        t = m.Theme({"timing": {"type_delay": 0.001, "cmd_pause": 0.01,
                                "output_pause": 0.01, "section_pause": 0.01,
                                "text_pause": 0.01, "end_pause": 0.01}})
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = os.path.join(tmpdir, "assets")
            html, _ = m.render_html(md, t, assets)
            self.assertIn("<title>My Amazing Tutorial</title>", html)


# ── HTML escape ───────────────────────────────────────────────────────────

class TestHtmlEscape(unittest.TestCase):
    def test_ampersand(self):
        self.assertEqual(m._html_escape("a & b"), "a &amp; b")

    def test_angle_brackets(self):
        self.assertEqual(m._html_escape("<script>"), "&lt;script&gt;")

    def test_quotes(self):
        self.assertEqual(m._html_escape('"hello"'), "&quot;hello&quot;")

    def test_no_escape_needed(self):
        self.assertEqual(m._html_escape("plain text"), "plain text")


# ── Browser steps parser ─────────────────────────────────────────────────

class TestParseBrowserSteps(unittest.TestCase):
    def test_open(self):
        steps = m.parse_browser_steps("open https://example.com")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["action"], "open")
        self.assertEqual(steps[0]["url"], "https://example.com")

    def test_click(self):
        steps = m.parse_browser_steps("click #login-btn")
        self.assertEqual(steps[0]["action"], "click")
        self.assertEqual(steps[0]["selector"], "#login-btn")

    def test_type(self):
        steps = m.parse_browser_steps("type #email user@test.com")
        self.assertEqual(steps[0]["action"], "type")
        self.assertEqual(steps[0]["selector"], "#email")
        self.assertEqual(steps[0]["text"], "user@test.com")

    def test_wait(self):
        steps = m.parse_browser_steps("wait .loaded")
        self.assertEqual(steps[0]["action"], "wait")
        self.assertEqual(steps[0]["selector"], ".loaded")

    def test_screenshot(self):
        steps = m.parse_browser_steps("screenshot dashboard")
        self.assertEqual(steps[0]["action"], "screenshot")
        self.assertEqual(steps[0]["name"], "dashboard")

    def test_screenshot_default_name(self):
        steps = m.parse_browser_steps("screenshot")
        self.assertEqual(steps[0]["action"], "screenshot")

    def test_scroll(self):
        steps = m.parse_browser_steps("scroll down 500")
        self.assertEqual(steps[0]["action"], "scroll")
        self.assertEqual(steps[0]["direction"], "down")
        self.assertEqual(steps[0]["amount"], 500)

    def test_sleep(self):
        steps = m.parse_browser_steps("sleep 2")
        self.assertEqual(steps[0]["action"], "sleep")
        self.assertEqual(steps[0]["seconds"], 2.0)

    def test_hover(self):
        steps = m.parse_browser_steps("hover .menu-item")
        self.assertEqual(steps[0]["action"], "hover")
        self.assertEqual(steps[0]["selector"], ".menu-item")

    def test_resize(self):
        steps = m.parse_browser_steps("resize 1920 1080")
        self.assertEqual(steps[0]["action"], "resize")
        self.assertEqual(steps[0]["width"], 1920)
        self.assertEqual(steps[0]["height"], 1080)

    def test_video_start(self):
        steps = m.parse_browser_steps("video start demo")
        self.assertEqual(steps[0]["action"], "video_start")
        self.assertEqual(steps[0]["name"], "demo")

    def test_video_stop(self):
        steps = m.parse_browser_steps("video stop")
        self.assertEqual(steps[0]["action"], "video_stop")

    def test_select(self):
        steps = m.parse_browser_steps("select #country US")
        self.assertEqual(steps[0]["action"], "select")
        self.assertEqual(steps[0]["selector"], "#country")
        self.assertEqual(steps[0]["value"], "US")

    def test_multiple_steps(self):
        text = "open https://example.com\nwait .loaded\nscreenshot home\n"
        steps = m.parse_browser_steps(text)
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0]["action"], "open")
        self.assertEqual(steps[1]["action"], "wait")
        self.assertEqual(steps[2]["action"], "screenshot")

    def test_empty_lines_skipped(self):
        text = "open https://example.com\n\n\nscreenshot home\n"
        steps = m.parse_browser_steps(text)
        self.assertEqual(len(steps), 2)


# ── GUI steps parser ─────────────────────────────────────────────────────

class TestParseGuiSteps(unittest.TestCase):
    def test_launch(self):
        steps = m.parse_gui_steps("launch code .")
        self.assertEqual(steps[0]["action"], "launch")
        self.assertEqual(steps[0]["command"], "code .")

    def test_focus(self):
        steps = m.parse_gui_steps('focus "VS Code"')
        self.assertEqual(steps[0]["action"], "focus")

    def test_click_coords(self):
        steps = m.parse_gui_steps("click 500 300")
        self.assertEqual(steps[0]["action"], "click")
        self.assertEqual(steps[0]["x"], 500)
        self.assertEqual(steps[0]["y"], 300)

    def test_type_text(self):
        steps = m.parse_gui_steps('type "Hello World"')
        self.assertEqual(steps[0]["action"], "type")

    def test_key_combo(self):
        steps = m.parse_gui_steps("key ctrl+s")
        self.assertEqual(steps[0]["action"], "key")
        self.assertEqual(steps[0]["key"], "ctrl+s")

    def test_move(self):
        steps = m.parse_gui_steps("move 100 200")
        self.assertEqual(steps[0]["action"], "move")
        self.assertEqual(steps[0]["x"], 100)
        self.assertEqual(steps[0]["y"], 200)

    def test_drag(self):
        steps = m.parse_gui_steps("drag 100 100 500 500")
        self.assertEqual(steps[0]["action"], "drag")
        self.assertEqual(steps[0]["x1"], 100)
        self.assertEqual(steps[0]["y1"], 100)
        self.assertEqual(steps[0]["x2"], 500)
        self.assertEqual(steps[0]["y2"], 500)

    def test_screenshot(self):
        steps = m.parse_gui_steps("screenshot editor")
        self.assertEqual(steps[0]["action"], "screenshot")
        self.assertEqual(steps[0]["name"], "editor")

    def test_window_screenshot(self):
        steps = m.parse_gui_steps("window-screenshot mywin")
        self.assertEqual(steps[0]["action"], "window-screenshot")
        self.assertEqual(steps[0]["title"], "mywin")

    def test_sleep(self):
        steps = m.parse_gui_steps("sleep 2")
        self.assertEqual(steps[0]["action"], "sleep")
        self.assertEqual(steps[0]["seconds"], 2.0)

    def test_multiple_steps(self):
        text = "launch code .\nsleep 2\nscreenshot editor\n"
        steps = m.parse_gui_steps(text)
        self.assertEqual(len(steps), 3)


# ── Theme auto-discovery ─────────────────────────────────────────────────

class TestFindTheme(unittest.TestCase):
    def test_finds_md2cast_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            theme_path = os.path.join(tmpdir, "md2cast.json")
            with open(theme_path, "w") as f:
                json.dump({"terminal": {"cols": 80}}, f)
            input_path = os.path.join(tmpdir, "test.md")
            result = m.find_theme(input_path)
            self.assertEqual(result, theme_path)

    def test_finds_hidden_md2cast_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            theme_path = os.path.join(tmpdir, ".md2cast.json")
            with open(theme_path, "w") as f:
                json.dump({"terminal": {"cols": 80}}, f)
            input_path = os.path.join(tmpdir, "test.md")
            result = m.find_theme(input_path)
            self.assertEqual(result, theme_path)

    def test_no_theme_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "test.md")
            result = m.find_theme(input_path)
            # May or may not find global theme — just check it doesn't crash
            # and returns None or a valid path
            if result is not None:
                self.assertTrue(os.path.isfile(result))


# ── Cast file format validation ──────────────────────────────────────────

class TestCastFormat(unittest.TestCase):
    def test_valid_v2_format(self):
        """Ensure generated cast files are valid asciinema v2 format."""
        md = "# Test\n\n```bash\necho hello\n```\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(md)
            md_path = f.name
        cast_path = md_path.replace(".md", ".cast")
        try:
            subprocess.run([MD2CAST, md_path, "-o", cast_path],
                           capture_output=True, text=True, check=True)
            with open(cast_path) as f:
                lines = f.readlines()

            # Header
            header = json.loads(lines[0])
            self.assertEqual(header["version"], 2)
            self.assertIn("width", header)
            self.assertIn("height", header)

            # All event lines must be [time, type, data]
            for line in lines[1:]:
                event = json.loads(line)
                self.assertEqual(len(event), 3)
                self.assertIsInstance(event[0], (int, float))
                self.assertEqual(event[1], "o")
                self.assertIsInstance(event[2], str)

            # Timestamps must be non-decreasing
            times = [json.loads(l)[0] for l in lines[1:]]
            for i in range(1, len(times)):
                self.assertGreaterEqual(times[i], times[i-1])
        finally:
            os.unlink(md_path)
            if os.path.exists(cast_path):
                os.unlink(cast_path)


if __name__ == "__main__":
    unittest.main()
