#!/bin/bash

#ssh longwell@thelongwellwalk.org -p 2222
rsync -r -u --append-verify [OPTION]... SRC [SRC]... [USER@]HOST::DEST


#--rsh=ssh
#--partial 
#--remove-source-files
#--ignore-existing    
