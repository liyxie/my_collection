## lombok注解失效（@Data）

检查pom文件是否添加依赖；

Spring官方建项目添加lombok依赖时通常会自动导入lombok插件，需要注释掉

```xml
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
<!--            <optional>true</optional>-->
        </dependency>


	<build>
        <plugins>
<!--            <plugin>-->
<!--                <groupId>org.apache.maven.plugins</groupId>-->
<!--                <artifactId>maven-compiler-plugin</artifactId>-->
<!--                <configuration>-->
<!--                    <annotationProcessorPaths>-->
<!--                        <path>-->
<!--                            <groupId>org.projectlombok</groupId>-->
<!--                            <artifactId>lombok</artifactId>-->
<!--                        </path>-->
<!--                    </annotationProcessorPaths>-->
<!--                </configuration>-->
<!--            </plugin>-->
<!--            <plugin>-->
<!--                <groupId>org.springframework.boot</groupId>-->
<!--                <artifactId>spring-boot-maven-plugin</artifactId>-->
<!--                <configuration>-->
<!--                    <excludes>-->
<!--                        <exclude>-->
<!--                            <groupId>org.projectlombok</groupId>-->
<!--                            <artifactId>lombok</artifactId>-->
<!--                        </exclude>-->
<!--                    </excludes>-->
<!--                </configuration>-->
<!--            </plugin>-->
        </plugins>
    </build>
```



## 打包配置

配置好启动类路径

```xml
    <build>
        <resources>
            <resource>
                <directory>src/main/java</directory>
                <includes>
                    <include>**/*.xml</include>
                </includes>
                <filtering>false</filtering>
            </resource>
            <resource>
                <directory>src/main/resources</directory>
            </resource>
        </resources>
        <testResources>
            <testResource>
                <directory>src/main/java</directory>
                <includes>
                    <include>**/*.xml</include>
                </includes>
                <filtering>false</filtering>
            </testResource>
        </testResources>
        <plugins>
            <!-- maven打包插件 -> 将整个工程打成一个 fatjar -->
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <!-- 作用:项目打成jar，同时把本地jar包也引入进去 -->
                <configuration>
                    <includeSystemScope>true</includeSystemScope>
                    
                    <mainClass>com.dc.dc_project.DcProjectApplication</mainClass>
                </configuration>
            </plugin>
            <!--添加配置跳过测试-->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>2.22.1</version>
                <configuration>
                    <skipTests>true</skipTests>
                </configuration>
            </plugin>
        </plugins>
        <finalName>dc-project</finalName>
    </build>
```

