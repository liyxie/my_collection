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

### ERROR 1698 (28000): Access denied for user 'root'@'localhost'

**原因**：MySQL root 用户使用的是 auth_socket 插件，而不是密码认证

**解决**

使用 sudo 登录 MySQL，不需要密码

```bash
sudo mysql
sudo mysql -u root -p
```

修改 root 认证方式

```sql
-- 查看当前认证方式
mysql> SELECT user, host, plugin FROM mysql.user WHERE user='root';
+------+-----------+-------------+
| user | host      | plugin      |
+------+-----------+-------------+
| root | localhost | auth_socket |
+------+-----------+-------------+
1 row in set (0.00 sec)

-- 修改 root 为密码认证（MySQL 8.0+）
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'yuxindazhineng001';

-- 刷新权限
FLUSH PRIVILEGES;
 
-- 退出
EXIT;
```





### ERROR 1819 (HY000): Your password does not satisfy the current policy requirements

**原因**：这是因为 MySQL 的密码验证策略太严格了

**解决**

使用复杂密码

MySQL 默认密码策略要求： 

- • 至少 8 个字符
-  • 包含大写字母
-  • 包含小写字母
-  • 包含数字
-  • 包含特殊字符（如 !@#$%^&*）

降低密码策略级别

```sql
-- 查看当前密码策略
mysql> SHOW VARIABLES LIKE 'validate_password%';
+-------------------------------------------------+-------+
| Variable_name                                   | Value |
+-------------------------------------------------+-------+
| validate_password.changed_characters_percentage | 0     |
| validate_password.check_user_name               | ON    |
| validate_password.dictionary_file               |       |
| validate_password.length                        | 8     |
| validate_password.mixed_case_count              | 1     |
| validate_password.number_count                  | 1     |
| validate_password.policy                        | LOW   |
| validate_password.special_char_count            | 1     |
+-------------------------------------------------+-------+
8 rows in set (0.01 sec)

-- 设置密码策略为 LOW（最低）
SET GLOBAL validate_password.policy = LOW;

-- 设置最小长度为 6
SET GLOBAL validate_password.length = 6;

-- 现在可以设置简单密码
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'xxxxxxxg001';

FLUSH PRIVILEGES;
```



### Public Key Retrieval is not allowe

**原因**： MySQL 8.0+ 使用 caching_sha2_password 认证插件导致的问题

*添加 allowPublicKeyRetrieval=True*

修改用户认证插件为 mysql_native_password（推荐）



### Access denied for user 'railway'@'%' to database 'railway'

**原因**：用户未开启远程访问

### 重启报错

```
(base) yxd@server2:~/mysql$ sudo systemctl restart mysql
Job for mysql.service failed because the control process exited with error code.
See "systemctl status mysql.service" and "journalctl -xeu mysql.service" for details.

```

```bash
# 查看服务状态
sudo systemctl status mysql.service

# 查看详细日志
sudo journalctl -xeu mysql.service -n 50

# 查看 MySQL 错误日志
sudo tail -n 50 /var/log/mysql/error.log

# 或者
sudo cat /var/log/mysql/error.log | tail -n 50

```
