" Vim color file
" Converted from Textmate theme Kelly using Coloration v0.2.5 (http://github.com/sickill/coloration)

set background=dark
highlight clear

if exists("syntax_on")
  syntax reset
endif

let g:colors_name = "Kelly"

hi Cursor  guifg=NONE guibg=#ffffff gui=NONE
hi Visual  guifg=NONE guibg=#797d67 gui=NONE
hi CursorLine  guifg=NONE guibg=#0d1c1f gui=NONE
hi CursorLineNr  term=bold ctermfg=Yellow gui=bold guifg=Yellow
hi CursorColumn  guifg=NONE guibg=#0d1c1f gui=NONE
hi LineNr  guifg=#808c8e guibg=#132b2f gui=NONE
hi VertSplit  guifg=#3c5053 guibg=#3c5053 gui=NONE
hi MatchParen  guifg=#ff9d00 guibg=NONE gui=NONE
hi StatusLine  guifg=#ededed guibg=#3c5053 gui=bold
hi StatusLineNC  guifg=#ededed guibg=#3c5053 gui=NONE
hi Pmenu  guifg=#ffdd00 guibg=NONE gui=NONE
hi PmenuSel  guifg=NONE guibg=#797d67 gui=NONE
" hi IncSearch  guifg=NONE guibg=#506063 gui=NONE
" hi Search  guifg=NONE guibg=#506063 gui=NONE
hi IncSearch  guifg=#ffffff guibg=#506063 gui=bold
hi Search  guifg=#ffffff guibg=#506063 gui=bold
hi Directory  guifg=#ff628c guibg=NONE gui=NONE
hi Folded  guifg=#47c2ff guibg=#132b2f gui=NONE

hi Normal  guifg=#ededed guibg=#132b2f gui=NONE
hi Boolean  guifg=#ff628c guibg=NONE gui=NONE
hi Character  guifg=#ff628c guibg=NONE gui=NONE
hi Comment  guifg=#47c2ff guibg=NONE gui=italic
hi Conditional  guifg=#ff9d00 guibg=NONE gui=NONE
hi Constant  guifg=#ff628c guibg=NONE gui=NONE
hi Define  guifg=#ff9d00 guibg=NONE gui=NONE
hi ErrorMsg  guifg=#f8f8f8 guibg=#800f00 gui=NONE
hi WarningMsg  guifg=#f8f8f8 guibg=#800f00 gui=NONE
hi Float  guifg=#ff628c guibg=NONE gui=NONE
hi Function  guifg=#ffdd00 guibg=NONE gui=NONE
hi Identifier  guifg=#ffee80 guibg=NONE gui=NONE
hi Keyword  guifg=#ff9d00 guibg=NONE gui=NONE
hi Label  guifg=#85ff4e guibg=NONE gui=NONE
hi NonText  guifg=#5f7373 guibg=#0d1c1f gui=NONE
hi Number  guifg=#ff628c guibg=NONE gui=NONE
hi Operator  guifg=#ff9d00 guibg=NONE gui=NONE
hi PreProc  guifg=#ff9d00 guibg=NONE gui=NONE
hi Special  guifg=#ededed guibg=NONE gui=NONE
hi SpecialKey  guifg=#5f7373 guibg=#0d1c1f gui=NONE
hi Statement  guifg=#ff9d00 guibg=NONE gui=NONE
hi StorageClass  guifg=#ffee80 guibg=NONE gui=NONE
hi String  guifg=#85ff4e guibg=NONE gui=NONE
hi Tag  guifg=#ffdd00 guibg=NONE gui=NONE
hi Title  guifg=#ededed guibg=NONE gui=bold
hi Todo  guifg=#47c2ff guibg=NONE gui=inverse,bold,italic
hi Type  guifg=#ffdd00 guibg=NONE gui=NONE
hi Underlined  guifg=NONE guibg=NONE gui=underline
hi rubyClass  guifg=#ff9d00 guibg=NONE gui=NONE
hi rubyFunction  guifg=#ffdd00 guibg=NONE gui=NONE
hi rubyInterpolationDelimiter  guifg=NONE guibg=NONE gui=NONE
hi rubySymbol  guifg=#ff628c guibg=NONE gui=NONE
hi rubyConstant  guifg=#80ffbb guibg=NONE gui=NONE
hi rubyStringDelimiter  guifg=#85ff4e guibg=NONE gui=NONE
hi rubyBlockParameter  guifg=#cccccc guibg=NONE gui=NONE
hi rubyInstanceVariable  guifg=#ff80e1 guibg=NONE gui=NONE
hi rubyInclude  guifg=#ff9d00 guibg=NONE gui=NONE
hi rubyGlobalVariable  guifg=#cccccc guibg=NONE gui=NONE
hi rubyRegexp  guifg=#80ffc2 guibg=NONE gui=NONE
hi rubyRegexpDelimiter  guifg=#80ffc2 guibg=NONE gui=NONE
hi rubyEscape  guifg=#ff628c guibg=NONE gui=NONE
hi rubyControl  guifg=#ff9d00 guibg=NONE gui=NONE
hi rubyClassVariable  guifg=#cccccc guibg=NONE gui=NONE
hi rubyOperator  guifg=#ff9d00 guibg=NONE gui=NONE
hi rubyException  guifg=#ff9d00 guibg=NONE gui=NONE
hi rubyPseudoVariable  guifg=#ff80e1 guibg=NONE gui=NONE
hi rubyRailsUserClass  guifg=#80ffbb guibg=NONE gui=NONE
hi rubyRailsARAssociationMethod  guifg=#ffb054 guibg=NONE gui=NONE
hi rubyRailsARMethod  guifg=#ffb054 guibg=NONE gui=NONE
hi rubyRailsRenderMethod  guifg=#ffb054 guibg=NONE gui=NONE
hi rubyRailsMethod  guifg=#ffb054 guibg=NONE gui=NONE
hi erubyDelimiter  guifg=#f07d5a guibg=NONE gui=NONE
hi erubyComment  guifg=#47c2ff guibg=NONE gui=italic
hi erubyRailsMethod  guifg=#ffb054 guibg=NONE gui=NONE
hi htmlTag  guifg=#9effff guibg=NONE gui=NONE
hi htmlEndTag  guifg=#9effff guibg=NONE gui=NONE
hi htmlTagName  guifg=#9effff guibg=NONE gui=NONE
hi htmlArg  guifg=#9effff guibg=NONE gui=NONE
hi htmlSpecialChar  guifg=#ff628c guibg=NONE gui=NONE
hi javaScriptFunction  guifg=#ffee80 guibg=NONE gui=NONE
hi javaScriptRailsFunction  guifg=#ffb054 guibg=NONE gui=NONE
hi javaScriptBraces  guifg=NONE guibg=NONE gui=NONE
hi yamlKey  guifg=#ffdd00 guibg=NONE gui=NONE
hi yamlAnchor  guifg=#cccccc guibg=NONE gui=NONE
hi yamlAlias  guifg=#cccccc guibg=NONE gui=NONE
hi yamlDocumentHeader  guifg=#85ff4e guibg=NONE gui=NONE
hi cssURL  guifg=#cccccc guibg=NONE gui=NONE
hi cssFunctionName  guifg=#ffb054 guibg=NONE gui=NONE
hi cssColor  guifg=#ff628c guibg=NONE gui=NONE
hi cssPseudoClassId  guifg=#ffdd00 guibg=NONE gui=NONE
hi cssClassName  guifg=#ffdd00 guibg=NONE gui=NONE
hi cssValueLength  guifg=#ff628c guibg=NONE gui=NONE
hi cssCommonAttr  guifg=#eb939a guibg=NONE gui=NONE
hi cssBraces  guifg=#f07d5a guibg=NONE gui=NONE
