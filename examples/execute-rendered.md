# Execute Mode Test

Run with: `md2cast tests/manual/execute.md --execute -o /tmp/execute-test.cast`

## System Info

![System Info](assets/01-system-info.gif)

```bash
uname -a
```

![System Info](assets/02-system-info.gif)

```bash
whoami
```

## Working with Files

![Working with Files](assets/03-working-with-files.gif)

```bash
echo "hello from md2cast" > /tmp/md2cast-test.txt
cat /tmp/md2cast-test.txt
rm /tmp/md2cast-test.txt
```

## View-Exec Mode

<!-- view-exec -->
![View-Exec Mode](assets/04-view-exec-mode.gif)

```bash
echo "Step 1: Check directory"
ls /tmp | head -5
echo "Step 3: Done"
```

## Mixed: No-Exec Override

This one should NOT execute even with --execute:

<!-- no-exec -->
![Mixed: No-Exec Override](assets/05-mixed-no-exec-override.gif)

```bash
echo "This stays simulated"
```

## Python Code Display

This block should render as static syntax-highlighted output (not executed):

![Python Code Display](assets/06-python-code-display.gif)

```python
import sys
print(f"Python {sys.version}")
for i in range(3):
    print(f"  item {i}")
```


<p align="center"><sub>Made with <a href="https://github.com/markamo/md2cast">md2cast</a></sub></p>
