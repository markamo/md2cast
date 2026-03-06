# md2cast Tutorial

Learn how to convert Markdown into terminal screencasts with md2cast.

## Getting Started

Install md2cast — it's a single Python script with no dependencies:

```bash
sudo ln -s $(pwd)/md2cast /usr/local/bin/md2cast
```

Verify it's working:

```bash
md2cast --version
```

## Your First Screencast

Create a simple markdown file:

```bash
cat > hello.md << 'EOF'
# Hello World

A simple demo.

## Say Hello

```bash
echo "Hello, world!"
```

## List Files

```bash
ls -la
```
EOF
```

Convert it to a screencast:

```bash
md2cast hello.md
```

Play it back:

```bash
asciinema play hello.cast
```

> **Tip:** Install asciinema with `pip install asciinema` or `apt install asciinema`.

## How Markdown Maps to Screencasts

md2cast turns each Markdown element into a terminal animation:

- `# Heading` becomes a **title card** with a box border
- `## Heading` becomes a **section divider** that clears the screen
- `### Heading` becomes a **subsection label** in bold
- Regular paragraphs become **dimmed narration** (`# comment style`)
- ` ```bash ` blocks are **typed character-by-character** with a `$` prompt
- ` ``` ` blocks (no language) are **static output** shown at once
- `> blockquotes` become **highlighted notes** with a yellow sidebar
- `---` clears the screen

No special syntax needed — just write normal Markdown.

## Splitting into Multiple Casts

For longer tutorials, split at each `##` heading:

```bash
md2cast hello.md --split
```

This creates a directory with numbered files:

```
hello-casts/
  01-hello-world.cast
  02-say-hello.cast
  03-list-files.cast
```

List sections without generating anything:

```bash
md2cast hello.md --list
```

Render just one section:

```bash
md2cast hello.md --section 2
```

## Execute Mode

By default, md2cast simulates commands — it types them but doesn't run them. To capture real output:

```bash
md2cast hello.md --execute
```

Set the working directory for executed commands:

```bash
md2cast hello.md --execute -C /path/to/project
```

> **Warning:** Execute mode runs real shell commands. Only use with trusted Markdown files.

## Directives

HTML comment directives give you per-block control. They're invisible when the Markdown is rendered as normal documentation.

### Execute a single block

Run one specific command without enabling global `--execute`:

```markdown
<!-- exec -->
` ` `bash
echo "Only this command runs for real"
` ` `
```

### Skip execution for a block

Keep a dangerous command from running even with `--execute`:

```markdown
<!-- no-exec -->
` ` `bash
rm -rf /tmp/demo
` ` `
```

### Change the prompt

Show a root shell or Python REPL:

```markdown
<!-- prompt # -->
` ` `bash
systemctl restart nginx
` ` `

<!-- prompt >>> -->
` ` `bash
print("Hello from Python")
` ` `
```

### Control typing speed

Type a command slowly for emphasis, or fast to skip boilerplate:

```markdown
<!-- type-delay 0.1 -->
` ` `bash
echo "Watch each character appear slowly..."
` ` `

<!-- type-delay 0.005 -->
` ` `bash
npm install --save-dev webpack webpack-cli babel-loader css-loader
` ` `
```

### Show bash as output

Sometimes a ` ```bash ` block is really output (like a log), not a command to type:

```markdown
<!-- output -->
` ` `bash
[INFO] Server started on port 8080
[INFO] Connected to database
[INFO] Ready to accept connections
` ` `
```

### Stack directives

Directives apply to the next block and can be combined:

```markdown
<!-- prompt # -->
<!-- type-delay 0.08 -->
<!-- exec -->
` ` `bash
apt update && apt install -y curl
` ` `
```

### Other directives

```markdown
<!-- pause 5 -->       Pause for 5 seconds

<!-- skip -->          Skip the next block entirely
` ` `bash
echo "This never appears in the cast"
` ` `

<!-- clear -->         Clear the screen (same as ---)
```

## Themes

Customize colors, fonts, terminal size, and timing.

### Generate a theme file

```bash
md2cast --init-theme > md2cast.json
```

### Example: dark orange theme

```json
{
  "terminal": { "cols": 120, "rows": 40 },
  "player": { "theme": "solarized-dark", "font_size": 18 },
  "colors": {
    "prompt": "#00ff88",
    "title_border": "#ff6600",
    "section_border": "256:208",
    "quote": "#ffcc00"
  },
  "timing": { "type_delay": 0.02, "section_pause": 1.5 }
}
```

You only need to include the values you want to override — everything else uses defaults.

### Use a theme

```bash
md2cast tutorial.md --theme my-theme.json
```

Or place `md2cast.json` in the same directory as your Markdown file and it's picked up automatically.

### Color formats

| Format | Example | What it does |
|--------|---------|-------------|
| Named | `"green"` | Standard ANSI color |
| Bold/dim | `"bold"`, `"dim"` | Text style |
| Hex | `"#ff6600"` | 24-bit RGB |
| 256-color | `"256:208"` | xterm palette |
| Raw SGR | `"1;38;5;214"` | Direct escape codes |
| Empty | `""` | Terminal default |

## Terminal Size

Set terminal dimensions in your theme or on the command line:

```bash
md2cast tutorial.md --cols 120 --rows 40
```

CLI flags always override theme values.

## Converting to GIF

Use [agg](https://github.com/asciinema/agg) to convert `.cast` files to GIF:

```bash
agg output.cast output.gif
```

Or upload to asciinema.org:

```bash
asciinema upload output.cast
```

## Tips

- **Start with structure.** Write your tutorial as normal Markdown first, then run md2cast. No special markup needed for the common case.
- **Use `--list` to preview.** Check section breakdown before generating.
- **Use `--split` for long tutorials.** Each section becomes its own cast — easier to re-record one part.
- **Use `--section N` to iterate.** Tweak one section at a time without regenerating everything.
- **Put `md2cast.json` in your project.** Theme travels with your docs — anyone can regenerate the same screencasts.
- **Directives are optional.** Most tutorials work perfectly with just standard Markdown.

## License

MIT
