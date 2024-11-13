#!/usr/bin/env bash

# shellcheck source=/dev/null
if [[ $- == *i* ]]; then
  [[ -f ${HOME}/.bashrc ]] && . "${HOME}/.bashrc"
  [[ -f ${HOME}/.bash_aliases ]] && . "${HOME}/.bash_aliases"
  [[ -f ${HOME}/.bash_local ]] && . "${HOME}/.bash_local"

  bind -f "${HOME}/.inputrc"
fi

[ -e ~/.iterm2_shell_integration.bash ] && source ~/.iterm2_shell_integration.bash
