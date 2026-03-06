# md2cast Examples

Generated with `md2cast v0.3.0`. Each example shows the rendered output (Markdown with embedded GIFs + self-contained HTML).

| Example | Source | Rendered Markdown | HTML |
|---------|--------|-------------------|------|
| **Basic** — core features | [basic.md](../tests/manual/basic.md) | [basic-rendered.md](basic-rendered.md) | [basic.html](basic.html) |
| **Directives** — prompts, delays, exec, skip | [directives.md](../tests/manual/directives.md) | [directives-rendered.md](directives-rendered.md) | [directives.html](directives.html) |
| **Execute** — real command output | [execute.md](../tests/manual/execute.md) | [execute-rendered.md](execute-rendered.md) | [execute.html](execute.html) |
| **Render** — syntax highlighting, multi-lang | [render.md](../tests/manual/render.md) | [render-rendered.md](render-rendered.md) | [render.html](render.html) |

## Basic

![hello world](assets/01-hello-world.gif)

```bash
echo "Hello, world!"
```

## Directives

### Custom prompt (`<!-- prompt # -->`)
![custom prompt](assets/01-custom-prompt.gif)

### Slow typing (`<!-- type-delay 0.08 -->`)
![slow typing](assets/02-slow-typing.gif)

### Execute directive (`<!-- exec -->`)
![exec](assets/05-exec-directive.gif)

## Execute Mode (`--execute`)

![system info](assets/01-system-info.gif)

![working with files](assets/03-working-with-files.gif)

## Syntax Highlighting

### YAML
![yaml](assets/03-config-block.gif)

### JSON
![json](assets/04-json-example.gif)

### Python
![python](assets/05-python-code.gif)
