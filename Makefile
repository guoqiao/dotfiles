SHELL = /bin/bash
.ONESHELL:

.PHONY: all build clean test

all:
	@uname | grep Darwin && make mac || true
	@uname | grep Linux && make ubuntu || true

apt:
	which apt && \
	sudo apt-get update && \
	sudo apt-get install -y \
		build-essential make \
		openssh-server ssh-import-id \
		curl wget \
		git vim zsh tmux tree time watch

homebrew:
	command -v brew || bash setup/homebrew.sh
	@echo "please add brew bin to your PATH"

brew:
	brew install \
		bat \
		direnv \
		eza \
		fd \
		htop \
		jq \
		ncdu \
		ripgrep \
		tldr \
		tree \
		uv \
		vim \
		yq \
		zoxide

fonts:
	brew install --cask \
		font-fire-code \
		font-hack \
		font-jetbrains-mono \
		font-source-code-pro
	fc-cache -fv

fonts-family:
	fc-list : family

ghostty-list-fonts:
	ln -s /Applications/Ghostty.app/Contents/MacOS/ghostty ~/bin/ || true
	~/bin/ghostty +list-fonts

uv:
	brew install uv
	uv sync

npm:
	brew install node@24 pnpm
	mkdir -p ~/.npm-global/bin/
	npm config set prefix '~/.npm-global'
	bin/link .npmrc
	npm i -g hunk

git:
	brew install git tig lazygit git-delta bat
	bin/link .gitconfig
	bash setup/git_config_user.sh

tmux:
	brew install tmux
	bin/link .tmux.conf

direnv:
	brew install direnv
	mkdir -p ~/.config/direnv
	# cp when missing, instead of ln
	cp -n .config/direnv/direnv.toml ~/.config/direnv/direnv.toml || true

omz: git tmux direnv
	bash setup/omz.sh
	brew install zoxide
	# cp when missing, instead of ln
	cp -n .zshrc ~/.zshrc || true

vim:
	git clone https://github.com/guoqiao/vimrc.git ~/.vim || true
	cd ~/.vim; git pull; make all

path:
	@echo "add to top of your ~/.zshrc:"
	@bin/path-gen.py

hooks:
	brew install prek
	prek install -f --prepare-hooks

hooks-run:
	prek run --all-files

hooks-update:
	prek auto-update

pull:
	git pull || true


setup: pull brew npm uv omz vim hooks path


ubuntu:
	make apt
	make homebrew
	which brew || eval "$(shell /home/linuxbrew/.linuxbrew/bin/brew shellenv)"
	make setup


mac:
	xcode-select --install || true
	make homebrew
	which brew || eval "$(shell /opt/homebrew/bin/brew shellenv)"
	make setup

