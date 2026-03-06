#!/bin/bash
set -e

PREFIX="${1:-/usr/local}"
BIN_DIR="$PREFIX/bin"
TARGET="$BIN_DIR/md2cast"

if [ ! -f "$TARGET" ]; then
    echo "md2cast is not installed at $TARGET"
    exit 0
fi

echo "Removing $TARGET"

if [ -w "$BIN_DIR" ]; then
    rm "$TARGET"
else
    sudo rm "$TARGET"
fi

echo "md2cast uninstalled."
