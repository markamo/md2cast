# md2cast

Convert Markdown documentation into [asciinema](https://asciinema.org) screencasts.

Write your tutorial in Markdown, run `md2cast`, get a `.cast` file you can play, embed, or convert to GIF.

## Prerequisites

- **Python 3.6+** — md2cast itself has no other dependencies
- **asciinema** — for playing back `.cast` files ([asciinema.org](https://asciinema.org))
- **agg** *(optional)* — for converting `.cast` to GIF ([github.com/asciinema/agg](https://github.com/asciinema/agg))
- **pygments** *(optional)* — for syntax highlighting in code blocks (`pip install pygments`)

```bash
# Install asciinema
pip install asciinema
# or: sudo apt install asciinema  (Debian/Ubuntu)
# or: brew install asciinema      (macOS)

# Install agg (optional, for GIF export)
# Download prebuilt binary from https://github.com/asciinema/agg/releases
# or via package manager:
# brew install agg                (macOS)
# nix-env -i agg                 (Nix)
# cargo install --git https://github.com/asciinema/agg  (from source)
```

## Install

```bash
# Using the install script
./install.sh

# Or manually
sudo cp md2cast /usr/local/bin/
```

To uninstall: `./uninstall.sh`

## Usage

```bash
# Generate a screencast from a markdown file
md2cast tutorial.md                         # → tutorial.cast

# Custom output
md2cast tutorial.md -o demo.cast

# List sections
md2cast tutorial.md --list

# Render only one section
md2cast tutorial.md --section 3

# Split into one .cast per ## section
md2cast tutorial.md --split

# Actually execute bash commands (captures real output)
md2cast tutorial.md --execute

# Custom terminal size
md2cast tutorial.md --cols 120 --rows 40

# Generate cast + GIF in one step (requires agg)
md2cast tutorial.md --gif

# Split into sections and generate GIFs for each
md2cast tutorial.md --split --gif

# Render: generate new Markdown with GIFs embedded above code blocks
md2cast tutorial.md --render

# Use a custom theme
md2cast tutorial.md --theme my-theme.json
```

## Markdown Mapping

| Markdown | Screencast |
|----------|-----------|
| `# Heading` | Title card (clear screen, box) |
| `## Heading` | Section divider (clear, banner) |
| `### Heading` | Subsection label (bold) |
| Regular text | Narrated comment (dimmed `# text`) |
| ` ```bash ` | Typed command (green `$` prompt, character-by-character) |
| ` ``` ` (no lang) | Static output (displayed at once) |
| ` ```yaml ` etc | Static output (config/code shown at once) |
| `> blockquote` | Highlighted note (yellow sidebar) |
| `---` | Screen clear |
| `<!-- pause 3 -->` | Custom pause (seconds) |
| `<!-- skip -->` | Skip the next block |

### Directives

HTML comment directives give per-block control without breaking normal Markdown rendering:

| Directive | Effect |
|-----------|--------|
| `<!-- exec -->` | Execute only the next bash block (no global `--execute` needed) |
| `<!-- no-exec -->` | Skip execution for the next block (even with `--execute`) |
| `<!-- type-delay 0.01 -->` | Override typing speed for the next block |
| `<!-- prompt # -->` | Change prompt character (e.g., `#` for root, `>>>` for Python) |
| `<!-- output -->` | Force next ` ```bash ` block to display as static output |
| `<!-- view-exec -->` | Show commands as preview first, then execute each one with real output |
| `<!-- clear -->` | Clear screen (alternative to `---`) |
| `<!-- skip -->` | Skip the next block entirely |
| `<!-- pause 3 -->` | Pause for N seconds |

Directives apply to the next block only and can be stacked:

```markdown
<!-- prompt # -->
<!-- type-delay 0.08 -->
` ` `bash
apt install -y nginx
` ` `
```

## Themes

Customize colors, terminal size, timing, and asciinema player settings with a JSON config file.

### Generate a default theme

```bash
md2cast --init-theme > md2cast.json
```

### Theme structure

```json
{
  "terminal": {
    "cols": 110,
    "rows": 35,
    "shell": "/bin/bash",
    "env": { "TERM": "xterm-256color" }
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
    "syntax_highlight": true,
    "highlight_style": "monokai"
  },
  "timing": {
    "type_delay": 0.03,
    "cmd_pause": 0.8,
    "output_pause": 1.5,
    "section_pause": 2.0,
    "text_pause": 0.8,
    "end_pause": 2.0
  }
}
```

### Color formats

Colors accept multiple formats:

| Format | Example | Description |
|--------|---------|-------------|
| Named | `"green"`, `"bold"`, `"dim"` | Standard ANSI names |
| Hex | `"#ff6600"` | 24-bit RGB color |
| 256-color | `"256:208"` | xterm 256-color palette |
| Raw SGR | `"1;38;5;214"` | Direct SGR parameters |
| Empty | `""` | No color (terminal default) |

### Syntax highlighting

Code blocks (` ```python `, ` ```yaml `, ` ```json `, etc.) are automatically syntax-highlighted using [Pygments](https://pygments.org/) when installed. Bash commands are also highlighted after typing.

- Enabled by default when pygments is available
- Disable in theme: `"syntax_highlight": false`
- Change style: `"highlight_style": "dracula"` (any Pygments style — `monokai`, `solarized-dark`, `nord`, `one-dark`, etc.)
- List available styles: `python3 -c "from pygments.styles import get_all_styles; print(list(get_all_styles()))"`

### Auto-discovery

If no `--theme` flag is given, md2cast looks for config files in this order:

1. `md2cast.json` (current directory)
2. `.md2cast.json` (current directory, hidden)
3. `~/.config/md2cast/theme.json` (global default)

CLI flags (`--cols`, `--rows`, `--type-delay`) override theme values.

### Player settings

The `player` section sets metadata in the `.cast` file header that asciinema web players use:

- `theme` — player color theme (`monokai`, `solarized-dark`, `dracula`, etc.)
- `font_family` — CSS font stack for web embeds
- `font_size` — font size in pixels
- `idle_time_limit` — cap idle pauses at this many seconds during playback

## Example

Given this markdown:

```markdown
# My Tutorial

A quick demo of the tool.

## Step 1: Hello World

Run a simple command:

` ` `bash
echo "Hello, world!"
` ` `

> **Tip:** You can also use `printf` for more control.

## Step 2: Files

` ` `bash
ls -la
` ` `
```

Running `md2cast tutorial.md --split` produces:
- `01-my-tutorial.cast` — title card
- `02-step-1-hello-world.cast` — typed `echo` command with narration
- `03-step-2-files.cast` — typed `ls` command

## Playback

```bash
# Terminal playback
asciinema play output.cast

# Convert to GIF (requires agg)
agg output.cast output.gif

# Upload to asciinema.org
asciinema upload output.cast
```

## Render Mode

Generate a new Markdown file with GIF screencasts embedded above each code block:

```bash
md2cast tutorial.md --render
```

This produces:
- `tutorial-rendered.md` — new Markdown with `![](assets/01-name.gif)` above each code block
- `assets/` — directory containing `.cast` and `.gif` files for each block

The original code blocks are preserved below each GIF so readers can still copy-paste commands. Non-bash blocks (YAML, Python, JSON, etc.) get syntax-highlighted GIFs.

Use with `--execute` to capture real command output in the GIFs:

```bash
md2cast tutorial.md --render --execute -C /path/to/project
```

Custom output path:

```bash
md2cast tutorial.md --render -o docs/VISUAL-GUIDE.md
```

## Execute Mode

With `--execute`, bash code blocks are actually run and their output is captured:

```bash
md2cast tutorial.md --execute -C /path/to/project
```

This is useful for generating screencasts with real command output. Use `-C` to set the working directory.

## Author

Mark Amo-Boateng, PhD

## License

MIT — see [LICENSE](LICENSE) for details.
