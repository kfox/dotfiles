# Kelly Fox's dotfiles

These are the files I use to make the terminal a happy place to live.
:heart:

Follow these directions to set up: https://developer.atlassian.com/blog/2016/02/best-way-to-store-dotfiles-git-bare-repo/

**NOTE:** I highly encourage the use of [iTerm2](https://www.iterm2.com/)
instead of the basic Terminal.app that comes with macOS. This will make
your life on the command-line much easier.

## What do we have here?

### Bash

#### `.bash_profile`

* A simple wrapper to load `.bashrc` and `.bash_aliases`

#### `.bashrc`

The guts of my Bash setup. Here's what it does for you:

##### Functions

* `serve` lets you serve files using a simple web server in the current
  directory or a directory you specify. Usage: `serve [documentroot]
  [port]`. The `documentroot` defaults to the current directory and the
  port defaults to `8080`.

* `st` launches [SourceTree](https://www.sourcetreeapp.com/) using your
  current repository, regardless of your current directory depth.

* `gh` is a handy way to open the appropriate respository home page for
  projects on github.com via the command line. It works in three different
  modes:

  1. Without arguments and in a git repository, it will open the project
     home page on github.com
  2. With an argument of a project name, e.g. `vim-vinegar`, it will use
     the github API to find the URL of the repo most likely to be the one
     you're looking for, then opens that project's home page. Best used
     when feeling lucky.
  3. With an argument like username/repo, e.g. `tpope/vim-vinegar`, it
     will just open that repo

* `gpr` will compare the current branch to another branch on github.com,
  assuming you're in a repo

##### Environment

Lots of environment variables are set to do many things.

* The main thing here is the git-repo-friendly prompt courtesy of
  [bash-git-prompt](https://github.com/magicmonty/bash-git-prompt). You
  may want to tweak the colors/symbols to your liking.

* The paths are set up for `npm`, `node`, `go`, and `rbenv`

* The `GREP_OPTIONS` are given some degree of sanity

* Your shell command history is constrained to 10000 commands

* Minor typos in `cd` commands will be auto-corrected when possible

* Several other things are initialized, e.g.
  [virtualenv](http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/)
  for Python, [rbenv](https://github.com/rbenv/rbenv) for Ruby, shell
  integration for [iTerm2](https://www.iterm2.com/),
  [bash-completion](https://github.com/scop/bash-completion),
  and [z](https://github.com/rupa/z).

#### `.bash_aliases`

Nothing overwhelming here.

* Make `ls` output more useful. Show all directories and use some color
  while doing it.

* Add the `ll` alias because I fell in love with it while using Linux
  systems

* "Clear the screen" just by typing `c`

* Add a couple of Rails and git aliases. The keystrokes you save may be
  your own.

#### `.editrc`

* Lets you use <kbd>Ctrl</kbd>-R to search backward through your
  entire command history

#### `.inputrc`

* Ignores case when tab-completing directories and filenames

* Disables the terminal bell

* Sets the default command-line editing mode to use vim keybinds
  instead of emacs, e.g. hit <kbd>Esc</kbd>-`k` to enter edit mode,
  then `k` to move back through your command history or other `vi`
  command-mode commands to move and edit the current commmand.

* Shows all matches if your tab-completion would be ambiguous

### Ruby configuration files

.gemrc
.irbrc
.pryrc

### Git configuration files

.gitconfig
.gitignore_global

### Vim configuration files

.vimrc
.vimrc.pager
.gvimrc
.gvimrc.pager
.vim/colors/kelly.vim
.vim/colors/kellys.vim

### Homebrew Bundle

Brewfile

## Scripts

bin/bing-wallpaper.sh
bin/colors
bin/excuse
bin/logicprefs
bin/mkbr
bin/mkfavicon
bin/mvbr
bin/ql
bin/reassociate
bin/rmbr
bin/sayphrase
bin/svg-to-data-uri.sh
bin/svim
bin/updall

### Miscellaneous configuration files

#### `.eslintrc`

Some defaults for [ESLint](https://github.com/eslint/eslint). Probably
will be changing this a lot.

#### `.ptconfig.toml`

Some settings for use with the `pt` command, a.k.a. [The Platinum
Searcher](https://github.com/monochromegane/the_platinum_searcher).
