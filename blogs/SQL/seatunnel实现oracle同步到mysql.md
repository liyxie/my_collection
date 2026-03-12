## 背景

同步oralce数据库到mysql数据库，一次全量同步，后面设置增量同步； 

- oracle为Oracle Database 11g Enterprise Edition Release 11.2.0.4.0 - 64bit Production；
- mysql为8.0.45-0ubuntu0.24.04.1；
- java11
- seatunnel 2.3.8
- ubantu 24

同步过程有数据处理，比如多表数据整理到一表，只替换等；

## 参考

[Oracle CDC | Apache SeaTunnel](https://seatunnel.apache.org/zh-CN/docs/2.3.8/connector-v2/source/Oracle-CDC)

## Oracle 配置

开启归档和增量日志

```sql
-- 1. 确认已开启归档日志 (结果必须是 ARCHIVELOG)
SELECT log_mode FROM v$database;
-- 开启归档日志
-- 首先用sys登录数据库，查看oracle是否开启归档模式（su - oracle切换用户，然后sqlplus / as sysdba进入sql模式）
-- 输入archive log list来查看是否开启，如下说明不是归档模式
-- 归档模式的更改需要在 MOUNT 状态下进行：
shutdown immediate; -- 关闭数据库
startup mount; -- 启动到 MOUNT 模式
alter database archivelog; -- 开启归档模式
alter database open; -- 打开数据库

-- 2. 确认开启了追加日志 (结果必须是 YES)
SELECT supplemental_log_data_min FROM v$database;
-- 如果没有开启，请执行：ALTER DATABASE ADD SUPPLEMENTAL LOG DATA;


-- 3. 给你的同步用户(假设叫 user) 赋予 LogMiner 必须的权限
-- 注意SYSDBA用户操作，不然权限不足
-- 1. 基础连接与全库查询权限（全量同步必须）
GRANT CREATE SESSION TO myjjzd;
-- 查询全库所有表
-- GRANT SELECT ANY TABLE TO myjjzd;
GRANT FLASHBACK ANY TABLE TO myjjzd;
-- 2. 赋予读取数据字典的系统角色（覆盖大部分 V_$ 视图，避免表不存在错误）
GRANT SELECT ANY DICTIONARY TO myjjzd;
GRANT SELECT_CATALOG_ROLE TO myjjzd;
GRANT EXECUTE_CATALOG_ROLE TO myjjzd;
GRANT SELECT ANY TRANSACTION TO myjjzd;
-- 3. LogMiner 核心执行权限（增量同步必须）
GRANT EXECUTE ON DBMS_LOGMNR TO myjjzd;
GRANT EXECUTE ON DBMS_LOGMNR_D TO myjjzd;
-- 4. 核心底层视图显式授权 (SeaTunnel 底层引擎强烈依赖)
GRANT SELECT ON V_$DATABASE TO myjjzd;
GRANT SELECT ON V_$ARCHIVED_LOG TO myjjzd;
GRANT SELECT ON V_$LOG TO myjjzd;
GRANT SELECT ON V_$LOGFILE TO myjjzd;
GRANT SELECT ON V_$INSTANCE TO myjjzd;
GRANT SELECT ON V_$LOGMNR_LOGS TO myjjzd;
GRANT SELECT ON V_$LOGMNR_CONTENTS TO myjjzd;
-- 5. Debezium(SeaTunnel底层)需要的特殊底层表
GRANT SELECT ON SYS.OBJ$ TO myjjzd;
GRANT SELECT ON SYS.DBA_REGISTRY TO myjjzd;
-- 注意：如果下面这句 SYS.ENC$ 仍然报错“表不存在”，请直接忽略！
-- 它是用于 TDE(透明数据加密) 的，如果没有开启加密，不授权也不影响同步。
GRANT SELECT ON SYS.ENC$ TO myjjzd;

-- 赋予分析任何表的权限（推荐，以后加其他表也不会报错）
GRANT ANALYZE ANY TO myjjzd;

-- 测试 1：看能不能查到底层视图
SELECT count(1) FROM V$LOGFILE;
-- 测试 2：看能不能查到 LogMiner 包
SELECT count(1) FROM ALL_OBJECTS WHERE OBJECT_NAME = 'DBMS_LOGMNR';
```



## 准备

**java**（推荐11或者8）

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

**Seatunnel**

```bash
sudo wget https://archive.apache.org/dist/seatunnel/2.3.8/apache-seatunnel-2.3.8-bin.tar.gz
sudo tar -zxvf apache-seatunnel-2.3.8-bin.tar.gz
sudo mv apache-seatunnel-2.3.8 seatunnel
cd seatunnel
# 编辑 SeaTunnel 的启动脚本环境，让它强制使用 Java 11
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

**数据库驱动**

下载mysql8、oracle11g 驱动

[Maven Repository： com.mysql » mysql-connector-j » 8.3.0](https://mvnrepository.com/artifact/com.mysql/mysql-connector-j/8.3.0)

[Maven Repository： com.oracle.database.jdbc » ojdbc8 » 19.3.0.0](https://mvnrepository.com/artifact/com.oracle.database.jdbc/ojdbc8/19.3.0.0)

复制到 seatunnel/lib 目录下

**连接器**

下载 oracle-CDC 和 JDBC（mysql）,注意 CDC 和 普通连接不同

[Central Repository: org/apache/seatunnel](https://repo.maven.apache.org/maven2/org/apache/seatunnel/)

 connector-cdc-oracle-2.3.8.jar 、 connector-jdbc-2.3.8.jar 复制到 seatunnel/connectors/ 目录下

## **配置文件**

```bash
# 文件名自定
vim seatunnel/config/oracle_to_mysql.config
```

```properties
env {
  # 运行模式：STREAMING 代表先全量，然后一直挂着做增量
  job.mode = "STREAMING"
  # 检查点间隔(毫秒)，保证断点续传
  checkpoint.interval = 10000
}

source {
  Oracle-CDC {
    # 连接信息
    base-url = "jdbc:oracle:thin:@192.168.10.241:1522/ORCL"
    username = "my"
    password = "****"
    
    # CDC 推荐显式指定 schema（模式）进行过滤，提升解析性能
    schema-names = ["MYTBK"]
    database-names = ["ORCL"]
    # 表名必须带上模式前缀
    table-names = ["ORCL.MYTBK.VIO_VIOLATION"]
    
    # startup.mode = "INITIAL"
    
    result_table_name = "oracle_source_table"
  }
}
transform {
  # 使用 SQL 进行数据处理（这里处理您的“替换”需求）
  Sql {
    source_table_name = "oracle_source_table"
    result_table_name = "transformed_table"
    
    # 其他字段原样查出。这里语法遵循标准 SQL 语法。
    query = "select * FROM oracle_source_table"
  }
}

sink {
  Jdbc {
    source_table_name = "transformed_table"
    
    # MySQL 连接信息
    driver = "com.mysql.cj.jdbc.Driver"
    url = "jdbc:mysql://127.0.0.1:3306/myjjzd?useSSL=false&serverTimezone=Asia/Shanghai"
    user = "my"
    password = "*****"
    
    # 告诉 SeaTunnel 根据 CDC 日志自动生成 INSERT/UPDATE/DELETE 语句
    generate_sink_sql = true
    # 目标表名
    database = "myj"
    table = "VIO_VIOLATION"
    
    # 目标表的主键（必须指定，否则 Update/Delete 无法执行）
    primary_keys = ["WFBH"]
  }
}
```

## 运行

```bash
./bin/seatunnel.sh --config ./config/oracle_to_mysql.conf -e local
```

```
# 集群运行
cd /opt/seatunnel/apache-seatunnel-2.3.x
nohup bin/seatunnel-cluster.sh > logs/seatunnel-cluster.log 2>&1 &
```



## 其他

#### JVM 内存调优

修改 `bin/seatunnel.sh` 或者 `config/jvm_options` 文件，根据服务器的物理内存，适当调优参数。 如果单表数据量非常大，读取快照时很容易内存溢出，建议至少给每个任务/集群分配 4GB-8GB 内存： `-Xms4g -Xmx4g -XX:+UseG1GC`



## 问题

### 连接器缺失

```
Caused by: java.lang.RuntimeException: Plugin PluginIdentifier{engineType='seatunnel', pluginType='source', pluginName='Oracle-CDC'} not found.
```

查看是否有下载连接器 connectors/

### 时区不匹配

oracle时区与Seatunnel时区需一致，观察Seatunnal日志输出时间，有可能JVM时间与系统时间不一致，注意docker运行情况时容器时间

```
Caused by: org.apache.seatunnel.api.table.catalog.exception.CatalogException: ErrorCode:[API-03], ErrorDescription:[Catalog initialize failed] - Failed connecting to jdbc:oracle:thin:@192.168.10.241:1522/ORCL via JDBC.
        at org.apache.seatunnel.connectors.seatunnel.jdbc.catalog.AbstractJdbcCatalog.getConnection(AbstractJdbcCatalog.java:124)
        at org.apache.seatunnel.connectors.seatunnel.jdbc.catalog.AbstractJdbcCatalog.open(AbstractJdbcCatalog.java:130)
        at org.apache.seatunnel.api.table.catalog.CatalogTableUtil.lambda$getCatalogTables$0(CatalogTableUtil.java:122)
        at java.base/java.util.Optional.map(Optional.java:265)
        at org.apache.seatunnel.api.table.catalog.CatalogTableUtil.getCatalogTables(CatalogTableUtil.java:118)
        at org.apache.seatunnel.api.table.catalog.CatalogTableUtil.getCatalogTables(CatalogTableUtil.java:98)
        at org.apache.seatunnel.connectors.seatunnel.cdc.oracle.source.OracleIncrementalSourceFactory.lambda$createSource$1(OracleIncrementalSourceFactory.java:108)
        at org.apache.seatunnel.api.table.factory.FactoryUtil.createAndPrepareSource(FactoryUtil.java:113)
        at org.apache.seatunnel.api.table.factory.FactoryUtil.createAndPrepareSource(FactoryUtil.java:74)
        ... 7 more
Caused by: java.sql.SQLException: ORA-00604: error occurred at recursive SQL level 1
ORA-01882: timezone region not found
```

从Seatunnel端修改时间 2种方式

```bash
# 临时设置环境变量（关闭终端后失效，如果想永久生效可以写进 ~/.bashrc）
export JAVA_OPTS="-Duser.timezone=GMT+8 -Doracle.jdbc.timezoneAsRegion=false"
```

```
# 新增这一行，强制 SeaTunnel 引擎使用东八区
source {
  Oracle-CDC {
    server-time-zone = "Asia/Shanghai" 
  }
}
```



### query缺失

```
Caused by: org.apache.seatunnel.api.configuration.util.OptionValidationException: ErrorCode:[API-02], ErrorDescription:[Option item validate failed] - There are unconfigured options, the options('query') are required.
```





## sql语句错误

```
2026-03-02 13:47:39,184 ERROR [o.a.s.c.s.SeaTunnel           ] [main] - Exception StackTrace:org.apache.seatunnel.core.starter.exception.CommandExecuteException: SeaTunnel job executed failed
        at org.apache.seatunnel.core.starter.seatunnel.command.ClientExecuteCommand.execute(ClientExecuteCommand.java:213)
        at org.apache.seatunnel.core.starter.SeaTunnel.run(SeaTunnel.java:40)
        at org.apache.seatunnel.core.starter.seatunnel.SeaTunnelClient.main(SeaTunnelClient.java:34)
Caused by: org.apache.seatunnel.engine.common.exception.SeaTunnelEngineException: java.lang.RuntimeException: java.lang.RuntimeException: java.lang.IllegalArgumentException: Named parameters in SQL statement must not be empty.
```

