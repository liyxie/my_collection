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

## @Value和@Bean的执行顺序问题

```java
// 无法在静态字段上使用 @Value 
@Value("${minio.endpoint}")
private static String endpoint;

@Configuration
public class MyConfig {
    @Value("${minio.endpoint}")
    private String endpoint;  // 可能为 null
    @Bean
    public MinioClient minioClient() {
        System.out.println(endpoint);  // ❌ 可能输出 null
        return MinioClient.builder()
            .endpoint(endpoint)
            .build();
    }
}
```

## XML中 IN 写法注意

```java
Page<UserVo> getUserListByAll(@Param("userReqDto") UserReqDto userReqDto, @Param("orgIds") List<Long> orgIds);
```

```xml
    <select id="getUserListByAll" resultType="com.dc.dc_project.model.vo.UserVo">
        SELECT
        u.id,
		······
        LEFT JOIN sys_org o ON spo.org_id = o.id
        <where>
			······
            <if test="orgIds != null">
                AND o.id in (#{orgIds})
            </if>
            <!-- 以上写法是错误，无法识别到List-->
            and u.is_deleted = 0
        </where>
    </select>

<!-- 正确-->
<if test="orgIds != null">
    o.id in
    <foreach item="item" collection="orgIds" separator="," open="(" close=")">
         #{item}
    </foreach>
</if>

```

