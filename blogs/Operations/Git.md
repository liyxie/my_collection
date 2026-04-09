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

## 提交代码

```bash

# 不再跟踪文件模式的更改
git config core.filemode false
# 全局
git config --global core.filemode false
```



## 分支

```bash
#查看分支
git branch

# 创建一个新的分支
git checkout [branch_name]

# 切换到新分支
git checkout [branch_name]

# 创建并切换到新分支
git checkout -b [branch_name]

# 删除本地分支
git branch -d [branch_name]

# 删除远程分支
git push origin :[branch_name]
```

