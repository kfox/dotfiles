# essentials
alias ls='ls -aFG'
alias ll='ls -lh'
alias c='clear'
alias less='less -R'

# ls replacement
alias e='exa -bghla --git --color-scale --group-directories-first'

# rails-specific aliases
alias be='bundle exec'
alias ber='bundle exec rails'

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
