# Directives Test

## Custom Prompt

<!-- prompt # -->
```bash
apt install -y nginx
```

## Slow Typing

<!-- type-delay 0.08 -->
```bash
echo "This should type slowly"
```

## Fast Typing

<!-- type-delay 0.005 -->
```bash
echo "This should type very fast"
```

## Output Override

This bash block should display as static output, not typed:

<!-- output -->
```bash
echo "This is shown as output, not typed"
```

## Exec Directive

This block executes even without --execute flag:

<!-- exec -->
```bash
echo "I was executed via directive!"
date
```

## Stacked Directives

<!-- prompt # -->
<!-- type-delay 0.06 -->
```bash
systemctl restart nginx
```

## Skip Test

The next block should be skipped entirely:

<!-- skip -->
```bash
echo "You should NOT see this"
```

## Pause Test

<!-- pause 3 -->

```bash
echo "After a 3-second pause"
```

## Clear Test

<!-- clear -->

```bash
echo "After a screen clear"
```
