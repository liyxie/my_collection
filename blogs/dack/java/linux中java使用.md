

## 手动下载

oracle官网下载 [Java Archive Downloads - Java SE 11 | Oracle 中国](https://www.oracle.com/cn/java/technologies/javase/jdk11-archive-downloads.html)，jdk-11.0.29_linux-x64_bin.deb（根据系统下载），安装 sudo dpkg -i jdk-21_linux-x64_bin.deb；

```bash
# 检查
java -version
# 多版本切换
# 查看可选版本
sudo update-alternatives --config java
# 切换javac
sudo update-alternatives --config javac
```

