#/usr/bin/bash

UUID="$(svnlook uuid ${PWD}/freeorion.svnserve)"
svn log --quiet file://${PWD}/freeorion.svnserve/ | cut -s -d '|' -f 2 | sort -u | sed -n "s/^[ \\t]*//;s/[ \\t]*$//;s/^.*$/\\0 = \\0 <\\0@${UUID}>/p"
