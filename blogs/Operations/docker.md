# Docker使用记录

## 配置文件

更新docker配置文件daemon.json后

```
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 查看是否使用配置文件镜像

```
docker info | grep -i registry

```

sudo install -m 0755 -d /etc/apt/keyrings curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

docker run -d -it --name presenton -p 5001:80 -v "./user_data:/app/user_data" ghcr.io/presenton/presenton:latest
