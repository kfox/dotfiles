#!/bin/bash

# shellcheck source=/dev/null

[ -e "${HOME}/.bashrc" ] && . "${HOME}/.bashrc"
[ -e "${HOME}/.bash_aliases" ] && . "${HOME}/.bash_aliases"
[ -e "${HOME}/.bash_local" ] && . "${HOME}/.bash_local"

bind -f "${HOME}/.inputrc"

test -e "${HOME}/.iterm2_shell_integration.bash" && source "${HOME}/.iterm2_shell_integration.bash"
