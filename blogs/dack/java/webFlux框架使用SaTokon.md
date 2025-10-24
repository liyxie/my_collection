依赖



过滤器



登录用户信息

# Sa-Token 在 WebFlux 异步环境下的上下文丢失问题与解决方案

## 1. 问题现象

在使用 Spring WebFlux 框架时，整合 Sa-Token 可能会遇到一个典型问题：在 `SaReactorFilter` 过滤器中，可以正常通过 `StpUtil.getLoginId()` 获取到登录用户 ID，但在控制器 (`@RestController`) 或更深层次的业务逻辑（Service 层、AI 工具函数等）中，调用 `StpUtil.getLoginId()` 却会抛出 `SaTokenContext 上下文尚未初始化` 异常。

**示例代码中的表现：**

- 过滤器中正常：

  ```
  public class SaTokenConfigureAsync {
  
      // ...
  
      .setAuth(obj -> {
  
          log.info("过滤器：{}", StpUtil.getLoginId()); // 这里可以正常获取
  
          // ...
  
      })
  
      // ...
  
  }
  ```

- 接口中异常：

  ```
  @RestController
  
  public class ChatController {
  
      @PostMapping("/chat")
  
      public Flux<String> chat(@RequestBody MessageVo messageVo){
  
          log.info("ai : {}", StpUtil.isLogin()); // 可能会报异常
  
          String userId = StpUtil.getLoginId().toString(); // <-- 这里会抛出异常
  
          // ...
  
      }
  
  }
  ```

## 2. 问题根源：`ThreadLocal` 在 WebFlux 异步流中的失效

Sa-Token（以及许多其他基于传统 Servlet 模型的框架）默认使用 `ThreadLocal` 来存储和访问当前请求的上下文信息，例如登录用户 ID、请求对象等。

然而，Spring WebFlux 是一个基于 Reactor 的**响应式非阻塞**框架。它的核心特点是：

1. **异步非阻塞：** 请求的处理不再是“一个请求一个线程”的同步模式，而是通过事件循环、回调和响应式流 (`Mono`/`Flux`) 来处理。
2. **线程切换：** 在处理一个 WebFlux 请求的生命周期中，底层的线程可能会频繁地进行切换。例如，请求可能从 Netty I/O 线程开始，然后被调度到 Reactor 的工作线程池，最后可能在不同的线程上执行业务逻辑或订阅异步操作。

**当线程发生切换时，存储在 `ThreadLocal` 中的数据就会丢失，因为 `ThreadLocal` 的数据是与当前线程绑定的。**

在你的 `SaReactorFilter` 中，`setAuth` 方法在请求处理的**早期阶段**执行，通常在初始的请求处理线程中，此时 `ThreadLocal` 上下文是存在的。但当请求进入到你的控制器方法或更深层的异步 Service 调用时，如果发生了线程切换，`StpUtil` 就无法从 `ThreadLocal` 中获取到上下文，从而抛出异常。

## 3. Sa-Token 官方 WebFlux 解决方案：Reactor `Context` 与 `SaReactorHolder`

为了解决 `ThreadLocal` 在 WebFlux 中的失效问题，Sa-Token 针对 WebFlux 提供了专门的适配机制，主要依赖于 Reactor 的 `Context` 和 `SaReactorHolder` 类。

- **Reactor `Context`：** Reactor `Context` 是 Reactor 框架提供的一种机制，用于在响应式流中（即 `Mono` 和 `Flux` 链）**传播数据**。与 `ThreadLocal` 绑定线程不同，`Context` 是绑定到订阅者（Subscriber）的，并且会在整个响应式流中传递，即使线程发生切换。
- **`SaReactorFilter`：** Sa-Token 的 `SaReactorFilter` 在 WebFlux 请求开始时，除了进行鉴权，还会负责将当前的 Sa-Token 上下文（如 `LoginId`）从 `ThreadLocal` **同步到 Reactor 的 `Context` 中**。
- **`SaReactorHolder`：** 这是 Sa-Token 提供的在 WebFlux 环境下获取上下文的辅助类。它内部会从当前的 Reactor `Context` 中读取之前由 `SaReactorFilter` 存入的 Sa-Token 相关数据。

## 4. 推荐解决方案

核心思想是：**在 WebFlux 异步流中，Service 层方法应显式接收 `userId` 作为参数，而不是依赖 `StpUtil.getLoginId()`。而控制器方法则通过 `SaReactorHolder.getContext().getLoginId()` 从 Reactor `Context` 中获取 `userId`，并向下传递。**

### 步骤一：配置 `SaReactorFilter` (过滤器)

确保你的 `SaReactorFilter` 配置正确。它会负责将 `ThreadLocal` 中的 Sa-Token 上下文同步到 Reactor `Context` 中。通常，你只需要配置鉴权逻辑即可，Sa-Token 的 WebFlux 适配器会处理上下文同步。

```
import cn.dev33.sa.token.reactor.filter.SaReactorFilter;

import cn.dev33.sa.token.stp.StpUtil;

import cn.dev33.sa.token.util.SaHolder;

import cn.dev33.sa.token.util.SaResult;

import org.springframework.context.annotation.Bean;

import org.springframework.context.annotation.Configuration;

import reactor.core.publisher.Mono;

 

@Configuration

public class SaTokenConfigureAsync {

 

    @Bean

    public SaReactorFilter getSaReactorFilter() {

        return new SaReactorFilter()

                .addInclude("/**")

                .addExclude("/user/login", "/user/doLogin", "/error")

                .setAuth(obj -> {

                    // 在这里，StpUtil.getLoginId() 是可以正常工作的，

                    // SaReactorFilter 会将此信息同步到 Reactor Context 中。

                    String requestPath = SaHolder.getRequest().getRequestPath();

                    if (requestPath.startsWith("/project/")) {

                        StpUtil.checkLogin(); // 校验是否登录

                    }

                    return Mono.empty(); // 继续处理请求

                })

                .setError(e -> {

                    e.printStackTrace();

                    return SaResult.error(e.getMessage());

                });

    }

}
```

### 步骤二：修改控制器 (`@RestController`) 接口

控制器方法不再直接调用 `StpUtil.getLoginId()`，而是通过 `Mono.deferContextual` 结合 `SaReactorHolder.getContext()` 获取 `userId`。

```

import cn.dev33.sa.token.reactor.context.SaReactorHolder; // 引入 SaReactorHolder

import cn.dev33.sa.token.stp.StpUtil; // 仅用于 NotLoginException 的 getLoginType()

import cn.dev33.sa.token.exception.NotLoginException;

import org.springframework.web.bind.annotation.PostMapping;

import org.springframework.web.bind.annotation.RequestBody;

import org.springframework.web.bind.annotation.RequestMapping;

import org.springframework.web.bind.annotation.RestController;

import reactor.core.publisher.Flux;

import reactor.core.publisher.Mono;

import java.util.Map; // For Map.of()

 

@RestController

@RequestMapping("/ai")

public class ChatController {

 

    private final ChatClient chatClient; // 假设 chatClient 是通过构造函数注入的

    // ... constructor

 

    @PostMapping(value = "/chat", produces = "text/html;charset=UTF-8")

    public Flux<String> chat(@RequestBody MessageVo messageVo) {

        return Mono.deferContextual(ctx -> {

            // 从 SaReactorHolder 中获取 Sa-Token 上下文，它会从 Reactor Context 中读取

            Object loginIdObj = SaReactorHolder.getContext().getLoginId();

            if (loginIdObj == null) {

                // 如果未登录，抛出异常，由全局异常处理器处理

                throw new NotLoginException("SaTokenContext 上下文尚未初始化或登录状态丢失", StpUtil.getLoginType(), "");

            }

            String userId = loginIdObj.toString();

 

            // 将 userId 显式传递给后续的异步操作或服务

            Flux<String> content = chatClient.prompt()

                                            .user(messageVo.getContent())

                                            .toolContext(Map.of("userid", userId)) // 显式传递 userId

                                            .stream()

                                            .content();

            return content;

        }).flatMapMany(flux -> flux); // 扁平化 Mono<Flux<String>> 为 Flux<String>

    }

 

    // 其他 WebFlux 接口

    @PostMapping("/otherBiz")

    public Mono<String> otherBiz() {

        return Mono.deferContextual(ctx -> {

            Object loginIdObj = SaReactorHolder.getContext().getLoginId();

            if (loginIdObj == null) {

                throw new NotLoginException("未登录", StpUtil.getLoginType(), "");

            }

            String userId = loginIdObj.toString();

            // 调用 Service 层方法，显式传递 userId

            return Mono.just("Hello, User: " + userId);

        });

    }

}
```

### 步骤三：修改 Service 层方法签名和调用方式

所有需要用户 ID 的 Service 层方法，都应该**显式地接收 `userId` 作为参数**。

```java

import org.springframework.stereotype.Service;

import reactor.core.publisher.Mono;

import java.util.List;

 

@Service

public class MyBizService {

 

    // 假设 DataRepository 是你的数据访问层

    private final DataRepository dataRepository;

 

    public MyBizService(DataRepository dataRepository) {

        this.dataRepository = dataRepository;

    }

 

    /**

     * 获取用户相关数据，userId 显式传入

     * @param userId 登录用户ID

     * @return 用户数据列表

     */

    public Mono<List<Data>> getUserRelatedData(String userId) {

        // 根据 userId 执行业务逻辑和数据查询

        return dataRepository.findByUserId(userId);

    }

 

    /**

     * 执行复杂业务，也应显式传递 userId

     * @param userId 登录用户ID

     * @param param 业务参数

     * @return 业务结果

     */

    public Mono<SomeOtherResult> doSomethingComplex(String userId, SomeParam param) {

        return getUserRelatedData(userId) // 内部调用也传递 userId

                .flatMap(dataList -> {

                    // 使用 userId 和 dataList 执行更多操作

                    return Mono.just(new SomeOtherResult());

                });

    }

}
```

### 步骤四：AI 工具函数调用 Service

在 AI 工具函数中，你已经通过 `toolContext.getContext().get("userid")` 获取到了 `userId`。直接将此 `userId` 传递给 Service 方法。

```
import reactor.core.publisher.Mono;

import java.util.Map;

 

// 假设这是你的 AI 工具服务

public class AiToolService {

    private final MyBizService myBizService;

 

    public AiToolService(MyBizService myBizService) {

        this.myBizService = myBizService;

    }

 

    public Mono<String> callToolFunction(Map<String, Object> toolContext) {

        String userId = (String) toolContext.get("userid"); // 从工具上下文获取 userId

 

        if (userId == null) {

            return Mono.error(new IllegalArgumentException("AI 工具调用缺少用户ID"));

        }

 

        // 调用 Service 层方法，显式传递 userId

        return myBizService.getUserRelatedData(userId)

                .map(dataList -> "AI 工具查询到用户数据: " + dataList.size() + " 条");

    }

}
```

## 5. 优点总结

1. **线程安全与异步兼容：** 消除了对 `ThreadLocal` 的依赖，确保在 WebFlux 的异步线程切换环境中，`userId` 始终可达且正确。
2. **清晰的依赖关系：** Service 方法的签名明确表示了它需要 `userId` 参数，增强了代码可读性和可维护性。
3. **高度解耦：** Service 层不依赖特定的 WebFlux 上下文或 Sa-Token 内部机制，使其更具通用性，可以被各种调用方（HTTP 请求、AI 工具、定时任务、消息队列等）复用。
4. **避免副作用：** 避免了在异步非 HTTP 线程中错误地调用 `StpUtil.login()` 导致原有用户被挤下线的问题。
5. **易于测试：** Service 层单元测试时可以直接传入模拟的 `userId`，无需模拟复杂的 `ThreadLocal` 或 Reactor `Context`。

通过上述方法，你可以构建一个在 WebFlux 异步环境中稳定、高效且易于维护的 Sa-Token 集成方案。