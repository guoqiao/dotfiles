DOTFILES="$HOME/Dropbox/dotfiles"

cd "$HOME/.config/sublime-text-3/Packages/User"
pwd
ln -is $DOTFILES/.vintageousrc
ln -is $DOTFILES/Preferences.sublime-settings
