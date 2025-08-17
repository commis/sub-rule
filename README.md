# sub-rule

```shell
git remote add origin git@github.com:commis/sub-rule.git
git config core.sparseCheckout true
echo ".gitsubmodules.d/" >> .git/info/sparse-checkout
echo "backend/" >> .git/info/sparse-checkout
echo "scripts/" >> .git/info/sparse-checkout
```