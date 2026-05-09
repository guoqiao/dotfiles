# dot

Personal dot files for macOS and Ubuntu, quickly setup work env for developer.

Example tools:
- brew/npm/uv
- git/vim/zsh/tmux/direnv

## Quick Start

Clone the repo with https:

```bash
git clone https://github.com/guoqiao/dot.git ~/.dot && cd ~/.dot
```
Or if you prefer ssh:
```
git clone git@github.com:guoqiao/dot.git ~/.dot && cd ~/.dot
```

### Ubuntu

Install basic deps:
```
sudo apt install -y make zsh
```
change shell to zsh if not yet:
```
echo $SHELL | grep zsh || chsh -s $(which zsh)
```
NOTE: You may need to logout if you changed your shell.

Verify shell is zsh:
```
echo $SHELL
```
Now run:
```
make ubuntu
```

### macOS

Just run:
```
make mac
```

### Persist $PATH
At the end, on either Ubuntu or macOS, run this to print `$PATH` and add to top of your `.zshrc`:
```bash
make path
```

## Git Hooks

This repo uses [prek](https://prek.j178.dev/) for Git hooks.

Install it with Homebrew and set up the hooks:

```bash
make hooks
```

Run the hooks manually across the repo:

```bash
make hooks-run
```

Update hook revisions:

```bash
make hooks-update
```

`prek` uses this repo's existing `.pre-commit-config.yaml`, so no config rename is required.
