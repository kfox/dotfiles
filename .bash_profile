#!/bin/bash

[ -f $HOME/.bashrc ] && . $HOME/.bashrc
[ -f $HOME/.bash_aliases ] && . $HOME/.bash_aliases

test -e "${HOME}/.iterm2_shell_integration.bash" && source "${HOME}/.iterm2_shell_integration.bash"
