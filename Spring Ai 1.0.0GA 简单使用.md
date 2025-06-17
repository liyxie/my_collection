# Spring Ai 1.0.0GA 简单使用

## 前言

Spring Ai 的简单demo；主要为连接deepseek模型，构建聊天系统，MCP使用等；

由于版本更新比较快，每个版本变动会较大，具体的使用建议看 官方文档 [Introduction :: Spring AI Reference](https://docs.spring.io/spring-ai/reference/index.html) 注意版本

------



## 版本与依赖

只列举了主要的，其他的web那些自己导

```xml
<spring-boot.version>3.3.3</spring-boot.version>
<spring-ai>1.0.0</spring-ai>
<java.version>17</java.version>

<dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>${spring-boot.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>


		   <!-- maven central，通过 bom导入依赖项 -->
            <dependency>
                <groupId>org.springframework.ai</groupId>
                <artifactId>spring-ai-bom</artifactId>
                <version>${spring-ai}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
```

------



## deepseek聊天模型

导入依赖，版本由 `spring-ai-bom` 控制；

```xml
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-starter-model-deepseek</artifactId>
        </dependency>
```

配置文件

```yaml
spring:
  ai:
    deepseek:
      api-key: 
      chat:
        options:
          model: deepseek-chat
          temperature: 0.8
          # 这里会覆盖上一个
        api-key: 
```

主要填 `api-key` `model` 就行

