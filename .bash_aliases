# essentials
alias ls='ls -aFG'
alias ll='ls -l'
alias c='clear'

# rails-specific aliases
alias be='bundle exec'
alias ber='bundle exec rails'

# macvim
alias vt='mvim --remote-tab'

# git-related aliases
alias gd='git diff'
alias gdf='git diff --follow'
alias gp='git pull'
alias gs='git status --ignore-submodules=dirty'

# dotfile management
alias config='git --git-dir=$HOME/.managed-config --work-tree=$HOME'
