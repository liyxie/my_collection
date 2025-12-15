

## 移动、重命名文件

```bash
# 移动文件到某个目录
mv file.txt /home/user/docs/
mv file1.txt file2.txt /home/user/docs/
# 重命名文件
mv oldname.txt newname.txt
# 移动目录
mv /home/user/oldDir /home/user/newDir
# 保存备份
mv -b file.txt /home/user/docs/
-i：交互模式，防止误覆盖。
-f：强制模式，不提示直接覆盖。
-u：只移动源文件比目标文件新的情况。


```



## 运维

### `ss` 命令

```bash
# 查看服务
ss -tulnp
-t : TCP
-u : UDP
-l : 显示监听（listening）状态的端口
-n : 不解析服务名（显示数字端口）
-p : 显示占用端口的进程（需 root 权限）

sudo ss -lntup | grep 8000

```

### `lsof` 命令（查看端口与进程的关系）

```bash
sudo lsof -i :<端口号>	

```

```bash
# 追踪用户和详情
ps -f -p PID
```

