# PostgreSQL使用记录



## MySQL 切换 PostgreSQL坑

### 切换流程

1. 项目引入postgresql驱动包

   ```
   <dependency>
       <groupId>org.postgresql</groupId>
       <artifactId>postgresql</artifactId>
   </dependency>
   ```

2. 修改jdbc连接信息

   ```
   spring:
     datasource:
       # 修改驱动类
       driver-class-name: org.postgresql.Driver
       # 修改连接地址
       url: jdbc:postgresql://数据库地址/数据库名?currentSchema=模式名&useUnicode=true&characterEncoding=utf8&serverTimezone=GMT%2B8&useSSL=false
   ```

   postgres相比mysql多了一层模式的概念， 一个数据库下可以有多个模式。这里的模型名等价于以前的mysql的数据库名。如果不指定默认是public。

### 踩坑记录

1. #### **TIMESTAMPTZ类型与LocalDateTime不匹配**

   ```
   PSQLException: Cannot convert the column of type TIMESTAMPTZ to requested type java.time.LocalDateTime.
   ```

   如果postgres表的字段类型是`TIMESTAMPTZ` ，但是java对象的字段类型是`LocalDateTime`， 这时会无法转换映射上。postgres表字段类型应该用`timestamp` 或者 java字段类型用Date

2. #### **参数值不能用双引号**

   ```sql
    WHERE name = "jay"   ===>    WHERE name = 'jay'
   ```

3. #### **字段不能用``包起来**

   ```sql
    WHERE `name` = 'jay'  ==>    WHERE name = 'jay'
   ```

4. #### **convert函数不存在**

   ```sql
   -- mysql语法: 
   select convert(name, DECIMAL(20, 2))
   
   -- postgreSQL语法:
   select CAST(name as DECIMAL(20, 2))
   ```

5. #### **date_format 函数不存在**

   ```
   Cause: org.postgresql.util.PSQLException: ERROR: function date_format(timestamp without time zone, unknown) does not exist
   ```

   postgreSQL没有`date_format`函数，用`to_char`函数替换

6. #### **group by语法问题**

   ```
   Cause: org.postgresql.util.PSQLException: ERROR: column  "r.name" must appear in the GROUP BY clause or be used in an  aggregate function
   ```

   postgreSQL 的 selectd的字段必须是`group by`的字段里的 或者使用了聚合函数。mysql则没有这个要求，非聚合列会随机取值

7. #### **类型转换异常 **

   这个可以说是最坑的， 因为mysql是支持自动类型转换的。在表字段类型和参数值之间如果类型不一样也会自动进行转换。而postgreSQL是强数据类型，字段类型和参数值类型之间必须一样否则就会抛出异常。

   这时候解决办法一般有两种

   - 手动修改代码里的字段类型和传参类型保证 或者 postgreSQL表字段类型，反正保证双方一一对应
   - 添加自动隐式转换函数，达到类似mysql的效果

   布尔值和int类型类型转换错误

8. 