#!/usr/bin/env bash

# shellcheck source=/dev/null
if [ -n "$PS1" ]; then
  [ -e "${HOME}/.bashrc" ] && . "${HOME}/.bashrc"
  [ -e "${HOME}/.bash_aliases" ] && . "${HOME}/.bash_aliases"
  [ -e "${HOME}/.bash_local" ] && . "${HOME}/.bash_local"

  bind -f "${HOME}/.inputrc"
fi

[ -e ~/.iterm2_shell_integration.bash ] && source ~/.iterm2_shell_integration.bash
