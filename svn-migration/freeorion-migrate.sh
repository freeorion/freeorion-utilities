#!/usr/bin/bash

function tag_fo {
    HASH=$(echo $1 | ../kde-ruleset/bin/translateRevlist.py 2> /dev/null)
    export GIT_COMMITTER_NAME=$3
    export GIT_COMMITTER_EMAIL=$4
    export GIT_COMMITTER_DATE="$(git log -1 --format='%cD' $HASH)"
    git tag -a -F <(git log -1 --format="%B" $HASH) $2 $HASH
    unset GIT_COMMITTER_NAME
    unset GIT_COMMITTER_EMAIL
    unset GIT_COMMITTER_DATE
}

svn2git/svn-all-fast-export --add-metadata --identity-map freeorion-authors --rules freeorion-ruleset freeorion.svnserve

cd freeorion.git

tag_fo 2607 v0.3.10 Geoff "g_topping@hotmail.com"
tag_fo 2729 v0.3.11-win Geoff "g_topping@hotmail.com"
tag_fo 2732 v0.3.11-lin Geoff "g_topping@hotmail.com"
tag_fo 2807 v0.3.12-win Geoff "g_topping@hotmail.com"
tag_fo 2918 v0.3.12-lin Geoff "g_topping@hotmail.com"
tag_fo 3094 v0.3.13-mac Geoff "g_topping@hotmail.com"
tag_fo 3094 v0.3.13-win Geoff "g_topping@hotmail.com"
tag_fo 3571 v0.3.14 Geoff "g_topping@hotmail.com"
tag_fo 3727 v0.3.15 Geoff "g_topping@hotmail.com"
tag_fo 4046 v0.3.16 Geoff "g_topping@hotmail.com"
tag_fo 4282 v0.3.17 Geoff "g_topping@hotmail.com"
tag_fo 4635 v0.4 Geoff "g_topping@hotmail.com"
tag_fo 5096 v0.4.1 Geoff "g_topping@hotmail.com"
tag_fo 5771 v0.4.2 Geoff "g_topping@hotmail.com"

export RULESETDIR=../kde-ruleset/

../kde-ruleset/bin/parent-adder ../freeorion-parent-remap

../kde-ruleset/bin/remove-fb-backup-refs.sh

cd ..

git clone freeorion.git freeorion.wk

cd freeorion.wk

git checkout master

git filter-branch --env-filter '
export GIT_COMMITTER_NAME=$GIT_AUTHOR_NAME
export GIT_COMMITTER_EMAIL=$GIT_AUTHOR_EMAIL
export GIT_COMMITTER_DATE=$GIT_AUTHOR_DATE
' origin/master..master

git update-ref -d refs/original/refs/heads/master

git push origin master

cd ../freeorion.git

rm -rf ../freeorion.wk

git filter-branch --tree-filter 'git ls-files -z | xargs -0 dos2unix' --prune-empty --tag-name-filter cat -d /dev/shm/repo-temp -- --all

git gc --prune=now

git repack -a -d -f --window=400 --depth=400
