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

