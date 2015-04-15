#!/usr/bin/bash

# clone svn2git
git clone --depth=1 https://gitorious.org/svn2git/svn2git.git
# clone kde-ruleset to get some additional utility scripts
git clone --depth=1 git://anongit.kde.org/kde-ruleset

# compile svn2git
cd svn2git
qmake
make

# download complete svn repository
rsync -av svn.code.sf.net::p/freeorion/code .
mv code freeorion.svnserve
