#!/usr/bin/env bash

set -ueo pipefail


cd ~/.config

if [[ ! -d tmux-palette ]]; then
    git clone https://github.com/eduwass/tmux-palette
fi

cd tmux-palette
pwd
git pull
bun install

