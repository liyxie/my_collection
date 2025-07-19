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

