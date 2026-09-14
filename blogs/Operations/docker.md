# Docker使用记录

## 配置文件

更新docker配置文件daemon.json后

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 查看是否使用配置文件镜像

```bash
    docker info | grep -i registry

```

sudo install -m 0755 -d /etc/apt/keyrings curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

docker run -d -it --name presenton -p 5001:80 -v "./user_data:/app/user_data" ghcr.io/presenton/presenton:latest

## docker compose

```bash
# 后台运行
docker compose up -d
# 停止并清理容器、网络、匿名卷
docker compose down
# 清理挂载的匿名卷
docker compose down -v
# 停止并清理容器、网络、卷、镜像
docker compose down --rmi all -v
# --rmi all 删除 compose 项目用到的所有镜像
# -v → 删除 compose 创建的匿名卷
```

## 清理

```bash
# 删除镜像
# 强制删除（删除 image 及所有 tag）
docker rmi -f id
# 删除指定 tag
docker rmi adminblog:2.0
docker rmi adminblog:2.1



# 清理垃圾
# 清理悬挂镜像
docker image prune -f
# 清理悬挂卷
docker volume prune -f
# 清理悬挂网络
docker network prune -f
# 一次性清理全部（慎用，会清理没用的容器/镜像/卷/网络）
docker system prune -a -f --volumes


```





## 安装docker

使用命令 `sudo apt-get update`（对于Debian/Ubuntu）或 `sudo yum update`（对于CentOS）。

安装必要的依赖包，例如 `apt-transport-https` 和 `ca-certificates`，使用命令 `sudo apt-get install apt-transport-https ca-certificates curl software-properties-common`

添加Docker的官方GPG密钥：使用命令 curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -。



### 离线安装

Ubuntu 版本假设是 **20.04 / 22.04**（不同版本包不同）

访问官方仓库（有网机器）：

```
https://download.docker.com/linux/ubuntu/dists/
```

以 **22.04 (jammy)** 为例，进入：

```
jammy/pool/stable/amd64/
```

下载以下 **4 个核心包**（版本号以当时最新为准）：

```
containerd.io_*.deb
docker-ce_*.deb
docker-ce-cli_*.deb
docker-buildx-plugin_*.deb
docker-compose-plugin_*.deb   （建议一起下）
```

📦 下载后拷贝到 U 盘 / scp 到离线服务器，比如：

```
/opt/docker-offline/
```

------

#### 2️⃣ 在离线 Ubuntu 服务器安装

```
cd /opt/docker-offline
sudo dpkg -i *.deb
```

如果出现依赖错误：

```
sudo apt --fix-broken install
```

（⚠️ `--fix-broken` 不会联网，只是整理依赖）

------

#### 3️⃣ 启动并验证 Docker

```
sudo systemctl enable docker
sudo systemctl start docker
docker version
```

非 root 用户使用 Docker（你服务器上大概率需要）：

```
sudo usermod -aG docker $USER
# 重新登录生效
```
