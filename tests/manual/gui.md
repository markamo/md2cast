# GUI Capture Test

Run with: `md2cast tests/manual/gui.md --render`

Requires: screenshot tool (gnome-screenshot, grim, scrot, or import)

## Full Desktop Screenshot

<!-- gui -->
```steps
screenshot full-desktop
```

## Region Screenshot

Captures a 400x300 area starting at coordinates 100,100:

<!-- gui -->
```steps
screenshot --region 100,100 400x300 top-left-region
```

## Multiple Screenshots

Take several screenshots in sequence:

<!-- gui -->
```steps
screenshot step-1
sleep 1
screenshot step-2
sleep 1
screenshot step-3
```

## Done

```bash
echo "GUI test complete"
```
