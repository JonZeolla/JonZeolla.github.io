" Build the site on md file save
autocmd BufWritePost *.md,*.py,*.rst silent !task build &
