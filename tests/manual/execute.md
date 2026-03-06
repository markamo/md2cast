# Execute Mode Test

Run with: `md2cast tests/manual/execute.md --execute -o /tmp/execute-test.cast`

## System Info

```bash
uname -a
```

```bash
whoami
```

## Working with Files

```bash
echo "hello from md2cast" > /tmp/md2cast-test.txt
cat /tmp/md2cast-test.txt
rm /tmp/md2cast-test.txt
```

## View-Exec Mode

<!-- view-exec -->
```bash
echo "Step 1: Check directory"
ls /tmp | head -5
echo "Step 3: Done"
```

## Mixed: No-Exec Override

This one should NOT execute even with --execute:

<!-- no-exec -->
```bash
echo "This stays simulated"
```

## Python Code Display

This block should render as static syntax-highlighted output (not executed):

```python
import sys
print(f"Python {sys.version}")
for i in range(3):
    print(f"  item {i}")
```
