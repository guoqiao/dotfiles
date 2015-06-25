DOTFILES="$HOME/Dropbox/dotfiles"

cd "$HOME/Library/Application Support/Sublime Text 3/Packages/User"
pwd
ln -is $DOTFILES/.vintageousrc
ln -is $DOTFILES/Preferences.sublime-settings
