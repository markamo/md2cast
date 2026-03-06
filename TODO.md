# md2cast — TODO & Ideas

## Pro Features (Paid Tier)

### AI Enhancement (`md2cast enhance`)
- [ ] `md2cast enhance tutorial.md` — AI scans markdown and inserts optimal directives
- [ ] Auto-insert `<!-- pause -->` at natural breakpoints
- [ ] Auto-insert `<!-- type-delay -->` — slower for important commands, faster for boilerplate
- [ ] Auto-insert `<!-- prompt # -->` for sudo/root commands
- [ ] Suggest `<!-- exec -->` for blocks that benefit from real output
- [ ] Split long bash blocks into logical groups with narration between them
- [ ] Generate explanatory text paragraphs between code blocks missing context
- [ ] Optimize pacing — longer pauses after complex output, shorter for simple commands
- [ ] `--model` flag to choose LLM (Claude, GPT, local)
- [ ] `--dry-run` to preview suggested changes without applying
- [ ] Output diff showing what was added/changed

### Browser Capture
- [x] Playwright integration — screenshots, video, navigation
- [x] Browser step DSL (open, click, type, wait, screenshot, scroll, etc.)
- [x] Video-to-GIF via ffmpeg
- [ ] Chrome DevTools Protocol support (alternative to Playwright)
- [ ] Network request capture (show API calls alongside browser actions)
- [ ] Console log capture
- [ ] Mobile viewport presets (iPhone, iPad, Pixel)

### GUI Capture
- [x] xdotool/ydotool desktop automation
- [x] Full screen + window + region screenshots
- [x] Silent screenshots via XDG Desktop Portal (no flash/sound)
- [ ] OCR-based element detection (click on "Save" instead of coordinates)
- [ ] Template matching for visual assertions

### AI Features (Future)
- [ ] `md2cast narrate` — generate voiceover script from markdown
- [ ] `md2cast review` — AI reviews screencast for pacing, clarity, completeness
- [ ] Auto-generate `<!-- browser -->` blocks from URLs mentioned in text
- [ ] Auto-generate alt text for screenshots
- [ ] Smart section splitting — AI decides where to break for `--split`

## Free Features (CLI)

### Done
- [x] Auto-size terminal rows to content (short blocks no longer waste 35 rows)
- [x] "md2cast" watermark at bottom-right of every GIF

### In Progress
- [ ] Bump version to 0.4.0
- [ ] Update TUTORIAL.md with browser, GUI, render, render-html docs

### Jupyter Notebook Support (`md2cast notebook.ipynb`)
**Free:**
- [ ] Read `.ipynb` JSON, map cells to cast (code → typed `In [N]:`, markdown → narration, text output → static)
- [ ] Same 15-block limit, watermark

**Pro:**
- [ ] Re-execute cells in live kernel (`--execute`, needs `jupyter` installed)
- [ ] Image/plot outputs embedded as assets (matplotlib, plotly, etc.)
- [ ] Rich output rendering (HTML tables, LaTeX)
- [ ] Unlimited blocks, no watermark

### Planned
- [ ] `--watch` mode — regenerate on file change
- [ ] `--preview` — play cast immediately after generation
- [ ] `--speed` — global playback speed multiplier
- [ ] Custom prompt strings (not just single char — e.g., `user@host:~$`)
- [ ] Table rendering in screencasts (markdown tables → formatted terminal output)
- [ ] List rendering (bullet points, numbered lists)
- [ ] `--no-footer` flag to disable "Made with md2cast" attribution
- [ ] SVG output (alternative to GIF, sharper, smaller files)
- [ ] Embed mode — generate embeddable HTML snippet (not full page)

### Quality of Life
- [ ] Progress bar for `--render` and `--render-html` (show block N/total)
- [ ] `--quiet` / `--verbose` flags
- [ ] `md2cast validate tutorial.md` — check for common issues (missing code blocks, broken directives)
- [ ] Theme gallery — `md2cast themes` to list built-in themes
- [ ] Built-in themes (dracula, solarized, nord, one-dark, github-dark)

## Distribution
- [ ] PyPI package (`pip install md2cast`)
- [ ] Homebrew formula
- [ ] GitHub Actions integration (`md2cast-action`)
- [ ] VS Code extension (preview pane)

## Feature Tiers

### Free (MIT, public repo `md2cast`)
- Cast generation from markdown (all directives, all block types)
- `--execute`, `--split`, `--section`, `--list`
- `--render` (markdown + GIFs), `--render-html`, `--embed`
- Custom themes, syntax highlighting
- `--gif` (agg conversion)
- Auto-sized rows
- Basic Jupyter notebook support (read saved outputs, `In [N]:` prompts)
- **Limits**: 10 sections (`--split`), 15 code blocks per doc
- **Watermark**: "md2cast" on every GIF (cannot be removed)

### Pro ($12/mo, private repo `md2cast-pro`)
- Everything in Free, no limits
- `--no-watermark` — clean GIFs
- Browser capture (`<!-- browser -->` + Playwright)
- GUI capture (`<!-- gui -->` + screenshots)
- Jupyter: live kernel execution, image/plot output, rich rendering
- AI enhance (`md2cast enhance` — auto-insert directives)
- AI narrate / AI review (future)
- Built-in theme gallery
- Priority support

### Team ($25/user/mo)
- Everything in Pro
- Shared theme library
- CI/CD integration (GitHub Action)
- Private cast hosting
- VS Code extension

### Distribution
- **Free binary**: `md2cast` — public GitHub repo, MIT license, `pip install md2cast`
- **Pro binary**: `md2cast` (same name) — commercial license, license key check
- Shutterstock model: free = branded output, paid = clean output
