# SpringBoot 2.4.1 升级 SpringBoot 3 记录

------

## 背景 

javaWeb项目、模块化结构，准备加入SpringAi

## 记录

java升级17以上

直接修改springboot版本

```xml
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.3</version>
    </parent>
```

### 处理报错

### mysql版本未指定

```xml
        <!--mysql数据库驱动依赖-->
        <dependency>
            <groupId>mysql</groupId>
            <artifactId>mysql-connector-java</artifactId>
        </dependency>

        <!--mysql数据库驱动依赖-->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
        </dependency>
```

### mybitispuls报错

mybatis-plus-boot-starter替换为mybatis-plus-spring-boot3-starter

```xml
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
            <version>3.5.10.1</version>
        </dependency>
```

#### 报错

```
java: 无法访问com.baomidou.mybatisplus.extension.repository.IRepository
  找不到com.baomidou.mybatisplus.extension.repository.IRepository的类文件
```

mybatisplus版本部分未更新，由以下代码生成器影响产生

#### 代码生成器

代码生成器需要更新，不如会影响mybatisplus版本

```
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-generator</artifactId>
            <version>3.5.12</version>
        </dependency>
```



**Mapper.selectCount**

返回值改为 Long

#### 分页问题

**pagehelper 不支持3.x版本需要排除掉pagehelper中mybatis相关依赖**

如果使用了`pagehelper`分页插件，先手动排查掉`pagehelper`中的`mybatis`相关依赖

```xml
        <dependency>
            <groupId>com.github.pagehelper</groupId>
            <artifactId>pagehelper-spring-boot-starter</artifactId>
            <version>2.1.0</version>
            <exclusions>
                <exclusion>
                    <groupId>org.mybatis</groupId>
                    <artifactId>mybatis</artifactId>
                </exclusion>
                <exclusion>
                    <groupId>org.mybatis</groupId>
                    <artifactId>mybatis-spring</artifactId>
                </exclusion>
                <exclusion>
                    <groupId>org.mybatis.spring.boot</groupId>
                    <artifactId>mybatis-spring-boot-starter</artifactId>
                </exclusion>
            </exclusions>
        </dependency>
```

Mybatisplus**分页插件须自行导入依赖**，版本与Mybatisplus一致

```
        <!--分页插件-->
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-jsqlparser</artifactId>
            <version>3.5.10.1</version>
        </dependency>
```

```java
    @Bean
    public MybatisPlusInterceptor paginationInterceptor() {
//        PaginationInterceptor paginationInterceptor = new PaginationInterceptor();
//        // 设置最大分页100条
//        paginationInterceptor.setLimit(100);
//        paginationInterceptor.setCountSqlParser(new JsqlParserCountOptimize(true));
//        paginationInterceptor.setDbType(DbType.MYSQL);

        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        PaginationInnerInterceptor innerInterceptor = new PaginationInnerInterceptor();
        innerInterceptor.setMaxLimit(100L);
        innerInterceptor.setDbType(DbType.MYSQL);
        innerInterceptor.setOptimizeJoin(true);
        interceptor.addInnerInterceptor(innerInterceptor);

        return interceptor;
    }

//    @Bean
//    public OptimisticLockerInterceptor optimisticLockerInterceptor() {
//        return new OptimisticLockerInterceptor();
//    }

    @Bean
    public OptimisticLockerInnerInterceptor optimisticLockerInnerInterceptor(){
        return new OptimisticLockerInnerInterceptor();
    }
```



#### javax.servlet:javax.servlet-api迁移

javax.servlet:javax.servlet-api相关的依赖全部迁移到jakarta.servlet:jakarta.servlet-api

例如：

- import javax.servlet.http.HttpServletRequest; -> import jakarta.servlet.http.HttpServletRequest;

- import javax.servlet.http.HttpServletResponse; -> import jakarta.servlet.http.HttpServletResponse;
- import javax.servlet.http.HttpSession; -> import jakarta.servlet.http.HttpSession;
- import javax.servlet.http.Cookie; -> import jakarta.servlet.http.Cookie;
- import javax.annotation.PostConstruct; -> import jakarta.annotation.PostConstruct;

### druid版本更新