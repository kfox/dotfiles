# essentials
alias ls='ls -aFG'
alias ll='ls -l'
alias c='clear'

# ls replacement
alias e='exa -bghla --git --color-scale --group-directories-first'

# rails-specific aliases
alias be='bundle exec'
alias ber='bundle exec rails'

# macvim
alias vt='mvim --remote-tab'

# git-related aliases
alias gd='git diff'
alias gdf='git diff --follow'
alias gp='git rm-merged && git pull'
alias gs='git status --ignore-submodules=dirty'

# dotfile management
alias config='git --git-dir=$HOME/.managed-config --work-tree=$HOME'

alias tf='terraform'
alias k='kubectl'
complete -F __start_kubectl k
