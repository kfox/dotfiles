#!/bin/bash

pushd ~ >/dev/null 2>&1

echo "==> installing Homebrew"
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
/usr/local/bin/brew tap Homebrew/bundle

echo "==> installing Homebrew formulae"
/usr/local/bin/brew bundle

ruby_version=$(rbenv install -l | egrep '^\s+\d+\.\d+\.\d+$' | tail -1 | tr -d ' ')
echo "==> installing Ruby ${ruby_version}"
/usr/local/bin/rbenv install ${ruby_version}
/usr/local/bin/rbenv global ${ruby_version}

echo "==> installing crontab"
/usr/bin/crontab ${HOME}/.crontab

echo "==> installing global Node modules"

node_modules=(
  caniuse-cmd
  deps-report
  generator-code
  http-server
  jsinspect
  json-diff
  js-yaml
  npm-check-updates
  prettier
  react-native-cli
  stylelint
  typescript
  typescript-language-server
  uglify-js
  xml-json
)

for module in "${node_modules[@]}"
do
  echo "==> installing Node module: ${module}"
  /usr/local/bin/npm install -g ${module}
done

echo "==> setting up Go environment"
mkdir ~/go

echo "==> setting up Python virtual environments"

/usr/local/bin/pip3 install virtualenvwrapper
export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3
export PROJECT_HOME=$HOME/src
export WORKON_HOME=$HOME/.virtualenvs
mkdir -p ${WORKON_HOME}
source /usr/local/bin/virtualenvwrapper.sh

popd >/dev/null 2>&1
