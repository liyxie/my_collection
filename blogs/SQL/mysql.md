## 更换端口

Linux

**找到配置文件** Linux 系统：/etc/my.cnf 或 /etc/mysql/my.cnf ；

```
[mysqld]  
port=3506  
```

```bash
# 重启mysql
systemctl restart mysqld
```

```sql
-- 进入mysql，检查端口
show global variables like 'port'
```

## 连接相关

用 Nginx 的“域名映射（HTTP 反向代理）”不能让 JDBC 连上 MySQL。MySQL 是二进制的 TCP 协议，不是 HTTP。需要走原生的 3306/TCP（或其他自定义 TCP 端口），而不是 http://。