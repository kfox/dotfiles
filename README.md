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

* Open a file in a new tab of an existing MacVim window using `vt`

* Add a couple of Rails and git aliases. The keystrokes you save may be
  your own.

#### `.editrc`

* Lets you use <kbd>Ctrl</kbd>-<kbd>R</kbd> to search backward through your
  entire command history

#### `.inputrc`

* Ignores case when tab-completing directories and filenames

* Disables the terminal bell

* Sets the default command-line editing mode to use vim keybinds
  instead of emacs, e.g. hit <kbd>Esc</kbd>-<kbd>K</kbd> to enter
  edit mode, then <kbd>K</kbd> again to move back through your
  command history or other `vi` command-mode commands to move and
  edit the current commmand.

* Shows all matches if your tab-completion would be ambiguous

### Ruby configuration files

* `.gemrc` will not auto-install rubydocs when you install a gem

* `.irbrc` enables readline support, with a simple prompt, and enables
  [awesome_print](https://github.com/awesome-print/awesome_print) by
  default

* `.pryrc` adds some spiffy prompt stuff and a few convenience methods

### Git configuration files

The `.gitignore_global` file specifies filename patterns to ignore
globally, and is specified in the `.gitconfig` file.

In addition to setting up MacVim to be used as your difftool, the
`.gitconfig` file also defines several handy aliases:

* `alias` will add a new alias, e.g. `git alias <alias> <original
  command>`

* `aliases` will list all defined aliases

* `br` is short for `branch`

* `changes` is a more concise way of showing changed files and their
  status

* `ci` is short for `commit`

* `co` is short for `checkout`

* `dc` will show a diff of staged changes

* `df` is short for `diff`

* `diffstat` shows the number of additions/deletions per file

* `history` shows a complete diff history for each commit of a given
  file, e.g. `git history package.json`

* `laststash` shows the diff of the most recent stash against the
  current branch

* `lc` gives you an annotated log of changes to file(s) or the repo

* `lg` is a log with "graphing", showing merges and commits with lots of
  pretty colors :rainbow:

* `new` is a shorter way to create a new branch

* `rm-merged` will locally delete merged branches

* `st` is short for `status`

* `undo-commit` will undo the most recent commit

* `whatis` shows the commit message and date for a given sha commit hash

* `whatsnew` displays the most recent commit message, author, and date

* `who` shows the number of commits per committer. Will make use of a
  `~/.mailmap` file if present to deduplicate and aggregate user names.

* `whois` gives you the full name and email address of a user if you
  provide a username

### Vim configuration files

* .vimrc
* .vimrc.pager
* .gvimrc
* .gvimrc.pager
* .vim/colors/kelly.vim
* .vim/colors/kellys.vim

### Homebrew

My [Homebrew](https://brew.sh/) environment is preserved by way of
[Homebrew Bundle](https://github.com/Homebrew/homebrew-bundle) which
uses the `Brewfile` to specify formulae and casks to be installed.

## Scripts

These scripts are all located in the `bin` directory.

* `bing-wallpaper.sh` will download the latest
  [Bing Homepage image](http://www.bing.com/gallery/)
  to your `~/Pictures/Bing` directory and sets your primary desktop
  background to that image. Add it to a cron job for a fresh picture
  every day.

* `colors` shows a color palette so you can tweak your terminal colors

* `excuse` generates a programmer's excuse, for example:
  ```bash
  git commit -m "$(excuse.sh)"
  ```

* `logicprefs` makes backups of your
  [Logic Pro X](https://www.apple.com/logic-pro/) preferences, and lets
  you restore them in case you happen to jack them up.

* `mkbr` creates a new git branch

* `mkfavicon` generates a `favicon.ico` file at all the different
  resolutions you probably will ever need

* `mvbr` renames a git branch

* `ql` is an easy way to use the macOS
  [Quick Look](https://support.apple.com/kb/PH25575) functionality from
  the command line

* `reassociate` will associate source code file extensions with
  MacVim so you can <kbd>Command</kbd>-click a filename in iTerm2 and
  have it open up in MacVIm

* `rmbr` deletes a git branch, locally and remotely

* `sayphrase` says something using the built-in macOS speech synthesis

* `svg-to-data-uri.sh` will take an SVG and URL-encode it for use in a
  data: URI. Full base64 encoding isn't necessary.

* `svim` launches MacVim with the session saved in `Session.vim`

* `updall` updates homebrew, npm global installs, and MacVim plugins

### Miscellaneous configuration files

#### `.eslintrc`

Some defaults for [ESLint](https://github.com/eslint/eslint). Probably
will be changing this a lot.

#### `.ptconfig.toml`

Some settings for use with the `pt` command, a.k.a. [The Platinum
Searcher](https://github.com/monochromegane/the_platinum_searcher).
