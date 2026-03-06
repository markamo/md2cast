# Render Mode Test

Run with: `md2cast tests/manual/render.md --render` or `md2cast tests/manual/render.md --render-html`

## Introduction

This file tests the render pipeline — each code block should get a GIF (render) or player (render-html) above it.

## Simple Command

![Simple Command](assets/01-simple-command.gif)

```bash
echo "Hello from render mode"
```

## Multiple Commands

![Multiple Commands](assets/02-multiple-commands.gif)

```bash
ls -la
pwd
whoami
```

## Config Block

![Config Block](assets/03-config-block.gif)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
    - name: app
      image: nginx:latest
```

## JSON Example

![JSON Example](assets/04-json-example.gif)

```json
{
  "name": "md2cast",
  "version": "0.3.0",
  "features": ["cast", "gif", "render", "html"]
}
```

## Python Code

![Python Code](assets/05-python-code.gif)

```python
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

for num in fibonacci(10):
    print(num, end=" ")
```

> **Note:** The render output should have a "Made with md2cast" footer at the bottom.


<p align="center"><sub>Made with <a href="https://github.com/markamo/md2cast">md2cast</a></sub></p>
