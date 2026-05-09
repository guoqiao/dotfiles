export PATH=~/.dot/bin:~/.dot/.venv/bin:~/bin:~/.local/bin:~/.npm-global/bin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH

# zsh generic config, add custom config into ~/.localrc
export ZSH="$HOME/.oh-my-zsh"
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="bira"
DISABLE_MAGIC_FUNCTIONS="true"

plugins=(
    brew
    uv
    git
    tig
    direnv
    history
    tmux
    eza
    zoxide
    zsh-autosuggestions
)

source $ZSH/oh-my-zsh.sh

# ctrl + r
# eval "$(mcfly init zsh)"

export LANG=en_US.UTF-8
export EDITOR='vim'
# for XQuantz to use for X11
export DISPLAY=:0

# Compilation flags
# export ARCHFLAGS="-arch $(uname -m)"

# funcs
mkcd() {
    mkdir -p $1;
    cd $1
}

mktmp() {
    cd $(mktemp -d);
}

alias k="kubectl"
alias gti="git"
alias wip="git commit -nm wip"
# cd to git root
alias gg='cd "$(git rev-parse --show-toplevel)"'

alias m="make"
alias maek="make"

alias ff="readlink -f"
alias ab="agent-browser"

# list docker images with time
alias lsi="docker image ls --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}""

# for local config:
# source ~/.envrc.d/deepseek/.envrc

