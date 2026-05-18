## 无界面（Headless）操作

生产环境的服务器通常没有图形界面，Kettle作业和转换必须通过命令行工具 `pan.sh`（用于转换）和 `kitchen.sh`（用于作业）来执行。这是实现自动化调度和集成的基础。

首先，你需要将之前在图形界面中创建的数据库连接信息“导出”为无界面模式可用的形式。在图形界面中，右键点击你的数据库连接，选择“共享”或“导出”，可以将其保存为一个XML文件（例如 `gaussdb-connection.xml`）。这个文件包含了连接的所有细节。将其上传到服务器，例如 `/opt/kettle/conf/` 目录下。

现在，让我们来看一个最简单的转换执行命令。假设你已经在图形界面设计好了一个名为 `sync_data.ktr` 的转换文件，并已上传到服务器的 `/opt/kettle/jobs/` 目录。

```bash
cd /opt/kettle/data-integration

./pan.sh -file=/opt/kettle/jobs/sync_data.ktr -level=Basic
bash
```

这个命令会以基本日志级别运行指定的转换。`-level` 参数控制日志输出的详细程度，可选值有 `Nothing`, `Error`, `Minimal`, `Basic`, `Detailed`, `Debug`, `Rowlevel`。在生产环境，建议使用 `Basic` 或 `Detailed` 以平衡可读性和信息量。

然而，直接这样运行很可能失败，因为转换文件里引用的数据库连接，在无界面模式下找不到。这就是上一步导出的连接XML文件发挥作用的时候。你需要使用 `-rep` 和 `-user` 等参数来指定仓库，但对于简单的文件仓库模式，更常用的方法是**在转换内部使用“静态”定义的连接，或者在命令行通过参数传递连接信息**。

一种更工程化的做法是使用Kettle的“资源库”模式，但维护起来较复杂。对于大多数场景，我推荐使用 **“变量+参数”** 的方式来动态化连接信息。在图形界面设计转换时，不要将数据库连接的IP、端口、数据库名、用户名密码写死，而是使用Kettle变量（如 `${DB_HOST}`）。然后在执行时，通过命令行传递这些参数：

```bash
./pan.sh -file=/opt/kettle/jobs/sync_data.ktr \

  -param:DB_HOST=192.168.1.100 \

  -param:DB_PORT=8000 \

  -param:DB_NAME=mydb \

  -param:DB_USER=myuser \

  -param:DB_PASS='your_password' \

  -level=Basic -logfile=/opt/kettle/logs/sync_$(date +%Y%m%d).log
bash
```

> 提示：注意密码中包含特殊字符时的处理，最好用单引号包裹。同时，将日志重定向到文件是一个好习惯，便于事后排查问题。

为了让这个流程更健壮，我们可以编写一个shell脚本 wrapper 来封装这些命令，处理环境变量、错误重试和日志轮转