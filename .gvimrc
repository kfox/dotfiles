set t_Co=256
colorscheme one
set background=dark

set guitablabel=%M%t
set lines=60
set columns=120
set textwidth=80
set guioptions-=T guioptions-=L guioptions-=r
set transparency=0

if has("gui_macvim")
  set macligatures
  set guifont=Fira\ Code\ Retina:h18

  hi User1 guifg=#ededed guibg=#3c5053 gui=bold
  hi User2 guifg=#ededed guibg=#506063 gui=NONE
  hi User3 guifg=#cacaca guibg=#506063 gui=italic
  hi User4 guifg=#ededed guibg=#506063 gui=NONE

  " just reload changed files, stop asking me already
  set autoread

  " Command-t for new tab
  macmenu &File.New\ Tab key=<D-t>

  " Command-Shift-F for fullscreen
  macmenu Window.Toggle\ Full\ Screen\ Mode key=<D-S-F>

  " Command-F for Pt (The Platinum Searcher)
  map <D-F> :Pt<space>-i<space>

  " disable accidental printing
  macmenu &File.Print key=<nop>
  map <D-p> <nop>

  " tcomment_vim
  " Command-/ to toggle comments
  nmap <D-/> gcc
  vmap <D-/> gc
  imap <D-/> <Esc>gci

  " Command-Return to move down, e.g. to exit a comment block
  imap <D-CR> <Down>
  vmap <Enter> <Nop>

  " Command-][ to increase/decrease indentation
  vmap <D-]> >gv
  vmap <D-[> <gv

  " Map Command-# to switch tabs
  map  <D-0> 0gt
  imap <D-0> <Esc>0gt
  map  <D-1> 1gt
  imap <D-1> <Esc>1gt
  map  <D-2> 2gt
  imap <D-2> <Esc>2gt
  map  <D-3> 3gt
  imap <D-3> <Esc>3gt
  map  <D-4> 4gt
  imap <D-4> <Esc>4gt
  map  <D-5> 5gt
  imap <D-5> <Esc>5gt
  map  <D-6> 6gt
  imap <D-6> <Esc>6gt
  map  <D-7> 7gt
  imap <D-7> <Esc>7gt
  map  <D-8> 8gt
  imap <D-8> <Esc>8gt
  map  <D-9> 9gt
  imap <D-9> <Esc>9gt

  " Command-Option-ArrowKey to switch viewports
  map <D-M-Up> <C-w>k
  imap <D-M-Up> <Esc> <C-w>k
  map <D-M-Down> <C-w>j
  imap <D-M-Down> <Esc> <C-w>j
  map <D-M-Right> <C-w>l
  imap <D-M-Right> <Esc> <C-w>l
  map <D-M-Left> <C-w>h
  imap <D-M-Left> <C-w>h

  " Adjust viewports to the same size
  map <Leader>= <C-w>=
  imap <Leader>= <Esc> <C-w>=

  " Open files under cursor in new tab
  nnoremap gf :tabe **/<cfile><CR>
  vnoremap gf :tabe **/<cfile><CR>

  macm Window.Select\ Previous\ Tab key=<D-Left>
  macm Window.Select\ Next\ Tab     key=<D-Right>

  if &diff
    let &columns = 200 + 2*&foldcolumn + 1
  endif
endif
