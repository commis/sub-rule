#!/bin/bash

ROOT_DIR=$(cd "$(dirname "$(readlink -f "$0")")" && pwd)

function del_history_commit() {
    git checkout --orphan latest_branch
    git add -A
    git commit -am "commit message"
    git branch -D master
    git branch -m master
    git push -f origin master
}

# main function code
OLD=$(pwd)
del_history_commit
cd "$OLD" || exit
