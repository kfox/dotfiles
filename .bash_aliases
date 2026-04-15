# essentials
alias ls='ls -aF'
alias ll='ls -alh'
alias c='clear'
alias less='less -R'

# git-related aliases
alias gd='git diff'
alias gdc='git diff --cached'
alias gdf='git diff --follow'
alias gp='git rm-merged && git pull'
alias gs='git status --ignore-submodules=dirty'

# location of the git files for the bare dotfiles repo
alias config='git --git-dir=$HOME/.repo --work-tree=$HOME'

alias tf='terraform'
alias k='kubectl'
complete -F __start_kubectl k
