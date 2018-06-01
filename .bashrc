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
  if [ -n "$(which http-server)" ]; then
    # to make this work: brew install http-server
    http-server -r -c-1 --cors $dir -p $port
  else
    ruby -run -e httpd $dir -p $port
  fi
}

#
# open SourceTree
#

function st {
  dir=$(git rev-parse --show-toplevel 2>/dev/null)

  [ $? -ne 0 ] && { echo "Not in a git repo."; return; }

  command -v stree >/dev/null 2>&1 && stree $dir || {
    echo "Please install SourceTree first!"
    open https://www.sourcetreeapp.com/
  }
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
  elif [[ $repo != *\/* ]]; then
    # arg format: vim-vinegar
    repo=$(curl -s -X GET "https://api.github.com/search/repositories?q=$repo&fork=false&in=html_url&order=desc" | python -c 'import sys,json;data=json.loads(sys.stdin.read()); print(data["items"][0]["html_url"])')
  else
    # arg format: tpope/vim-vinegar
    repo="https://github.com/$repo"
  fi

  # open the URL in your default browser (Ubuntu)
  # xdg-open $repo (or possibly gnome-open $repo)

  # open the URL in your default browser (macOS)
  open $repo
}

#
# in a git repo, compare current branch to another branch on github.com
#
# usage: gpr
#

function gpr {
  local repo=$(git ls-remote --get-url 2>/dev/null)
  local branch=$(git branch --no-color --contains HEAD 2>/dev/null | awk '{ print $2 }')
  local title=$(git log -1 --pretty=%B | tr -d '\n')

  if [[ $repo == *"git@github.com"* ]]; then
    repo=${repo/git@github.com:/https:\/\/github.com/}
    repo=${repo/.git/}
  fi

  if [ -n "${repo}" -a -n "${branch}" ]; then
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
  iterm2_set_user_var gitRepo $(git remote -v 2>/dev/null | grep fetch | sed -E -e 's#^.*/(.*)$#\1#' -e 's/.git .*$//' 2>/dev/null)
  iterm2_set_user_var gitBranch $(git branch --no-color --contains HEAD 2>/dev/null | grep '^\*' | awk '$2=="(HEAD" { print $5 } $2!="(HEAD" { print $2 }' | tr -d ')')
}


################################################################################
#
# PROMPT
#
################################################################################

# use a colorized prompt and put some info in the title/tab bar
export MAINPROMPT='\e]0;$(basename $PWD)\007\e[33;01m\u\e[37;02m:\e[0m\e[31;01m\w\e[0m'
export PS1="$MAINPROMPT\n$ "
export PS2='> '
export PS4='+ '

if [ -f "/usr/local/opt/bash-git-prompt/share/gitprompt.sh" ]; then
  GIT_PROMPT_ONLY_IN_REPO=1
  # GIT_PROMPT_SHOW_UPSTREAM=1

  GIT_PROMPT_THEME=Custom
  GIT_PROMPT_THEME_FILE=~/.git-prompt-colors.sh

  source /usr/local/opt/bash-git-prompt/share/gitprompt.sh
fi

################################################################################
#
# ENVIRONMENT VARIABLES AND SHELL BEHAVIOR
#
################################################################################

# set up the path
export PATH="/usr/local/share/npm/bin:/usr/local/opt/go/libexec/bin:$HOME/.cargo/bin:/usr/local/bin:$HOME/bin:$PATH"

export CDPATH=.

# customize the directory listing colors
export LSCOLORS=GxFxCxDxBxegedabagacad

export NODE_PATH=/usr/local/lib/node:/usr/local/lib/node_modules
# node >= 8.2
export NODE_OPTIONS="--abort-on-uncaught-exception"

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

# Golang stuff
export GOPATH=$HOME/go
export PATH=$PATH:/usr/local/opt/go/libexec/bin:$HOME/go/bin

# rbenv setup
export PATH="$HOME/.rbenv/bin:$PATH"
command -v rbenv >/dev/null 2>&1 && eval "$(rbenv init -)"

# bash shell command completion
[ -f $(brew --prefix)/etc/bash_completion ] && . $(brew --prefix)/etc/bash_completion

# apex autocomplete
_apex()  {
  COMPREPLY=()
  local cur="${COMP_WORDS[COMP_CWORD]}"
  local opts="$(apex autocomplete -- ${COMP_WORDS[@]:1})"
  COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
  return 0
}

complete -F _apex apex

# python virtualenv setup
if [ -x /usr/local/bin/virtualenvwrapper.sh ]; then
  export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3
  export WORKON_HOME=$HOME/.virtualenvs
  export PROJECT_HOME=$HOME/src
  source /usr/local/bin/virtualenvwrapper.sh
fi

# use z to track most-used directories and jump around more easily than
# with cd
source `brew --prefix`/etc/profile.d/z.sh

# enable direnv
eval "$(direnv hook bash)"
