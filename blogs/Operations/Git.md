# Git使用记录

## 放弃本地修改

```powershell
# 彻底丢掉所有未提交的本地修改，无法恢复
# 放弃所有本地修改
git restore .

# 再次拉取远程最新代码
git pull gitee main

# 或者
git reset --hard
git pull gitee main

```

