#!/bin/bash

git submodule init
git submodule update --depth=1

for SUBMODULE in $(git submodule --quiet foreach 'echo $name'); do
  if [ -f ".gitsubmodules.d/${SUBMODULE}/sparse-checkout" ]; then
    echo "应用 ${SUBMODULE} 的稀疏检出规则..."
    cd "$(git rev-parse --show-toplevel)/${SUBMODULE}"
    git config core.sparseCheckout true
    cp "../.gitsubmodules.d/${SUBMODULE}/sparse-checkout" ../.git/modules/spider/info/
    git read-tree -mu HEAD
    cd - >/dev/null
    echo "子模块 ${SUBMODULE} 初始化完成！"
  fi
done
