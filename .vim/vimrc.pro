source ~/.vim/vimrc.basic

Plugin 'Syntastic'


"Plugin 'Valloric/YouCompleteMe'
"let g:ycm_filetype_whitelist = { 'python':1 }
"nnoremap <leader>j :YcmCompleter GoToDefinitionElseDeclaration<CR>


Plugin 'YankRing.vim'
map <leader>p :YRShow<CR>
let yankring_min_element_length=4

" change command only in pro
let g:ctrlp_user_command = 'ag %s -S --nocolor --nogroup --hidden
      \ --ignore .git
      \ --ignore .svn
      \ --ignore .hg
      \ --ignore .DS_Store
      \ --ignore "**/*.pyc"
      \ -g ""'


Plugin 'majutsushi/tagbar'
map TT :TagbarToggle<CR>
let g:tagbar_autofocus = 1
let g:tagbar_autoclose = 1


Plugin 'SirVer/ultisnips'
Plugin 'guoqiao/django-snippets'
let g:UltiSnipsExpandTrigger = "<c-j>"
let g:UltiSnipsJumpForwardTrigger = "<c-j>"
let g:UltiSnipsJumpBackwardTrigger = "<c-k>"


Plugin 'terryma/vim-multiple-cursors'
let g:multi_cursor_use_default_mapping=0
let g:multi_cursor_next_key='<C-n>'
let g:multi_cursor_prev_key='<C-b>'
let g:multi_cursor_skip_key='<C-x>'
let g:multi_cursor_quit_key='<Esc>'

