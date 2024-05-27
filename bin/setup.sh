#!/usr/bin/env bash

pushd ~ >/dev/null 2>&1 || exit 1

echo "==> installing Homebrew"
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew tap Homebrew/bundle

echo "==> installing Homebrew formulae"
brew bundle

echo "==> installing crontab"
/usr/bin/crontab "${HOME}/.crontab"

popd >/dev/null 2>&1 || exit 1
