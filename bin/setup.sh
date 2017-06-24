#!/bin/bash

pushd ~ >/dev/null 2>&1

echo "==> installing Homebrew"
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew tap Homebrew/bundle
brew bundle

ruby_version=$(rbenv install -l | egrep '^\s+\d+\.\d+\.\d+$' | tail -1 | tr -d ' ')
echo "==> installing Ruby ${ruby_version}"
rbenv install ${ruby_version}
rbenv global ${ruby_version}

node_modules=(
  eslint
  nodemon
  npm-check-updates
  stylelint
  trevor
)

for module in "${node_modules[@]}"
do
  echo "==> installing Node module: ${module}"
  npm install -g ${module}
done

# create the backup directory for Vim
mkdir -p ~/.vim/backup

popd >/dev/null 2>&1
