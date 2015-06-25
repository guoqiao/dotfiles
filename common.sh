#!/bin/bash
DOTFILES="$HOME/dotfiles"

VIMSRC="$DOTFILES/.vim"
VIMDST="$HOME/.vim"

mkdir -p $VIMDST
cd $VIMDST
ln -is $VIMSRC/vimrc
ln -is $VIMSRC/install.sh
ln -is $VIMSRC/update.sh

cd $HOME
ln -is $DOTFILES/.zshrc
ln -is $DOTFILES/.gitconfig
ln -is $DOTFILES/.tmux.conf

cd /tmp
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
