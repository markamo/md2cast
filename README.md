# md2cast

Convert Markdown documentation into [asciinema](https://asciinema.org) screencasts.

Write your tutorial in Markdown, run `md2cast`, get a `.cast` file you can play, embed, or convert to GIF.

## Install

```bash
# Copy the script
sudo cp md2cast /usr/local/bin/
# Or symlink
sudo ln -s $(pwd)/md2cast /usr/local/bin/md2cast
```

No dependencies — just Python 3.6+.

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

## Execute Mode

With `--execute`, bash code blocks are actually run and their output is captured:

```bash
md2cast tutorial.md --execute -C /path/to/project
```

This is useful for generating screencasts with real command output. Use `-C` to set the working directory.

## License

MIT
