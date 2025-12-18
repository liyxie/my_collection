# vLLM 深入解析：高吞吐量 LLM 推理系统剖析

> 原文：Inside vLLM: Anatomy of a High-Throughput LLM Inference System - Aleksa Gordić
> 
> 从 paged attention（分页注意力）、continuous batching（连续批处理）、prefix caching（前缀缓存）、speculative decoding（推测解码）等技术，到多 GPU、多节点的大规模动态服务

**发布日期：2025年8月29日**

---

在这篇文章中，我将逐步介绍构成现代高吞吐量 LLM 推理系统的所有核心系统组件和高级特性。特别地，我将对 vLLM [1] 的工作原理进行详细分析。

这篇文章是系列文章的第一篇。它从宏观开始，然后逐层深入细节（采用倒金字塔方法），这样你可以在不被细枝末节淹没的情况下，形成对完整系统的准确高层心智模型。

后续文章将深入探讨特定子系统。

本文分为五个部分：

1. [LLM 引擎与引擎核心](#llm-引擎与引擎核心)：vLLM 的基础（调度、分页注意力、连续批处理等）
2. [高级特性](#高级特性)：分块预填充、前缀缓存、引导解码与推测解码、P/D 分离
3. [扩展](#从-uniprocexecutor-到-multiprocexecutor)：从单 GPU 到多 GPU 执行
4. [服务层](#分布式系统服务-vllm)：分布式/并发 Web 架构
5. [基准测试与自动调优](#基准测试与自动调优---延迟与吞吐量)：测量延迟和吞吐量

> 📝 **说明**
> - 分析基于 [commit 42172ad](https://github.com/vllm-project/vllm/tree/42172ad)（2025年8月9日）
> - 目标读者：任何对最先进的 LLM 引擎工作原理感兴趣的人，以及有兴趣为 vLLM、SGLang 等项目做贡献的人
> - 我将重点关注 [V1 引擎](https://docs.vllm.ai/en/latest/usage/v1_guide.html)。我也研究了 V0（[现已弃用](https://github.com/vllm-project/vllm/issues/18571)），这对理解项目演进很有价值，许多概念仍然适用
> - 关于 LLM 引擎/引擎核心的第一部分可能有点难以消化——但文章其余部分有大量示例和图示 :)

---

## LLM 引擎与引擎核心

LLM 引擎是 vLLM 的基础构建块。它本身已经能够实现高吞吐量推理——但仅限于离线场景。你还不能通过 Web 向客户提供服务。

我们将使用以下离线推理代码片段作为运行示例（改编自 [basic.py](https://github.com/vllm-project/vllm/blob/main/examples/offline_inference/basic/basic.py)）：

```python
from vllm import LLM, SamplingParams

prompts = [
    "Hello, my name is",
    "The president of the United States is",
]

sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

def main():
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    outputs = llm.generate(prompts, sampling_params)

if __name__ == "__main__":
    main()
```

> 📝 **环境变量**
> - VLLM_USE_V1="1" # 使用引擎 V1
> - VLLM_ENABLE_V1_MULTIPROCESSING="0" # 在单进程中运行

这个配置是：
- **离线**（没有 Web/分布式系统架构）
- **同步**（所有执行都在单个阻塞进程中进行）
- **单 GPU**（没有数据/模型/流水线/专家并行；DP/TP/PP/EP = 1）
- **使用标准 transformer** [2]（支持像 Jamba 这样的混合模型需要更复杂的混合 KV 缓存内存分配器）

从这里开始，我们将逐步构建一个在线、异步、多 GPU、多节点的推理系统——但仍然服务于标准 transformer。

在这个示例中，我们做两件事：
1. 实例化一个引擎
2. 调用 `generate` 从给定的提示词中采样

让我们开始分析构造函数。

### LLM 引擎构造函数

引擎的主要组件包括：

- **vLLM 配置**（包含配置模型、缓存、并行性等的所有参数）
- **处理器**（通过验证、分词和处理将原始输入转换为 `EngineCoreRequests`）
- **引擎核心客户端**（在我们的运行示例中使用 `InprocClient`，它基本上等同于 `EngineCore`；我们将逐步构建到 `DPLBAsyncMPClient`，它允许大规模服务）
- **输出处理器**（将原始 `EngineCoreOutputs` 转换为用户看到的 `RequestOutput`）

> 📝 **注意**
> 随着 V0 引擎被弃用，类名和细节可能会发生变化。我将强调核心思想而不是确切的签名。我会抽象掉一些但不是全部的细节。

引擎核心本身由几个子组件组成：

- **Model Executor（模型执行器）**（驱动模型的前向传播，我们目前处理的是 `UniProcExecutor`，它在单个 GPU 上有一个 `Worker` 进程）。我们将逐步构建到支持多 GPU 的 `MultiProcExecutor`
- **Structured Output Manager（结构化输出管理器）**（用于引导解码——稍后介绍）
- **Scheduler（调度器）**（决定哪些请求进入下一个引擎步骤）——它进一步包含：
  - 策略设置——可以是 **FCFS**（先来先服务）或 **priority**（优先级，高优先级请求优先服务）
  - `waiting` 和 `running` 队列
  - **KV 缓存管理器**——分页注意力 [3] 的核心

KV 缓存管理器维护一个 `free_block_queue`——一个可用 KV 缓存块的池（通常有数十万个，取决于 VRAM 大小和块大小）。在分页注意力期间，这些块作为索引结构，将 token 映射到它们计算出的 KV 缓存块。

![LLM 引擎构造函数](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/engine_constructor.png)
*本节描述的核心组件及其关系*

> 💡 **块大小计算**
> 标准 transformer 层（非 MLA [4]）的块大小计算如下：
> 2（key/value）× `block_size`（默认=16）× `num_kv_heads` × `head_size` × `dtype_num_bytes`（例如 bf16 为 2）

在模型执行器构造期间，会创建一个 `Worker` 对象，并执行三个关键过程。（稍后，使用 `MultiProcExecutor` 时，这些相同的过程会在不同 GPU 上的每个 worker 进程中独立运行。）

1. **初始化设备**：
   - 为 worker 分配 CUDA 设备（例如 "cuda:0"）并检查模型数据类型是否支持（例如 bf16）
   - 验证是否有足够的 VRAM，根据请求的 `gpu_memory_utilization`（例如 0.8 → 总 VRAM 的 80%）
   - 设置分布式设置（DP / TP / PP / EP 等）
   - 实例化 `model_runner`（持有采样器、KV 缓存和前向传播缓冲区，如 `input_ids`、`positions` 等）
   - 实例化 `InputBatch` 对象（持有 CPU 端前向传播缓冲区、KV 缓存索引的块表、采样元数据等）

2. **加载模型**：
   - 实例化模型架构
   - 加载模型权重
   - 调用 model.eval()（PyTorch 的推理模式）
   - 可选：在模型上调用 torch.compile()

3. **初始化 KV 缓存**：
   - 获取每层 KV 缓存规格。历史上这总是 `FullAttentionSpec`（同质 transformer），但随着混合模型（滑动窗口、Transformer/SSM 如 Jamba）变得更加复杂（参见 Jenga [5]）
   - 运行虚拟/分析前向传播并获取 GPU 内存快照，以计算可用 VRAM 中可以容纳多少 KV 缓存块
   - 分配、重塑并将 KV 缓存张量绑定到注意力层
   - 准备注意力元数据（例如将后端设置为 FlashAttention），稍后在前向传播期间由内核使用
   - 除非提供 `--enforce-eager`，否则对于每个预热批次大小进行虚拟运行并捕获 CUDA 图。CUDA 图将整个 GPU 工作序列记录到 DAG 中。稍后在前向传播期间，我们启动/重放预先烘焙的图，减少内核启动开销，从而提高延迟

我在这里抽象了许多底层细节——但这些是我现在要介绍的核心部分，因为我将在后续章节中反复引用它们。

现在引擎已初始化，让我们继续看 `generate` 函数。

### Generate 函数

第一步是验证并将请求馈送到引擎。对于每个提示词，我们：

1. 创建唯一的请求 ID 并捕获其到达时间
2. 调用输入预处理器对提示词进行分词，返回包含 `prompt`、`prompt_token_ids` 和 `type`（文本、token、嵌入等）的字典
3. 将此信息打包到 `EngineCoreRequest` 中，添加优先级、采样参数和其他元数据
4. 将请求传递到引擎核心，引擎核心将其包装在 `Request` 对象中并将其状态设置为 `WAITING`。然后将此请求添加到调度器的 `waiting` 队列（如果是 FCFS 则追加，如果是优先级则堆推送）

此时引擎已被馈送，可以开始执行。在同步引擎示例中，这些初始提示词是我们将处理的唯一提示词——没有机制在运行中注入新请求。相比之下，异步引擎支持这一点（即 **continuous batching（连续批处理）** [6]）：在每一步之后，新旧请求都会被考虑。

> 💡 因为前向传播将批次展平为单个序列，自定义内核高效处理它，所以即使在同步引擎中也从根本上支持连续批处理。

接下来，只要有请求要处理，引擎就会重复调用其 `step()` 函数。每一步有三个阶段：

1. **调度**：选择在此步骤中运行哪些请求（解码和/或（分块）预填充）
2. **前向传播**：运行模型并采样 token
3. **后处理**：将采样的 token ID 追加到每个 `Request`，解码，并检查停止条件。如果请求完成，清理（例如将其 KV 缓存块返回到 `free_block_queue`）并提前返回输出

> 📝 **停止条件**
> - 请求超过其长度限制（`max_model_length` 或其自身的 `max_tokens`）
> - 采样的 token 是 EOS ID（除非启用 `ignore_eos` → 用于基准测试，当我们想强制生成一定数量的输出 token 时很有用）
> - 采样的 token 匹配采样参数中指定的任何 `stop_token_ids`
> - 输出中存在停止字符串——我们截断输出直到第一个停止字符串出现并在引擎中中止请求（注意 `stop_token_ids` 将出现在输出中，但停止字符串不会）

![引擎循环](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/engine_loop.png)
*引擎循环*

> 💡 在流式模式下，我们会在生成时发送中间 token，但我们现在先忽略这一点。

接下来，我们将更详细地检查调度。

### 调度器

推理引擎处理两种主要类型的工作负载：

1. **Prefill（预填充）请求** — 对所有提示词 token 进行前向传播。这些通常是**计算密集型**的（阈值取决于硬件和提示词长度）。最后，我们从最终 token 位置的概率分布中采样单个 token。

2. **Decode（解码）请求** — 仅对最近的 token 进行前向传播。所有早期的 KV 向量已经被缓存。这些是**内存带宽密集型**的，因为我们仍然需要加载所有 LLM 权重（和 KV 缓存）只是为了计算一个 token。

> 💡 在[基准测试部分](#基准测试与自动调优---延迟与吞吐量)，我们将分析所谓的 GPU 性能 roofline 模型。这将更详细地介绍预填充/解码性能特征。

V1 调度器可以在同一步骤中混合两种类型的请求，这得益于更智能的设计选择。相比之下，V0 引擎一次只能处理预填充或解码。

调度器优先处理解码请求——即那些已经在 `running` 队列中的请求。对于每个这样的请求，它：

1. 计算要生成的新 token 数量（由于推测解码和异步调度，不总是 1——稍后详述）
2. 调用 KV 缓存管理器的 `allocate_slots` 函数（详情见下文）
3. 通过减去步骤 1 中的 token 数量来更新 token 预算

之后，它处理来自 `waiting` 队列的预填充请求，它：

1. 检索已计算块的数量（如果禁用前缀缓存则返回 0——稍后介绍）
2. 调用 KV 缓存管理器的 `allocate_slots` 函数
3. 从 waiting 弹出请求并将其移动到 running，将其状态设置为 `RUNNING`
4. 更新 token 预算

现在让我们看看 `allocate_slots` 做什么：

1. **计算块数量** — 确定必须分配多少新的 KV 缓存块（`n`）。每个块默认存储 16 个 token。例如，如果预填充请求有 17 个新 token，我们需要 `ceil(17/16) = 2` 个块。

2. **检查可用性** — 如果管理器池中没有足够的块，提前退出。根据是解码还是预填充请求，引擎可能会尝试重计算抢占（V0 支持交换抢占），通过驱逐低优先级请求（调用 `kv_cache_manager.free` 将 KV 块返回到块池），或者它可能跳过调度并继续执行。

3. **分配块** — 通过 KV 缓存管理器的协调器，从块池（前面提到的 `free_block_queue` 双向链表）获取前 `n` 个块。存储到 `req_to_blocks`，这是将每个 `request_id` 映射到其 KV 缓存块列表的字典。

![KV 缓存块](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/kv_cache_blocks.png)
*KV 缓存块列表*

我们终于准备好进行前向传播了！

### 运行前向传播

我们调用模型执行器的 `execute_model`，它委托给 `Worker`，后者又委托给模型运行器。

以下是主要步骤：

1. **更新状态** — 从 `input_batch` 中修剪已完成的请求；更新杂项前向传播相关元数据（例如，每个请求的 KV 缓存块，将用于索引分页 KV 缓存内存）。

2. **准备输入** — 将缓冲区从 CPU→GPU 复制；计算位置；构建 `slot_mapping`（稍后在示例中详述）；构造注意力元数据。

3. **前向传播** — 使用自定义分页注意力内核运行模型。所有序列被展平并连接成一个长的"超级序列"。位置索引和注意力掩码确保每个序列只关注自己的 token，这使得连续批处理无需右填充。

4. **收集最后 token 状态** — 提取每个序列最终位置的隐藏状态并计算 logits。

5. **采样** — 根据采样配置（贪婪、温度、top-p、top-k 等）从计算的 logits 中采样 token。

前向传播步骤本身有两种执行模式：

1. **Eager 模式** — 当启用 eager 执行时运行标准 PyTorch 前向传播。
2. **"Captured" 模式** — 当不强制 eager 时执行/重放预捕获的 CUDA 图（记住我们在引擎构造期间的初始化 KV 缓存过程中捕获了这些）。

这是一个具体示例，应该能让连续批处理和分页注意力变得清晰：

![前向传播 - 连续批处理和分页注意力](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/fwd_pass.png)
*前向传播：连续批处理和分页注意力*

---

## 高级特性

有了基本的引擎流程，我们现在可以看看高级特性。

我们已经讨论了抢占、分页注意力和连续批处理。

接下来，我们将深入探讨：

1. Chunked prefill（分块预填充）
2. Prefix caching（前缀缓存）
3. Guided decoding（引导解码）（通过语法约束的有限状态机）
4. Speculative decoding（推测解码）
5. Disaggregated P/D（P/D 分离，预填充/解码分离）

### Chunked Prefill（分块预填充）

分块预填充是一种通过将长提示词的预填充步骤分成更小块来处理的技术。没有它，我们可能会遇到单个非常长的请求独占一个引擎步骤，不允许其他预填充请求运行的情况。这会推迟所有其他请求并增加它们的延迟。

例如，让每个块包含 `n`（=8）个 token，用小写字母标记，用"-"分隔。一个长提示词 `P` 可能看起来像 `x-y-z`，其中 `z` 是一个不完整的块（例如 2 个 token）。执行 `P` 的完整预填充将需要 ≥ 3 个引擎步骤（如果在某个步骤中没有被调度执行，可能会更多），只有在最后一个分块预填充步骤中我们才会采样一个新 token。

![分块预填充](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/chunked_pt1.png)

实现很简单：限制每步新 token 的数量。如果请求的数量超过 `long_prefill_token_threshold`，将其重置为该值。底层索引逻辑（前面描述的）会处理其余部分。

在 vLLM V1 中，通过将 `long_prefill_token_threshold` 设置为正整数来启用分块预填充。（技术上，如果提示词长度超过 token 预算，我们会截断它并运行分块预填充，这种情况也可能发生。）

### Prefix Caching（前缀缓存）

为了解释前缀缓存的工作原理，让我们稍微调整一下原始代码示例：

```python
from vllm import LLM, SamplingParams

long_prefix = "<一段编码成超过 block_size 个 token 的文本>"

prompts = [
    "Hello, my name is",
    "The president of the United States is",
]

sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

def main():
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    outputs = llm.generate(long_prefix + prompts[0], sampling_params)
    outputs = llm.generate(long_prefix + prompts[1], sampling_params)

if __name__ == "__main__":
    main()
```

前缀缓存避免重新计算多个提示词在开头共享的 token——因此称为**前缀**。

关键部分是 `long_prefix`：它被定义为任何长于 KV 缓存块（默认 16 个 token）的前缀。为了简化我们的示例，假设 `long_prefix` 的长度正好是 `n x block_size`（其中 `n ≥ 1`）。

> 💡 即它与块边界完美对齐——否则我们必须重新计算 `long_prefix_len % block_size` 个 token，因为我们无法缓存不完整的块。

没有前缀缓存，每次我们处理具有相同 `long_prefix` 的新请求时，我们都会重新计算所有 `n x block_size` 个 token。

有了前缀缓存，这些 token 只计算一次（它们的 KV 存储在 KV 缓存分页内存中），然后被重用，所以只需要处理新的提示词 token。这加速了预填充请求（尽管它对解码没有帮助）。

**这在 vLLM 中如何工作？**

在第一次 `generate` 调用期间，在调度阶段，在 `kv_cache_manager.get_computed_blocks` 内部，引擎调用 `hash_request_tokens`：

1. 此函数将 `long_prefix + prompts[0]` 分成 16 个 token 的块。
2. 对于每个完整的块，它计算一个哈希（使用内置哈希或 SHA-256，后者较慢但碰撞更少）。哈希结合了前一个块的哈希、当前 token 和可选元数据。

> 💡 可选元数据包括：MM 哈希、LoRA ID、缓存盐（注入到第一个块的哈希中，确保只有具有此缓存盐的请求才能重用块）。

3. 每个结果存储为包含哈希及其 token ID 的 `BlockHash` 对象。我们返回块哈希列表。

该列表存储在 `self.req_to_block_hashes[request_id]` 中。

接下来，引擎调用 `find_longest_cache_hit` 检查这些哈希是否已存在于 `cached_block_hash_to_block` 中。在第一个请求时，没有找到命中。

![前缀缓存逻辑 - 第 1 部分](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/prefix_pt1.png)

然后我们调用 `allocate_slots`，它调用 `coordinator.cache_blocks`，将新的 `BlockHash` 条目与分配的 KV 块关联，并将它们记录在 `cached_block_hash_to_block` 中。

之后，前向传播将在我们上面分配的 KV 缓存块对应的分页 KV 缓存内存中填充 KV。

> 💡 经过多个引擎步骤后，它会分配更多 KV 缓存块，但这对我们的示例无关紧要，因为前缀在 `long_prefix` 之后立即分叉。

![前缀缓存逻辑 - 第 2 部分](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/prefix_pt2.png)

在具有相同前缀的第二次 `generate` 调用时，步骤 1-3 重复，但现在 `find_longest_cache_hit` 找到所有 `n` 个块的匹配（通过线性搜索）。引擎可以直接重用这些 KV 块。

![前缀缓存逻辑 - 第 3 部分](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/prefix_pt3.png)

如果原始请求仍然存活，这些块的引用计数将增加（例如增加到 2）。在这个示例中，第一个请求已经完成，所以块被释放回池中，它们的引用计数设置回 0。因为我们能够从 `cached_block_hash_to_block` 检索它们，我们知道它们是有效的（KV 缓存管理器的逻辑是这样设置的），所以我们只是再次从 `free_block_queue` 中移除它们。

> 📝 **高级说明**
> KV 缓存块只有在即将从 `free_block_queue`（从左侧弹出）重新分配时才会变得无效，并且我们发现该块仍然有关联的哈希并存在于 `cached_block_hash_to_block` 中。在那一刻，我们清除块的哈希并从 `cached_block_hash_to_block` 中删除其条目，确保它不能通过前缀缓存重用（至少不能用于那个旧前缀）。

这就是前缀缓存的要点：不要重新计算你已经见过的前缀——只需重用它们的 KV 缓存！

> 💡 如果你理解了这个示例，你也理解了分页注意力的工作原理。

前缀缓存默认启用。要禁用它：`enable_prefix_caching = False`。

### Guided Decoding（引导解码）- FSM

引导解码是一种技术，在每个解码步骤中，logits 受到基于语法的有限状态机的约束。这确保只有语法允许的 token 才能被采样。

这是一个强大的设置：你可以强制执行从正则语法（乔姆斯基 3 型，例如任意正则表达式模式）一直到上下文无关语法（2 型，涵盖大多数编程语言）的任何内容。

为了使这不那么抽象，让我们从最简单的示例开始，基于我们之前的代码：

```python
from vllm import LLM, SamplingParams
from vllm.sampling_params import GuidedDecodingParams

prompts = [
    "This sucks",
    "The weather is beautiful",
]

guided_decoding_params = GuidedDecodingParams(choice=["Positive", "Negative"])
sampling_params = SamplingParams(guided_decoding=guided_decoding_params)

def main():
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    outputs = llm.generate(prompts, sampling_params)

if __name__ == "__main__":
    main()
```

在我给出的玩具示例中（假设字符级分词）：在预填充时，FSM 掩码 logits 使得只有 "P" 或 "N" 是可行的。如果采样 "P"，FSM 移动到 "Positive" 分支；下一步只允许 "o"，依此类推。

![FSM](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/fsm.png)
*玩具示例 FSM*

**这在 vLLM 中如何工作：**

1. 在 LLM 引擎构造时，创建一个 `StructuredOutputManager`；它可以访问分词器并维护一个 `_grammar_bitmask` 张量。
2. 添加请求时，其状态设置为 `WAITING_FOR_FSM`，`grammar_init` 选择后端编译器（例如 `xgrammar` [7]；注意后端是第三方代码）。
3. 此请求的语法被异步编译。
4. 在调度期间，如果异步编译已完成，状态切换到 `WAITING`，`request_id` 被添加到 `structured_output_request_ids`；否则它被放入 `skipped_waiting_requests` 以在下一个引擎步骤重试。
5. 在调度循环之后（仍在调度内部），如果有 FSM 请求，`StructuredOutputManager` 要求后端准备/更新 `_grammar_bitmask`。
6. 前向传播产生 logits 后，xgr_torch_compile 的函数将位掩码扩展到词汇表大小（32 倍扩展比，因为我们使用 32 位整数）并将不允许的 logits 掩码为 –∞。
7. 采样下一个 token 后，请求的 FSM 通过 `accept_tokens` 前进。在视觉上，我们移动到 FSM 图上的下一个状态。

步骤 6 值得进一步澄清。

如果 `vocab_size = 32`，`_grammar_bitmask` 是单个整数；其二进制表示编码哪些 token 是允许的（"1"）vs 不允许的（"0"）。例如，"101…001" 扩展为长度为 32 的数组 `[1, 0, 1, …, 0, 0, 1]`；位置为 0 的 logits 设置为 –∞。对于更大的词汇表，使用多个 32 位字并相应地扩展/连接。后端（例如 `xgrammar`）负责使用当前 FSM 状态生成这些位模式。

> 📝 **注意**
> 这里的大部分复杂性隐藏在像 xgrammar 这样的第三方库中。

这是一个更简单的示例，vocab_size = 8 和 8 位整数（给那些喜欢我的图示的人）：

![FSM 示例](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/fsm2.png)
*玩具示例*

你可以通过传入所需的 `guided_decoding` 配置在 vLLM 中启用此功能。

### Speculative Decoding（推测解码）

在自回归生成中，每个新 token 都需要大型 LM 的前向传播。这很昂贵——每一步都重新加载并应用所有模型权重只是为了计算单个 token！（假设批次大小 == 1，一般是 `B`）

推测解码 [8] 通过引入一个较小的 draft LM（草稿模型）来加速这一过程。草稿模型廉价地提出 `k` 个 token。但我们最终不想从较小的模型采样——它只是用来猜测候选延续。大模型仍然决定什么是有效的。

以下是步骤：

1. **Draft（草稿）**：在当前上下文上运行小模型并提出 `k` 个 token
2. **Verify（验证）**：在上下文 + `k` 个草稿 token 上运行大模型一次。这为这 `k` 个位置加上一个额外位置产生概率（所以我们得到 `k+1` 个候选）
3. **Accept/reject（接受/拒绝）**：从左到右遍历 `k` 个草稿 token：
   - 如果大模型对草稿 token 的概率 ≥ 草稿的概率，接受它
   - 否则，以概率 `p_large(token)/p_draft(token)` 接受它
   - 在第一次拒绝时停止，或接受所有 `k` 个草稿 token
     - 如果所有 `k` 个草稿 token 都被接受，还可以从大模型"免费"采样额外的第 `(k+1)` 个 token（我们已经计算了那个分布）
     - 如果有拒绝，在该位置创建一个新的重新平衡分布（`p_large - p_draft`，最小值钳制为 0，归一化为和为 1）并从中采样最后一个 token

**为什么这有效**：虽然我们使用小模型来提出候选，但接受/拒绝规则保证在期望中序列的分布与我们逐 token 从大模型采样完全相同。这意味着推测解码在统计上等同于标准自回归解码——但可能快得多，因为单次大模型传播可以产生多达 `k+1` 个 token。

> 📝 **注意**
> 我推荐查看 [gpt-fast](https://github.com/meta-pytorch/gpt-fast) 获取简单实现，以及[原始论文](https://arxiv.org/abs/2302.01318)获取数学细节和与从完整模型采样等价的证明。

vLLM V1 不支持 LLM 草稿模型方法，而是实现了更快但不太准确的提议方案：n-gram、EAGLE [9] 和 Medusa [10]。

每个的一句话说明：

1. **n-gram**：取最后 `prompt_lookup_max` 个 token；在序列中找到先前的匹配；如果找到，提出该匹配后面的 `k` 个 token；否则减小窗口并重试直到 `prompt_lookup_min`

> 💡 当前实现返回**第一个**匹配后的 `k` 个 token。引入最近偏差并反转搜索方向（即最后一个匹配）感觉更自然？

2. **Eagle**：对大型 LM 进行"模型手术"——保留嵌入和 LM 头，用轻量级 MLP 替换 transformer 堆栈；将其微调为廉价草稿

3. **Medusa**：在大模型顶部（LM 头之前的嵌入）训练辅助线性头来并行预测下一个 `k` 个 token；使用这些头比运行单独的小 LM 更高效地提出 token

以下是如何使用 `ngram` 作为草稿方法在 vLLM 中调用推测解码：

```python
from vllm import LLM, SamplingParams

prompts = [
    "Hello, my name is",
    "The president of the United States is",
]

sampling_params = SamplingParams(temperature=0.8, top_p=0.95)
speculative_config={
    "method": "ngram",
    "prompt_lookup_max": 5,
    "prompt_lookup_min": 3,
    "num_speculative_tokens": 3,
}

def main():
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", speculative_config=speculative_config)
    outputs = llm.generate(prompts, sampling_params)

if __name__ == "__main__":
    main()
```

**这在 vLLM 中如何工作？**

**设置（在引擎构造期间）：**
1. 初始化设备：创建 `drafter`（草稿模型，例如 `NgramProposer`）和 `rejection_sampler`（部分用 Triton 编写）。
2. 加载模型：加载草稿模型权重（对于 n-gram 是空操作）。

**之后在 `generate` 函数中**（假设我们得到一个全新的请求）：

1. 使用大模型运行常规预填充步骤。
2. 前向传播和标准采样后，调用 `propose_draft_token_ids(k)` 从草稿模型采样 `k` 个草稿 token。
3. 将这些存储在 `request.spec_token_ids` 中（更新请求元数据）。
4. 在下一个引擎步骤，当请求在运行队列中时，将 `len(request.spec_token_ids)` 添加到"新 token"计数，以便 `allocate_slots` 为前向传播保留足够的 KV 块。
5. 将 `spec_token_ids` 复制到 `input_batch.token_ids_cpu` 以形成（上下文 + 草稿）token。
6. 通过 `_calc_spec_decode_metadata` 计算元数据（这从 `input_batch.token_ids_cpu` 复制 token，准备 logits 等），然后在草稿 token 上运行大模型前向传播。
7. 不是从 logits 进行常规采样，而是使用 `rejection_sampler` 从左到右接受/拒绝并产生 `output_token_ids`。
8. 重复步骤 2-7 直到满足停止条件。

内化这一点的最佳方式是启动调试器并逐步浏览代码库，但本节希望能给你一个初步印象。这些图示也是：

![草稿阶段](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/specdec_pt1.png)

![验证阶段和拒绝采样阶段](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/specdec_pt2.png)

### Disaggregated P/D（P/D 分离）

我之前已经暗示了 P/D 分离（预填充/解码分离）背后的动机。

预填充和解码有非常不同的性能特征（计算密集型 vs 内存带宽密集型），所以分离它们的执行是一个合理的设计。它提供了对延迟的更紧密控制——包括 `TTFT`（首 token 时间）和 `ITL`（token 间延迟）——更多内容在[基准测试](#基准测试与自动调优---延迟与吞吐量)部分。

在实践中，我们运行 `N` 个 vLLM 预填充实例和 `M` 个 vLLM 解码实例，根据实时请求组合自动扩展它们。预填充 worker 将 KV 写入专用的 KV 缓存服务；解码 worker 从中读取。这将长时间、突发的预填充与稳定、延迟敏感的解码隔离开来。

**这在 vLLM 中如何工作？**

为了清晰起见，下面的示例依赖于 `SharedStorageConnector`，这是一个用于说明机制的调试连接器实现。

> 💡 Connector 是 vLLM 处理实例之间 KV 交换的抽象。Connector 接口尚不稳定，有一些近期改进计划，将涉及更改，其中一些可能是破坏性的。

我们启动 2 个 vLLM 实例（GPU 0 用于预填充，GPU 1 用于解码），然后在它们之间传输 KV 缓存：

```python
import os
import time
from multiprocessing import Event, Process
import multiprocessing as mp

from vllm import LLM, SamplingParams
from vllm.config import KVTransferConfig

prompts = [
    "Hello, my name is",
    "The president of the United States is",
]

def run_prefill(prefill_done):
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    sampling_params = SamplingParams(temperature=0, top_p=0.95, max_tokens=1)
    ktc = KVTransferConfig(
        kv_connector="SharedStorageConnector",
        kv_role="kv_both",
        kv_connector_extra_config={"shared_storage_path": "local_storage"},
    )
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", kv_transfer_config=ktc)
    llm.generate(prompts, sampling_params)
    prefill_done.set()  # 通知解码实例 KV 缓存已准备好
    # 保持预填充节点运行以防解码节点未完成
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Script stopped by user.")

def run_decode(prefill_done):
    os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    sampling_params = SamplingParams(temperature=0, top_p=0.95)
    ktc = KVTransferConfig(
        kv_connector="SharedStorageConnector",
        kv_role="kv_both",
        kv_connector_extra_config={"shared_storage_path": "local_storage"},
    )
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", kv_transfer_config=ktc)
    prefill_done.wait()  # 阻塞等待来自预填充实例的 KV 缓存
    # 内部它会先获取 KV 缓存再开始解码循环
    outputs = llm.generate(prompts, sampling_params)

if __name__ == "__main__":
    prefill_done = Event()
    prefill_process = Process(target=run_prefill, args=(prefill_done,))
    decode_process = Process(target=run_decode, args=(prefill_done,))
    prefill_process.start()
    decode_process.start()
    decode_process.join()
    prefill_process.terminate()
```

> 📝 **注意**
> 我也尝试过 `LMCache` [11]，最快的生产就绪连接器（使用 NVIDIA 的 NIXL 作为后端），但它仍处于前沿，我遇到了一些 bug。由于它的大部分复杂性存在于外部仓库中，`SharedStorageConnector` 是更好的解释选择。

**这些是 vLLM 中的步骤：**

1. **实例化** — 在引擎构造期间，连接器在两个地方创建：
   - 在 worker 的初始化设备过程中（在初始化 worker 分布式环境函数下），角色为 "worker"
   - 在调度器构造函数中，角色为 "scheduler"

2. **缓存查找** — 当调度器处理来自 `waiting` 队列的预填充请求时（在本地前缀缓存检查之后），它调用连接器的 `get_num_new_matched_tokens`。这检查 KV 缓存服务器中外部缓存的 token。预填充在这里总是看到 0；解码可能有缓存命中。结果在调用 `allocate_slots` 之前添加到本地计数。

3. **状态更新** — 调度器然后调用 `connector.update_state_after_alloc`，记录有缓存的请求（对预填充是空操作）。

4. **元数据构建** — 在调度结束时，调度器调用 `meta = connector.build_connector_meta`：
   - 预填充添加所有 `is_store=True` 的请求（上传 KV）
   - 解码添加 `is_store=False` 的请求（获取 KV）

5. **上下文管理器** — 在前向传播之前，引擎进入 KV 连接器上下文管理器：
   - 进入时：调用 `kv_connector.start_load_kv`。对于解码，这从外部服务器加载 KV 并将其注入分页内存。对于预填充，这是空操作。
   - 退出时：调用 `kv_connector.wait_for_save`。对于预填充，这阻塞直到 KV 上传到外部服务器。对于解码，这是空操作。

这是一个可视化示例：

![P/D 分离](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/pd.png)
*P/D 分离*

> 📝 **附加说明**
> - 对于 `SharedStorageConnector`，"外部服务器"只是本地文件系统
> - 根据配置，KV 传输也可以逐层进行（在每个注意力层之前/之后）
> - 解码只在其请求的第一步加载外部 KV 一次；之后它在本地计算/存储

---

## 从 UniProcExecutor 到 MultiProcExecutor

有了核心技术，我们现在可以讨论扩展。

假设你的模型权重不再适合单个 GPU 的 VRAM。

第一个选项是使用张量并行在同一节点上的多个 GPU 之间分片模型（例如 `TP=8`）。如果模型仍然不适合，下一步是跨节点的流水线并行。

> 📝 **说明**
> - 张量并行（TP）通常优于流水线并行（PP）。（PP 通信的数据也比 TP 少，这也是事实。）
> - 我不涉及专家并行（EP），因为我们关注的是标准 transformer 而不是 MoE，也不涉及序列并行，因为 TP 和 PP 在实践中最常用。

在这个阶段，我们需要多个 GPU 进程（worker）和一个协调层来协调它们。这正是 `MultiProcExecutor` 提供的。

![MultiProcExecutor](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/multiprocexecutor.png)
*TP=8 设置中的 MultiProcExecutor（driver worker 是 rank 0）*

**这在 vLLM 中如何工作：**

1. `MultiProcExecutor` 初始化一个 `rpc_broadcast_mq` 消息队列（底层使用共享内存实现）。
2. 构造函数遍历 `world_size`（例如 `TP=8 ⇒ world_size=8`）并通过 `WorkerProc.make_worker_process` 为每个 rank 生成一个守护进程。
3. 对于每个 worker，父进程首先创建一个读取器和写入器管道。
4. 新进程运行 `WorkerProc.worker_main`，它实例化一个 worker（经历与 `UniprocExecutor` 相同的"初始化设备"、"加载模型"等）。
5. 每个 worker 确定它是 driver（TP 组中的 rank 0）还是普通 worker。每个 worker 设置两个队列：
   - `rpc_broadcast_mq`（与父进程共享）用于接收工作
   - `worker_response_mq` 用于发送响应
6. 在初始化期间，每个子进程通过管道将其 `worker_response_mq` 句柄发送给父进程。一旦全部收到，父进程解除阻塞——这完成了协调。
7. Worker 然后进入忙循环，阻塞在 `rpc_broadcast_mq.dequeue`。当工作项到达时，它们执行它（就像在 `UniprocExecutor` 中一样，但现在有 TP/PP 特定的分区工作）。结果通过 `worker_response_mq.enqueue` 发送回去。
8. 在运行时，当请求到达时，`MultiProcExecutor` 将其入队到 `rpc_broadcast_mq`（非阻塞）给所有子 worker。然后它等待指定输出 rank 的 `worker_response_mq.dequeue` 来收集最终结果。

从引擎的角度来看，什么都没有改变——所有这些多进程复杂性都通过调用模型执行器的 `execute_model` 抽象掉了。

- 在 `UniProcExecutor` 情况下：execute_model 直接导致在 worker 上调用 execute_model
- 在 `MultiProcExecutor` 情况下：execute_model 间接导致通过 `rpc_broadcast_mq` 在每个 worker 上调用 execute_model

此时，我们可以使用相同的引擎接口运行资源允许的任意大模型。

下一步是扩展：启用数据并行（`DP > 1`）跨节点复制模型，添加轻量级 DP 协调层，引入跨副本的负载均衡，并在前面放置一个或多个 API 服务器来处理传入流量。

---

## 分布式系统服务 vLLM

有很多方式来设置服务基础设施，但为了具体，这里有一个示例：假设我们有两个 H100 节点，想要在它们上运行四个 vLLM 引擎。

如果模型需要 `TP=4`，我们可以这样配置节点：

![服务器配置](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/server_setup.png)
*2 个 8xH100 节点的服务器配置（1 个无头，1 个 API 服务器）*

在第一个节点上，以无头模式（无 API 服务器）运行引擎，使用以下参数：

```bash
vllm serve <model-name>
  --tensor-parallel-size 4
  --data-parallel-size 4
  --data-parallel-size-local 2
  --data-parallel-start-rank 0
  --data-parallel-address <master-ip>
  --data-parallel-rpc-port 13345
  --headless
```

在另一个节点上运行相同的命令，稍作调整：
- 没有 `--headless`
- 修改 DP 起始 rank

```bash
vllm serve <model-name>
  --tensor-parallel-size 4
  --data-parallel-size 4
  --data-parallel-size-local 2
  --data-parallel-start-rank 2
  --data-parallel-address <master-ip>
  --data-parallel-rpc-port 13345
```

> 📝 **注意**
> 这假设网络已配置，所有节点都可以到达指定的 IP 和端口。

**这在 vLLM 中如何工作？**

### 在无头服务器节点上

在无头节点上，`CoreEngineProcManager` 启动 2 个进程（根据 `--data-parallel-size-local`），每个运行 `EngineCoreProc.run_engine_core`。每个函数创建一个 `DPEngineCoreProc`（引擎核心）然后进入其忙循环。

`DPEngineCoreProc` 初始化其父类 `EngineCoreProc`（`EngineCore` 的子类），它：

1. 创建 `input_queue` 和 `output_queue`（`queue.Queue`）
2. 使用 `DEALER` ZMQ 套接字（异步消息库）与另一个节点上的前端进行初始握手，并接收协调地址信息
3. 初始化 DP 组（例如使用 NCCL 后端）
4. 使用 `MultiProcExecutor` 初始化 `EngineCore`（如前所述在 4 个 GPU 上 `TP=4`）
5. 创建 `ready_event`（`threading.Event`）
6. 启动运行 `process_input_sockets(…, ready_event)` 的输入守护线程（`threading.Thread`）。类似地启动输出线程
7. 仍在主线程中，等待 `ready_event` 直到所有 4 个进程（跨 2 个节点）的所有输入线程完成协调握手，最终执行 `ready_event.set()`
8. 一旦解除阻塞，向前端发送带有元数据（例如分页 KV 缓存内存中可用的 `num_gpu_blocks`）的"ready"消息
9. 主线程、输入线程和输出线程然后进入各自的忙循环

**TL;DR**：我们最终有 4 个子进程（每个 DP 副本一个），每个运行主线程、输入线程和输出线程。它们与 DP 协调器和前端完成协调握手，然后每个进程的所有三个线程在稳态忙循环中运行。

![分布式系统](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/dpenginecoreproc.png)
*运行 4 个 DPEngineCoreProc 的 4 个 DP 副本的分布式系统*

**当前稳态：**

- **输入线程** — 阻塞在输入套接字上直到请求从 API 服务器路由过来；收到后，它解码有效载荷，通过 `input_queue.put_nowait(...)` 入队工作项，然后返回阻塞在套接字上
- **主线程** — 在 `input_queue.get(...)` 上唤醒，将请求馈送到引擎；`MultiProcExecutor` 运行前向传播并将结果入队到 `output_queue`
- **输出线程** — 在 `output_queue.get(...)` 上唤醒，通过输出套接字将结果发送回 API 服务器，然后恢复阻塞

**附加机制：**

- **DP 波计数器** — 系统跟踪"波"；当所有引擎变为空闲时它们静止，当新工作到达时计数器递增（用于协调/指标）
- **控制消息** — API 服务器可以发送的不仅仅是推理请求（例如中止和实用/控制 RPC）
- **锁步虚拟步骤** — 如果任何 DP 副本有工作，所有副本执行前向步骤；没有请求的副本执行虚拟步骤以参与所需的同步点（避免阻塞活动副本）

> 💡 **锁步澄清**
> 这实际上只对 MoE 模型是必需的，其中专家层形成 EP 或 TP 组，而注意力层仍然是 DP。目前它总是与 DP 一起完成——这只是因为"内置"非 MoE DP 的用途有限，因为你可以只运行多个独立的 vLLM 并以正常方式在它们之间进行负载均衡。

### 在 API 服务器节点上

我们实例化一个 `AsyncLLM` 对象（LLM 引擎的 asyncio 包装器）。内部这创建一个 `DPLBAsyncMPClient`（数据并行、负载均衡、异步、多进程客户端）。

在 `MPClient` 的父类内部，`launch_core_engines` 函数运行并：

1. 创建用于启动握手的 ZMQ 地址（如在无头节点上看到的）
2. 生成一个 `DPCoordinator` 进程
3. 创建一个 `CoreEngineProcManager`（与无头节点上相同）

在 `AsyncMPClient`（`MPClient` 的子类）内部，我们：

1. 创建 `outputs_queue`（`asyncio.Queue`）
2. 创建一个 asyncio 任务 `process_outputs_socket`，它通过输出套接字与所有 4 个 `DPEngineCoreProc` 的输出线程通信并写入 `outputs_queue`
3. 随后从 `AsyncLLM` 创建另一个 asyncio 任务 `output_handler`，从这个队列读取并最终将信息发送到 `create_completion` 函数

在 `DPAsyncMPClient` 内部，我们创建一个 asyncio 任务 `run_engine_stats_update_task`，它与 DP 协调器通信。

DP 协调器在前端（API 服务器）和后端（引擎核心）之间进行调解。它：

- 定期向前端的 `run_engine_stats_update_task` 发送负载均衡信息（队列大小、等待/运行请求）
- 处理来自前端的 `SCALE_ELASTIC_EP` 命令，动态更改引擎数量（仅适用于 Ray 后端）
- 向后端发送 `START_DP_WAVE` 事件（由前端触发时）并报告波状态更新

总结一下，前端（`AsyncLLM`）运行几个 asyncio 任务（记住：并发，不是并行）：

- 一类任务通过 `generate` 路径处理输入请求（每个新客户端请求生成一个新的 asyncio 任务）
- 两个任务（`process_outputs_socket`、`output_handler`）处理来自底层引擎的输出消息
- 一个任务（`run_engine_stats_update_task`）维护与 DP 协调器的通信：发送波触发器、轮询 LB 状态和处理动态扩展请求

最后，主服务器进程创建一个 FastAPI 应用并挂载端点如 `OpenAIServingCompletion` 和 `OpenAIServingChat`，它们暴露 `/completion`、`/chat/completion` 等。然后通过 Uvicorn 提供服务。

所以，把它们放在一起，这是完整的请求生命周期！

你从终端发送：

```bash
curl -X POST http://localhost:8000/v1/completions -H "Content-Type: application/json" -d '{
  "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "prompt": "The capital of France is",
  "max_tokens": 50,
  "temperature": 0.7
}'
```

**接下来发生什么：**

1. 请求到达 API 服务器上 `OpenAIServingCompletion` 的 `create_completion` 路由
2. 函数异步分词提示词，并准备元数据（请求 ID、采样参数、时间戳等）
3. 然后调用 `AsyncLLM.generate`，它遵循与同步引擎相同的流程，最终调用 `DPAsyncMPClient.add_request_async`
4. 这反过来调用 `get_core_engine_for_request`，它根据 DP 协调器的状态在引擎之间进行负载均衡（选择得分最低/负载最低的那个：`score = len(waiting) * 4 + len(running)`）
5. `ADD` 请求被发送到所选引擎的 `input_socket`
6. 在该引擎：
   - **输入线程** — 解除阻塞，从输入套接字解码数据，并将工作项放入主线程的 `input_queue`
   - **主线程** — 在 `input_queue` 上解除阻塞，将请求添加到引擎，并重复调用 `engine_core.step()`，将中间结果入队到 `output_queue` 直到满足停止条件
   > 💡 提醒：`step()` 调用调度器、模型执行器（它反过来可以是 `MultiProcExecutor`！）等。我们已经看过这个了！
   - **输出线程** — 在 `output_queue` 上解除阻塞并通过输出套接字发送结果
7. 这些结果触发 `AsyncLLM` 输出 asyncio 任务（`process_outputs_socket` 和 `output_handler`），它们将 token 传播回 FastAPI 的 `create_completion` 路由
8. FastAPI 附加元数据（完成原因、logprobs、使用信息等）并通过 Uvicorn 返回 `JSONResponse` 到你的终端！

就这样，你的补全回来了——整个分布式机制隐藏在一个简单的 `curl` 命令后面！:) 太有趣了！！！

> 📝 **附加说明**
> - 添加更多 API 服务器时，负载均衡在 OS/套接字级别处理。从应用程序的角度来看，没有什么重大变化——复杂性被隐藏了
> - 使用 Ray 作为 DP 后端，你可以暴露一个 URL 端点（`/scale_elastic_ep`），启用引擎副本数量的自动上下扩展

---

## 基准测试与自动调优 - 延迟与吞吐量

到目前为止，我们一直在分析"气体粒子"——请求如何流经引擎/系统的内部。现在是时候缩小视角，从整体上看系统，并问：我们如何衡量推理系统的性能？

在最高层面有两个竞争指标：

1. **延迟（Latency）** — 从提交请求到返回 token 的时间
2. **吞吐量（Throughput）** — 系统每秒可以生成/处理的 token/请求数量

**延迟**对交互式应用最重要，用户在等待响应。

**吞吐量**在离线工作负载中很重要，如用于预训练/后训练运行的合成数据生成、数据清理/处理，以及一般的任何类型的离线批量推理作业。

在解释为什么延迟和吞吐量竞争之前，让我们定义一些常见的推理指标：

| 指标 | 定义 |
|------|------|
| `TTFT`（首 token 时间） | 从请求提交到收到第一个输出 token 的时间 |
| `ITL`（token 间延迟） | 两个连续 token 之间的时间（例如从 token i-1 到 token i） |
| `TPOT`（每输出 token 时间） | 请求中所有输出 token 的平均 ITL |
| `Latency / E2E`（端到端延迟） | 处理请求的总时间，即 TTFT + 所有 ITL 之和，或等价地，提交请求和收到最后一个输出 token 之间的时间 |
| `Throughput`（吞吐量） | 每秒处理的总 token（输入、输出或两者），或者每秒请求数 |
| `Goodput`（有效吞吐量） | 满足服务级别目标（SLO）的吞吐量，如最大 TTFT、TPOT 或 e2e 延迟。例如，只计算满足这些 SLO 的请求的 token |

![延迟图](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/latency_diagram.png)
*TTFT、ITL、E2E 延迟*

这是一个解释这两个指标竞争性质的简化模型。

> 💡 **假设**：权重 I/O 而非 KV 缓存 I/O 占主导；即我们处理的是短序列。

当查看批次大小 `B` 如何影响单个解码步骤时，权衡变得清晰。当 `B ↓` 趋向 1 时，ITL 下降：每步工作更少，token 不与其他 token "竞争"。当 `B ↑` 趋向无穷大时，ITL 上升，因为我们每步做更多 FLOP——但吞吐量提高（直到达到峰值性能），因为权重 I/O 在更多 token 之间摊销。

Roofline 模型有助于理解这一点：在饱和批次 `B_sat` 以下，步骤时间由 HBM 带宽主导（逐层将权重流式传输到片上内存），所以步骤延迟几乎是平的——计算 1 个 vs 10 个 token 可能需要相似的时间。超过 `B_sat`，内核变成计算密集型，步骤时间大致随 `B` 增长；每个额外的 token 都增加 ITL。

![Roofline 性能模型](./Inside%20vLLM_%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System%20-%20Aleksa%20Gordić_files/roofline.png)
*Roofline 性能模型*

> 📝 **注意**
> 对于更严格的处理，我们必须考虑内核自动调优：随着 `B` 增长，运行时可能会切换到对该形状更高效的内核，改变实现的性能 `P_kernel`。步骤延迟是 `t = FLOPs_step / P_kernel`，其中 `FLOPs_step` 是步骤中的工作。你可以看到，当 `P_kernel` 达到 `P_peak` 时，每步更多的计算将直接导致延迟增加。

### 如何在 vLLM 中进行基准测试

vLLM 提供了 `vllm bench {serve,latency,throughput}` CLI，它包装了 vllm/benchmarks/{server,latency,throughput}.py。

以下是脚本的功能：

- **latency** — 使用短输入（默认 32 个 token）并用小批次（默认 8）采样 128 个输出 token。它运行几次迭代并报告批次的 e2e 延迟。
- **throughput** — 一次性提交固定的提示词集（默认：1000 个 ShareGPT 样本）（即 `QPS=Inf` 模式），并报告整个运行的输入/输出/总 token 和每秒请求数。
- **serve** — 启动 vLLM 服务器并通过从泊松（或更一般地，伽马）分布采样请求到达间隔时间来模拟真实世界工作负载。它在时间窗口内发送请求，测量我们讨论过的所有指标，并可以选择强制执行服务器端最大并发（通过信号量，例如将服务器限制为 64 个并发请求）。

以下是如何运行延迟脚本的示例：

```bash
vllm bench latency
  --model <model-name>
  --input-tokens 32
  --output-tokens 128
  --batch-size 8
```

> 💡 CI 中使用的基准测试配置位于 `.buildkite/nightly-benchmarks/tests` 下。

还有一个自动调优脚本，它驱动 serve 基准测试来找到满足目标 SLO 的参数设置（例如，"在保持 p99 e2e < 500 ms 的同时最大化吞吐量"），返回建议的配置。

---

## 结语

我们从基本的引擎核心（`UniprocExecutor`）开始，添加了推测解码和前缀缓存等高级特性，扩展到 `MultiProcExecutor`（`TP/PP > 1`），最后扩展出去，将所有内容包装在异步引擎和分布式服务栈中——最后介绍了如何测量系统性能。

vLLM 还包括我跳过的专门处理。例如：

- **多样化硬件后端**：TPU、AWS Neuron（Trainium/Inferentia）等
- **架构/技术**：`MLA`、`MoE`、编码器-解码器（例如 Whisper）、池化/嵌入模型、`EPLB`、`m-RoPE`、`LoRA`、`ALiBi`、无注意力变体、滑动窗口注意力、多模态 LM 和状态空间模型（例如 Mamba/Mamba-2、Jamba）
- **TP/PP/SP**
- **混合 KV 缓存逻辑**（Jenga）、更复杂的采样方法如束搜索等
- **实验性**：异步调度

好消息是，这些大多与上述主流程正交——你几乎可以把它们当作"插件"（实际上当然有一些耦合）。

我喜欢理解系统。话虽如此，在这个高度上分辨率确实受到了影响。在接下来的文章中，我将放大特定子系统并深入细节。

> 💡 **联系方式**
> 如果你在文章中发现任何错误，请私信我——欢迎在 [X](https://x.com/gordic_aleksa) 或 [LinkedIn](https://www.linkedin.com/in/aleksagordic/) 上给我发消息，或通过[匿名反馈](https://docs.google.com/forms/d/1z1fEirrN2xtGxAsJvptpM7yV4ByT5SF25S-XiMPrXNA/edit)。

---

## 致谢

非常感谢 [Hyperstack](https://www.hyperstack.cloud/) 在过去一年为我的实验提供 H100！

感谢 Nick Hill（vLLM 核心贡献者，RedHat）、Mark Saroufim（PyTorch）、Kyle Krannen（NVIDIA，Dynamo）和 Ashish Vaswani 阅读本博客文章的预发布版本并提供反馈！

---

## 参考文献

1. vLLM https://github.com/vllm-project/vllm
2. "Attention Is All You Need", https://arxiv.org/abs/1706.03762
3. "Efficient Memory Management for Large Language Model Serving with PagedAttention", https://arxiv.org/abs/2309.06180
4. "DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model", https://arxiv.org/abs/2405.04434
5. "Jenga: Effective Memory Management for Serving LLM with Heterogeneity", https://arxiv.org/abs/2503.18292
6. "Orca: A Distributed Serving System for Transformer-Based Generative Models", https://www.usenix.org/conference/osdi22/presentation/yu
7. "XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models", https://arxiv.org/abs/2411.15100
8. "Accelerating Large Language Model Decoding with Speculative Sampling", https://arxiv.org/abs/2302.01318
9. "EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty", https://arxiv.org/abs/2401.15077
10. "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads", https://arxiv.org/abs/2401.10774
11. LMCache, https://github.com/LMCache/LMCache
