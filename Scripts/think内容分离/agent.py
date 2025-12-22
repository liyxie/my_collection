# 初始化 think 标签提取器
think_extractor = ThinkTagExtractor()

response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=node.list_tools(),
    tool_choice="auto",
    stream=True,
)

for chunk in response:
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    # 处理常规文本（可能包含 <think>...</think> 标签）
    if hasattr(delta, "content") and delta.content is not None and len(delta.content) > 0:
        # 思考内容字段提取
        text_to_render, thinking_text = think_extractor.process(delta.content)
        if thinking_text:
            reasoning_content += thinking_text
            # 流式传输前端
            self.queue_call({"think": thinking_text})

        # 内容字段提取
        if text_to_render:
            content += text_to_render
            # 流式传输前端
            self.queue_call({"content": text_to_render})