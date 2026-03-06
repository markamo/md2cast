# Browser Capture Test

Run with: `md2cast tests/manual/browser.md --render`

Requires: `pip install playwright && playwright install chromium`

## Start Server

```bash
echo "Server running on http://localhost:3000"
```

## Visit Homepage

<!-- browser -->
```steps
open https://example.com
sleep 1
screenshot example-home
scroll down 300
sleep 0.5
screenshot example-scrolled
```

## Back to CLI

```bash
echo "Browser test complete"
```
