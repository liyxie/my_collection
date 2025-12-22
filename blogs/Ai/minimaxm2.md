# miniMax M2本地vllm部署记录

## 结论

sglang部署失败，A800显卡不支持FB8精度，强制使用FB16显存翻倍，320G不够，可以尝试 AWQ/GPTQ 版本（huggingface有，未尝试）；

vllm 新版支持 minimaxm2， vLLM 会自动处理 FP8/MoE 分片与降级；

4张A800（80G）用vllm运行成功，上下文输入长度降到158560，目前设置了131072；

## 前言

**此为20251209截止信息**

### **minimax m2模型信息**

- 官方模型：230B参数，激活参数10B，FB8精度，最大200K上下文长度，模型文件230GB左右；
-  `MiniMax-M2` 是一个交错思考模型，思考内容会输出正文中使用使用 `<think>... </think>` 格式包裹，必须确保以原始格式传递回历史内容，没有思考内容会影响模型性能；
- 官方教程支持vllm、sglang、MLX、Transformers部署，本文章只记录sglang和vllm；

### **部署服务器信息**

- 4张A800 (A800-SXM4-80GB)，显存总共320G；
- CUDA 12.8、torch 2.9.0、python 3.12.3、vllm 0.13.0rc2.dev173+gc881db364.precompiled；
- Linux Ubuntu；

## VLLM部署

### 模型下载

使用huggingface或者modelscope下载，huggingface慢的话可以配代理，具体看命令看这2个平台教程；

**也可以vllm或者sglang运行时自动下载**，这2个框架默认从huggingface下载；

模型下载后默认存放路径是 home/用户名/.cache/ 下各自目录；

注意模型较大，下载命令要指定断点续传（一般默认有）；ssh操作的最好后台下载；

### 配置vllm库

```bash
# 准备好python环境，文章用python3.12.3，最好3.11或者3.10

# 创建一个目录，创建虚拟环境
cd minimax_vllm
python -m venv .venv
source .venv/bin/activate

# 安装 PyTorch（CUDA 12.x），版本自行查看CUDA官网和PyTorch教程，也可以直接问ai，一定要适配
pip install -U pip setuptools wheel
pip install torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu121
# 验证
python - << 'EOF'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("gpu count:", torch.cuda.device_count())
EOF

# 安装vllm依赖 最好官方 nightly 版，支持 MiniMax-M2
pip install -U vllm --pre --extra-index-url https://wheels.vllm.ai/nightly

# 或者直接下vllm源码
git clone https://github.com/vllm-project/vllm.git
VLLM_USE_PRECOMPILED=1 uv pip install --editable .
```

### 运行

```bash
# 准备
# 先查看显卡情况
nvidia-smi
# 确保显存足够，如果多卡情况要用其中几张的，可以指定要用的卡序号
# 以下为 设置1、3、4、5 GPU 对当前进程可见，其他的0、2显卡不用
export CUDA_VISIBLE_DEVICES=1,3,4,5
# 确保你的端口可使用
```

```bash
# 该命令为nohup后台运行，输出到日志文件 vllm_output.log
# 第一次运行最好直接跑，不用nohup，方便观察输出，去掉nohup开头和最后一段即可
nohup vllm serve \
/home/xxx/.cache/huggingface/hub/models--MiniMaxAI--MiniMax-M2/snapshots/f62f643a718e8be697da52e7d5d8b8d12b991001 \
--tensor-parallel-size 4 \
--tool-call-parser minimax_m2 \
--reasoning-parser minimax_m2_append_think \
--enable-auto-tool-choice \
--port 8100 \
--trust-remote-code \
--max-model-len 131072 \
--api-key yuxinda \
> vllm_output.log 2>&1 &

# /home/cjl/.cache/huggingface/hub/models--MiniMaxAI--MiniMax-M2/snapshots/f62f643a718e8be697da52e7d5d8b8d12b991001 是我的模型路径，因为sglang下过，有改过内部文件，直接用ID的话vllm不识别，最好使用 MiniMaxAI/MiniMax-M2 代替；
# --tensor-parallel-size 4 用4张卡，具体那些卡可以屏蔽显卡实现
# --reasoning-parser minimax_m2_append_think 使用推理解析器，可以换 minimax_m2
# --port 8100 端口
# --max-model-len 131072 设置上下文长度
# --api-key yuxinda 设置key
```



## 注意

### Huggingface 网络问题

如果遇到网络问题，可以设置代理后再进行拉取。

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### MiniMax-M2 model is not currently supported

该 vLLM 版本过旧，请升级到最新版本。

### torch.AcceleratorError: CUDA error: an illegal memory access was encountered

在启动参数添加 `--compilation-config "{\"cudagraph_mode\": \"PIECEWISE\"}"` 可以解决。例如：

```bash
SAFETENSORS_FAST_GPU=1 vllm serve \
    MiniMaxAI/MiniMax-M2 --trust-remote-code \
    --enable_expert_parallel --tensor-parallel-size 8 \
    --enable-auto-tool-choice --tool-call-parser minimax_m2 \
    --reasoning-parser minimax_m2_append_think \
    --compilation-config "{\"cudagraph_mode\": \"PIECEWISE\"}"
```

### think思考内容

think思考内容会放在conten里面<think></think>包裹，openaiSDK暂时还找不到分离方法，只能自己代码实现；

官方说法

```
重要提示： MiniMax-M2 是一个交错思考模型。因此，在使用它时，必须保留助手轮次中的思考内容在历史消息中。在模型的输出内容中，我们使用 <think>... </think> 格式包裹助手的思考内容。在使用模型时，必须确保以原始格式传递回历史内容。不要移除 <think>... </think> 部分，否则会负面影响模型的性能。
```

openaiSDK的 `client.chat.completions.create()`中有个 `extra_body={"reasoning_split": True}`参数可以将思考内容分离到 reasoning_details 字段，但这个只对官方的api有效，但这是 **MiniMax 云服务的扩展行为，不是 OpenAI 标准 API**；

**目前情况应该是，minimaxm2模型需要回传think内容才能最大限度发挥模型能力，而各大工具（claudecode、codex等）、api平台（OpenRouter）和框架对模型的结构化输出处理模式不同，为了避免think没回传影响性能，就把think放在content里面确保回传；**

#### 参考

- [使用MiniMax-M2模型的OpenAI兼容接口返回的print(response.choices[0\].message.content)中有thinking的内容，能不能不返回thinking的内容 · Issue #18 · MiniMax-AI/MiniMax-M2](https://github.com/MiniMax-AI/MiniMax-M2/issues/18)
- [why is reasoning-parser needed in sglang or vllm as there is actually no reasoning_content in output? · Issue #1 · MiniMax-AI/MiniMax-M2](https://github.com/MiniMax-AI/MiniMax-M2/issues/1)
- [OpenAI API 兼容 - MiniMax 开放平台文档中心](https://platform.minimaxi.com/docs/api-reference/text-openai-api)
- [MiniMaxAI/MiniMax-M2 ·交错思维的歧义](https://huggingface.co/MiniMaxAI/MiniMax-M2/discussions/38)



### 端口占用问题

```
OSError: [Errno 98] Address already in use
```

```bash
# 查找8000端口进程，杀死进程
sudo netstat -tulnp | grep :8000
kill -9 12345

# 或者更换端口
```

### 本地模型识别错误

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for ModelConfig
  Value error, Invalid repository ID or local directory specified: '/home/1/.cache/huggingface/hub/models--MiniMaxAI--MiniMax-M2'.
Please verify the following requirements:
1. Provide a valid Hugging Face repository ID.
2. Specify a local directory that contains a recognized configuration file.
   - For Hugging Face models: ensure the presence of a 'config.json'.
   - For Mistral models: ensure the presence of a 'params.json'.

```

`vLLM` 需要以下两种类型的模型路径：

1. **Hugging Face Repository ID (推荐):** 例如 `"MiniMaxAI/MiniMax-M2"`。在这种情况下，vLLM 会根据这个 ID 自动去 Hugging Face Hub 下载模型，并将其缓存到正确的内部结构中，或者复用已有的正确缓存。
2. **直接的本地模型目录:** 这个目录必须是模型文件（例如 `config.json`, `pytorch_model.bin` 等）所在的**最顶层目录**。也就是说，`config.json` 必须直接位于你指定的路径下，而不是某个子目录下。

本地模型一般需要精准到id文件夹

### 信任本地模型错误

一般指定本地路径会出现

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for ModelConfig
  Value error, The repository /home/cjl/.cache/huggingface/hub/models--MiniMaxAI--MiniMax-M2/snapshots/f62f643a718e8be697da52e7d5d8b8d12b991001 contains custom code which must be executed to correctly load the model.
...
Please pass the argument `trust_remote_code=True` to allow custom code to be run.
```

1. **"contains custom code"：** 这意味着 `MiniMaxAI/MiniMax-M2` 这个模型（或它的特定实现）不仅仅是一个标准的预训练模型结构，它在 Hugging Face 仓库中包含了一些自定义的 Python 代码（Custom Code）。
2. **安全考虑：** Hugging Face 的 `transformers` 库（vLLM 在底层也依赖它来加载模型）为了安全起见，默认情况下不会执行从远程或未知来源加载的自定义代码。这是为了防止模型仓库中包含恶意代码，在用户加载模型时被执行。
3. **解决方案提示：** 错误信息明确指示你需要传递 **`trust_remote_code=True`** 这个参数，以明确表示你信任这个模型仓库中的代码，并允许其执行。

**解决方案：**

需要在 `vllm serve` 命令中添加 `--trust-remote-code` 标志。

### 显存不足

```
ValueError: Free memory on device (37.95/79.25 GiB) on startup is less than desired GPU memory utilization (0.9, 71.33 GiB). Decrease GPU memory utilization or reduce GPU memory used by other processes.
······
RuntimeError: Engine core initialization failed. See root cause above. Failed core proc(s): {}

```

这个错误是由于 **GPU 内存不足** 导致的。vLLM 在初始化引擎时尝试为模型分配 GPU 内存，但是发现当前可用的空闲显存达不到其预期的最低要求。

查看nvidia-smi，关闭一些进程或者屏蔽一些正在用的显卡

或者降低 --gpu-memory-utilization 0.45 

### **KV Cache 内存不足以支持模型的最大序列长度。**

```
ValueError: To serve at least one request with the models's max seq len (196608), (11.62 GiB KV cache is needed, which is larger than the available KV cache memory (9.38 GiB). Based on the available memory, the estimated maximum model length is 158560. Try increasing `gpu_memory_utilization` or decreasing `max_model_len` when initializing the engine.

```

1. **模型的最大序列长度 (max_seq_len)**: 196608 tokens。这是一个 *非常大* 的值。MiniMax-M2 是一个上下文窗口很长的模型。
2. **KV Cache 所需内存**: 为了支持这个 196608 的最大序列长度，vLLM 计算出每个 GPU 至少需要 **11.62 GiB** 的 KV Cache 内存。
3. **实际可用的 KV Cache 内存**: 然而，当前 vLLM 在每个 GPU 上只能分配到 **9.38 GiB** 的 KV Cache 内存。
4. **不匹配**: `9.38 GiB` < `11.62 GiB`，所以 vLLM 无法启动。
5. **vLLM 的建议**: "Try increasing `gpu_memory_utilization` or decreasing `max_model_len`."
6. **估算的最大序列长度**: vLLM 根据当前可用的 9.38 GiB KV Cache 内存，估算出它能支持的最大序列长度是 **158560**。

**解决方案：**

1. **降低 `max_model_len` (推荐的首选方法)**
2. **增加 `gpu_memory_utilization` (备选或辅助方法)**

```
--max-model-len 158560

--gpu-memory-utilization 0.95
```



## 参考

**模型仓库**

- [MiniMax-M2 · 模型库](https://www.modelscope.cn/models/MiniMax/MiniMax-M2/summary)
- [MiniMaxAI/MiniMax-M2 · Hugging Face](https://huggingface.co/MiniMaxAI/MiniMax-M2)
- [MiniMax-AI/MiniMax-M2: MiniMax-M2, a model built for Max coding & agentic workflows.](https://github.com/MiniMax-AI/MiniMax-M2)

**vllm官方教程**

- [MiniMax-M2 Usage Guide - vLLM Recipes](https://docs.vllm.ai/projects/recipes/en/latest/MiniMax/MiniMax-M2.html)

[MiniMaxAI/MiniMax-M2 ·讨论](https://huggingface.co/MiniMaxAI/MiniMax-M2/discussions)
