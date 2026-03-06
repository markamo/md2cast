#!/usr/bin/env python3
# Copyright (c) 2026 Mark Amo-Boateng, PhD. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
md2cast — Convert Markdown documentation into asciinema screencasts.

Parses a Markdown file and generates an asciinema v2 .cast file with:
  - Title cards for # headings
  - Section dividers for ## and ### headings
  - Typed + optionally executed bash commands from ```bash blocks
  - Static output display from plain ``` blocks
  - Narrated comments from regular text
  - Highlighted notes from > blockquotes
  - Screen clears on --- separators

Usage:
  md2cast input.md                        # generate input.cast
  md2cast input.md -o demo.cast           # custom output name
  md2cast input.md --execute              # actually run bash commands
  md2cast input.md --section 3            # only section 3
  md2cast input.md --split                # one .cast per ## section
  md2cast input.md --list                 # list sections
  md2cast input.md --theme dark.json      # custom theme
  md2cast input.md --init-theme           # generate default theme file

Markdown mapping:
  # Heading          → title card (configurable: box/line/text/none)
  ## Heading         → section divider (configurable: box/line/text/none)
  ### Heading        → subsection label (configurable: box/line/text/none)
  Regular text       → narrated comment (dimmed)
  ```bash            → typed command (green $ prompt, character-by-character)
  ```                → static output (shown at once)
  > blockquote       → hint/note (yellow)
  **bold**           → emphasized narration
  ---                → section break (clear screen)

Directives (HTML comments — invisible in rendered Markdown):
  <!-- pause 3 -->        → custom pause (seconds)
  <!-- skip -->           → skip the next block entirely
  <!-- exec -->           → execute only the next bash block (no global --execute needed)
  <!-- no-exec -->        → skip execution for the next block (even with --execute)
  <!-- type-delay 0.01 --> → override typing speed for the next block
  <!-- prompt # -->       → change prompt character for the next block (e.g., root shell)
  <!-- output -->         → force next ```bash block to display as static output
  <!-- view-exec -->     → show commands as preview, then execute each with real output
  <!-- browser -->       → next code block contains browser automation steps (playwright)
  <!-- gui -->           → next code block contains GUI automation steps (xdotool/ydotool)
  <!-- clear -->          → clear screen (alternative to ---)
"""

import argparse
import json
import os
import re

# Optional syntax highlighting — uses pygments if installed, plain text otherwise
try:
    from pygments import highlight as _pygments_highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import Terminal256Formatter
    from pygments.util import ClassNotFound
    _HAS_PYGMENTS = True
except ImportError:
    _HAS_PYGMENTS = False
import subprocess
import sys
import textwrap

import time

try:
    from PIL import Image as _PILImage
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

__version__ = "0.3.0"

# ── Free tier limits ──────────────────────────────────────────────────────
FREE_TIER = True
FREE_MAX_SECTIONS = 10      # ## headings
FREE_MAX_BLOCKS = 15        # code blocks (cast/gif generation)
_PRO_URL = "https://md2cast.dev/pro"


def _check_block_limit(block_count):
    """Return True if block is within free tier limit. Prints warning once at limit."""
    if not FREE_TIER:
        return True
    if block_count == FREE_MAX_BLOCKS + 1:
        print(f"\n  Free tier limit: {FREE_MAX_BLOCKS} code blocks per document.",
              file=sys.stderr)
        print(f"  Remaining blocks skipped. Upgrade: {_PRO_URL}\n", file=sys.stderr)
    return block_count <= FREE_MAX_BLOCKS


def _check_section_limit(sections):
    """Trim sections to free tier limit. Returns trimmed list."""
    if not FREE_TIER or len(sections) <= FREE_MAX_SECTIONS:
        return sections
    print(f"\n  Free tier limit: {FREE_MAX_SECTIONS} sections per document "
          f"(this doc has {len(sections)}).",
          file=sys.stderr)
    print(f"  Upgrade for unlimited: {_PRO_URL}\n", file=sys.stderr)
    return sections[:FREE_MAX_SECTIONS]

# ── Theme ──────────────────────────────────────────────────────────────────

# ANSI 256-color: \033[38;5;Nm (foreground), \033[48;5;Nm (background)
# ANSI true color: \033[38;2;R;G;Bm (fg), \033[48;2;R;G;Bm (bg)

def _parse_color(value):
    """Convert a color spec to an ANSI escape sequence.

    Accepts:
      - Named:  "green", "cyan", "bold", "dim", "red", "yellow", "magenta", "white", "blue"
      - Hex:    "#00ff88" → true-color (24-bit)
      - 256:    "256:39" → 256-color palette
      - ANSI:   "0;32" or "1;36" → raw SGR code
      - Reset:  "reset" or "" → \\033[0m
    """
    if not value or value == "reset":
        return "\033[0m"
    if value == "bold":
        return "\033[1m"
    if value == "dim":
        return "\033[2m"

    # Named colors
    named = {
        "black": "0;30", "red": "0;31", "green": "0;32", "yellow": "1;33",
        "blue": "0;34", "magenta": "0;35", "cyan": "0;36", "white": "0;37",
        "bright_black": "0;90", "bright_red": "0;91", "bright_green": "0;92",
        "bright_yellow": "0;93", "bright_blue": "0;94", "bright_magenta": "0;95",
        "bright_cyan": "0;96", "bright_white": "0;97",
    }
    if value in named:
        return f"\033[{named[value]}m"

    # Hex color → true color
    hex_match = re.match(r'^#([0-9a-fA-F]{6})$', value)
    if hex_match:
        h = hex_match.group(1)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"\033[38;2;{r};{g};{b}m"

    # 256-color: "256:N"
    c256_match = re.match(r'^256:(\d+)$', value)
    if c256_match:
        return f"\033[38;5;{c256_match.group(1)}m"

    # Raw SGR code: "0;32", "1;36", etc.
    if re.match(r'^[\d;]+$', value):
        return f"\033[{value}m"

    return f"\033[{value}m"


def _parse_bg_color(value):
    """Convert a color spec to an ANSI background escape sequence."""
    if not value or value == "reset":
        return ""

    hex_match = re.match(r'^#([0-9a-fA-F]{6})$', value)
    if hex_match:
        h = hex_match.group(1)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"\033[48;2;{r};{g};{b}m"

    c256_match = re.match(r'^256:(\d+)$', value)
    if c256_match:
        return f"\033[48;5;{c256_match.group(1)}m"

    return ""


def highlight_code(code, lang="", style="monokai"):
    """Syntax-highlight code using pygments if available.

    Returns the code with ANSI escape codes for terminal display.
    Falls back to plain text if pygments is not installed.
    """
    if not _HAS_PYGMENTS or not lang:
        return code

    try:
        lexer = get_lexer_by_name(lang)
    except ClassNotFound:
        return code

    formatter = Terminal256Formatter(style=style)
    result = _pygments_highlight(code, lexer, formatter)
    # pygments adds a trailing newline — strip it to match input
    if result.endswith("\n") and not code.endswith("\n"):
        result = result[:-1]
    return result


DEFAULT_THEME = {
    "terminal": {
        "cols": 110,
        "rows": 35,
        "shell": "/bin/bash",
        "env": {
            "TERM": "xterm-256color"
        }
    },
    "player": {
        "theme": "monokai",
        "font_family": "JetBrains Mono, Fira Code, Menlo, monospace",
        "font_size": 16,
        "idle_time_limit": 3
    },
    "colors": {
        "prompt": "green",
        "title_border": "cyan",
        "title_text": "bold",
        "section_border": "cyan",
        "section_text": "bold",
        "subsection": "bold",
        "narration": "dim",
        "quote": "yellow",
        "error": "red",
        "output": "",
        "command": "",
        "syntax_highlight": True,
        "highlight_style": "monokai"
    },
    "timing": {
        "type_delay": 0.03,
        "cmd_pause": 0.8,
        "output_pause": 1.5,
        "section_pause": 2.0,
        "text_pause": 0.8,
        "end_pause": 2.0
    },
    "render": {
        "background": "#1a1b26",
        "foreground": "#c0caf5",
        "accent": "#7aa2f7",
        "font_family": "Inter, system-ui, sans-serif",
        "code_font": "JetBrains Mono, Fira Code, Cascadia Code, monospace",
        "max_width": "900px",
        "image_max_width": "100%",
        "image_border_radius": "8px",
        "image_shadow": True,
        "video_autoplay": False,
        "video_controls": True,
        "video_loop": False
    },
    "headings": {
        "h1": {
            "style": "box",
            "clear": True,
            "width": 60,
            "align": "left",
            "border": "double",
            "padding": 1
        },
        "h2": {
            "style": "box",
            "clear": True,
            "width": "auto",
            "align": "center",
            "border": "single",
            "padding": 0
        },
        "h3": {
            "style": "text",
            "clear": False,
            "prefix": "",
            "suffix": "",
            "align": "left"
        }
    }
}


class Theme:
    """Holds resolved colors and timing from a theme config."""

    def __init__(self, config=None):
        cfg = _deep_merge(DEFAULT_THEME, config or {})

        # Terminal
        t = cfg["terminal"]
        self.cols = t["cols"]
        self.rows = t["rows"]
        self.shell = t.get("shell", "/bin/bash")
        self.env = t.get("env", {})

        # Player (asciinema header metadata)
        p = cfg["player"]
        self.player_theme = p.get("theme", "")
        self.font_family = p.get("font_family", "")
        self.font_size = p.get("font_size", 0)
        self.idle_time_limit = p.get("idle_time_limit", 0)

        # Colors → resolved ANSI escapes
        c = cfg["colors"]
        self.prompt = _parse_color(c.get("prompt", "green"))
        self.title_border = _parse_color(c.get("title_border", "cyan"))
        self.title_text = _parse_color(c.get("title_text", "bold"))
        self.section_border = _parse_color(c.get("section_border", "cyan"))
        self.section_text = _parse_color(c.get("section_text", "bold"))
        self.subsection = _parse_color(c.get("subsection", "bold"))
        self.narration = _parse_color(c.get("narration", "dim"))
        self.quote = _parse_color(c.get("quote", "yellow"))
        self.error = _parse_color(c.get("error", "red"))
        self.output = _parse_color(c.get("output", ""))
        self.command = _parse_color(c.get("command", ""))
        self.syntax_highlight = c.get("syntax_highlight", True)
        self.highlight_style = c.get("highlight_style", "monokai")
        self.nc = "\033[0m"

        # Timing
        tm = cfg["timing"]
        self.type_delay = tm.get("type_delay", 0.03)
        self.cmd_pause = tm.get("cmd_pause", 0.8)
        self.output_pause = tm.get("output_pause", 1.5)
        self.section_pause = tm.get("section_pause", 2.0)
        self.text_pause = tm.get("text_pause", 0.8)
        self.end_pause = tm.get("end_pause", 2.0)

        # Heading formats
        h = cfg.get("headings", {})
        self.h1 = h.get("h1", DEFAULT_THEME["headings"]["h1"])
        self.h2 = h.get("h2", DEFAULT_THEME["headings"]["h2"])
        self.h3 = h.get("h3", DEFAULT_THEME["headings"]["h3"])

        # Render (HTML output) config
        r = cfg.get("render", {})
        dr = DEFAULT_THEME["render"]
        self.render_bg = r.get("background", dr["background"])
        self.render_fg = r.get("foreground", dr["foreground"])
        self.render_accent = r.get("accent", dr["accent"])
        self.render_font = r.get("font_family", dr["font_family"])
        self.render_code_font = r.get("code_font", dr["code_font"])
        self.render_max_width = r.get("max_width", dr["max_width"])
        self.render_image_max_width = r.get("image_max_width", dr["image_max_width"])
        self.render_image_border_radius = r.get("image_border_radius", dr["image_border_radius"])
        self.render_image_shadow = r.get("image_shadow", dr["image_shadow"])
        self.render_video_autoplay = r.get("video_autoplay", dr["video_autoplay"])
        self.render_video_controls = r.get("video_controls", dr["video_controls"])
        self.render_video_loop = r.get("video_loop", dr["video_loop"])


def _deep_merge(base, override):
    """Deep merge override into base (returns new dict)."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_theme(path):
    """Load a theme from a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def find_theme(input_path):
    """Auto-discover a theme file next to the input markdown."""
    # Look for: md2cast.json, .md2cast.json, md2cast-theme.json
    candidates = [
        os.path.join(os.path.dirname(input_path) or ".", "md2cast.json"),
        os.path.join(os.path.dirname(input_path) or ".", ".md2cast.json"),
        os.path.join(os.path.dirname(input_path) or ".", "md2cast-theme.json"),
        os.path.expanduser("~/.config/md2cast/theme.json"),
        os.path.expanduser("~/.md2cast.json"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


# ── Asciinema v2 cast writer ───────────────────────────────────────────────

class CastWriter:
    """Generates asciinema v2 .cast format."""

    def __init__(self, theme, title=""):
        self.theme = theme
        self.title = title
        self.events = []
        self.time = 0.0

    def _emit(self, text):
        """Emit an output event at the current time."""
        self.events.append([round(self.time, 4), "o", text])

    def pause(self, seconds):
        """Advance time without output."""
        self.time += seconds

    def write(self, text):
        """Write text to terminal instantly."""
        self._emit(text)

    def write_line(self, text=""):
        """Write a line to terminal."""
        self._emit(text + "\r\n")

    def type_text(self, text, delay=None):
        """Type text character by character."""
        delay = delay or self.theme.type_delay
        for ch in text:
            self._emit(ch)
            self.time += delay

    def clear(self):
        """Clear screen."""
        self._emit("\033[2J\033[H")

    def save(self, path):
        """Write the .cast file."""
        t = self.theme
        header = {
            "version": 2,
            "width": t.cols,
            "height": t.rows,
        }
        if self.title:
            header["title"] = self.title
        header["timestamp"] = int(time.time())

        # Standard asciinema v2 fields
        if t.env:
            header["env"] = dict(t.env)
        if t.idle_time_limit:
            header["idle_time_limit"] = t.idle_time_limit

        # Player metadata (used by asciinema web player embeds, ignored by agg)
        if t.player_theme:
            header["env"]["THEME"] = t.player_theme
        if t.font_family:
            header.setdefault("env", {})["FONT_FAMILY"] = t.font_family
        if t.font_size:
            header.setdefault("env", {})["FONT_SIZE"] = str(t.font_size)

        with open(path, "w") as f:
            f.write(json.dumps(header) + "\n")
            for event in self.events:
                f.write(json.dumps(event) + "\n")


# ── Markdown parser ────────────────────────────────────────────────────────

class Block:
    """A parsed markdown block."""
    def __init__(self, kind, content, level=0, lang="", directives=None):
        self.kind = kind        # heading, text, code, output, quote, hr, pause, skip
        self.content = content  # raw text content
        self.level = level      # heading level (1, 2, 3)
        self.lang = lang        # code block language
        self.directives = directives or {}  # per-block overrides from <!-- --> comments


def parse_markdown(text):
    """Parse markdown into a list of Blocks."""
    blocks = []
    lines = text.split("\n")
    i = 0
    pending_directives = {}  # accumulate directives for the next block

    while i < len(lines):
        line = lines[i]

        # HTML comment directives: <!-- pause 3 -->, <!-- skip -->, etc.
        pause_match = re.match(r'^\s*<!--\s*pause\s+(\d+(?:\.\d+)?)\s*-->\s*$', line)
        if pause_match:
            blocks.append(Block("pause", pause_match.group(1)))
            i += 1
            continue

        if re.match(r'^\s*<!--\s*skip\s*-->\s*$', line):
            i += 1
            if i < len(lines) and lines[i].startswith("```"):
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    i += 1
                i += 1
            continue

        if re.match(r'^\s*<!--\s*clear\s*-->\s*$', line):
            blocks.append(Block("hr", ""))
            i += 1
            continue

        if re.match(r'^\s*<!--\s*browser\s*-->\s*$', line):
            pending_directives["browser"] = True
            i += 1
            continue

        if re.match(r'^\s*<!--\s*gui\s*-->\s*$', line):
            pending_directives["gui"] = True
            i += 1
            continue

        if re.match(r'^\s*<!--\s*exec\s*-->\s*$', line):
            pending_directives["exec"] = True
            i += 1
            continue

        if re.match(r'^\s*<!--\s*no-exec\s*-->\s*$', line):
            pending_directives["no-exec"] = True
            i += 1
            continue

        if re.match(r'^\s*<!--\s*output\s*-->\s*$', line):
            pending_directives["output"] = True
            i += 1
            continue

        if re.match(r'^\s*<!--\s*view-exec\s*-->\s*$', line):
            pending_directives["view-exec"] = True
            i += 1
            continue

        td_match = re.match(r'^\s*<!--\s*type-delay\s+(\d+(?:\.\d+)?)\s*-->\s*$', line)
        if td_match:
            pending_directives["type-delay"] = float(td_match.group(1))
            i += 1
            continue

        prompt_match = re.match(r'^\s*<!--\s*prompt\s+(.+?)\s*-->\s*$', line)
        if prompt_match:
            pending_directives["prompt"] = prompt_match.group(1)
            i += 1
            continue

        # Fenced code block
        code_match = re.match(r'^```(\w*)\s*$', line)
        if code_match:
            lang = code_match.group(1).lower()
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```

            content = "\n".join(code_lines)
            dirs = pending_directives
            pending_directives = {}

            # <!-- gui --> and <!-- browser --> make special block types
            if dirs.get("gui"):
                blocks.append(Block("gui", content, lang=lang, directives=dirs))
            elif dirs.get("browser"):
                blocks.append(Block("browser", content, lang=lang, directives=dirs))
            # <!-- output --> forces bash blocks to be shown as static output
            elif dirs.get("output") and lang in ("bash", "sh", "shell", "console", "zsh"):
                blocks.append(Block("output", content, lang=lang, directives=dirs))
            elif lang in ("bash", "sh", "shell", "console", "zsh"):
                blocks.append(Block("code", content, lang=lang, directives=dirs))
            else:
                blocks.append(Block("output", content, lang=lang, directives=dirs))
            continue

        # Heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text_content = heading_match.group(2).strip()
            blocks.append(Block("heading", text_content, level=level))
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^---+\s*$', line) or re.match(r'^\*\*\*+\s*$', line):
            blocks.append(Block("hr", ""))
            i += 1
            continue

        # Image: ![alt](path)
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line)
        if img_match:
            alt = img_match.group(1)
            src = img_match.group(2)
            blocks.append(Block("image", src, directives={"alt": alt}))
            i += 1
            continue

        # Blockquote
        if line.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].startswith(">"):
                quote_lines.append(re.sub(r'^>\s?', '', lines[i]))
                i += 1
            content = "\n".join(quote_lines)
            blocks.append(Block("quote", content))
            continue

        # Regular text (paragraph)
        if line.strip():
            para_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith("#") \
                    and not lines[i].startswith("```") and not lines[i].startswith(">") \
                    and not re.match(r'^---+\s*$', lines[i]) \
                    and not re.match(r'^\s*<!--', lines[i]) \
                    and not re.match(r'^!\[', lines[i]):
                para_lines.append(lines[i])
                i += 1
            content = " ".join(para_lines)
            blocks.append(Block("text", content))
            continue

        # Blank line — skip
        i += 1

    return blocks


# ── Markdown text cleaning ─────────────────────────────────────────────────

def strip_md(text):
    """Strip markdown formatting for plain display."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'!\[.*?\]\(.+?\)', '', text)
    return text.strip()


def word_wrap(text, width=100):
    """Wrap text to fit terminal width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip() if current else word
        if len(test) <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ── Screencast renderer ───────────────────────────────────────────────────

class Renderer:
    """Renders parsed blocks into a CastWriter."""

    def __init__(self, cast, theme, execute=False, working_dir=None):
        self.cast = cast
        self.t = theme
        self.execute = execute
        self.working_dir = working_dir
        self.image_markers = []  # [(timestamp, image_path)] for GIF stitching

    def _render_heading_box(self, title, hcfg, color_border, color_text, subtitle=""):
        """Render a heading as a box with configurable border, width, alignment."""
        t = self.t
        title_clean = strip_md(title)
        sub_clean = strip_md(subtitle) if subtitle else ""

        border = hcfg.get("border", "double")
        w = hcfg.get("width", 60)
        if w == "auto":
            w = max(len(title_clean) + 4, len(sub_clean) + 4 if sub_clean else 0)
        pad = hcfg.get("padding", 1)
        align = hcfg.get("align", "left")

        # Border characters
        if border == "double":
            tl, tr, bl, br, h, v = "\u2554", "\u2557", "\u255a", "\u255d", "\u2550", "\u2551"
        elif border == "heavy":
            tl, tr, bl, br, h, v = "\u250f", "\u2513", "\u2517", "\u251b", "\u2501", "\u2503"
        elif border == "rounded":
            tl, tr, bl, br, h, v = "\u256d", "\u256e", "\u2570", "\u256f", "\u2500", "\u2502"
        else:  # single
            tl, tr, bl, br, h, v = "\u250c", "\u2510", "\u2514", "\u2518", "\u2500", "\u2502"

        bar = h * w

        def align_text(text, width):
            if align == "center":
                return text.center(width)
            elif align == "right":
                return text.rjust(width - 1) + " "
            return f"   {text:<{width-3}}"

        self.cast.write_line("")
        self.cast.write_line(f"  {color_border}{tl}{bar}{tr}{t.nc}")
        for _ in range(pad):
            self.cast.write_line(f"  {color_border}{v}{t.nc}{' ' * w}{color_border}{v}{t.nc}")
        self.cast.write_line(f"  {color_border}{v}{t.nc}{color_text}{align_text(title_clean, w)}{color_border}{v}{t.nc}")
        if sub_clean:
            self.cast.write_line(f"  {color_border}{v}{t.nc}{t.narration}{align_text(sub_clean, w)}{color_border}{v}{t.nc}")
        for _ in range(pad):
            self.cast.write_line(f"  {color_border}{v}{t.nc}{' ' * w}{color_border}{v}{t.nc}")
        self.cast.write_line(f"  {color_border}{bl}{bar}{br}{t.nc}")
        self.cast.write_line("")

    def _render_heading_line(self, title, hcfg, color_border, color_text):
        """Render a heading as a decorated line."""
        t = self.t
        title_clean = strip_md(title)
        prefix = hcfg.get("prefix", "\u2500\u2500 ")
        suffix = hcfg.get("suffix", " " + "\u2500" * 30)
        align = hcfg.get("align", "left")

        if align == "center":
            fill = "\u2500" * 10
            line = f"  {color_border}{fill} {color_text}{title_clean}{t.nc} {color_border}{fill}{t.nc}"
        else:
            line = f"  {color_border}{prefix}{color_text}{title_clean}{t.nc}{color_border}{suffix}{t.nc}"
        self.cast.write_line("")
        self.cast.write_line(line)
        self.cast.write_line("")

    def _render_heading_text(self, title, hcfg, color_text):
        """Render a heading as styled text."""
        t = self.t
        title_clean = strip_md(title)
        prefix = hcfg.get("prefix", "")
        suffix = hcfg.get("suffix", "")
        self.cast.write_line("")
        self.cast.write_line(f"  {color_text}{prefix}{title_clean}{suffix}{t.nc}")
        self.cast.write_line("")

    def _render_heading(self, title, hcfg, color_border, color_text, subtitle=""):
        """Route to the right heading renderer based on style."""
        t = self.t
        if hcfg.get("clear", False):
            self.cast.clear()
            self.cast.pause(0.3)

        style = hcfg.get("style", "box")
        if style == "box":
            self._render_heading_box(title, hcfg, color_border, color_text, subtitle)
        elif style == "line":
            self._render_heading_line(title, hcfg, color_border, color_text)
        elif style == "text":
            self._render_heading_text(title, hcfg, color_text)
        elif style == "none":
            pass
        else:
            self._render_heading_box(title, hcfg, color_border, color_text, subtitle)

        self.cast.pause(t.section_pause if hcfg.get("clear", False) else 0.8)

    def render_title_card(self, title, subtitle=""):
        """Render a # heading (h1)."""
        self._render_heading(title, self.t.h1, self.t.title_border, self.t.title_text, subtitle)

    def render_section(self, title):
        """Render a ## heading (h2)."""
        self._render_heading(title, self.t.h2, self.t.section_border, self.t.section_text)

    def render_subsection(self, title):
        """Render a ### heading (h3)."""
        self._render_heading(title, self.t.h3, self.t.subsection, self.t.subsection)

    def render_text(self, text):
        """Render narrated text as dimmed comments."""
        t = self.t
        clean = strip_md(text)
        lines = word_wrap(clean, t.cols - 10)
        self.cast.write_line("")
        for line in lines:
            self.cast.write_line(f"  {t.narration}# {line}{t.nc}")
        self.cast.pause(t.text_pause + len(lines) * 0.3)
        self.cast.write_line("")

    def render_quote(self, text):
        """Render a blockquote as a highlighted note."""
        t = self.t
        clean = strip_md(text)
        lines = word_wrap(clean, t.cols - 15)
        self.cast.write_line("")
        for line in lines:
            self.cast.write_line(f"  {t.quote}\u2502 {line}{t.nc}")
        self.cast.pause(t.text_pause + len(lines) * 0.4)
        self.cast.write_line("")

    def render_image(self, src, alt=""):
        """Render an image reference. Records timestamp for GIF stitching."""
        t = self.t
        ext = os.path.splitext(src)[1].lower()
        if ext in (".mp4", ".webm", ".mov", ".avi"):
            icon = "\u25b6"  # ▶
            label = "Video"
        elif ext in (".gif",):
            icon = "\U0001f3ac"  # 🎬
            label = "GIF"
        else:
            icon = "\U0001f4f7"  # 📷
            label = "Image"
        display = alt if alt else os.path.basename(src)

        # Record position for GIF stitching (image inserted after this narration)
        self.image_markers.append({"time": self.cast.time, "src": src, "alt": alt})

        self.cast.write_line("")
        self.cast.write_line(f"  {t.narration}{icon} {label}: {display}{t.nc}")
        self.cast.write_line(f"  {t.narration}   [{src}]{t.nc}")
        self.cast.pause(1.5)
        self.cast.write_line("")

    def render_command(self, command, directives=None):
        """Type and optionally execute a bash command.

        Directives (from HTML comments):
          exec       — execute this block even without global --execute
          no-exec    — skip execution even with global --execute
          type-delay — override typing speed for this block
          prompt     — override prompt character (e.g., "#" for root)
        """
        t = self.t
        dirs = directives or {}
        do_exec = self.execute
        if dirs.get("exec"):
            do_exec = True
        if dirs.get("no-exec"):
            do_exec = False
        type_delay = dirs.get("type-delay", t.type_delay)
        prompt_char = dirs.get("prompt", "$")

        for line in command.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                self.cast.write_line(f"  {t.narration}{line}{t.nc}")
                self.cast.pause(0.3)
                continue

            # Type the command with prompt
            self.cast.write(f"{t.prompt}{prompt_char} {t.nc}")
            if t.command:
                self.cast.write(t.command)
            self.cast.type_text(line, delay=type_delay)
            if t.command:
                self.cast.write(t.nc)

            # Repaint line with syntax highlighting after typing
            if t.syntax_highlight and _HAS_PYGMENTS:
                highlighted = highlight_code(line, lang="bash", style=t.highlight_style)
                if highlighted != line:
                    # Move cursor to start of command (after prompt), overwrite
                    prompt_len = len(prompt_char) + 2  # "$ " or "# "
                    self.cast.write(f"\r{t.prompt}{prompt_char} {t.nc}{highlighted}{t.nc}")

            self.cast.pause(t.cmd_pause)
            self.cast.write_line("")

            if do_exec:
                try:
                    result = subprocess.run(
                        line, shell=True, capture_output=True, text=True,
                        timeout=30, cwd=self.working_dir
                    )
                    output = result.stdout
                    if result.stderr:
                        output += result.stderr
                    if output.strip():
                        for out_line in output.rstrip().split("\n"):
                            if t.output:
                                self.cast.write_line(f"{t.output}{out_line}{t.nc}")
                            else:
                                self.cast.write_line(out_line)
                except subprocess.TimeoutExpired:
                    self.cast.write_line(f"{t.error}(command timed out){t.nc}")
                except Exception as e:
                    self.cast.write_line(f"{t.error}(error: {e}){t.nc}")

            self.cast.pause(t.output_pause)

    def render_view_exec(self, command, directives=None):
        """Two-phase display: show all commands as a static preview, then execute each one.

        Phase 1: Display the entire block as static code (dimmed, no prompt)
        Phase 2: Re-run each command with prompt, typing, and real execution
        """
        t = self.t
        dirs = directives or {}
        type_delay = dirs.get("type-delay", t.type_delay)
        prompt_char = dirs.get("prompt", "$")

        lines = [l.strip() for l in command.strip().split("\n")]
        cmd_lines = [l for l in lines if l and not l.startswith("#")]

        # Phase 1: Show all commands as a static preview
        self.cast.write_line("")
        self.cast.write_line(f"  {t.narration}# Commands to run:{t.nc}")
        self.cast.write_line(f"  {t.section_border}\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500{t.nc}")
        for line in cmd_lines:
            self.cast.write_line(f"  {t.narration}  {line}{t.nc}")
        self.cast.write_line(f"  {t.section_border}\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500{t.nc}")
        self.cast.pause(t.section_pause)
        self.cast.write_line("")

        # Phase 2: Execute each command
        for line in lines:
            if not line or line.startswith("#"):
                self.cast.write_line(f"  {t.narration}{line}{t.nc}")
                self.cast.pause(0.3)
                continue

            self.cast.write(f"{t.prompt}{prompt_char} {t.nc}")
            if t.command:
                self.cast.write(t.command)
            self.cast.type_text(line, delay=type_delay)
            if t.command:
                self.cast.write(t.nc)
            self.cast.pause(t.cmd_pause)
            self.cast.write_line("")

            try:
                result = subprocess.run(
                    line, shell=True, capture_output=True, text=True,
                    timeout=30, cwd=self.working_dir
                )
                output = result.stdout
                if result.stderr:
                    output += result.stderr
                if output.strip():
                    for out_line in output.rstrip().split("\n"):
                        if t.output:
                            self.cast.write_line(f"{t.output}{out_line}{t.nc}")
                        else:
                            self.cast.write_line(out_line)
            except subprocess.TimeoutExpired:
                self.cast.write_line(f"{t.error}(command timed out){t.nc}")
            except Exception as e:
                self.cast.write_line(f"{t.error}(error: {e}){t.nc}")

            self.cast.pause(t.output_pause)

    def render_output(self, text, lang=""):
        """Show output text (not typed, shown at once), with optional syntax highlighting."""
        t = self.t
        if not text.strip():
            return

        # Apply syntax highlighting if enabled and language is known
        if t.syntax_highlight and lang:
            highlighted = highlight_code(text, lang=lang, style=t.highlight_style)
            for line in highlighted.split("\n"):
                self.cast.write_line(line)
        else:
            for line in text.split("\n"):
                if t.output:
                    self.cast.write_line(f"{t.output}{line}{t.nc}")
                else:
                    self.cast.write_line(line)
        self.cast.pause(t.output_pause)

    def render_blocks(self, blocks):
        """Render a list of blocks."""
        i = 0
        while i < len(blocks):
            block = blocks[i]

            if block.kind == "heading":
                if block.level == 1:
                    subtitle = ""
                    if i + 1 < len(blocks) and blocks[i + 1].kind in ("text", "quote"):
                        subtitle = blocks[i + 1].content
                    self.render_title_card(block.content, subtitle)
                elif block.level == 2:
                    self.render_section(block.content)
                else:
                    self.render_subsection(block.content)

            elif block.kind == "text":
                if i > 0 and blocks[i - 1].kind == "heading" and blocks[i - 1].level == 1:
                    pass  # already shown as subtitle
                else:
                    self.render_text(block.content)

            elif block.kind == "code":
                if block.directives.get("view-exec"):
                    self.render_view_exec(block.content, directives=block.directives)
                else:
                    self.render_command(block.content, directives=block.directives)

            elif block.kind == "output":
                self.render_output(block.content, lang=block.lang)

            elif block.kind == "quote":
                if i > 0 and blocks[i - 1].kind == "heading" and blocks[i - 1].level == 1:
                    pass
                else:
                    self.render_quote(block.content)

            elif block.kind == "image":
                self.render_image(block.content, block.directives.get("alt", ""))

            elif block.kind == "hr":
                self.cast.clear()
                self.cast.pause(0.5)

            elif block.kind == "pause":
                self.cast.pause(float(block.content))

            i += 1

        # End card
        self.cast.write_line("")
        self.cast.pause(self.t.end_pause)


# ── Section splitting ──────────────────────────────────────────────────────

def split_sections(blocks):
    """Split blocks into sections at ## headings."""
    sections = []
    current = []
    current_title = None

    for block in blocks:
        if block.kind == "heading" and block.level <= 2:
            if current:
                sections.append((current_title or "untitled", current))
            current = [block]
            current_title = block.content
        else:
            current.append(block)

    if current:
        sections.append((current_title or "untitled", current))

    return sections


def list_sections(blocks):
    """Print a numbered list of sections."""
    sections = split_sections(blocks)
    for i, (title, section_blocks) in enumerate(sections, 1):
        level = section_blocks[0].level if section_blocks and section_blocks[0].kind == "heading" else 0
        prefix = "#" * level if level else " "
        cmd_count = sum(1 for b in section_blocks if b.kind == "code")
        print(f"  {i:3d}  {prefix} {strip_md(title):<50s}  ({cmd_count} commands)")


# ── Browser capture (Pro) ──────────────────────────────────────────────────

def _pro_required(feature):
    """Print upgrade message for Pro features."""
    print(f"\n  {feature} requires md2cast Pro.", file=sys.stderr)
    print(f"  Upgrade: {_PRO_URL}\n", file=sys.stderr)

def parse_browser_steps(text):
    """Parse a browser steps block into a list of action dicts.

    Supported actions:
      open <url>                    — navigate to URL
      wait <selector> [timeout]     — wait for element (default 10s)
      click <selector>              — click element
      type <selector> <text>        — type into input field
      scroll <direction> [amount]   — scroll down/up (pixels, default 300)
      screenshot [name]             — capture screenshot
      sleep <seconds>               — wait N seconds
      video start [name]            — start recording video
      video stop                    — stop recording video
      hover <selector>              — hover over element
      select <selector> <value>     — select dropdown option
      resize <width> <height>       — resize viewport
    """
    steps = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(None, 1)
        action = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if action == "open":
            steps.append({"action": "open", "url": args.strip()})
        elif action == "wait":
            wait_parts = args.split(None, 1)
            steps.append({
                "action": "wait",
                "selector": wait_parts[0],
                "timeout": float(wait_parts[1]) * 1000 if len(wait_parts) > 1 else 10000
            })
        elif action == "click":
            steps.append({"action": "click", "selector": args.strip()})
        elif action == "type":
            # type "#selector" "text value"
            type_match = re.match(r'^(["\']?)(.+?)\1\s+(["\']?)(.+?)\3$', args)
            if type_match:
                steps.append({"action": "type", "selector": type_match.group(2),
                              "text": type_match.group(4)})
            else:
                # type selector text
                type_parts = args.split(None, 1)
                steps.append({"action": "type", "selector": type_parts[0],
                              "text": type_parts[1] if len(type_parts) > 1 else ""})
        elif action == "scroll":
            scroll_parts = args.split()
            direction = scroll_parts[0] if scroll_parts else "down"
            amount = int(scroll_parts[1]) if len(scroll_parts) > 1 else 300
            steps.append({"action": "scroll", "direction": direction, "amount": amount})
        elif action == "screenshot":
            steps.append({"action": "screenshot", "name": args.strip() or None})
        elif action == "sleep":
            steps.append({"action": "sleep", "seconds": float(args)})
        elif action == "video":
            video_parts = args.split(None, 1)
            if video_parts and video_parts[0] == "stop":
                steps.append({"action": "video_stop"})
            else:
                name = video_parts[1] if len(video_parts) > 1 else None
                steps.append({"action": "video_start", "name": name})
        elif action == "hover":
            steps.append({"action": "hover", "selector": args.strip()})
        elif action == "select":
            sel_parts = args.split(None, 1)
            steps.append({"action": "select", "selector": sel_parts[0],
                          "value": sel_parts[1] if len(sel_parts) > 1 else ""})
        elif action == "resize":
            dims = args.split()
            steps.append({"action": "resize",
                          "width": int(dims[0]) if dims else 1280,
                          "height": int(dims[1]) if len(dims) > 1 else 720})
        else:
            steps.append({"action": "unknown", "raw": line})

    return steps



def run_browser_steps(steps, assets_dir, name_prefix="browser",
                      viewport_width=1280, viewport_height=720):
    """Browser capture requires md2cast Pro."""
    _pro_required("Browser capture (<!-- browser -->)")
    return []

def video_to_gif(video_path, gif_path=None, fps=10, width=800):
    """Video-to-GIF conversion — Pro only."""
    _pro_required("Video-to-GIF conversion")
    return None


# ── GUI capture (Pro) ─────────────────────────────────────────────────────

def parse_gui_steps(text):
    """Parse a GUI steps block into a list of action dicts.

    Supported actions:
      launch <command>                        — launch an application
      focus <window-title>                    — focus a window by title
      click <x> <y>                          — click at screen coordinates
      type <text>                             — type text via keyboard
      key <combo>                             — press key combo (e.g., ctrl+s, alt+F4)
      move <x> <y>                           — move mouse to coordinates
      drag <x1> <y1> <x2> <y2>              — drag from one point to another
      screenshot [name]                       — capture full screen
      screenshot --region <x>,<y> <w>x<h> [name]  — capture a region
      screenshot --window <title> [name]      — capture a specific window
      window-screenshot <title> [name]        — capture specific window (alias)
      sleep <seconds>                         — wait N seconds
    """
    steps = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(None, 1)
        action = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if action == "launch":
            steps.append({"action": "launch", "command": args.strip()})
        elif action == "focus":
            steps.append({"action": "focus", "title": args.strip()})
        elif action == "click":
            coords = args.split()
            steps.append({"action": "click",
                          "x": int(coords[0]), "y": int(coords[1])})
        elif action == "type":
            # Strip surrounding quotes if present
            text_val = args.strip().strip('"').strip("'")
            steps.append({"action": "type", "text": text_val})
        elif action == "key":
            steps.append({"action": "key", "key": args.strip()})
        elif action == "move":
            coords = args.split()
            steps.append({"action": "move",
                          "x": int(coords[0]), "y": int(coords[1])})
        elif action == "drag":
            coords = args.split()
            steps.append({"action": "drag",
                          "x1": int(coords[0]), "y1": int(coords[1]),
                          "x2": int(coords[2]), "y2": int(coords[3])})
        elif action == "screenshot":
            args_parts = args.split()
            if args_parts and args_parts[0] == "--region":
                # screenshot --region x,y wxh [name]
                region_str = args_parts[1] if len(args_parts) > 1 else "0,0"
                size_str = args_parts[2] if len(args_parts) > 2 else "800x600"
                name = args_parts[3] if len(args_parts) > 3 else None
                rx, ry = [int(v) for v in region_str.split(",")]
                rw, rh = [int(v) for v in size_str.lower().split("x")]
                steps.append({"action": "screenshot", "name": name,
                              "region": (rx, ry, rw, rh)})
            elif args_parts and args_parts[0] == "--window":
                # screenshot --window "Title" [name]
                rest = args[len("--window"):].strip()
                # Parse quoted title or single word
                if rest.startswith('"'):
                    end_q = rest.index('"', 1)
                    title = rest[1:end_q]
                    name = rest[end_q+1:].strip() or None
                else:
                    ws = rest.split(None, 1)
                    title = ws[0]
                    name = ws[1].strip() if len(ws) > 1 else None
                steps.append({"action": "window-screenshot", "title": title, "name": name})
            else:
                steps.append({"action": "screenshot", "name": args.strip() or None})
        elif action == "window-screenshot":
            ws_parts = args.split(None, 1)
            title = ws_parts[0] if ws_parts else ""
            name = ws_parts[1] if len(ws_parts) > 1 else None
            steps.append({"action": "window-screenshot", "title": title, "name": name})
        elif action == "sleep":
            steps.append({"action": "sleep", "seconds": float(args)})
        else:
            steps.append({"action": "unknown", "raw": line})

    return steps




def run_gui_steps(steps, assets_dir, name_prefix="gui"):
    """GUI capture requires md2cast Pro."""
    _pro_required("GUI capture (<!-- gui -->)")
    return []


# ── CLI ────────────────────────────────────────────────────────────────────

def cast_to_gif(cast_path):
    """Convert a .cast file to .gif using agg."""
    gif_path = os.path.splitext(cast_path)[0] + ".gif"
    try:
        result = subprocess.run(
            ["agg", cast_path, gif_path],
            capture_output=True, text=True, timeout=120
        )
        ok = "\033[0;32m[OK]\033[0m"
        err = "\033[0;31m[ERR]\033[0m"
        if result.returncode == 0:
            print(f"  {ok} {gif_path}")
        else:
            print(f"  {err} agg failed: {result.stderr.strip()}", file=sys.stderr)
    except FileNotFoundError:
        print("  Error: agg not found. Install from https://github.com/asciinema/agg/releases",
              file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("  Error: agg timed out", file=sys.stderr)


def image_to_gif_frame(image_path, width=800, bg_color=(13, 17, 23)):
    """Convert an image to a GIF-compatible frame, resized to fit terminal width.

    Returns a PIL Image or None if Pillow not available / file not found.
    """
    if not _HAS_PIL:
        return None
    try:
        img = _PILImage.open(image_path)
    except (FileNotFoundError, OSError):
        return None

    # Handle animated GIFs — take first frame
    if hasattr(img, 'n_frames') and img.n_frames > 1:
        img.seek(0)
    img = img.convert("RGBA")

    # Resize to fit width, maintaining aspect ratio
    ratio = width / img.width
    new_h = int(img.height * ratio)
    img = img.resize((width, new_h), _PILImage.LANCZOS)

    # Place on dark background with padding
    pad = 20
    canvas = _PILImage.new("RGBA", (width, new_h + pad * 2), bg_color + (255,))
    canvas.paste(img, (0, pad), img)
    return canvas.convert("RGB")


def stitch_gif_with_images(gif_path, image_insertions, duration_ms=2000):
    """Insert image frames into an existing GIF at specific positions.

    image_insertions: list of (position_index, PIL Image frame)
    position_index: frame number after which to insert the image

    Modifies the GIF in place.
    """
    if not _HAS_PIL or not image_insertions:
        return

    try:
        base_gif = _PILImage.open(gif_path)
    except (FileNotFoundError, OSError):
        return

    # Extract all frames from the base GIF
    frames = []
    durations = []
    try:
        while True:
            frames.append(base_gif.copy().convert("RGB"))
            durations.append(base_gif.info.get("duration", 100))
            base_gif.seek(base_gif.tell() + 1)
    except EOFError:
        pass

    if not frames:
        return

    # Get target size from first frame
    target_size = frames[0].size

    # Build insertion map: position → list of image frames
    inserts = {}
    for pos, img_frame in image_insertions:
        pos = min(pos, len(frames))
        if pos not in inserts:
            inserts[pos] = []
        # Resize image frame to match GIF dimensions
        resized = img_frame.resize(target_size, _PILImage.LANCZOS)
        inserts[pos].append(resized)

    # Rebuild frames list with insertions
    new_frames = []
    new_durations = []
    for i, (frame, dur) in enumerate(zip(frames, durations)):
        new_frames.append(frame)
        new_durations.append(dur)
        if i in inserts:
            for img_frame in inserts[i]:
                new_frames.append(img_frame)
                new_durations.append(duration_ms)

    # Check for insertions at the end
    if len(frames) in inserts:
        for img_frame in inserts[len(frames)]:
            new_frames.append(img_frame)
            new_durations.append(duration_ms)

    # Save
    new_frames[0].save(
        gif_path,
        save_all=True,
        append_images=new_frames[1:],
        duration=new_durations,
        loop=0,
        optimize=False
    )


def _stitch_images_into_gif(gif_path, image_markers, working_dir=None):
    """Stitch real images into a GIF at positions where image narration appears.

    image_markers: list of {"time": float, "src": str, "alt": str}
    """
    ok = "\033[0;32m[OK]\033[0m"

    # Load image frames
    insertions = []
    for marker in image_markers:
        src = marker["src"]
        # Resolve relative paths
        if working_dir and not os.path.isabs(src):
            src = os.path.join(working_dir, src)

        frame = image_to_gif_frame(src)
        if frame is None:
            continue

        # Estimate frame position from timestamp
        # agg generates ~10 fps, so position ≈ time * 10
        frame_pos = int(marker["time"] * 10)
        insertions.append((frame_pos, frame))

    if insertions:
        stitch_gif_with_images(gif_path, insertions, duration_ms=2500)
        print(f"  {ok} Stitched {len(insertions)} image(s) into {gif_path}")


def _estimate_block_rows(code_content, lang, dirs, execute=False):
    """Estimate how many terminal rows a block needs.

    Returns a row count sized to the content with padding,
    so short blocks don't render with 35 rows of blank space.
    """
    lines = code_content.strip().split("\n")
    is_command = lang in ("bash", "sh", "shell", "console", "zsh")

    if is_command:
        # Each command gets: prompt line + potential output
        cmd_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        # Estimate: 1 line per command, 2 lines output each if executing, plus prompt spacing
        if execute or dirs.get("exec"):
            row_count = len(lines) + len(cmd_lines) * 2 + 2
        else:
            row_count = len(lines) + 2
    else:
        # Static output: just the lines
        row_count = len(lines) + 2

    # Add padding: 3 top + 2 bottom
    return row_count + 5


def _generate_block_cast(code_content, lang, dirs, theme, assets_dir, index,
                         section_name, execute=False, working_dir=None):
    """Generate a .cast file for a single code block. Returns (cast_name, cast_path)."""
    slug = slugify(section_name)
    cast_name = f"{index:02d}-{slug}"
    cast_path = os.path.join(assets_dir, f"{cast_name}.cast")

    is_command = lang in ("bash", "sh", "shell", "console", "zsh")
    force_output = dirs.get("output", False)
    is_view_exec = dirs.get("view-exec", False)

    # Auto-size: use smaller row count for short blocks
    block_rows = _estimate_block_rows(code_content, lang, dirs, execute)
    block_rows = min(block_rows, theme.rows)  # never exceed theme max

    # Create a copy of the theme with adjusted rows for this block
    block_theme = _theme_with_rows(theme, block_rows)

    cast = CastWriter(block_theme, title=strip_md(section_name))
    renderer = Renderer(cast, block_theme, execute=execute, working_dir=working_dir)
    cast.pause(0.3)

    if is_view_exec and is_command:
        renderer.render_view_exec(code_content, directives=dirs)
    elif is_command and not force_output:
        renderer.render_command(code_content, directives=dirs)
    else:
        renderer.render_output(code_content, lang=lang)

    # Watermark: dim "md2cast" at bottom-right of last frame
    watermark = "md2cast"
    pad = block_theme.cols - len(watermark) - 1
    cast.write(f"\033[{block_rows};1H")  # move to last row
    cast.write(f"\033[2m{' ' * pad}{watermark}\033[0m")

    cast.pause(block_theme.end_pause)
    cast.save(cast_path)
    return cast_name, cast_path


def _theme_with_rows(theme, rows):
    """Create a shallow copy of a theme with a different row count."""
    import copy
    t = copy.copy(theme)
    t.rows = rows
    return t


def _walk_markdown_blocks(md_text):
    """Walk markdown line by line, yielding structured events.

    Yields tuples of:
      ("line", line_text)
      ("directive", key, value, line_text)
      ("skip", [lines including skip comment and code block])
      ("code", lang, code_lines, original_lines, directives)
    """
    lines = md_text.split("\n")
    pending_directives = {}
    i = 0

    while i < len(lines):
        line = lines[i]

        # Directives
        directive_match = re.match(
            r'^\s*<!--\s*(exec|no-exec|output|view-exec|clear|browser|gui)\s*-->\s*$', line)
        td_match = re.match(r'^\s*<!--\s*type-delay\s+(\d+(?:\.\d+)?)\s*-->\s*$', line)
        prompt_match = re.match(r'^\s*<!--\s*prompt\s+(.+?)\s*-->\s*$', line)
        skip_match = re.match(r'^\s*<!--\s*skip\s*-->\s*$', line)

        if directive_match:
            pending_directives[directive_match.group(1)] = True
            yield ("directive", directive_match.group(1), True, line)
            i += 1
            continue
        if td_match:
            pending_directives["type-delay"] = float(td_match.group(1))
            yield ("directive", "type-delay", float(td_match.group(1)), line)
            i += 1
            continue
        if prompt_match:
            pending_directives["prompt"] = prompt_match.group(1)
            yield ("directive", "prompt", prompt_match.group(1), line)
            i += 1
            continue

        # Skip — consume the next code block too
        if skip_match:
            skip_lines = [line]
            i += 1
            if i < len(lines) and lines[i].startswith("```"):
                skip_lines.append(lines[i])
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    skip_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    skip_lines.append(lines[i])
                    i += 1
            yield ("skip", skip_lines)
            continue

        # Fenced code block
        code_match = re.match(r'^```(\w*)\s*$', line)
        if code_match:
            lang = code_match.group(1).lower()
            original_lines = [line]
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                original_lines.append(lines[i])
                i += 1
            if i < len(lines):
                original_lines.append(lines[i])
                i += 1

            dirs = pending_directives
            pending_directives = {}
            if dirs.get("gui"):
                yield ("gui", lang, code_lines, original_lines, dirs)
            elif dirs.get("browser"):
                yield ("browser", lang, code_lines, original_lines, dirs)
            else:
                yield ("code", lang, code_lines, original_lines, dirs)
            continue

        yield ("line", line)
        i += 1


def render_markdown(md_text, theme, assets_dir, execute=False, working_dir=None):
    """Generate a new Markdown with GIF screencasts embedded above code blocks.

    Returns the new Markdown text and the number of GIFs generated.
    """
    os.makedirs(assets_dir, exist_ok=True)
    output_lines = []
    block_count = 0
    current_section = "intro"
    ok = "\033[0;32m[OK]\033[0m"
    err = "\033[0;31m[ERR]\033[0m"

    for event in _walk_markdown_blocks(md_text):
        if event[0] == "line":
            line = event[1]
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                current_section = strip_md(heading_match.group(2))
            output_lines.append(line)

        elif event[0] == "directive":
            output_lines.append(event[3])

        elif event[0] == "skip":
            output_lines.extend(event[1])

        elif event[0] == "code":
            _, lang, code_lines, original_lines, dirs = event
            code_content = "\n".join(code_lines)
            block_count += 1
            if not _check_block_limit(block_count):
                output_lines.extend(original_lines)
                continue

            cast_name, cast_path = _generate_block_cast(
                code_content, lang, dirs, theme, assets_dir,
                block_count, current_section, execute, working_dir)

            # Convert to GIF
            gif_path = os.path.splitext(cast_path)[0] + ".gif"
            gif_ok = False
            try:
                result = subprocess.run(
                    ["agg", cast_path, gif_path],
                    capture_output=True, text=True, timeout=120
                )
                gif_ok = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            if gif_ok:
                print(f"  {ok} {gif_path}")
                rel_gif = os.path.join(os.path.basename(assets_dir), f"{cast_name}.gif")
                alt_text = strip_md(current_section)
                output_lines.append(f"![{alt_text}]({rel_gif})")
                output_lines.append("")
            else:
                print(f"  {err} Failed to generate {gif_path}", file=sys.stderr)

            output_lines.extend(original_lines)

        elif event[0] == "browser":
            _, lang, code_lines, original_lines, dirs = event
            code_content = "\n".join(code_lines)
            block_count += 1
            slug = slugify(current_section)
            name_prefix = f"{block_count:02d}-{slug}"

            steps = parse_browser_steps(code_content)
            browser_assets = run_browser_steps(steps, assets_dir, name_prefix=name_prefix)

            alt_text = strip_md(current_section)
            for asset in browser_assets:
                rel_path = os.path.join(os.path.basename(assets_dir),
                                        os.path.basename(asset["path"]))
                if asset["type"] == "screenshot":
                    output_lines.append(f"![{alt_text}]({rel_path})")
                    output_lines.append("")
                elif asset["type"] == "video":
                    gif_path = video_to_gif(asset["path"])
                    if gif_path:
                        rel_gif = os.path.join(os.path.basename(assets_dir),
                                               os.path.basename(gif_path))
                        output_lines.append(f"![{alt_text}]({rel_gif})")
                        output_lines.append("")

        elif event[0] == "gui":
            _, lang, code_lines, original_lines, dirs = event
            code_content = "\n".join(code_lines)
            block_count += 1
            slug = slugify(current_section)
            name_prefix = f"{block_count:02d}-{slug}"

            steps = parse_gui_steps(code_content)
            gui_assets = run_gui_steps(steps, assets_dir, name_prefix=name_prefix)

            alt_text = strip_md(current_section)
            for asset in gui_assets:
                rel_path = os.path.join(os.path.basename(assets_dir),
                                        os.path.basename(asset["path"]))
                if asset["type"] == "screenshot":
                    output_lines.append(f"![{alt_text}]({rel_path})")
                    output_lines.append("")

    output_lines.append("")
    output_lines.append(
        '<p align="center"><sub>Made with <a href="https://github.com/markamo/md2cast">md2cast</a></sub></p>')
    output_lines.append("")

    generated = min(block_count, FREE_MAX_BLOCKS) if FREE_TIER else block_count
    return "\n".join(output_lines), generated


def render_html(md_text, theme, assets_dir, execute=False, working_dir=None, embed=False):
    """Generate an HTML page with asciinema players.

    When embed=True, cast data is base64-encoded inline (single-file, no server needed).
    When embed=False, cast files are in assets_dir (needs HTTP server for file:// access).

    Returns the HTML string and the number of players generated.
    """
    os.makedirs(assets_dir, exist_ok=True)
    block_count = 0
    current_section = "intro"
    page_title = ""
    sections_html = []
    ok = "\033[0;32m[OK]\033[0m"

    for event in _walk_markdown_blocks(md_text):
        if event[0] == "line":
            line = event[1]
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = strip_md(heading_match.group(2))
                current_section = title
                if level == 1 and not page_title:
                    page_title = title
                sections_html.append(f"<h{level}>{_html_escape(title)}</h{level}>")
            elif line.startswith(">"):
                text = strip_md(re.sub(r'^>\s?', '', line))
                sections_html.append(f'<blockquote><p>{_html_escape(text)}</p></blockquote>')
            elif re.match(r'^---+\s*$', line) or re.match(r'^\*\*\*+\s*$', line):
                sections_html.append("<hr>")
            else:
                # Image: ![alt](src)
                img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line)
                if img_match:
                    alt = _html_escape(img_match.group(1))
                    src = img_match.group(2)
                    ext = os.path.splitext(src)[1].lower()
                    if ext in (".mp4", ".webm", ".mov"):
                        attrs = []
                        if theme.render_video_controls:
                            attrs.append("controls")
                        if theme.render_video_autoplay:
                            attrs.append("autoplay muted")
                        if theme.render_video_loop:
                            attrs.append("loop")
                        attr_str = " ".join(attrs)
                        sections_html.append(
                            f'<div class="media-block">'
                            f'<video {attr_str} class="media">'
                            f'<source src="{_html_escape(src)}" type="video/{ext.lstrip(".")}">'
                            f'</video></div>')
                    else:
                        shadow = "box-shadow:0 4px 20px rgba(0,0,0,.3);" if theme.render_image_shadow else ""
                        sections_html.append(
                            f'<div class="media-block">'
                            f'<img src="{_html_escape(src)}" alt="{alt}" class="media" '
                            f'style="{shadow}">'
                            f'</div>')
                elif line.strip():
                    # Check if it's a list item
                    li_match = re.match(r'^(\s*[-*])\s+(.+)$', line)
                    if li_match:
                        sections_html.append(f"<li>{_html_inline(li_match.group(2))}</li>")
                    else:
                        sections_html.append(f"<p>{_html_inline(line)}</p>")

        elif event[0] == "skip":
            pass  # skip blocks don't appear in HTML

        elif event[0] == "code":
            _, lang, code_lines, original_lines, dirs = event
            code_content = "\n".join(code_lines)
            block_count += 1
            if not _check_block_limit(block_count):
                continue

            cast_name, cast_path = _generate_block_cast(
                code_content, lang, dirs, theme, assets_dir,
                block_count, current_section, execute, working_dir)

            print(f"  {ok} {cast_path}")

            if embed:
                import base64
                with open(cast_path, "r") as cf:
                    cast_data = cf.read()
                cast_src = "data:application/json;base64," + base64.b64encode(
                    cast_data.encode()).decode()
            else:
                cast_src = os.path.join(os.path.basename(assets_dir), f"{cast_name}.cast")
            player_id = f"player-{block_count}"

            # Collapsible code block + player
            escaped_code = _html_escape(code_content)
            lang_label = lang.upper() if lang else "OUTPUT"
            sections_html.append(f'''<div class="cast-block">
  <div id="{player_id}" class="player" data-cast-src="{cast_src}"
       data-theme="{theme.player_theme or 'monokai'}"
       data-font="{theme.font_family or 'monospace'}"
       data-font-size="{theme.font_size or 16}"
       data-idle="{theme.idle_time_limit or 3}"
       data-cols="{theme.cols}"
       data-rows="{_player_rows(code_lines, theme)}"></div>
  <div class="code-copy">
    <button class="copy-btn" onclick="copyCode(this)">Copy</button>
    <pre><code class="language-{lang or 'text'}">{escaped_code}</code></pre>
  </div>
</div>''')

        elif event[0] == "browser":
            _, lang, code_lines, original_lines, dirs = event
            code_content = "\n".join(code_lines)
            block_count += 1
            slug = slugify(current_section)
            name_prefix = f"{block_count:02d}-{slug}"

            steps = parse_browser_steps(code_content)
            browser_assets = run_browser_steps(steps, assets_dir, name_prefix=name_prefix)

            alt_text = _html_escape(strip_md(current_section))
            for asset in browser_assets:
                rel_path = os.path.join(os.path.basename(assets_dir),
                                        os.path.basename(asset["path"]))
                if asset["type"] == "screenshot":
                    sections_html.append(
                        f'<div class="browser-capture">'
                        f'<img src="{rel_path}" alt="{alt_text}" '
                        f'style="max-width:100%;border-radius:8px;border:1px solid var(--border);">'
                        f'</div>')
                elif asset["type"] == "video":
                    sections_html.append(
                        f'<div class="browser-capture">'
                        f'<video controls style="max-width:100%;border-radius:8px;">'
                        f'<source src="{rel_path}" type="video/webm">'
                        f'</video></div>')

        elif event[0] == "gui":
            _, lang, code_lines, original_lines, dirs = event
            code_content = "\n".join(code_lines)
            block_count += 1
            slug = slugify(current_section)
            name_prefix = f"{block_count:02d}-{slug}"

            steps = parse_gui_steps(code_content)
            gui_assets = run_gui_steps(steps, assets_dir, name_prefix=name_prefix)

            alt_text = _html_escape(strip_md(current_section))
            for asset in gui_assets:
                rel_path = os.path.join(os.path.basename(assets_dir),
                                        os.path.basename(asset["path"]))
                if asset["type"] == "screenshot":
                    sections_html.append(
                        f'<div class="gui-capture">'
                        f'<img src="{rel_path}" alt="{alt_text}" '
                        f'style="max-width:100%;border-radius:8px;border:1px solid var(--border);">'
                        f'</div>')

    body = "\n".join(sections_html)
    html = _html_template(page_title or "Documentation", body, theme)
    generated = min(block_count, FREE_MAX_BLOCKS) if FREE_TIER else block_count
    return html, generated


def _player_rows(code_lines, theme):
    """Calculate appropriate player rows — just enough to show the content."""
    # Commands: prompt line + output lines; output: just the lines
    # Add a few rows for padding, cap at theme.rows
    return min(len(code_lines) + 5, theme.rows)


def _html_escape(text):
    """Escape HTML special characters."""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def _html_inline(text):
    """Escape HTML and convert inline Markdown links to <a> tags."""
    # First escape, then convert [text](url) patterns
    escaped = _html_escape(strip_md(text))
    # Re-apply link conversion (strip_md removes **, not links)
    def link_repl(m):
        link_text = m.group(1)
        url = m.group(2)
        return f'<a href="{url}" style="color:var(--accent)">{link_text}</a>'
    # Match [text](url) but not ![text](url)
    result = re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', link_repl, text)
    # Still escape the non-link parts
    parts = re.split(r'(<a [^>]+>[^<]+</a>)', result)
    out = []
    for p in parts:
        if p.startswith('<a '):
            out.append(p)
        else:
            out.append(_html_escape(strip_md(p)))
    return ''.join(out)


def _html_template(title, body, theme):
    """Generate the full HTML page with embedded asciinema player."""
    img_radius = theme.render_image_border_radius
    img_max_w = theme.render_image_max_width
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_html_escape(title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/asciinema-player@3.8.0/dist/bundle/asciinema-player.css">
<style>
  :root {{
    --bg: {theme.render_bg};
    --fg: {theme.render_fg};
    --muted: #565f89;
    --accent: {theme.render_accent};
    --border: #292e42;
    --code-bg: #24283b;
    --blockquote-border: #e0af68;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: {theme.render_font};
    background: var(--bg);
    color: var(--fg);
    line-height: 1.7;
    max-width: {theme.render_max_width};
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }}
  h1 {{
    font-size: 2rem;
    margin: 2rem 0 1rem;
    color: #c0caf5;
    border-bottom: 2px solid var(--border);
    padding-bottom: 0.5rem;
  }}
  h2 {{
    font-size: 1.5rem;
    margin: 2.5rem 0 1rem;
    color: var(--accent);
  }}
  h3 {{ font-size: 1.2rem; margin: 1.5rem 0 0.5rem; color: var(--fg); }}
  p {{ margin: 0.8rem 0; }}
  li {{ margin: 0.3rem 0 0.3rem 1.5rem; }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 2rem 0; }}
  blockquote {{
    border-left: 3px solid var(--blockquote-border);
    padding: 0.5rem 1rem;
    margin: 1rem 0;
    color: var(--muted);
    background: rgba(224, 175, 104, 0.05);
    border-radius: 0 4px 4px 0;
  }}
  .cast-block {{
    margin: 1.5rem 0;
  }}
  .player {{
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border);
  }}
  details {{
    margin-top: 0.5rem;
  }}
  summary {{
    cursor: pointer;
    color: var(--muted);
    font-size: 0.85rem;
    padding: 0.3rem 0;
    user-select: none;
  }}
  summary:hover {{ color: var(--accent); }}
  pre {{
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    overflow-x: auto;
    margin-top: 0.5rem;
  }}
  code {{
    font-family: {theme.render_code_font};
    font-size: 0.9rem;
    color: var(--fg);
  }}
  .media-block {{
    margin: 1.5rem 0;
    text-align: center;
  }}
  .media {{
    max-width: {img_max_w};
    border-radius: {img_radius};
    border: 1px solid var(--border);
  }}
  .code-copy {{
    position: relative;
    margin-top: 0.5rem;
  }}
  .copy-btn {{
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: var(--border);
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.25rem 0.6rem;
    font-size: 0.75rem;
    cursor: pointer;
    font-family: inherit;
    z-index: 1;
    transition: color 0.2s, background 0.2s;
  }}
  .copy-btn:hover {{ color: var(--fg); background: var(--code-bg); }}
  .copy-btn.copied {{ color: #9ece6a; }}
  /* Asciinema player overrides */
  .ap-wrapper {{ border-radius: 8px !important; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/asciinema-player@3.8.0/dist/bundle/asciinema-player.min.js" defer></script>
</head>
<body>
{body}
<script>
function copyCode(btn) {{
  var code = btn.parentElement.querySelector('code').textContent;
  navigator.clipboard.writeText(code).then(function() {{
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(function() {{ btn.textContent = 'Copy'; btn.classList.remove('copied'); }}, 2000);
  }});
}}
document.addEventListener('DOMContentLoaded', function() {{
  document.querySelectorAll('.player[data-cast-src]').forEach(function(el) {{
    AsciinemaPlayer.create(el.dataset.castSrc, el, {{
      theme: el.dataset.theme,
      fontFamily: el.dataset.font,
      fontSize: el.dataset.fontSize + 'px',
      idleTimeLimit: parseInt(el.dataset.idle),
      cols: parseInt(el.dataset.cols),
      rows: parseInt(el.dataset.rows),
      fit: 'width',
      autoPlay: false,
      preload: true
    }});
  }});
}});
</script>
<footer style="margin-top:4rem;padding:1.5rem 0 0.5rem;text-align:center;font-size:0.75rem;color:var(--muted);opacity:0.6;">
  Made with <a href="https://github.com/markamo/md2cast" style="color:var(--accent);text-decoration:none;">md2cast</a>
</footer>
</body>
</html>'''


def slugify(text):
    """Convert text to a filename-safe slug."""
    text = strip_md(text).lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:60]


def main():
    parser = argparse.ArgumentParser(
        prog="md2cast",
        description="Convert Markdown documentation into asciinema screencasts.",
        epilog="Examples:\n"
               "  md2cast tutorial.md\n"
               "  md2cast tutorial.md --execute --section 3\n"
               "  md2cast tutorial.md --split -o output-dir/\n"
               "  md2cast tutorial.md --theme mytheme.json\n"
               "  md2cast --init-theme > mytheme.json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", nargs="?", help="Markdown file to convert")
    parser.add_argument("-o", "--output", help="Output .cast file or directory (with --split)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually execute bash commands (requires appropriate permissions)")
    parser.add_argument("--section", type=int, help="Only render section N (1-indexed)")
    parser.add_argument("--split", action="store_true",
                        help="Generate one .cast per ## section")
    parser.add_argument("--list", action="store_true",
                        help="List sections and exit")
    parser.add_argument("--cols", type=int, help="Terminal columns (overrides theme)")
    parser.add_argument("--rows", type=int, help="Terminal rows (overrides theme)")
    parser.add_argument("--type-delay", type=float,
                        help="Delay between typed characters (overrides theme)")
    parser.add_argument("--working-dir", "-C", help="Working directory for executed commands")
    parser.add_argument("--title", help="Override cast title")
    parser.add_argument("--theme", help="Theme JSON file (auto-discovers md2cast.json if not set)")
    parser.add_argument("--gif", action="store_true",
                        help="Also generate GIF via agg (requires agg installed)")
    parser.add_argument("--render", action="store_true",
                        help="Generate a new Markdown with embedded GIF screencasts for each code block")
    parser.add_argument("--render-html", action="store_true",
                        help="Generate an HTML page with asciinema players for each code block")
    parser.add_argument("--embed", action="store_true",
                        help="Embed cast data inline in HTML (single file, no server needed). Use with --render-html")
    parser.add_argument("--init-theme", action="store_true",
                        help="Print default theme JSON and exit (redirect to a file to customize)")
    parser.add_argument("--version", action="version", version=f"md2cast {__version__}")

    args = parser.parse_args()

    # Init theme mode — print default and exit
    if args.init_theme:
        print(json.dumps(DEFAULT_THEME, indent=2))
        return

    if not args.input:
        parser.error("the following arguments are required: input")

    # Load theme
    theme_path = args.theme
    if not theme_path:
        theme_path = find_theme(args.input)

    theme_config = {}
    if theme_path:
        try:
            theme_config = load_theme(theme_path)
            if not args.list:
                print(f"  Using theme: {theme_path}", file=sys.stderr)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: failed to load theme {theme_path}: {e}", file=sys.stderr)

    # CLI overrides → merge into theme config
    overrides = {}
    if args.cols:
        overrides.setdefault("terminal", {})["cols"] = args.cols
    if args.rows:
        overrides.setdefault("terminal", {})["rows"] = args.rows
    if args.type_delay is not None:
        overrides.setdefault("timing", {})["type_delay"] = args.type_delay

    theme_config = _deep_merge(theme_config, overrides)
    theme = Theme(theme_config)

    # Read input
    try:
        with open(args.input, "r") as f:
            md_text = f.read()
    except FileNotFoundError:
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    blocks = parse_markdown(md_text)

    # Render mode — generate new Markdown with embedded GIFs
    if args.render:
        base = os.path.splitext(args.input)[0]
        out_md = args.output or f"{base}-rendered.md"
        assets_dir = os.path.join(os.path.dirname(out_md) or ".", "assets")

        print(f"\n  Rendering {args.input} → {out_md}\n")
        rendered_md, gif_count = render_markdown(
            md_text, theme,
            assets_dir=assets_dir,
            execute=args.execute,
            working_dir=args.working_dir,
        )

        with open(out_md, "w") as f:
            f.write(rendered_md)

        ok = "\033[0;32m[OK]\033[0m"
        print(f"\n  {ok} {out_md}  ({gif_count} GIFs)")
        print(f"  Assets: {assets_dir}/")
        print()
        return

    # Render HTML mode — generate HTML page with asciinema players
    if args.render_html:
        base = os.path.splitext(args.input)[0]
        out_html = args.output or f"{base}.html"
        assets_dir = os.path.join(os.path.dirname(out_html) or ".", "assets")

        print(f"\n  Rendering {args.input} → {out_html}\n")
        html, player_count = render_html(
            md_text, theme,
            assets_dir=assets_dir,
            execute=args.execute,
            working_dir=args.working_dir,
            embed=args.embed,
        )

        with open(out_html, "w") as f:
            f.write(html)

        ok = "\033[0;32m[OK]\033[0m"
        print(f"\n  {ok} {out_html}  ({player_count} players)")
        if args.embed:
            print(f"  Self-contained — open directly in any browser")
        else:
            print(f"  Assets: {assets_dir}/")
        print(f"  Open:   xdg-open {out_html}")
        print()
        return

    # List mode
    if args.list:
        print(f"\nSections in {args.input}:\n")
        list_sections(blocks)
        print()
        return

    sections = split_sections(blocks)
    sections = _check_section_limit(sections)

    # Section filter
    if args.section:
        if args.section < 1 or args.section > len(sections):
            print(f"Error: section {args.section} out of range (1-{len(sections)})",
                  file=sys.stderr)
            sys.exit(1)
        sections = [sections[args.section - 1]]

    # Split mode
    if args.split:
        out_dir = args.output or os.path.splitext(args.input)[0] + "-casts"
        os.makedirs(out_dir, exist_ok=True)

        ok = "\033[0;32m[OK]\033[0m"
        for i, (title, section_blocks) in enumerate(sections, 1):
            slug = slugify(title)
            outfile = os.path.join(out_dir, f"{i:02d}-{slug}.cast")
            cast_title = args.title or strip_md(title)

            cast = CastWriter(theme, title=cast_title)
            renderer = Renderer(cast, theme, execute=args.execute,
                                working_dir=args.working_dir)
            renderer.render_blocks(section_blocks)
            cast.save(outfile)
            print(f"  {ok} {outfile}  ({strip_md(title)})")
            if args.gif:
                cast_to_gif(outfile)

        print(f"\n  {len(sections)} cast(s) written to {out_dir}/")
        print(f"  Play: asciinema play {out_dir}/<name>.cast")

    else:
        # Single file mode
        outfile = args.output or os.path.splitext(args.input)[0] + ".cast"
        first_title = ""
        for b in blocks:
            if b.kind == "heading":
                first_title = strip_md(b.content)
                break
        cast_title = args.title or first_title

        target_blocks = sections[0][1] if len(sections) == 1 else blocks
        if args.section:
            target_blocks = sections[0][1]

        cast = CastWriter(theme, title=cast_title)
        renderer = Renderer(cast, theme, execute=args.execute,
                            working_dir=args.working_dir)
        renderer.render_blocks(target_blocks)
        cast.save(outfile)

        duration = cast.time
        event_count = len(cast.events)
        ok = "\033[0;32m[OK]\033[0m"
        print(f"\n  {ok} {outfile}")
        print(f"  Duration: {duration:.1f}s  Events: {event_count}")
        print(f"  Play: asciinema play {outfile}")
        if args.gif:
            cast_to_gif(outfile)
            # Stitch images into the GIF if any were recorded
            if renderer.image_markers and _HAS_PIL:
                gif_path = os.path.splitext(outfile)[0] + ".gif"
                if os.path.exists(gif_path):
                    wd = args.working_dir or os.path.dirname(os.path.abspath(args.input))
                    _stitch_images_into_gif(gif_path, renderer.image_markers,
                                            working_dir=wd)
        else:
            print(f"  GIF:  agg {outfile} {os.path.splitext(outfile)[0]}.gif")
        print()


if __name__ == "__main__":
    main()
