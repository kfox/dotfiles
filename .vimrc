if (has('termguicolors'))
  set termguicolors
endif

" every autocmd below goes in this group, so re-sourcing replaces them
" rather than stacking another copy of each
augroup vimrc
  autocmd!
augroup END

let mapleader = ','

cabbrev help tab help

""""""""""""""""" Vim Tweaking

" Quickly edit/reload the vimrc file
nmap <silent> <leader>ev :e $MYVIMRC<CR>
nmap <silent> <leader>sv :so $MYVIMRC<CR>

" Highlight matching parens
set showmatch

" Disable Ex mode (who/what still uses this?)
nnoremap Q <nop>

""""""""""""""""" Encoding
set encoding=utf-8

""""""""""""""""" Clipboard
if !has('nvim')
  set clipboard=unnamed
endif

if has('nvim')
  set clipboard+=unnamedplus
endif

""""""""""""""""" Whitespace
set shiftround
set tabstop=2 shiftwidth=2 softtabstop=2
set expandtab
set smarttab
set smartindent
" set list listchars=tab:»·,trail:·,precedes:<,extends:>
if has('multi_byte') && &encoding ==# 'utf-8'
  " set list listchars=tab:\|·,trail:·,precedes:<,extends:>
  set list
  let &listchars = 'tab:⌐·,extends:»,precedes:«,nbsp:±,trail:·'
  let &fillchars = 'diff:▚'
  " let &showbreak = '↪ '
endif
set backspace=start,indent,eol

""""""""""""""""" Search
set hlsearch
set incsearch
set ignorecase
set smartcase

""""""""""""""""" Status Bar
set laststatus=2
set report=0
set noshowcmd
set noshowmode

""""""""""""""""" Terminal
set mouse=a
set ttimeoutlen=10     " Esc leaves insert mode without a visible pause
set lazyredraw         " don't redraw mid-macro or across multi-cursor edits
set synmaxcol=300      " stop highlighting past column 300 (minified files)

if !has('nvim')
  set ttymouse=xterm2
endif

""""""""""""""""" Visual Junk
set ruler
set visualbell
set noerrorbells
set cursorline

""""""""""""""""" Completion
set wildmenu
set wildmode=list:longest,full
set wildignore+=*.o,.git,*.class,*.gif,*.png,*.jpg,*.pyc
set wildignore+=*/tmp/*,*.so,*.swp,*.zip

""""""""""""""""" Folding
set foldmethod=indent
set foldnestmax=3
set nofoldenable

" Enable folding with the spacebar
" nnoremap <space> za

""""""""""""""""" Line Numbering
set number
set relativenumber
nmap <silent> <leader>n :set nonumber! norelativenumber!<CR>

""""""""""""""""" Window Title
set title
if !has("gui_macvim")
  set t_ts=k
  set t_fs=\
  autocmd vimrc BufEnter * let &titlestring = 'Vim - ' . expand("%:t")
endif

""""""""""""""""" viminfo and history
if !has('nvim')
  set history=1000
  set viminfo='10,\"100,:20,%,n~/.viminfo
endif

""""""""""""""""" modeline config
set modeline
set modelines=10

""""""""""""""""" default directories
set backupdir=~/.vim/backup
set directory=~/.vim/backup

""""""""""""""""" redraw and clear search
nnoremap <C-L> :nohls<CR><C-L>
inoremap <C-L> <C-O>:nohls<CR>

""""""""""""""""" Visual search
function! s:VSetSearch()

  let temp = @@
  norm! gvy
  let @/ = '\V' . substitute(escape(@@, '\'), '\n', '\\n', 'g')
  let @@ = temp

endfunction

vnoremap * :<C-u>call <SID>VSetSearch()<CR>//<CR>
vnoremap # :<C-u>call <SID>VSetSearch()<CR>??<CR>

""""""""""""""""" Initial cursor position

"jump to last cursor position when opening a file
"dont do it when writing a commit log entry
autocmd vimrc BufReadPost * call SetCursorPosition()
function! SetCursorPosition()
  if &filetype !~ 'commit\c'
      if line("'\"") > 0 && line("'\"") <= line("$")
          exe "normal! g`\""
          normal! zz
      endif
  end
endfunction

""""""""""""""""" diff mode
if &diff
  set diffopt+=iwhite
endif

""""""""""""""""" disable annoying keybinds
map K <nop>

""""""""""""""""" format options
set formatoptions=crql
" set formatoptions=crqn

""""""""""""""""" ctags

" vim-gutentags keeps the tags file current; this just walks the matches
map <C-\> :tnext<CR>
set tags+=tags;$HOME

""""""""""""""""" text wrapping

function! s:setupWrapping()
  setlocal wrap
  setlocal wrapmargin=2
  setlocal textwidth=72
endfunction

" Format text files
autocmd vimrc BufRead,BufNewFile *.txt call s:setupWrapping()

""""""""""""""""" file formatting

" These files are Ruby
autocmd vimrc BufRead,BufNewFile config.ru,{Brew,Gem,Guard,Rake,Thor}file set filetype=ruby

" PostgreSQL config
autocmd vimrc BufRead,BufNewFile .psqlrc set filetype=sql

" cson (coffeescript)
autocmd vimrc BufNewFile,BufRead *.cson set filetype=coffee

" various rc files (json)
autocmd vimrc BufNewFile,BufRead .{babel,eslint,stylelint}rc set filetype=json
autocmd vimrc BufNewFile,BufRead .{direnv,env}rc set filetype=sh

" make javascript prettier
" au FileType javascript set formatprg=prettier\ --stdin
" au BufWritePre *.js :normal gggqG
" au BufWritePre *.js exe 'normal! gggqG\<C-o>\<C-o>'

" md, markdown, and mk are markdown and define buffer-local preview
autocmd vimrc BufRead,BufNewFile *.{md,markdown,mdown,mkd,mkdn} call s:setupMarkup()

function! s:setupMarkup()
  call s:setupWrapping()
  nnoremap <buffer> <leader>p :Xmark<CR>
endfunction

" highlight code inside ```lang fences (vim-polyglot's markdown)
let g:vim_markdown_fenced_languages = [
  \ 'bash=sh', 'c', 'cpp', 'js=javascript', 'json', 'python', 'sh', 'vim', 'yaml'
  \ ]

" colored markdown headings and markup, in the One palette. Re-applied on
" every colorscheme load, since a colorscheme starts with :hi clear.
function! s:markdownColors()
  let l:c = &background ==# 'dark'
    \ ? {'red': '#e06c75', 'orange': '#d19a66', 'yellow': '#e5c07b',
    \    'green': '#98c379', 'cyan': '#56b6c2', 'blue': '#61afef',
    \    'purple': '#c678dd', 'gray': '#5c6370', 'codebg': '#2c313a'}
    \ : {'red': '#e45649', 'orange': '#986801', 'yellow': '#c18401',
    \    'green': '#50a14f', 'cyan': '#0184bc', 'blue': '#4078f2',
    \    'purple': '#a626a4', 'gray': '#a0a1a7', 'codebg': '#e5e5e6'}

  execute 'hi htmlH1 gui=bold guifg=' . l:c.red    . ' cterm=bold ctermfg=204'
  execute 'hi htmlH2 gui=bold guifg=' . l:c.orange . ' cterm=bold ctermfg=173'
  execute 'hi htmlH3 gui=bold guifg=' . l:c.yellow . ' cterm=bold ctermfg=180'
  execute 'hi htmlH4 gui=bold guifg=' . l:c.green  . ' cterm=bold ctermfg=114'
  execute 'hi htmlH5 gui=bold guifg=' . l:c.cyan   . ' cterm=bold ctermfg=38'
  execute 'hi htmlH6 gui=bold guifg=' . l:c.purple . ' cterm=bold ctermfg=170'
  execute 'hi mkdHeading guifg=' . l:c.gray . ' ctermfg=59'

  execute 'hi mkdCode guifg=' . l:c.green . ' guibg=' . l:c.codebg . ' ctermfg=114'
  execute 'hi mkdCodeDelimiter guifg=' . l:c.gray . ' ctermfg=59'
  hi! link mkdCodeStart mkdCodeDelimiter
  hi! link mkdCodeEnd   mkdCodeDelimiter

  execute 'hi mkdLink      gui=underline guifg=' . l:c.blue . ' cterm=underline ctermfg=39'
  execute 'hi mkdInlineURL gui=underline guifg=' . l:c.cyan . ' cterm=underline ctermfg=38'
  execute 'hi mkdURL guifg=' . l:c.cyan . ' ctermfg=38'
  execute 'hi mkdListItem gui=bold guifg=' . l:c.purple . ' cterm=bold ctermfg=170'
  execute 'hi mkdBlockquote gui=italic guifg=' . l:c.gray . ' cterm=italic ctermfg=59'
  execute 'hi mkdRule guifg=' . l:c.gray . ' ctermfg=59'

  hi htmlBold       gui=bold        cterm=bold
  hi htmlItalic     gui=italic      cterm=italic
  hi htmlBoldItalic gui=bold,italic cterm=bold,italic
endfunction

" highlights of my own, which the colorscheme's :hi clear would wipe too
function! s:customColors()
  highlight VertSplit ctermfg=242
  highlight BadWhitespace ctermbg=red guibg=red
  highlight VendorPrefix guifg=#00ffff gui=bold
endfunction

autocmd vimrc ColorScheme * call s:customColors() | call s:markdownColors()
autocmd vimrc Syntax markdown call s:markdownColors()

" crontab stuff
autocmd vimrc FileType crontab setlocal nobackup nowritebackup

" python
" au FileType python setl tabstop=4 shiftwidth=4 softtabstop=4 textwidth=99 colorcolumn=101
autocmd vimrc FileType python setl tabstop=4 shiftwidth=4 softtabstop=4
autocmd vimrc BufRead,BufNewFile *.py,*.pyw match BadWhitespace /^\t\+/
let g:pyindent_open_paren = 'shiftwidth()'
let python_highlight_all = 1

" -- virtualenv support
" python << EOF
" import os
" if 'VIRTUAL_ENV' in os.environ:
"    project_base_dir = os.environ['VIRTUAL_ENV']
"    activate_this = os.path.join(project_base_dir, 'bin/activate_this.py')
"    exec(compile(open(activate_this).read(), activate_this, 'exec'), dict(__file__=activate_this))
" EOF

""""""""""""""""" cscope

if has('cscope')
  set csprg=/opt/homebrew/bin/cscope
  set csto=0
  set cscopetag
  set nocscopeverbose
  " add any database in current directory
  if filereadable("cscope.out")
      cs add cscope.out
  " else add database pointed to by environment
  elseif $CSCOPE_DB != ""
      cs add $CSCOPE_DB
  endif
  set cscopeverbose

  if has('quickfix')
    set cscopequickfix=s-,c-,d-,i-,t-,e-
  endif

  " Using 'CTRL-spacebar' then a search type makes the vim window
  " split horizontally, with search result displayed in
  " the new window.

  nmap <C-Space>s :scs find s <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space>g :scs find g <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space>c :scs find c <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space>t :scs find t <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space>e :scs find e <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space>f :scs find f <C-R>=expand("<cfile>")<CR><CR>
  nmap <C-Space>i :scs find i ^<C-R>=expand("<cfile>")<CR>$<CR>
  nmap <C-Space>d :scs find d <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space>a :scs find a <C-R>=expand("<cword>")<CR><CR>

  " Hitting CTRL-space *twice* before the search type does a vertical
  " split instead of a horizontal one

  nmap <C-Space><C-Space>s
    \:vert scs find s <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space><C-Space>g
    \:vert scs find g <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space><C-Space>c
    \:vert scs find c <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space><C-Space>t
    \:vert scs find t <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space><C-Space>e
    \:vert scs find e <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space><C-Space>i
    \:vert scs find i ^<C-R>=expand("<cfile>")<CR>$<CR>
  nmap <C-Space><C-Space>d
    \:vert scs find d <C-R>=expand("<cword>")<CR><CR>
  nmap <C-Space><C-Space>a
    \:vert scs find a <C-R>=expand("<cword>")<CR><CR>

  " cnoreabbrev cfa cs add
  " cnoreabbrev cff cs find
  " cnoreabbrev cfk cs kill
  " cnoreabbrev cfr cs reset
  " cnoreabbrev cfs cs show
  " cnoreabbrev cfh cs help

  command! -nargs=0 Cscope cs add $VIMSRC/src/cscope.out $VIMSRC/src
endif

""""""""""""""""" session management

set sessionoptions-=folds      " don't track folds
set sessionoptions-=options    " don't track global and local values

" " Creates a session
" function! MakeSession()
"   let b:sessiondir = $HOME . '/.vim/sessions' . getcwd()
"   if (filewritable(b:sessiondir) != 2)
"     exe 'silent !mkdir -p ' b:sessiondir
"     redraw!
"   endif
"   let b:sessionfile = b:sessiondir . '/session.vim'
"   exe 'mksession! ' . b:sessionfile
" endfunction
"
" " Updates a session, but only if it already exists
" function! UpdateSession()
"   let b:sessiondir = $HOME . '/.vim/sessions' . getcwd()
"   let b:sessionfile = b:sessiondir . '/session.vim'
"   if (filereadable(b:sessionfile))
"     exe 'mksession! ' . b:sessionfile
"     echo 'updating session'
"   endif
" endfunction
"
" " Loads a session if it exists
" function! LoadSession()
"   if argc() == 0
"     let b:sessiondir = $HOME . '/.vim/sessions' . getcwd()
"     let b:sessionfile = b:sessiondir . '/session.vim'
"     if (filereadable(b:sessionfile))
"       exe 'source ' b:sessionfile
"     else
"       echo 'No session loaded.'
"     endif
"   else
"     let b:sessionfile = ''
"     let b:sessiondir = ''
"   endif
" endfunction
"
" au VimEnter * nested :call LoadSession()
" au VimLeave * :call UpdateSession()
" map <leader>m :call MakeSession()<CR>

""""""""""""""""" vim-gitgutter

" let g:gitgutter_highlight_lines = 1
let g:gitgutter_diff_args = '-w'

" not exactly a vim-gitgutter setting, but related
set updatetime=250

""""""""""""""""" CtrlP

let g:ctrlp_map = '<c-p>'
let g:ctrlp_cmd = 'CtrlP'
let g:ctrlp_use_caching = 0
" let g:ctrlp_clear_cache_on_exit = 0
" let g:ctrlp_cache_dir = $HOME.'/.vim/cache/ctrlp'
let g:ctrlp_match_func = { 'match': 'pymatcher#PyMatch' }
let g:ctrlp_match_window = 'bottom,order:btt,min:1,max:25,results:25'
let g:ctrlp_working_path_mode = 'ra'
let g:ctrlp_user_command = ['.git', 'git --git-dir=%s/.git ls-files -co --exclude-standard']
" let g:ctrlp_reuse_window = 'netrw'
let g:ctrlp_custom_ignore = {
  \ 'dir':  '\.git$\|bower_components\|node_modules\|log$\|tmp$\|vendor$',
  \ 'file': '\.so$\|\.dat$\|\.DS_Store$\|\.log$|\.ico$'
  \ }

""""""""""""""""" Tagbar

map <leader>c :TagbarToggle<CR>
let g:tagbar_autoclose   = 1
let g:tagbar_autofocus   = 1
let g:tagbar_autoshowtag = 1
let g:tagbar_compact     = 1
let g:tagbar_ctags_bin   = '/opt/homebrew/bin/ctags'
let g:tagbar_left        = 1
let g:tagbar_singleclick = 1
let g:tagbar_width       = 40

let g:tagbar_type_coffee = {
    \ 'ctagstype' : 'coffee',
    \ 'kinds'     : [
        \ 'c:classes',
        \ 'm:methods',
        \ 'f:functions',
        \ 'v:variables',
        \ 'f:fields',
    \ ]
\ }

""""""""""""""""" Dispatch

map <leader>t :Dispatch pytest %<CR>

""""""""""""""""" ripgrep

if executable('rg')
  set grepprg=rg\ --vimgrep\ --smart-case
  set grepformat=%f:%l:%c:%m
endif

" :Grep {pattern} [path...] fills the quickfix list and opens it
command! -nargs=+ -complete=file -bar Grep silent! grep! <args>|cwindow|redraw!

nnoremap <leader>f :Grep<Space>

""""""""""""""""" CSS

autocmd vimrc FileType css setlocal iskeyword+=-
autocmd vimrc FileType css match VendorPrefix /-\(moz\|webkit\|o\|ms\)-[a-zA-Z-]\+/

""""""""""""""""" Tabularize

nmap <leader>a= :Tabularize/=<CR>
vmap <leader>a= :Tabularize/=<CR>
nmap <leader>a: :Tabularize/:<CR>
vmap <leader>a: :Tabularize/:<CR>
nmap <leader>a:: :Tabularize/:\zs<CR>
vmap <leader>a:: :Tabularize/:\zs<CR>
nmap <leader>a, :Tabularize/,<CR>
vmap <leader>a, :Tabularize/,<CR>
nmap <leader>a<bar> :Tabularize/<bar><CR>
vmap <leader>a<bar> :Tabularize/<bar><CR>
inoremap <silent> <Bar>   <Bar><Esc>:call <SID>align()<CR>a

" automatically align tables delimited by pipe characters
function! s:align()
  let p = '^\s*|\s.*\s|\s*$'
  if exists(':Tabularize') && getline('.') =~# '^\s*|' && (getline(line('.')-1) =~# p || getline(line('.')+1) =~# p)
    let column = strlen(substitute(getline('.')[0:col('.')],'[^|]','','g'))
    let position = strlen(matchstr(getline('.')[0:col('.')],'.*|\s*\zs.*'))
    Tabularize/|/l1
    normal! 0
    call search(repeat('[^|]*|',column).'\s\{-\}'.repeat('.',position),'ce',line('.'))
  endif
endfunction

""""""""""""""""" vim-airline

" variable names                default contents
" ----------------------------------------------------------------------------
" let g:airline_section_a       (mode, crypt, paste, spell, iminsert)
" let g:airline_section_b       (hunks, branch)
" let g:airline_section_c       (bufferline or filename)
" let g:airline_section_gutter  (readonly, csv)
" let g:airline_section_x       (tagbar, filetype, virtualenv)
" let g:airline_section_y       (fileencoding, fileformat)
" let g:airline_section_z       (percentage, line number, column number)
" let g:airline_section_error   (ycm_error_count, syntastic, eclim)
" let g:airline_section_warning (ycm_warning_count, whitespace)
"
" " here is an example of how you could replace the branch indicator with
" " the current working directory, followed by the filename.
" let g:airline_section_b = '%{getcwd()}'
" let g:airline_section_c = '%t'

" call airline#init#bootstrap()

function! AirlineInit()
  " let g:airline_section_a = airline#section#create_left(['mode', 'iminsert'])
  " let g:airline_section_b = airline#section#create_left(['branch'])
  " let g:airline_section_c = '%4b,0x%-6B'
  " let g:airline_section_c = airline#section#create([])
  let g:airline_section_c = '%{synIDattr(synID(line("."),col("."),1),"name")!=""?synIDattr(synID(line("."),col("."),1),"name"):""}'
  " let g:airline_section_x = '%{synIDattr(synID(line("."),col("."),1),"name")!=""?synIDattr(synID(line("."),col("."),1),"name"):""}'
  " let g:airline_section_x = '%{fugitive#statusline()}'
  " let g:airline_section_y = '%{strlen(&ft)?&ft:"none"},%{&fileformat},%{strlen(&fenc)?&fenc:&enc}'
  " let g:airline_section_y = '%{strlen(&fenc)?&fenc:&enc}'
  let g:airline_section_z = airline#section#create(['%-14.( %l:%c/%L%)', ' ', '%<%P'])

  let g:airline#extensions#ale#enabled = 1

  if !exists('g:airline_symbols')
    let g:airline_symbols = {}
  endif

  let g:airline_symbols.crypt = '🔒'
  let g:airline_symbols.maxlinenr = '☰'
  let g:airline_symbols.spell = 'Ꞩ'
  let g:airline_symbols.notexists = '∄'
  let g:airline_symbols.whitespace = 'Ξ'
endfunction

autocmd vimrc User AirlineAfterInit call AirlineInit()

let g:airline_powerline_fonts = 1
let g:airline_theme = 'base16_isotope'
let g:airline_detect_paste = 1
let g:airline_inactive_collapse = 1
" let g:airline_skip_empty_sections = 1

" extensions
let g:airline_extensions = ['ale', 'branch', 'ctrlp', 'obsession', 'tagbar', 'virtualenv']
let g:airline#extensions#branch#displayed_head_limit = 10
let g:airline#extensions#obsession#indicator_text = '$'

let g:airline#parts#ffenc#skip_expected_string='utf-8[unix]'

let g:airline_mode_map = {
      \ '__' : '-',
      \ 'n'  : 'N',
      \ 'i'  : 'I',
      \ 'R'  : 'R',
      \ 'c'  : 'C',
      \ 'v'  : 'V',
      \ 'V'  : 'V',
      \ '' : 'V',
      \ 's'  : 'S',
      \ 'S'  : 'S',
      \ '' : 'S',
      \ }

""""""""""""""""" vim-easy-align

" xmap <CR> <plug>(LiveEasyAlign)
xmap ga <Plug>(EasyAlign)

" Start interactive EasyAlign in visual mode (e.g. vip<Enter>)
vmap <CR> <Plug>(EasyAlign)

" Start interactive EasyAlign for a motion/text object (e.g. gaip)
nmap ga <Plug>(EasyAlign)

""""""""""""""""" matchit

" use % to move between opening/closing block markers
packadd! matchit

""""""""""""""""" netrw
" disable netrw
let g:loaded_netrwPlugin = 1

let g:netrw_altv = 1
let g:netrw_banner = 0
let g:netrw_browse_split = 4
let g:netrw_liststyle = 3
let g:netrw_preview = 1
let g:netrw_sort_options = 'i'
let g:netrw_winsize = -30

" augroup ProjectDrawer
"   autocmd!
"   autocmd VimEnter * :Vexplore
" augroup END

""""""""""""""""" dirvish

let g:dirvish_mode = ':sort ,^.*[\/],'

augroup dirvish_events
  autocmd!

  " Map `t` to open in new tab.
  autocmd FileType dirvish
    \  nnoremap <silent><buffer> t :call dirvish#open('tabedit', 0)<CR>
    \ |xnoremap <silent><buffer> t :call dirvish#open('tabedit', 0)<CR>

  " Enable fugitive.vim in Dirvish buffers.
  autocmd FileType dirvish call FugitiveDetect(@%)

  " Map `gr` to reload.
  autocmd FileType dirvish nnoremap <silent><buffer>
    \ gr :<C-U>Dirvish %<CR>

  " Map `gh` to hide dot-prefixed files.  Press `R` to 'toggle' (reload).
  autocmd FileType dirvish nnoremap <silent><buffer>
    \ gh :silent keeppatterns g@\v/\.[^\/]+/?$@d _<cr>
augroup END

""""""""""""""""" delimitMate

let g:delimitMate_expand_cr = 1
let g:delimitMate_expand_space = 1
autocmd vimrc FileType html,javascript let b:delimitMate_insert_eol_marker = 2
autocmd vimrc FileType html,javascript let g:delimitMate_eol_marker = ';'

""""""""""""""""" vim-javascript

let g:javascript_plugin_jsdoc = 1

""""""""""""""""" nginx

autocmd vimrc BufRead,BufNewFile *.nginx,{nginx,default}.conf set filetype=nginx

""""""""""""""""" vim-indent-guides

let g:indent_guides_guide_size = 1
let g:indent_guides_start_level = 2

""""""""""""""""" ale

let g:ale_linters = {
\  'javascript': [
\    'standard'
\  ],
\  'javascriptreact': [
\    'standard'
\  ],
\  'python': [
\    'pylint'
\  ],
\  'rust': [
\    'cargo',
\    'rustc'
\  ],
\  'scss': [
\    'stylelint'
\  ]
\}

let g:ale_fixers = {
\  'javascript': [
\    'prettier',
\    'standard'
\  ],
\  'json': [
\    'prettier'
\  ],
\  'javascriptreact': [
\    'prettier',
\    'standard'
\  ],
\  'python': [
\    'black',
\    'isort',
\    'remove_trailing_lines'
\  ],
\  'scss': [
\    'prettier',
\    'stylelint'
\  ]
\}

" Bind F8 to fixing problems with ALE
nmap <F8> <Plug>(ale_fix)

let g:ale_sign_error = '❌'
let g:ale_sign_warning = '💩'
let g:ale_echo_msg_format = '[%linter%] %s'

" python
let g:ale_python_auto_pipenv = 1
let g:ale_python_pylint_auto_pipenv = 1
let g:ale_python_pylint_options = '--extension-pkg-whitelist=cv2 --generated-members=cv2'

nmap <silent> <C-k> <Plug>(ale_previous_wrap)
nmap <silent> <C-j> <Plug>(ale_next_wrap)

""""""""""""""""" vim-plug

let g:plug_window = 'tab new'

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" VIM-PLUG CONFIG
"
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" auto-install vim-plug and plugins
let data_dir = has('nvim') ? stdpath('data') . '/site' : '~/.vim'
if empty(glob(data_dir . '/autoload/plug.vim'))
  silent execute '!curl -fLo '.data_dir.'/autoload/plug.vim --create-dirs  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
  autocmd vimrc VimEnter * PlugInstall --sync | source $MYVIMRC
endif

call plug#begin('~/.vim/plugged')

Plug 'airblade/vim-gitgutter'
Plug 'bogado/file-line'
Plug 'ctrlpvim/ctrlp.vim' | Plug 'FelikZ/ctrlp-py-matcher'
Plug 'ervandew/supertab'
Plug 'godlygeek/tabular'
Plug 'jmcantrell/vim-virtualenv'
Plug 'junegunn/rainbow_parentheses.vim'
Plug 'junegunn/vim-easy-align'
Plug 'junegunn/vim-xmark', { 'do': 'make' }
Plug 'justinmk/vim-dirvish'
Plug 'kshenoy/vim-signature'
Plug 'lilydjwg/colorizer', { 'for': [ 'css', 'html', 'scss', 'vim' ]}
Plug 'ludovicchabant/vim-gutentags'
Plug 'majutsushi/tagbar'
Plug 'mg979/vim-visual-multi', { 'branch': 'master' }
Plug 'nathanaelkane/vim-indent-guides'
Plug 'Raimondi/delimitMate'
Plug 'sheerun/vim-polyglot'
Plug 'syngan/vim-vimlint', { 'for': 'vim' }
Plug 'terryma/vim-expand-region'
Plug 'tomtom/tcomment_vim'
Plug 'tpope/vim-characterize'
Plug 'tpope/vim-dispatch'
Plug 'tpope/vim-endwise'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-obsession'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-vinegar'
Plug 'vim-airline/vim-airline' | Plug 'vim-airline/vim-airline-themes'
Plug 'dense-analysis/ale'

" colorschemes
Plug 'arcticicestudio/nord-vim'
Plug 'zanglg/nova.vim'
Plug 'bluz71/vim-moonfly-colors'
Plug 'rakr/vim-one'

call plug#end()

colorscheme one

" source a local vim configuration (if present)
if filereadable('.vimlocal')
  source .vimlocal
endif
