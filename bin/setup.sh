#!/bin/bash

pushd ~ >/dev/null 2>&1

echo "==> installing Homebrew"
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew tap Homebrew/bundle

echo "==> installing Homebrew formulae"
brew bundle

ruby_version=$(rbenv install -l | egrep '^\s+\d+\.\d+\.\d+$' | tail -1 | tr -d ' ')
echo "==> installing Ruby ${ruby_version}"
rbenv install ${ruby_version}
rbenv global ${ruby_version}

echo "==> installing Node modules"

node_modules=(
  eslint
  nodemon
  npm-check-updates
  standard
  stylelint
  trevor
)

for module in "${node_modules[@]}"
do
  echo "==> installing Node module: ${module}"
  npm install -g ${module}
done

echo "==> setting up Python virtual environments"
/usr/local/bin/pip3 install virtualenvwrapper
export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3
export PROJECT_HOME=$HOME/src
export WORKON_HOME=$HOME/.virtualenvs
mkdir -p ${WORKON_HOME}
source /usr/local/bin/virtualenvwrapper.sh

echo "==> setting up Vim"

# create the backup directory for Vim
mkdir -p ~/.vim/backup

# install vim-plug
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

# install all vim plugins and exit vim
/usr/local/bin/vim +PlugInstall +qall

popd >/dev/null 2>&1
