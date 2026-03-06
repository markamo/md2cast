#!/bin/bash
set -e

PREFIX="${1:-/usr/local}"
BIN_DIR="$PREFIX/bin"

if [ ! -f "md2cast" ]; then
    echo "Error: run this script from the md2cast directory"
    exit 1
fi

echo "Installing md2cast to $BIN_DIR/md2cast"

if [ -w "$BIN_DIR" ]; then
    cp md2cast "$BIN_DIR/md2cast"
    chmod +x "$BIN_DIR/md2cast"
else
    sudo cp md2cast "$BIN_DIR/md2cast"
    sudo chmod +x "$BIN_DIR/md2cast"
fi

echo "Installed: $(md2cast --version)"
