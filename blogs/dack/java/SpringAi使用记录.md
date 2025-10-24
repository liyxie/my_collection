`工具调用`与`http接口调用`共用 `Service` 层业务



工具调用异常时，会被系统异常捕抓统一抛出，不响应回模型，不走ai对话



声明式工具（@Tool）的类多时，可创建接口，工具类继承接口并@Component生成beng，用List自动收集，再List.toArray()注入



工具参数可直接使用实体类，在实体类中使用Swwager注释描述字段属性能自动在调用时序列化供ai理解参数；

注意Swwager3中，必填属性变动；

工具共用实体类参数时，部分自动是否必填不同，可建一个新实体类继承父类，在子类中写同名字段来覆盖掉父类字段及注解

```
@Schema(description = "项目预算总金额", requiredMode = Schema.RequiredMode.REQUIRED)
```

