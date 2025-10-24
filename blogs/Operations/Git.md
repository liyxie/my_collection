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



其他

```sh
# 不再跟踪文件模式的更改
git config core.filemode false
# 全局
git config --global core.filemode false
```

