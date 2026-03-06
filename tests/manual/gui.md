# GUI Capture Test

Run with: `md2cast tests/manual/gui.md --render`

Requires: `xdotool` (X11) or `ydotool` (Wayland) + screenshot tool

## Launch App

```bash
echo "Launching application..."
```

## Desktop Capture

<!-- gui -->
```steps
sleep 1
screenshot desktop-current
```

## Done

```bash
echo "GUI test complete"
```
