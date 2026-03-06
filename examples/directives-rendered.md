# Directives Test

## Custom Prompt

<!-- prompt # -->
![Custom Prompt](assets/01-custom-prompt.gif)

```bash
apt install -y nginx
```

## Slow Typing

<!-- type-delay 0.08 -->
![Slow Typing](assets/02-slow-typing.gif)

```bash
echo "This should type slowly"
```

## Fast Typing

<!-- type-delay 0.005 -->
![Fast Typing](assets/03-fast-typing.gif)

```bash
echo "This should type very fast"
```

## Output Override

This bash block should display as static output, not typed:

<!-- output -->
![Output Override](assets/04-output-override.gif)

```bash
echo "This is shown as output, not typed"
```

## Exec Directive

This block executes even without --execute flag:

<!-- exec -->
![Exec Directive](assets/05-exec-directive.gif)

```bash
echo "I was executed via directive!"
date
```

## Stacked Directives

<!-- prompt # -->
<!-- type-delay 0.06 -->
![Stacked Directives](assets/06-stacked-directives.gif)

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

![Pause Test](assets/07-pause-test.gif)

```bash
echo "After a 3-second pause"
```

## Clear Test

<!-- clear -->

![Clear Test](assets/08-clear-test.gif)

```bash
echo "After a screen clear"
```


<p align="center"><sub>Made with <a href="https://github.com/markamo/md2cast">md2cast</a></sub></p>
