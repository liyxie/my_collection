## 安装运行

### Docker 安装 Oracle 11g 案例

参考文章：[Docker 安装 Oracle 11g - 蓝羽天空 - 博客园](https://www.cnblogs.com/lanyusky/p/19242165)

拉取镜像

```bash
# 国内镜像
docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/yycx/oracle11:11.2.0.4

# Docker Hub 镜像
docker pull yycx/oracle11

```

查看镜像

```
y@server1:~/project/oracle$ docker images
                                                                                                                                                                                                                                                          i Info →   U  In Use
IMAGE                                                                       ID             DISK USAGE   CONTENT SIZE   EXTRA
swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/yycx/oracle11:11.2.0.4   77fde14a1b73       10.3GB         2.82GB    U   
y@server1:~/project/oracle$ 

```

创建文件存储目录

```bash
mkdir -p ./oracle-11g/dump  # 创建目录
chmod -R 777 ./oracle-11g  # 授予读写执行权限 用于挂载，存放需要导入的 dmp 文件，如果不需要可以不建这个文件夹。

```

Oracle 目录

容器内 Oracle 安装位置：`/opt/oracle`

```
/opt/
├── ORCLfmap/                    # Oracle 文件映射目录
│   └── prot1_64/                # 协议相关目录
│       ├── bin/                 # 二进制文件
│       ├── etc/                 # 配置文件
│       └── log/                 # 日志文件
└── oracle/                      # Oracle 主目录
    ├── app/                     # Oracle 应用目录
    │   ├── admin/               # 管理文件
    │   ├── cfgtoollogs/         # 配置工具日志
    │   ├── checkpoints/         # 检查点
    │   ├── diag/                # 诊断文件
    │   ├── fast_recovery_area/  # 快速恢复区
    │   │   ├── ORCL/            # ORCL 实例恢复文件
    │   │   │   └── onlinelog/   # 在线重做日志（空目录）
    │   │   └── orcl/            # orcl 实例恢复文件
    │   │       └── control02.ctl # 控制文件副本
    │   ├── oradata/             # 数据文件目录
    │   │   └── orcl/            # orcl 实例数据文件
    │   │       ├── ODB1         # 数据文件
    │   │       ├── ODB2         # 数据文件
    │   │       ├── control01.ctl # 控制文件
    │   │       ├── redo01.log   # 重做日志文件
    │   │       ├── redo02.log   # 重做日志文件
    │   │       ├── redo03.log   # 重做日志文件
    │   │       ├── sysaux01.dbf # Sysaux 表空间
    │   │       ├── system01.dbf # System 表空间
    │   │       ├── temp01.dbf   # 临时表空间
    │   │       ├── undotbs01.dbf # Undo 表空间
    │   │       └── users01.dbf  # Users 表空间
    │   └── product/             # Oracle 产品目录
    │       └── 11.2.0/          # 11.2.0 版本
    │           └── dbhome_1/    # 数据库主目录
    │               ├── EMStage/           # Enterprise Manager 阶段
    │               ├── OPatch/            # 补丁工具
    │               ├── apex/              # APEX
    │               ├── assistants/        # 助手工具
    │               ├── bin/               # 可执行文件
    │               ├── ccr/               # 集群就绪服务
    │               ├── cdata/             # 字符数据
    │               ├── cfgtoollogs/       # 配置工具日志
    │               ├── clone/             # 克隆相关
    │               ├── config/            # 配置
    │               ├── crs/               # 集群就绪服务
    │               ├── css/               # 集群同步服务
    │               ├── ctx/               # 文本选项
    │               ├── csmig/             # 迁移工具
    │               ├── cv/                # 恢复目录
    │               ├── dbs/               # 数据库文件
    │               ├── dc_ocm/            # 配置管理器
    │               ├── deinstall/         # 卸载工具
    │               ├── demo/              # 演示文件
    │               ├── diagnostics/       # 诊断工具
    │               ├── dv/                # 数据库保险库
    │               ├── emcli/             # Enterprise Manager CLI
    │               ├── has/               # 高可用服务
    │               ├── hs/                # 异构服务
    │               ├── ide/               # 集成开发环境
    │               ├── install/           # 安装文件
    │               ├── instantclient/     # 即时客户端
    │               ├── inventory/         # 库存
    │               ├── j2ee/              # Java 2 Enterprise Edition
    │               ├── javavm/            # Java 虚拟机
    │               ├── jdbc/              # JDBC 驱动
    │               ├── jdev/              # JDeveloper
    │               ├── jdk/               # Java 开发工具包
    │               ├── jlib/              # Java 库
    │               ├── ldap/              # LDAP 目录
    │               ├── lib/               # 库文件
    │               ├── log/               # 日志
    │               ├── md/                # 元数据
    │               ├── mesg/              # 消息文件
    │               ├── mgw/               # 管理网关
    │               ├── network/           # 网络配置
    │               ├── nls/               # 国家语言支持
    │               ├── oc4j/              # Oracle Containers for J2EE
    │               ├── odbc/              # ODBC 驱动
    │               ├── olap/              # OLAP
    │               ├── opmn/              # Oracle Process Manager and Notification
    │               ├── oraInst.loc        # Oracle 安装位置
    │               ├── oracore/           # Oracle 核心
    │               ├── ord/               # Oracle 空间数据
    │               ├── oui/               # Oracle 通用安装程序
    │               ├── owb/               # Oracle Warehouse Builder
    │               ├── owm/               # Oracle Workspace Manager
    │               ├── perl/              # Perl
    │               ├── plsql/             # PL/SQL
    │               ├── precomp/           # 预编译器
    │               ├── racg/              # 真实应用集群守护进程
    │               ├── rdbms/             # 关系数据库管理系统
    │               ├── relnotes/          # 发布说明
    │               ├── root.sh            # 根脚本
    │               ├── scheduler/         # 调度程序
    │               ├── slax/              # 样式表语言
    │               ├── sqldeveloper/      # SQL 开发工具
    │               ├── sqlj/              # SQLJ
    │               ├── sqlplus/           # SQL*Plus
    │               ├── suptools/          # 支持工具
    │               ├── sysman/            # 系统管理
    │               ├── timingframework/   # 计时框架
    │               ├── ucp/               # 通用连接池
    │               ├── uix/               # 用户界面 XML
    │               ├── usm/               # 用户安全管理
    │               ├── utl/               # 实用程序
    │               └── wwg/               # 无线网关
    ├── dpdump/                   # 数据泵目录
    └── oraInventory/             # Oracle 库存目录

```

Docker Compose

```
lanyu@server:~$ vim ./oracle-11g/oracle-11g-compose.yml

```

```yml
name: oracle11g

services:
  oracle11g:
    container_name: oracle11g
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/yycx/oracle11:11.2.0.4
    ports:
      - "1522:1521"
    volumes:
      - oracle_oradata:/opt/oracle/app/oradata/orcl
      - oracle_fra:/opt/oracle/app/fast_recovery_area/orcl
      - ./oracle-11g/dump:/opt/oracle/dpdump
    privileged: true
    restart: unless-stopped

volumes:
  oracle_oradata:
  oracle_fra:
```

```
端口映射
ports:
  - "1522:1521"
配置数据持久化和文件共享
volumes:
  - oracle_oradata:/opt/oracle/app/oradata/orcl
  - oracle_fra:/opt/oracle/app/fast_recovery_area/orcl
  - ./oracle-11g/dump:/opt/oracle/dpdump
声明命名的 Docker 卷
volumes:
  oracle_oradata:
  oracle_fra:

```

启动

```
docker compose up -d

# 查看日志
docker logs -f oracle11g
```

进入容器

```bash
y@server:~$ docker exec -it oracle11g bash

# 切换用户
[root@cc81d423f128 /]# su - oracle
Last login: Tue Nov 18 06:23:12 UTC 2025 on pts/0

# 以 SYSDBA 身份连接
[oracle@cc81d423f128 ~]$ sqlplus / as sysdba

# 修改密码
# 当前数据库中所有用户的密码都是 5208，如果想要修改可以通过下面的语句进行修改，将每个语句中最后的 5208 改成你想要的新密码。
ALTER USER SYS IDENTIFIED BY 5208;

ALTER USER SYSTEM IDENTIFIED BY 5208;

# 修改密码策略
# Oracle 11 中，默认的密码策略存在密码过期时间，但当前为 Docker 容器环境，所以密码需要设置为永不过期。
Alter PROFILE DEFAULT LIMIT PASSWORD_LIFE_TIME UNLIMITED;
# 设置密码登录尝试次数为不受限。
ALTER PROFILE DEFAULT LIMIT FAILED_LOGIN_ATTEMPTS UNLIMITED;

```

问题

**数据库未启动**

```
# 启动数据库实例（加载参数文件 -> 分配内存 -> 挂载控制文件 -> 打开数据文件）
SQL> STARTUP;

# 数据库启动后，验证当前服务名
SELECT value FROM v$parameter WHERE name = 'service_names';
```

启动失败，内存参数（SGA）太小

```
SQL> STARTUP;
ORA-00821: Specified value of sga_target 500M is too small, needs to be at least 1144M
```

将当前的二进制配置导出为文本文件
在当前的 SQL> 提示符下执行以下 SQL 语句，将配置导出到一个临时文件中（假设你在 Linux 环境）

```
CREATE PFILE='/tmp/init_fix.ora' FROM SPFILE;
```

退出 SQL*Plus 修改文件*
*输入 exit 退出 SQL*Plus。
修改刚才生成的文件：

```
vi /tmp/init_fix.ora
```

找到 *.sga_target=524288000 (或类似 500M 的数字) 这一行。
修改 将其改为大于 1144M 的值，建议设置为 1200M 或更高（取决于服务器物理内存，确保不超过物理内存限制）。 例如修改为： *.sga_target=1258291200 (这是 1200M 的字节数，或者直接写 1200M)
保存并退出编辑器。

指定临时参数文件启动数据库
显式 Oracle 使用刚才修改过的那个文本文件来启动。

```
STARTUP PFILE='/tmp/init_fix.ora';
```

将修复后的配置永久写回 SPFILE
它是基于临时文件运行的。如果下次重启，它还是会读取旧的、错误的配置。需要用当前的正确配置覆盖掉那个损坏的默认配置。

```
# 利用当前的临时参数文件，重建默认的二进制参数文件
CREATE SPFILE FROM PFILE='/tmp/init_fix.ora';
```

