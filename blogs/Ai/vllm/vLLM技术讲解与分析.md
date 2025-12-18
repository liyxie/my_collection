# vLLM 技术讲解与深度分析

> 基于 Aleksa Gordić 的文章《Inside vLLM: Anatomy of a High-Throughput LLM Inference System》的学习笔记与技术解读

---

## 前言

这篇文章是对 vLLM 推理引擎的深度技术分析。vLLM 是目前最流行的开源 LLM 推理框架之一，被广泛应用于生产环境。理解其内部工作原理对于：

1. **优化推理性能** - 知道瓶颈在哪里才能针对性优化
2. **排查问题** - 理解系统架构有助于快速定位问题
3. **二次开发** - 为 vLLM 贡献代码或基于其开发
4. **技术选型** - 对比不同推理框架时做出明智决策

---

## 核心概念速览

在深入之前，先理解几个关键概念：

### 1. 为什么 LLM 推理需要特殊优化？

传统深度学习推理（如图像分类）是一次性的前向传播。但 LLM 推理是**自回归**的：

```
输入: "Hello, my name is"
第1步: 生成 "Alice" → 需要完整前向传播
第2步: 生成 "." → 又需要完整前向传播（但可以复用之前的 KV 缓存）
第3步: 生成 "I" → 又需要完整前向传播
...
```

每生成一个 token 都需要：
- 加载全部模型权重（几十 GB）
- 但只计算一个 token 的输出

这导致 **GPU 利用率极低**，大部分时间在等待内存读取。

### 2. 两个关键阶段

LLM 推理分为两个截然不同的阶段：

| 阶段 | Prefill（预填充） | Decode（解码） |
|------|------------------|----------------|
| 输入 | 整个 prompt | 单个 token |
| 特点 | 计算密集型 | 内存带宽密集型 |
| 瓶颈 | GPU 算力 | HBM 带宽 |
| 可并行 | 高度并行 | 难以并行 |

理解这个区别是理解 vLLM 所有优化的基础。

---

## vLLM 的核心创新

### 1. PagedAttention（分页注意力）

**问题**：传统实现为每个请求预分配连续的 KV 缓存空间，导致：
- 内存碎片化严重
- 无法动态调整
- 内存利用率低（通常只有 20-40%）

**解决方案**：借鉴操作系统的虚拟内存思想

```
传统方式：
请求1: [████████████████████████████████] 连续分配，可能有大量浪费
请求2: [████████████] 
请求3: [████████████████████]

PagedAttention：
Block Pool: [B1][B2][B3][B4][B5][B6][B7][B8][B9]...
请求1: B1 → B3 → B7 → B2  (按需分配，不连续)
请求2: B4 → B8
请求3: B5 → B6 → B9
```

**关键数据结构**：
- `free_block_queue`: 空闲块的双向链表
- `req_to_blocks`: 请求 ID → 块列表的映射
- 每个块默认存储 16 个 token 的 KV 缓存

**优势**：
- 内存利用率提升到 90%+
- 支持动态序列长度
- 便于实现前缀缓存等高级特性

### 2. Continuous Batching（连续批处理）

**问题**：传统静态批处理

```
传统方式：
时刻0: [请求1, 请求2, 请求3] 开始
时刻T: 请求1完成，但必须等待请求2、3
时刻2T: 请求2完成，继续等待
时刻3T: 全部完成，才能处理新请求
```

**解决方案**：动态插入/移除请求

```
Continuous Batching：
时刻0: [请求1, 请求2, 请求3]
时刻T: 请求1完成 → 立即插入请求4 → [请求2, 请求3, 请求4]
时刻T+1: [请求2, 请求3, 请求4, 请求5] 新请求随时加入
```

**实现关键**：
- 所有序列展平为一个"超级序列"
- 通过位置编码和注意力掩码区分不同请求
- 自定义 CUDA 内核高效处理

### 3. Prefix Caching（前缀缓存）

**场景**：多个请求共享相同的系统提示

```python
system_prompt = "You are a helpful assistant..."  # 1000 tokens

# 请求1
prompt1 = system_prompt + "What is Python?"
# 请求2  
prompt2 = system_prompt + "Explain machine learning"
# 请求3
prompt3 = system_prompt + "How to cook pasta?"
```

**没有前缀缓存**：每个请求都要计算 system_prompt 的 1000 个 token

**有前缀缓存**：
1. 请求1 计算 system_prompt，缓存其 KV
2. 请求2、3 直接复用，只计算各自的问题部分

**实现机制**：
```
1. 将 prompt 分成 16-token 的块
2. 对每个块计算哈希值（包含前一块的哈希，形成链式哈希）
3. 查找 cached_block_hash_to_block 字典
4. 命中则复用，未命中则计算并缓存
```

---

## 高级特性详解

### Chunked Prefill（分块预填充）

**问题**：超长 prompt 会独占 GPU 很长时间

```
场景：一个 10000 token 的 prompt
传统方式：这个请求独占 GPU 直到 prefill 完成
其他请求：只能等待，延迟飙升
```

**解决方案**：将长 prefill 分成多个小块

```
Chunked Prefill (chunk_size=512):
Step 1: 处理 token 0-511
Step 2: 处理 token 512-1023 + 其他请求的 decode
Step 3: 处理 token 1024-1535 + 其他请求的 decode
...
```

**效果**：
- 长请求不会饿死短请求
- 整体延迟更可预测
- 更好的 GPU 利用率

### Speculative Decoding（推测解码）

**核心思想**：用小模型猜测，大模型验证

```
传统解码（每步1个token）：
Step 1: 大模型 → token1
Step 2: 大模型 → token2
Step 3: 大模型 → token3
总计：3次大模型前向传播

推测解码：
Step 1: 小模型快速生成 [token1', token2', token3']
Step 2: 大模型一次验证 → 接受 token1', token2'，拒绝 token3'
Step 3: 从拒绝位置重新采样
总计：可能只需1-2次大模型前向传播
```

**vLLM 支持的方法**：
1. **N-gram**: 在已生成的序列中查找重复模式
2. **EAGLE**: 轻量级 MLP 替代 transformer 层
3. **Medusa**: 多个并行预测头

**适用场景**：
- 输出有重复模式（代码、格式化文本）
- 延迟敏感的应用
- 批次较小时效果更明显

### Guided Decoding（引导解码）

**场景**：强制输出符合特定格式

```python
# 情感分析，只能输出 "Positive" 或 "Negative"
guided_params = GuidedDecodingParams(choice=["Positive", "Negative"])

# JSON 输出
guided_params = GuidedDecodingParams(json_schema={...})

# 正则表达式约束
guided_params = GuidedDecodingParams(regex=r"\d{4}-\d{2}-\d{2}")
```

**实现原理**：
1. 将约束编译为有限状态机（FSM）
2. 每步解码时，FSM 生成允许的 token 掩码
3. 将不允许的 token 的 logits 设为 -∞
4. 采样后更新 FSM 状态

---

## 分布式架构

### 单机多卡：MultiProcExecutor

```
                    ┌─────────────────┐
                    │   LLM Engine    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ MultiProcExecutor│
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │ Worker 0│        │ Worker 1│        │ Worker 2│
    │ (GPU 0) │        │ (GPU 1) │        │ (GPU 2) │
    └─────────┘        └─────────┘        └─────────┘
```

**通信机制**：
- `rpc_broadcast_mq`: 共享内存消息队列，广播工作
- `worker_response_mq`: 每个 worker 的响应队列
- NCCL: GPU 间的张量通信

### 多机多卡：完整分布式

```
Node 1 (Headless)                    Node 2 (API Server)
┌─────────────────────┐              ┌─────────────────────┐
│ DPEngineCoreProc 0  │◄────────────►│    AsyncLLM         │
│ DPEngineCoreProc 1  │   ZMQ        │    FastAPI          │
└─────────────────────┘              │    Uvicorn          │
         │                           └─────────────────────┘
         │ NCCL                                │
         ▼                                     │
┌─────────────────────┐                        │
│   GPU 0-3 (TP=4)    │                        │
│   GPU 4-7 (TP=4)    │                        │
└─────────────────────┘                        │
                                               ▼
                                        ┌─────────────┐
                                        │   Client    │
                                        └─────────────┘
```

**关键组件**：
- **DPCoordinator**: 协调数据并行副本
- **负载均衡**: `score = len(waiting) * 4 + len(running)`
- **锁步执行**: 所有 DP 副本同步执行（MoE 模型需要）

---

## 性能调优指南

### 关键指标

| 指标 | 含义 | 优化方向 |
|------|------|----------|
| TTFT | 首 token 延迟 | 减少 prefill 时间 |
| ITL | token 间延迟 | 优化 decode 效率 |
| Throughput | 吞吐量 | 增大批次，提高 GPU 利用率 |
| Goodput | 有效吞吐量 | 在满足 SLO 前提下最大化 |

### 延迟 vs 吞吐量权衡

```
批次大小 B 的影响：

B 小 → ITL 低（延迟好）但吞吐量低
B 大 → 吞吐量高但 ITL 高（延迟差）

最佳点：B_sat（饱和批次大小）
- B < B_sat: 内存带宽瓶颈，增大 B 几乎不增加延迟
- B > B_sat: 计算瓶颈，增大 B 线性增加延迟
```

### 实用建议

1. **在线服务（延迟敏感）**：
   - 使用较小的 `max_num_seqs`
   - 启用 chunked prefill
   - 考虑 speculative decoding

2. **离线批处理（吞吐量优先）**：
   - 增大 `max_num_seqs`
   - 禁用 chunked prefill
   - 使用 `QPS=Inf` 模式

3. **混合场景**：
   - 使用 P/D 分离
   - 配置合适的 SLO
   - 监控 goodput 而非 throughput

---

## 总结

vLLM 的成功在于它系统性地解决了 LLM 推理的核心挑战：

1. **内存效率**: PagedAttention 将内存利用率从 ~30% 提升到 ~90%
2. **批处理效率**: Continuous Batching 消除了等待时间
3. **计算复用**: Prefix Caching 避免重复计算
4. **延迟优化**: Chunked Prefill + Speculative Decoding
5. **可扩展性**: 从单 GPU 到多节点的统一架构

理解这些原理不仅有助于使用 vLLM，也为理解其他推理框架（如 SGLang、TensorRT-LLM）打下基础。

---

## 延伸阅读

- [vLLM 官方文档](https://docs.vllm.ai/)
- [PagedAttention 论文](https://arxiv.org/abs/2309.06180)
- [Orca 论文（Continuous Batching）](https://www.usenix.org/conference/osdi22/presentation/yu)
- [Speculative Decoding 论文](https://arxiv.org/abs/2302.01318)
