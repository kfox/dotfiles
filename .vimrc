set nocompatible

if (has('termguicolors'))
  set termguicolors
endif

syntax on

let mapleader = ','

cabbrev help tab help

""""""""""""""""" Vim Tweaking

" Quickly edit/reload the vimrc file
nmap <silent> <leader>ev :e $MYVIMRC<CR>
nmap <silent> <leader>sv :so $MYVIMRC <BAR> :so $MYGVIMRC<CR>

" Highlight matching parens
set showmatch

" Disable Ex mode (who/what still uses this?)
nnoremap Q <nop>

""""""""""""""""" Encoding
set encoding=utf-8

""""""""""""""""" Clipboard
if !has('nvim')
  set clipboard=autoselectplus
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
  highlight VertSplit ctermfg=242
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

set statusline=   " clear the statusline when vimrc is reloaded
set statusline+=%1*\ %-3.3n\                      " buffer number
set statusline+=%2*\ %t                           " file basename
set statusline+=%h%m%r%w\                         " flags
set statusline+=[%{strlen(&ft)?&ft:'none'},       " filetype
set statusline+=%{strlen(&fenc)?&fenc:&enc},      " encoding
set statusline+=%{&fileformat}]\                  " file format
set statusline+=%=                                " right align
set statusline+=%3*%{synIDattr(synID(line('.'),col('.'),1),'name')!=''?synIDattr(synID(line('.'),col('.'),1),'name'):'none'}  " highlight
set statusline+=%4*\ %3b,0x%-8B                   " current char
set statusline+=%-14.(%l/%L,%c%)\ %<%P            " offset

""""""""""""""""" Terminal
set ttyfast
set mouse=a
set paste

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
set foldmethod=syntax
set foldnestmax=3
set nofoldenable

" Enable folding with the spacebar
" nnoremap <space> za

""""""""""""""""" Line Numbering
set number
set relativenumber
autocmd VimEnter * nmap <silent> <leader>n :set nonumber! norelativenumber!<CR>

""""""""""""""""" Window Title
set title
if !has("gui_macvim")
  set t_ts=k
  set t_fs=\
  autocmd BufEnter * let &titlestring = 'Vim - ' . expand("%:t")
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

""""""""""""""""" vimgrep result navigation
map <A-o> :copen<CR>
map <A-w> :cclose<CR>
map <A-j> :cnext<CR>
map <A-k> :cprevious<CR>

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
autocmd BufReadPost * call SetCursorPosition()
function! SetCursorPosition()
  if &filetype !~ 'commit\c'
      if line("'\"") > 0 && line("'\"") <= line("$")
          exe "normal! g`\""
          normal! zz
      endif
  end
endfunction

""""""""""""""""" Textmate-like indent/outdent
nmap <D-[> <<
nmap <D-]> >>
imap <D-[> <<
imap <D-]> >>
vmap <D-[> <gv
vmap <D-]> >gv

""""""""""""""""" MacVIM shift+arrow-keys
let macvim_hig_shift_movement = 1

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

map <leader>rt :!ctags --extra=+f -R *<CR><CR>
map <C-\> :tnext<CR>
set tags+=tags;$HOME

""""""""""""""""" text wrapping

if !exists("*s:setupWrapping")
  function s:setupWrapping()
    set wrap
    set wrapmargin=2
    set textwidth=72
  endfunction
endif

" Format text files
au BufRead,BufNewFile *.txt,*.md call s:setupWrapping()

""""""""""""""""" file formatting

" These files are Ruby
autocmd BufRead,BufNewFile config.ru,{Brew,Gem,Guard,Rake,Thor}file set filetype=ruby

" PostgreSQL config
autocmd BufRead,BufNewFile .psqlrc set filetype=sql

" cson (coffeescript)
au BufNewFile,BufRead *.cson set filetype=coffee

" various rc files (json)
au BufNewFile,BufRead .{babel,eslint,stylelint}rc set filetype=json
au BufNewFile,BufRead .{direnv,env}rc set filetype=sh

" make javascript prettier
" au FileType javascript set formatprg=prettier\ --stdin
" au BufWritePre *.js :normal gggqG
" au BufWritePre *.js exe 'normal! gggqG\<C-o>\<C-o>'

" md, markdown, and mk are markdown and define buffer-local preview
au BufRead,BufNewFile *.{md,markdown,mdown,mkd,mkdn} call s:setupMarkup()

if !exists("*s:setupMarkup")
  function s:setupMarkup()
    call s:setupWrapping()
    map <buffer> <leader>p :Hammer<CR>
  endfunction
endif

" crontab stuff
au filetype crontab setlocal nobackup nowritebackup

" python
" au FileType python setl tabstop=4 shiftwidth=4 softtabstop=4 textwidth=99 colorcolumn=101
au FileType python setl tabstop=4 shiftwidth=4 softtabstop=4
highlight BadWhitespace ctermbg=red guibg=red
autocmd BufRead,BufNewFile *.py,*.pyw match BadWhitespace /^\t\+/
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
  set csprg=/usr/local/bin/cscope
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

""""""""""""""""" ultisnips

let g:UltiSnipsExpandTrigger = "<c-enter>"
let g:UltiSnipsJumpForwardTrigger = "<c-k>"
let g:UltiSnipsJumpBackwardTrigger = "<c-j>"

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
let g:tagbar_ctags_bin   = '/usr/local/bin/ctags'
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

map <leader>t :Dispatch nosetests %<CR>

""""""""""""""""" The Silver Searcher

" if executable('ag')
"   " use ag instead of grep
"   set grepprg=ag\ --nogroup\ --nocolor
"   set grepformat=%f:%l:%m
"
"   " bind K to grep word under cursor
"   " nnoremap K :grep! "\b<C-R><C-W>\b"<CR>:cw<CR>
"
"   " bind \ (backward slash) to grep shortcut
"   " command -nargs=+ -complete=file -bar Ag silent! grep! <args>|cwindow|redraw!
"   nnoremap \ :Ag<SPACE>-i<SPACE>
" endif

""""""""""""""""" The Platinum Searcher

command! -nargs=+ -complete=file -bar Pt silent! grep! <args>|cwindow|redraw!

nnoremap <silent> <leader>f :<C-u>Unite grep:. -buffer-name=search-buffer<CR>
if executable('pt')
  let g:unite_source_grep_command = 'pt'
  let g:unite_source_grep_default_opts = '--nogroup --nocolor'
  let g:unite_source_grep_recursive_opt = ''
  let g:unite_source_grep_encoding = 'utf-8'
endif

""""""""""""""""" Unimpaired

" Bubble single lines
nmap <C-Up> [e
nmap <C-Down> ]e

" Bubble multiple lines
vmap <C-Up> [egv
vmap <C-Down> ]egv

""""""""""""""""" CSS

augroup VimCSS3Syntax
  autocmd!
  autocmd FileType css setlocal iskeyword+=-
  highlight VendorPrefix guifg=#00ffff gui=bold
  match VendorPrefix /-\(moz\|webkit\|o\|ms\)-[a-zA-Z-]\+/
augroup END

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

""""""""""""""""" YouCompleteMe

let g:ycm_python_binary_path = '/usr/local/bin/python3'
let g:ycm_collect_identifiers_from_comments_and_strings = 1
let g:ycm_collect_identifiers_from_tags_files = 1

function! BuildYCM(info)
  " info is a dictionary with 3 fields
  " - name:   name of the plugin
  " - status: 'installed', 'updated', or 'unchanged'
  " - force:  set on PlugInstall! or PlugUpdate!
  if a:info.status == 'installed' || a:info.force
    !./install.py
  endif
endfunction

""""""""""""""""" tern_for_vim

" let g:tern_show_argument_hints = 'on_hold'
let g:tern_map_keys = 1
let g:tern_map_prefix = '<leader>'

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

autocmd User AirlineAfterInit call AirlineInit()

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

set t_Co=256

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
  autocmd FileType dirvish call fugitive#detect(@%)

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
au FileType html,javascript let b:delimitMate_insert_eol_marker = 2
au FileType html,javascript let g:delimitMate_eol_marker = ';'

""""""""""""""""" vim-javascript

let g:javascript_plugin_jsdoc = 1

""""""""""""""""" nginx

au BufRead,BufNewFile *.nginx,{nginx,default}.conf set filetype=nginx

""""""""""""""""" vim-indent-guides

let g:indent_guides_guide_size = 1
let g:indent_guides_start_level = 2

""""""""""""""""" ale

let g:ale_linters = {
\  'javascript': [
\    'standard'
\  ],
\  'jsx': [
\    'standard',
\    'stylelint'
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

let g:ale_linter_aliases = {
\  'jsx': 'css'
\}

let g:ale_fixers = {
\  'javascript': [
\    'prettier',
\    'standard'
\  ],
\  'json': [
\    'prettier'
\  ],
\  'jsx': [
\    'prettier',
\    'standard',
\    'stylelint'
\  ],
\  'python': [
\		 'black',
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
let g:ale_statusline_format = ['❌ %d', '💩 %d', '👍']
let g:ale_echo_msg_format = '[%linter%] %s'

" javascript
let g:ale_javascript_eslint_executable = 'babel-eslint'
let g:ale_javascript_standard_options = '--parser babel-eslint'

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
  autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif

call plug#begin('~/.vim/plugged')

Plug 'airblade/vim-gitgutter'
Plug 'bogado/file-line'
Plug 'cakebaker/scss-syntax.vim', { 'for': 'scss' }
Plug 'ctrlpvim/ctrlp.vim' | Plug 'FelikZ/ctrlp-py-matcher'
Plug 'ekalinin/Dockerfile.vim', { 'for': [ 'docker-compose', 'Dockerfile' ] }
Plug 'elzr/vim-json', { 'for': 'json' }
Plug 'ervandew/supertab'
Plug 'fatih/vim-go', { 'for': 'go' }
Plug 'godlygeek/tabular'
Plug 'hail2u/vim-css3-syntax', { 'for': [ 'css', 'html' ] }
Plug 'jelera/vim-javascript-syntax', { 'for': [ 'html', 'javascript', 'javascript.jsx' ] }
Plug 'jmcantrell/vim-virtualenv'
Plug 'JulesWang/css.vim', { 'for': [ 'css', 'html' ] }
Plug 'junegunn/rainbow_parentheses.vim'
Plug 'junegunn/vim-easy-align'
Plug 'junegunn/vim-xmark', { 'do': 'make' }
Plug 'justinmk/vim-dirvish'
Plug 'kshenoy/vim-signature'
Plug 'lilydjwg/colorizer', { 'for': [ 'css', 'html', 'scss', 'vim' ]}
Plug 'ludovicchabant/vim-gutentags'
Plug 'majutsushi/tagbar'
Plug 'mxw/vim-jsx', { 'for': 'javascript.jsx' }
Plug 'nathanaelkane/vim-indent-guides'
Plug 'nazo/pt.vim'
Plug 'othree/html5.vim', { 'for': 'html' }
Plug 'othree/nginx-contrib-vim', { 'for': 'nginx' }
" Plug 'othree/yajs.vim', { 'for': [ 'html', 'javascript' ] } | Plug 'othree/es.next.syntax.vim'
Plug 'Raimondi/delimitMate'
Plug 'rust-lang/rust.vim', { 'for': 'rust' }
Plug 'sheerun/vim-polyglot'
Plug 'Shougo/unite.vim'
Plug 'Shougo/vimproc.vim', {'do' : 'make'}
"Plug 'SirVer/ultisnips' | Plug 'honza/vim-snippets'
Plug 'syngan/vim-vimlint', { 'for': 'vim' }
Plug 'ternjs/tern_for_vim', { 'do': 'yarn', 'for': [ 'html', 'javascript', 'javascript.jsx' ] }
Plug 'terryma/vim-expand-region'
Plug 'terryma/vim-multiple-cursors'
Plug 'tomtom/tcomment_vim'
Plug 'tpope/vim-characterize'
Plug 'tpope/vim-dispatch'
Plug 'tpope/vim-endwise'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-obsession'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-vinegar'
Plug 'vim-airline/vim-airline' | Plug 'vim-airline/vim-airline-themes'
Plug 'vim-ruby/vim-ruby', { 'for': [ 'eruby', 'ruby' ] }
Plug 'vim-scripts/indentpython.vim', { 'for': 'python' }
Plug 'dense-analysis/ale'

" colorschemes
Plug 'arcticicestudio/nord-vim'
Plug 'zanglg/nova.vim'
Plug 'bluz71/vim-moonfly-colors'
Plug 'rakr/vim-one'

call plug#end()

colorscheme one

" source a local vim configuration (if present)
silent! so .vimlocal
