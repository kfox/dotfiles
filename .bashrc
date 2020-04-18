#!/usr/bin/env bash
################################################################################
#
# FUNCTIONS
#
################################################################################

#
# serve files via web server
#
# usage: serve [documentroot] [port]
#

function serve {
  dir="${1:-.}"
  port="${2:-8080}"
  if [ -n "$(command -v http-server)" ]; then
    # to make this work: brew install http-server
    http-server -r -c-1 --cors "$dir" -p "$port"
  else
    ruby -run -e httpd "$dir" -p "$port"
  fi
}

#
# open the appropriate GitHub repository home page
#
# usage: gh [repo]
#
#  - in a repo directory with no arguments, goes to the repo home page
#  - if repo argument is given and doesn't have a slash, use the first
#    result from the github API
#  - if repo argument is given and includes the username, just go
#    directly to that repo
#

function gh {
  repo="$1"

  if [ -z "$repo" ]; then
    # if no argument provided, then get the
    # URL of the repo in your current working directory
    repo=$(git ls-remote --get-url 2>/dev/null)
    [ $? -ne 0 ] && { echo "Not in a git repo."; return; }

    if [[ $repo == *"git@github.com"* ]]; then
      repo=${repo/git@github.com:/https:\/\/github.com/}
      repo=${repo/.git//}
    fi
  elif [[ $repo != *\\/* ]]; then
    # arg format: vim-vinegar
    repo=$(curl -s -X GET "https://api.github.com/search/repositories?q=$repo&fork=false&in=html_url&order=desc" | python -c 'import sys,json;data=json.loads(sys.stdin.read()); print(data["items"][0]["html_url"])')
  else
    # arg format: tpope/vim-vinegar
    repo="https://github.com/$repo"
  fi

  # open the URL in your default browser (Ubuntu)
  # xdg-open $repo (or possibly gnome-open $repo)

  # open the URL in your default browser (macOS)
  open "$repo"
}

#
# in a git repo, compare current branch to another branch on github.com
#
# usage: gpr
#

function gpr {
  local repo
  local branch
  local title

  repo=$(git ls-remote --get-url 2>/dev/null)
  branch=$(git branch --no-color --contains HEAD 2>/dev/null | awk '{ print $2 }')
  title=$(git log -1 --pretty=%B | tr -d '\n')

  if [[ $repo == *"git@github.com"* ]]; then
    repo=${repo/git@github.com:/https:\/\/github.com/}
    repo=${repo/.git/}
  fi

  if [ -n "${repo}" ] && [ -n "${branch}" ]; then
    local url="${repo}/compare/${branch}?expand=1&title=${title}"
    echo "${url}" | pbcopy
    open "${url}"
  else
    echo "Not in a git repository."
  fi
}

#
# set up variables for iterm2 git repo badges
#
# more info: https://www.iterm2.com/documentation-badges.html
#

function iterm2_print_user_vars() {
  iterm2_set_user_var gitRepo "$(git config --get remote.origin.url | xargs basename -s .git)"
  iterm2_set_user_var gitBranch "$(git rev-parse --abbrev-ref HEAD 2>/dev/null | xargs)"
  iterm2_set_user_var nodeVersion "$(if command -v node >/dev/null 2>&1; then node -v; else echo -n 'Not installed'; fi)"
  iterm2_set_user_var rubyVersion "$(if command -v rbenv >/dev/null 2>&1; then (rbenv version | cut -d ' ' -f1); else ruby -v; fi)"
  iterm2_set_user_var pythonVersion "$(python --version 2>&1 | cut -d ' ' -f2)"
}

################################################################################
#
# PROMPT
#
################################################################################

# use a colorized prompt and put some info in the title/tab bar
export STARTPROMPT='\e]0;\W\007\e[31;01m \w\e[0m'
export ENDPROMPT='\n\[\e[32;01m\]⮑\[\e[0m\]  '
export PS1="${STARTPROMPT}${ENDPROMPT}"
export PS2='> '
export PS4='+ '

if [ -f "/usr/local/opt/bash-git-prompt/share/gitprompt.sh" ]; then
  export GIT_PROMPT_ONLY_IN_REPO=1
  # export GIT_PROMPT_SHOW_UPSTREAM=1

  export GIT_PROMPT_THEME=Custom
  export GIT_PROMPT_THEME_FILE=~/.git-prompt-colors.sh

  source /usr/local/opt/bash-git-prompt/share/gitprompt.sh
fi

################################################################################
#
# ENVIRONMENT VARIABLES AND SHELL BEHAVIOR
#
################################################################################

# set up the path
export PATH="/usr/local/share/npm/bin:/usr/local/opt/go/libexec/bin:$HOME/go/bin:$HOME/.cargo/bin:/usr/local/sbin:$HOME/bin:$PATH"

export CDPATH=.

# customize the directory listing colors
export LSCOLORS=GxFxCxDxBxegedabagacad

# Correct minor typos in a cd command
shopt -s cdspell

# Enable egrep-style extended pattern matching
shopt -s extglob

# grep stuff
export GREP_OPTIONS="--binary-files=without-match --directories=skip --color=auto"

# keep a lot more history than the default 500 previous commands
export HISTSIZE=10000
export HISTFILESIZE=10000
export HISTCONTROL=ignoreboth

# trim the number of directories shown in a prompt
export PROMPT_DIRTRIM=3

# Golang stuff
export GOPATH=$HOME/go

# rbenv setup
export PATH="$HOME/.rbenv/bin:$PATH"
hash rbenv 2>/dev/null && eval "$(rbenv init -)" >/dev/null

# bash shell command completion
[ -f "$(brew --prefix)/etc/bash_completion" ] && . "$(brew --prefix)/etc/bash_completion"

# python virtualenv setup
if [ -x /usr/local/bin/virtualenvwrapper.sh ]; then
  export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3
  export WORKON_HOME=$HOME/.virtualenvs
  export PROJECT_HOME=$HOME/src
  source /usr/local/bin/virtualenvwrapper.sh
fi

# use z to track most-used directories and jump around more easily than
# with cd
source "$(brew --prefix)/etc/profile.d/z.sh"

# enable direnv
eval "$(direnv hook bash)"
